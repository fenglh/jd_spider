#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2017-12-16 15:02:34
# Project: download_image

from pyspider.libs.base_handler import *
import MySQLdb.cursors
import MySQLdb
import threading
import thread
import time
import Queue
import os
import urllib
reload(sys)
sys.setdefaultencoding('utf8')

class SQLManager(object):
    """数据库管理者"""
    def __init__(self):
        super(SQLManager, self).__init__()
        self.is_finish_load_data = False
        self.total_count = 0
        #初始化队列
        ##连接数据库的配置信息
        hosts    = '127.0.0.1'
        username = 'root'
        password = '123456'
        database = 'SpiderDB'
        charsets = 'utf8'
        self.connection = False
        try:
            self.conn = MySQLdb.connect(host = hosts,user = username,passwd = password,db = database,charset = charsets,cursorclass = MySQLdb.cursors.SSCursor)
            self.cursor = self.conn.cursor()
            self.cursor.execute("set names "+charsets)
            self.connection = True
        except Exception,e:
            print "连接数据库失败!/n",e

    def fetch_data_queue(self):
        queue = Queue.Queue(-1)##无限队列
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM table_jingdong");
        row = cur.fetchone()
        while row is not None:
            ##放入队列
            queue.put(row)
            self.total_count += 1
            row = cur.fetchone()
        return queue


class ThreadDownload(threading.Thread):
    def __init__(self, queue,thread_id, root_dir):
        threading.Thread.__init__(self)
        self.queue = queue
        self.thread_id = thread_id
        self.root_dir = root_dir
        self.makedirs(root_dir)

    def makedirs(self,path):
        threadLock.acquire()
        if not path.endswith('/'):
            path = path + '/'
        if not os.path.exists(path):
            print '创建目录:', path
            os.makedirs(path)
        threadLock.release()

    def run(self):
        print '>>线程%d开始进行下载...' % (self.thread_id)
        i = 0
        while not self.queue.empty():
            i += 1
            row  = self.queue.get()
            number = row[0]
            title = row[1]
            url = row[2]
            category = row[3].strip()
            category_path = self.root_dir + '/' + category
            self.makedirs(category_path)
            file_name = url.split('/')[-1]
            file_path = category_path +'/' + file_name
            try:
                urllib.urlretrieve(url,file_path)
                pass
            except:
                self.queue.put(row)
            print '>>>>线程%d已下载:%s' % (self.thread_id ,url)
        print '>>>>queue中没有任务了,共下载数:%d，线程%d结束！' % (i, self.thread_id)

##线程锁
threadLock = threading.Lock()
root_dir = '/Users/fenglihai/Desktop/images'
queue = SQLManager().fetch_data_queue()
if not queue.empty():
    print '从数据库初始化数据队列成功,队列大小:%d' % (queue.qsize())
#3个线程
for i in range(30):
    t = ThreadDownload(queue, i+1,root_dir)
    t.start()
