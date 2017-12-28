京东图片批量爬取分析过程
====


--------------------------------



#### 一、需求
10000 张 男衬衫

![](http://ozhqm0ga1.bkt.clouddn.com/d67388d88ddee578842fea824d33efa1.png)
#### 二、目标
京东

![](http://ozhqm0ga1.bkt.clouddn.com/4b32df9d3d5be10911da89e25fc6c5ae.png)
> 其他如百度、天猫、淘宝等。不同站各自的反爬虫机制不同不同。

#### 三、踩点
逛一逛京东，看看哪里有大量图片的页面，可作为切入点去爬取。通常会选择具备`分页`功能的列表页面。

搜索：衬衫男，可以看到返回的页面是满足需求的

![](http://ozhqm0ga1.bkt.clouddn.com/7e73b28926780bf04aaa47d6e3552e03.png)
![](http://ozhqm0ga1.bkt.clouddn.com/6f4d1503022c03ab81d5af5fbddb2452.png)
#### 四、分析

###### 1. 分页url的关联

因为我们需要的是大量的图片，一页的图片数量有限，所以先分页每一页的URL的关联，以方便我们在代码中去构造URL

第1页

`https://search.jd.com/Search?keyword=%E8%A1%AC%E8%A1%AB%E7%94%B7&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=%E8%A1%AC%E8%A1%AB&page=1&s=1&click=0`

第2页

`https://search.jd.com/Search?keyword=%E8%A1%AC%E8%A1%AB%E7%94%B7&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=%E8%A1%AC%E8%A1%AB&page=3&s=56&click=0`

第1、2、3、4页的url比较:
![](http://ozhqm0ga1.bkt.clouddn.com/7c304b0ef13bdcfa5a03eff26d20cdc6.png)
![](http://ozhqm0ga1.bkt.clouddn.com/6a4ddba776ef5d945f703ac574716134.png)

可发现：只有参数`page`和`s`是变化的
###### 2. 控制变量法测试：

1. 点击右箭头`>`3次,发现`page`的值是1、3、5、7
2. 点击左箭头`<`3次,发现`page`的值是7、5、3、1
3. 点击右箭头`>`3次,发现`s`的值是1、56、112、168
4. 点击左箭头`<`3次,发现`s`的值是168、108、48、1

默认为“综合”排序，点击“销量”，重复3~4步骤发现
1. 点击右箭头`>`3次,发现`s`的值是1、61、121、181
2. 点击左箭头`<`3次,发现`s`的值是181、121、61、1



![](http://ozhqm0ga1.bkt.clouddn.com/7b05b5252bd29f2c3f8d5f7e3b2ad81a.png)

![](http://ozhqm0ga1.bkt.clouddn.com/15b085855cfaee8175b0b4d41a2a839c.png)

###### 3. 初步结论
1. 参数`page` 作用：表示页码、第几页
2. 参数`s`  暂不明白其作用，貌似在“销量”排序下，是`s`的值是有规律变化的。暂时理解为：列表的起始`商品索引`。例如：第一页，1表示从1开始取，取60张；第二页，61表示从第61开始取


#### 五、构造url
1. 从京东页面上看，可以看到页码最大值是`100`。
2. 结合上面分析的初步结论

我们可以开始构造url,假设
- `x`表示实际看到页码(1、2、3、4...)
- `y`表示url中的页码page(1、3、5、7、9)
- `z`表示url中的s(1、61、121、181)

![](http://ozhqm0ga1.bkt.clouddn.com/af384aec42c0a090c650b41c8ac6396e.png)

那么可以得出：

  ```python
  y = 2x -1
  z = (x-1) * 60 + 1
  ```
伪代码代码实现：

  ```python
  page = 1
  while page <= 100:
      p = 2 * page -1
      s = (page - 1) * 60 + 1
      ##psort=3，是根据销量排序
      page_url = base_url + '&psort=3&page=' + str(p) + '&s=' + str(s) + '&click=0'
      page += 1
  ```
#### 六、爬取

根据上述的规则，我们可以轻易的构造从第1页到第100页的`衬衫男`URL，接下来的就是对这个URL进行请求，并解析HTML取得相应的图片了。

假设我们以第1页的URL为测试对象：

`https://search.jd.com/Search?keyword=%E8%A1%AC%E8%A1%AB%E7%94%B7&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=%E8%A1%AC%E8%A1%AB&psort=3&page=1&s=1&click=0`

1. 通过`火狐浏览器`(或者Google Chrome) ，我们捕获这一次请求得知是使用`GET`请求。
![](http://ozhqm0ga1.bkt.clouddn.com/ae14c9f3b9798ff11a7a386ec8d4b358.png)

2. 发起http请求的方法有许多种，可以使用各种语言c、c++、oc、java、python等，这里选择python。为了方便演示和大家也可以快速上手，这里结合 [PySpider](http://www.pyspider.cn/index.html)
>PySpider
>
一个国人编写的强大的网络爬虫系统并带有强大的WebUI。采用Python语言编写，分布式架构，支持多种数据库后端，强大的WebUI支持脚本编辑器，任务监视器，项目管理器以及结果查看器。在线示例：[http://demo.pyspider.org/](http://demo.pyspider.org/)
![](http://ozhqm0ga1.bkt.clouddn.com/d6396f2d0b12a192148666fa4f83afd5.png)

+ 在PySpider提供的WebUI上调试并发起请求

  我在官方提供的[在线示例]([http://demo.pyspider.org/](http://demo.pyspider.org/)中，建立了一个[demo](http://demo.pyspider.org/debug/jingdong_itx_demo)，代码如下

  ```python
  #!/usr/bin/env python
  # -*- encoding: utf-8 -*-
  # Created on 2017-12-21 01:22:37
  # Project: jingdong_itx_demo
  from pyspider.libs.base_handler import *
  class Handler(BaseHandler):

      def on_start(self):
          self.crawl('https://search.jd.com/Search?keyword=%E8%A1%AC%E8%A1%AB%E7%94%B7&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=%E8%A1%AC%E8%A1%AB&psort=3&page=1&s=1&click=0', callback=self.index_page)

      @config(age=10 * 24 * 60 * 60)
      def index_page(self, response):
          print response.text
  ```
  ![](http://ozhqm0ga1.bkt.clouddn.com/0392efd2f0faf6abcd43e0c8f426dee6.png)

  在`index_page` 回调方法中，有一个`response`参数是一个用python封装JQuery的`PyQuery`对象，可以通过`PyQuery`提供的方法和属性很轻易的解析出HTML找那个我们想要的内容。

+ 解释HTML
  >pyspider爬取的内容通过回调的参数response返回，response有多种解析方式。
  >
1、response.json用于解析json数据
>
2、response.doc返回的是PyQuery对象
>
3、response.etree返回的是lxml对象
>
4、response.text返回的是unicode文本
>
5、response.content返回的是字节码

  不熟悉PyQuere 的可以查看 [pyspider示例代码三：用PyQuery解析页面数据](http://www.cnblogs.com/microman/p/6111711.html)

  通过`PySpider`提供的WebUI调试，可以看到返回的html对应的渲染好的页面(无法截图，看演示)。

  拖动滚动条，看看渲染好的页面是否和我们平常使用浏览器打开这个网址返回的页面是否一致！结果不一致！！只有30张图片，是显示出来的，剩下的只是空白的。

  是否是网页是用了一些什么异步、懒加载的方式？验证一下！
![](http://ozhqm0ga1.bkt.clouddn.com/520e4da2e9367bda44156b395f550e8e.png)
当滚动条下拉到下一半的时候，我们监听到了另外一个http请求：
![](http://ozhqm0ga1.bkt.clouddn.com/529ca217f6b67f9171531a8888b4721b.png)
原来，剩下30条是"当你滚动到网页下半部分"的时候，再去请求回来的...那么接下来就是，又要去分析这个请求是怎么构成的....


##### 欲听后事如何，请听下回分解....
存入mysql、批量下载图片等等
![](http://ozhqm0ga1.bkt.clouddn.com/ef9a30e22b9c8dd4e8a2669694ee6cea.png)
