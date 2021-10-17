# -*- coding: utf-8 -*-

"""
針對 booking.com 評語搜尋頁面，爬取相關資料
.. module:: booking.com 網站爬蟲
.. moduleauthor:: Yvaine
"""

from bs4 import BeautifulSoup
from itertools import chain
from fake_useragent import UserAgent
import csv
import re
import requests
import numpy as np
# 禁用安全请求警告 (requests 發送 HTTPS 請求，關閉認證 verify=False)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BookingCrawler():

    def __init__(self):
        self.BeautifulSoup = BeautifulSoup
        self.chain = chain
        self.re = re
        self.requests = requests
        self.np = np
        # 設定使用者代理
        self.ua = UserAgent()
        self.headers = {'User-Agent': self.ua.random}
        # 爬蟲對象
        self.url = 'https://www.booking.com/reviews/region/hualien.zh-tw.html'

    def get_max_page(self):
        """取得頁面總數"""
        # 透過 requests 的 get 方法把網頁抓下來
        res = self.requests.get(self.url)
        # 解析網頁 (解析器 lxml 套件)
        soup = self.BeautifulSoup(res.text, 'lxml')
        # 所有頁面
        total_page = soup.find_all("a", class_="rlp-main-pagination__btn-txt")
        # 最後一頁
        max_page = int(total_page[len(total_page)-1].string)
        return max_page

    def loop_page_search(self, page):
        """取得飯店評語 link"""
        offset = 0
        # 抓取欄位值
        hotel = []
        review_link = []
        for i in range(int(page)):
            # 每頁有 30 筆資料 (offset=30)
            params = {'offset': str(offset)}
            offset = offset + 30
            res = self.requests.get(self.url, params=params)
            soup = self.BeautifulSoup(res.text, 'lxml')
            # 飯店名稱
            hotel.append(soup.find_all(
                "a", class_="rlp-main-hotel__hotel-name-link"))
            # 飯店評語 link
            review_link.append(soup.find_all(
                "li", class_="rlp-main-hotel-review__review_link"))
        # 串連成一維 list
        return [list(self.chain.from_iterable(review_link)), list(self.chain.from_iterable(hotel))]

    def loop_reptile_comment(self, data):
        """取得住客資訊"""
        key = 0
        result_list = {}
        for url in data[0]:
            tmp_list = []
            key = key + 1
            result_list[key] = []
            url_review = 'https://www.booking.com' + url.a['href']
            try:
                res_page = self.requests.get(url_review, headers=self.headers, params={
                    'r_lang': 'zh-tw', 'rows': '75'})
                soup_page = self.BeautifulSoup(res_page.text, 'lxml')
                # 取得評論筆數
                review_count_text = soup_page.find(
                    "p", class_="review_list_score_count").string
                review_count = self.re.sub('\D', '', review_count_text)

                for page in range(1, round(int(review_count)/75)):
                    res = self.requests.get(url_review, headers=self.headers, verify=False, params={
                        'r_lang': 'zh-tw', 'rows': '75', 'page': str(page)})
                    soup = self.BeautifulSoup(res.text, 'lxml')
                    print(res.url)

                    # 住客姓名
                    name = [i.get_text().strip()
                            for i in soup.find_all("p", class_="reviewer_name")]
                    # 國籍
                    country = [i.get_text().strip() for i in soup.find_all(
                        "span", class_="reviewer_country")]
                    # 評語推薦數
                    review_count = [self.re.sub('\D', '', i.get_text().strip()) for i in soup.find_all(
                        "div", class_="review_item_user_review_count")]
                    # 評分
                    review_score_badge = [i.get_text().strip() for i in soup.find_all(
                        "div", class_="review_item_header_score_container")]
                    # 評分標題
                    review_score_text = [i.get_text().strip() for i in soup.find_all(
                        "div", class_="review_item_header_content_container")]
                    # 填寫日期
                    review_date = [i.get_text().strip().split("：")[1] for i in soup.find_all(
                        "p", class_="review_item_date")]
                    # 標籤
                    review_tags = soup.find_all(
                        "ul", class_="review_item_info_tags")
                    # 評語
                    reviews = soup.find_all(
                        "div", class_="review_item_review_content")

                    if (len(name) > 0):
                        index = 0
                        for review in reviews:
                            size = len(tmp_list)
                            # 住客姓名
                            tmp_list.append([name[index]])
                            # 國籍
                            tmp_list[size].append(country[index])
                            # 評語推薦數
                            tmp_list[size].append(review_count[index])
                            # 評分
                            tmp_list[size].append(review_score_badge[index])
                            # 評分標題
                            tmp_list[size].append(review_score_text[index])
                            # 填寫日期
                            tmp_list[size].append(review_date[index])
                            # 標籤
                            tags = review_tags[index].find_all(
                                "li", class_='review_info_tag')
                            tag = [i.get_text().replace('•', '').strip()
                                   for i in tags]
                            tmp_list[size].append("、".join(tag))
                            # 負評
                            try:
                                tmp_list[size].append(review.find(
                                    "p", class_="review_neg").get_text().strip('\n').strip())
                            except:
                                tmp_list[size].append(np.nan)
                            # 好評
                            try:
                                tmp_list[size].append(review.find(
                                    "p", class_="review_pos").get_text().strip('\n').strip())
                            except:
                                tmp_list[size].append(np.nan)
                            index = index + 1
                result_list[key].append(tmp_list)
            except self.requests.exceptions.RequestException as e:
                print('Connection Error: {}'.format(e))
        return [result_list, [hotel.get_text() for hotel in data[1]]]


if __name__ == "__main__":
    booking = BookingCrawler()
    max_page = booking.get_max_page()
    review_link = booking.loop_page_search(1)
    result = booking.loop_reptile_comment(review_link)

    # 匯出檔案 (csv)
    key = 0
    for i in result[0]:
        for data in result[0][i]:
            filename = 'result\\' + str(result[1][key]) + '.csv'
            key = key + 1
            with open(filename, 'w', encoding='utf_8_sig', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    ["住客姓名", "國籍", "評語推薦數", "評分", "評分標題", "填寫日期", "標籤", "負評", "好評"])
                for list in data:
                    writer.writerow(list)
