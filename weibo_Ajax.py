# 爬取Ajax加载的手机版的马云的微博,保存为txt,并保存在MongoDB下
import requests
from pyquery import PyQuery as pq
import json
from pymongo import MongoClient


class WeiBo:
    def __init__(self):
        self.url = "https://m.weibo.cn/api/container/getIndex?type=uid" \
                   "&value=2145291155&containerid=1076032145291155&page={}"
        self.headers = {"Referer": "https://m.weibo.cn/u/2145291155",
                        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36"
                                      " (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
                        "X-Requested-With": "XMLHttpRequest"}

    def parse(self, url):
        # 判断状态码是否是200，是的话调用json()方法，使结果返回为json
        # 如果出现异常，则捕获异常并输出异常
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.content.decode()
                # 注意！！！这边不能返回response.json()，不然后面保存为文本时候，
                # 调用json.dumps时，会提示字典没有dumps属性
        except requests.ConnectionError as e:
            print("Error", e.args)

    def get_shuju(self, html_str):
        data = json.loads(html_str)
        items = data.get('data').get('cards')
        weibo_list = []  # 一个页面下9条微博的列表
        for item in items:
            weibo_dict = {}  # 每一条微博
            item = item.get("mblog")
            weibo_dict["id"] = item.get("id")
            weibo_dict["评论"] = item.get("comments_count")
            weibo_dict["点赞"] = item.get("attitudes_count")
            weibo_dict["转发"] = item.get("reposts_count")
            weibo_dict["正文"] = pq(item.get("text")).text()
            weibo_list.append(weibo_dict)
        return weibo_list

    def save_to_txt(self,weibo_list):
        # 保存为txt格式，利用了json.dumps方法
        with open("weibo.txt", "a", encoding="utf-8") as f:
            for weibo in weibo_list:
                f.write(json.dumps(weibo, ensure_ascii=False))
                f.write("\n")

    def run(self):
        client = MongoClient()
        db = client['weibo']
        collection = db['weibo']
        # 观察network下preview，得知微博总数为157，每个Ajax加载的页面仅有9条微博，因此页数设置成18
        num = 0
        while num <= 18:
            url = self.url.format(num)  # 观察network，在抓包下，观察响应是在哪个url下
            # 由Ajax加载，并观察规律，用了urlencode()方法
            html_str = self.parse(url)
            weibo_list = self.get_shuju(html_str)
            self.save_to_txt(weibo_list)
            num += 1
            for result in weibo_list:
                if collection.insert(result):
                    print('Saved to Mongo')


if __name__ == '__main__':
    weibo = WeiBo()
    weibo.run()
