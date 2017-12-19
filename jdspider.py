#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2017-12-04 22:45:20
# Project: taobao

from pyquery import PyQuery as pq
from pyspider.libs.base_handler import *
import string
import urlparse
import urllib
import time
from pyspider.database.mysql.MySQLHandle import SQL

NUMBER_START = 1
NUMBER_END = 100

#self.crawl(url, callback=self.list_page, itag=1, fetch_type='js', save={"category":each.attr.title, 'keyword':params['keyword'], "page":page}

class Handler(BaseHandler):


    crawl_config = {
        'itag': 'v163', 'connect_timeout':120,
        'headers' : {'Connection':'keep-alive','Accept-Encoding':'gzip, deflate, br','Accept-Language':'zh-CN,zh;q=0.8','content-type':'application/x-www-form-urlencoded','Referer':'http://channel.jd.com/men.html','User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}
    }

    @every(minutes= 60 * 24)
    def on_start(self):

        self.crawl('http://channel.jd.com/men.html', callback=self.category_page)

    def get_headers(self, response):
        headers = {}
        referer_url = response.url + '#' + str(time.time())
        headers['User-Agent'] = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE) '
        headers['Accept'] = '*/*'
        headers['Accept-Language'] = 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2'
        headers['Accept-Encoding'] = 'gzip, deflate'
        headers['Referer'] = referer_url
        headers['X-Requested-With'] = 'XMLHttpRequest'
        return headers

    @config(age=60 * 60 * 24)
    def category_page(self, response):

        for each in response.doc('.fore3 ul a').items():
            query = urlparse.urlparse(each.attr.href).query
            params=  dict([(k,v[0]) for k,v in urlparse.parse_qs(query).items()])
            page = NUMBER_START
            while page <= NUMBER_END:
                s = ((page + 1) / 2 - 1) * 60 + 1
                url = each.attr.href + '&psort=3&page=' + str(page) + '&s=' + str(s) + '&click=0'
                page += 2
                headers = self.get_headers(response)
                self.crawl(url,headers = headers ,cookies=response.cookies, callback=self.list_page, fetch_type='js', save={"category":each.attr.title, 'keyword':params['keyword'], "page":page });


    def list_page(self, response):
        i = 1
        category = response.save['category']
        ##获取下一半图片的pid数组
        show_items=[]
        ##保存结果
        results = []

        for each in response.doc('#J_goodsList ul li[class="gl-item"]').items():
            obj = {}
            data_pid = each.attr('data-pid')
            ##保存data_pid，以便作为获取下一半图片的参数
            if data_pid is not None:
                show_items.append(string.atoi(data_pid))
            img_title = pq(each)('div[class="p-img"] a').attr.title
            img_src = pq(each)('div[class="p-img"] a>img').attr.src
            ##获取延时加载的图片地址代替src的地址
            if img_src is None:
                data_lazy_img= pq(each)('div[class="p-img"] a>img').attr('data-lazy-img')
                if data_lazy_img is not None:
                    img_src = 'http:' + data_lazy_img
                else:
                    continue
            #print i, img_title,img_src
            obj['url'] = img_src
            obj['title'] = img_title
            obj['category'] = category
            results.append(obj)
            i += 1


        ####获取剩下的一半图片
        ##用于获取另一半图片的参数
        keyword =  response.save['keyword']
        page = response.save['page']
        ##转化为字符串
        show_items_string = ','.join(str(i) for i in show_items)
        url = 'http://search.jd.com/s_new.php?keyword=' + keyword + '&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=' + keyword +'&page=' + str(page + 1) +'&s=26&scrolling=y&tpl=3_L&show_items=' + show_items_string
        ##headers
        headers = self.get_headers(response)
        self.crawl(url,cookies=response.cookies,headers = headers, callback=self.page_detail, save={'results':results, 'category':category})

    def page_detail(self, response):
        results = response.save['results']
        category = response.save['category']

        i = 1
        for each in response.doc('li[class="gl-item"]').items():
            obj = {}
            img_src = pq(each)('div[class="p-img"] a>img').attr.src
            img_title = pq(each)('div[class="p-img"] a').attr.title
            if img_src is None:
                data_lazy_img= pq(each)('div[class="p-img"] a>img').attr('data-lazy-img')
                if data_lazy_img is not None:
                    img_src = 'http:' + data_lazy_img
                else:
                    continue
            #print i,img_src
            obj['url'] = img_src
            obj['title'] = img_title
            obj['category'] = category
            results.append(obj)
            #i +=1
        return results



    def on_result(self,result):
        if not result:
            return
        sql = SQL()
        i= 1
        for each in result:
            print i, each
            sql.insert('table_jingdong',**each)
            i += 1
