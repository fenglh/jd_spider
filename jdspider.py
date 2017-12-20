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

##爬取特定的物品
FLAG_URLS = [
    {'keyword':'衬衫男','url':'https://search.jd.com/Search?keyword=%E8%A1%AC%E8%A1%AB%E7%94%B7&enc=utf-8&wq=%E8%A1%AC%E8%A1%AB%E7%94%B7&pvid=36aef68ebe994d96a9e92b83c687369f'},
    {'keyword':'衬衫女','url':'https://search.jd.com/Search?keyword=%E8%A1%AC%E8%A1%AB%E5%A5%B3&enc=utf-8&suggest=1.def.0.V06&wq=%E8%A1%AC%E8%A1%ABnv&pvid=5b3e121c473142bc96fbcc9a4bf9d3b1'},
    {'keyword':'毛衣男','url':'https://search.jd.com/Search?keyword=%E6%AF%9B%E8%A1%A3%E7%94%B7&enc=utf-8&wq=%E6%AF%9B%E8%A1%A3%E7%94%B7&pvid=1d9323194d04489094c38cfc3e2f63f8'},
    {'keyword':'毛衣女','url':'https://search.jd.com/Search?keyword=%E6%AF%9B%E8%A1%A3%E5%A5%B3&enc=utf-8&wq=%E6%AF%9B%E8%A1%A3%E5%A5%B3&pvid=ed77e400a4ef4240bff6b342305ddfef'},
]


class Handler(BaseHandler):


    crawl_config = {
        'itag': 'v163', 'connect_timeout':120,
        'headers' : {'Connection':'keep-alive','Accept-Encoding':'gzip, deflate, br','Accept-Language':'zh-CN,zh;q=0.8','content-type':'application/x-www-form-urlencoded','Referer':'http://channel.jd.com/men.html','User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}
    }

    def get_headers(self, referer_url):
        headers = {}
        headers['User-Agent'] = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE) '
        headers['Accept'] = '*/*'
        headers['Accept-Language'] = 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2'
        headers['Accept-Encoding'] = 'gzip, deflate'
        headers['Referer'] = referer_url
        headers['X-Requested-With'] = 'XMLHttpRequest'
        return headers

    def crawl_keyword_url(self, base_url,keyword, callback, cookies, headers):
        page = NUMBER_START
        while page <= NUMBER_END:
            p = 2 * page -1
            s = (page - 1) * 60 + 1
            ##psort=3，是根据销量排序
            page_url = base_url + '&psort=3&page=' + str(p) + '&s=' + str(s) + '&click=0'
            page += 1
            self.crawl(page_url,headers = headers ,cookies=cookies, callback=callback, fetch_type='js', save={"category":keyword, 'keyword':keyword, "page":p });

    @every(minutes= 60 * 24)
    def on_start(self):

        self.crawl('http://channel.jd.com/men.html', callback=self.category_page)


    @config(age=60 * 60 * 24)
    def category_page(self, response):

        flag = True

        if flag:
            ##从指定列表中爬取
            for each in FLAG_URLS:
                url = each['url']
                keyword = each['keyword']
                referer_url = response.url + '#' + str(time.time())
                headers = self.get_headers(referer_url)
                self.crawl_keyword_url(url, keyword, self.list_page, response.cookies, headers)
        else:
            ##从分类中获取关键字和url进行爬取
            for each in response.doc('.fore3 ul a').items():
                query = urlparse.urlparse(each.attr.href).query
                params=  dict([(k,v[0]) for k,v in urlparse.parse_qs(query).items()])
                referer_url = response.url + '#' + str(time.time())
                headers = self.get_headers(referer_url)
                self.crawl_keyword_url(each.attr.href, params['keyword'],self.list_page, response.cookies, headers)




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
        referer_url = response.url + '#' + str(time.time())
        headers = self.get_headers(referer_url)
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
            sql.insert('table_jingdong_2',**each)
            i += 1
