import re
import requests
import pyecharts
import pymysql


class TaoTie(object):
    
    def __init__(self):
        self.headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'}
        self.db = pymysql.connect('localhost', 'youraccount', 'yourpassword', 'fishc', charset='utf8')
        self.cursor = self.db.cursor()
        self.page = 1

    def get_page(self):
        url = 'http://bbs.fishc.com/forum.php?mod=collection&page=%d' % self.page
        html = requests.get(url, headers=self.headers).text
        self.page += 1
        return html

    def get_info(self, html):        
        # pat = '<a [^>]*ctid=%d[^>]>(.*?)</a>'
        title_pat = '<a href="forum\.php\?mod=collection&amp;action=view&amp;ctid=\d+" class="xi2" >(.*?)</a>'
        subscription_pat = '<p>.\n订阅 (\d+), 评论 \d+</p>'
        author_pat = '<p class="xg1"><a href="space-uid-\d+.html">(.*?)</a>'
        totalpost_pat = '<strong class="xi2" >(\d+)</strong>'
        title = re.compile(title_pat).findall(html)
        author = re.compile(author_pat).findall(html)
        totalpost = re.compile(totalpost_pat).findall(html)
        subscription = re.compile(subscription_pat, re.M).findall(html)
        return (title, author, subscription, totalpost)

    def initialized_db(self):
        sql = '''
        create table `taozhuanji` (
            `id` int not null auto_increment,
            `title` text(50) not null,
            `author` varchar(15) not null,
            `subscription` int not null,
            `totalpost` int(3) not null,
            primary key (`id`)
        );
        '''
        self.cursor.execute(sql)
        self.db.commit()

    def store_data(self, data):
        result = []
        title, author, subscription, totalpost = data
        for i in range(len(title) - 1):
            param = (title[i], author[i], int(subscription[i]), int(totalpost[i]))
            result.append(param)
        sql = '''insert into `taozhuanji` (`title`, `author`,`subscription`, `totalpost`) values (%s, %s, %s, %s);'''
        self.cursor.executemany(sql, result)
        self.db.commit()

    def get_data_by_subs(self):
        sql = "select * from taozhuanji order by subscription desc limit 10"
        self.cursor.execute(sql)
        top_10 = self.cursor.fetchmany(11)
        self.db.commit()
        return top_10

    def get_data_by_tota(self):
        sql = "select * from taozhuanji order by totalpost desc limit 10"
        self.cursor.execute(sql)
        top_10 = self.cursor.fetchmany(11)
        self.db.commit()
        return top_10

    def map(self, data, key, choice):
        title, subscription, totalpost = [], [], []
        for t in data:
            title.append(t[1]+'('+t[2]+')')
            subscription.append(t[3])
            totalpost.append(t[4])
        bar = pyecharts.Bar('FishC淘贴{}top10'.format(key), height=500, width=1000)
        bar.use_theme('macarons')
        bar.add('{}'.format(key), title, subscription if choice == 1 else totalpost, xaxis_interval=0, xaxis_rotate=9, yaxis_rotate=30)
        bar.render(r'filepath//%s.html' % key)

    def main(self):
        self.initialized_db()
        while self.page < 26:
            html = self.get_page()
            info = self.get_info(html)
            self.store_data(info)
        self.map(self.get_data_by_subs(), '订阅量', 1)
        self.map(self.get_data_by_tota(), '主题数', 2)
        return '完毕'

FishC = TaoTie()
FishC.main()
