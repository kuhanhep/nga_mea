import requests
from lxml import etree
import re
import json
import pymysql
import time

class nga:
    def __init__(self):
        self.baseurl = "http://bbs.nga.cn/read.php?tid=15923050&_ff=-447601&page="
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            "Cookie": Your_Cookie, # 此处填入自己登录账号后的cookie
            "Host": "bbs.nga.cn",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36"
        }
        self.con = pymysql.connect("localhost", "root", "123456", "nga", charset="utf8")
        self.cur = self.con.cursor()
        self.sql = "insert into mea_new values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        self.count = 0

    def get_page(self, page):
        res = requests.get(url=self.baseurl+str(page), headers=self.headers)
        res.encoding = "GBK"
        html = res.text
        return html

    def parse_page(self, html):
        parseHtml = etree.HTML(html)

        # UID-(昵称,注册时间)对应字典
        p_id = re.compile("commonui.userInfo.setAll\((.*?\})\s\)")
        ids = p_id.findall(html)
        ids = ids[0].replace("<br/>", "")
        ids = ids.replace("/*$js$*/", "")
        id_name = json.loads(ids.strip())

        # 日期时间
        datetimes = parseHtml.xpath('//*[@class="postInfo"]/span[@title="reply time"]')

        # 客户端,点赞数,楼层数信息
        p_message = re.compile("commonui\.postArg\.proc\((\s\d+.*?postcontainer.*?null.*?)\)", re.S)
        messages = p_message.findall(html)
        # print(messages)

        # uid
        p_uid = re.compile("\'nuke.php\?func=ucp&uid=(.*?)\'\sid=\'post")
        uids = p_uid.findall(html)

        # 回帖内容
        p_comment1 = re.compile("class=\'postcontent ubbcode\'\>(.*?)\<\/p\>")
        comments1 = p_comment1.findall(html)
        p_comment2 = re.compile("class=\'postcontent ubbcode\'\>(.*?)\<\/span\>")
        comments2 = p_comment2.findall(html)
        comments = comments1 + comments2

        return (id_name, datetimes, messages, uids, comments)

    def save_data(self, id_name, datetimes, messages, uids, comments):
        for i in range(len(comments)):
            if int(uids[i]) < 0:  # 判断是否匿名
                name = "匿名"
                regdate = None
                regtime = None
            else:
                name = id_name[uids[i]]["username"]  # 昵称
                reg = time.localtime(id_name[uids[i]]["regdate"])
                regdate = time.strftime("%Y-%m-%d", reg)  # 注册日期
                regtime = time.strftime("%H:%M:%S", reg)  # 注册时间
            comment = comments[i]  # 回帖内容
            date = datetimes[i].text.split()[0]  # 回帖日期
            t = datetimes[i].text.split()[1]  # 回帖时间
            num = int(messages[i].split(",")[0])  # 回帖所在楼层
            mobiephone = messages[i].split(",")[21].strip("'")  # 回帖所用设备
            praise = messages[i].split(",")[16]  # 被点赞数
            self.cur.execute(self.sql, [num, name, regdate, regtime, comment, mobiephone, date, t, praise])
            print(num, name, regdate, regtime, comment, mobiephone, date, t, praise)
            self.count += 1
            print("成功插入%d条" % self.count)
        self.con.commit()

    def main(self, start_page, end_page):
        for i in range(start_page, end_page):
            html = self.get_page(i)
            datas = self.parse_page(html)
            self.save_data(*datas)
            print("成功保存%d页" % i)
            time.sleep(0.3)
        self.cur.close()
        self.con.close()


if __name__ == "__main__":
    mea = nga()
    mea.main(5250, 5250)
