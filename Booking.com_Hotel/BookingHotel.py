# -*- coding: utf-8 -*-

"""
針對 booking.com 住宿搜尋頁面，爬取相關資料
.. module:: booking.com 網站爬蟲
.. moduleauthor:: Yvaine
"""

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import numpy as np
import pandas as pd
import requests


class BookingCrawler():

    def __init__(self):
        self.BeautifulSoup = BeautifulSoup
        self.requests = requests
        # 設定使用者代理
        self.ua = UserAgent()
        self.headers = {'User-Agent': self.ua.random}
        # 爬蟲對象
        self.url = 'https://www.booking.com/searchresults.zh-tw.html'
        # 地區 (花蓮縣: 5233；台東縣: 5237；高雄市: 5191；南投縣: 5231)
        self.region = '花蓮縣'
        self.regionID = '5233'

    def get_max_page(self):
        """取得頁面總數"""
        while True:
            try:
                params = {'region': self.regionID}
                # 透過 requests 的 get 方法把網頁抓下來
                res = self.requests.get(
                    self.url, headers=self.headers, params=params)
                # 解析網頁 (解析器 lxml 套件)
                soup = self.BeautifulSoup(res.content, 'lxml')
                try:
                    max_page = soup.select('.bui-u-inline')[-1].get_text()
                    break
                except IndexError:
                    print('list index out of range')
            except self.requests.exceptions.RequestException as e:
                print('Connection Error: {}'.format(e))
                break
        return max_page

    def loop_page_search(self, page):
        """取得單一區域住宿資料"""
        offset = 0
        # 抓取欄位值
        title_list = []
        score_badge_list = []
        score_text_list = []
        score_subtext_list = []
        thumbnail_list = []
        site_list = []

        for i in range(int(page)):
            # 每頁有 25 筆資料 (offset=25)
            params = {'region': self.regionID, 'offset': str(offset)}
            offset = offset + 25
            try:
                while True:
                    res = self.requests.get(
                        self.url, headers=self.headers, params=params)
                    soup = self.BeautifulSoup(res.content, 'lxml')
                    items = soup.select('.sr_property_block')
                    if (items):
                        break
                print(res.url)
                for item in items:
                    try:  # 名稱
                        title_list.append(item.select(
                            '.sr-hotel__name')[0].get_text().strip())
                    except:
                        title_list.append(np.nan)
                    try:  # 評分 (分數)
                        score_badge_list.append(item.select(
                            '.bui-review-score__badge')[0].get_text().strip())
                    except:
                        score_badge_list.append(np.nan)
                    try:  # 評分 (Text)
                        score_text_list.append(item.select(
                            '.bui-review-score__title')[0].get_text().strip())
                    except:
                        score_text_list.append(np.nan)
                    try:  # 評語總數
                        score_subtext_list.append(item.select(
                            '.bui-review-score__text')[0].get_text().strip())
                    except:
                        score_subtext_list.append(np.nan)
                    try:  # 圖片
                        old_image = item.select('.hotel_image')[
                            0]['data-highres']
                        new_image = old_image.split("&")[0]
                        thumbnail_list.append(new_image)
                    except:
                        thumbnail_list.append(np.nan)
                    try:  # Hotel Link
                        old_link = item.select('.hotel_name_link')[0]['href']
                        new_link = old_link.split("?")[0]
                        site_list.append(
                            ('https://www.booking.com' + new_link).replace('\n', ''))
                    except:
                        site_list.append(np.nan)
            except self.requests.exceptions.RequestException as e:
                print('Connection Error: {}'.format(e))

        # 資料儲存成 Dataframe
        df = pd.DataFrame({'title': title_list, 'score_badge': score_badge_list, 'score_text': score_text_list,
                          'score_subtext': score_subtext_list, 'thumbnail': thumbnail_list, 'site': site_list})
        # 移除重複的行
        df.drop_duplicates(inplace=True)
        # 移除缺失的索引
        df.reset_index(inplace=True, drop=True)
        # ID
        df.insert(0, 'id', df.index + 1)

        return df

    def loop_hotel_search(self, data):
        """根據 Hotel 網址，取得更詳細的住宿資料"""
        full_address_list = []
        full_desc_list = []
        room_list = []

        for i in range(len(data)):
            # Hotel Link
            url = str(data.iloc[i, 6])
            print(url)
            try:
                response = self.requests.get(url, headers=self.headers)
                soup = self.BeautifulSoup(response.content, 'lxml')
                try:  # 位置
                    full_address = soup.select('.hp_address_subtitle')[
                        0].get_text().strip()
                    full_address_list.append(
                        (self.region + full_address).replace('\n', ''))
                except:
                    full_address_list.append(np.nan)
                try:  # 介紹
                    for item in soup.select('#property_description_content'):
                        full_desc_list.append(item.get_text().strip())
                except:
                    full_desc_list.append(np.nan)
                try:  # 房型
                    new_room = []
                    for item in soup.select('.jqrt'):
                        new_room.append(item.get_text().strip())
                    room_list.append('、'.join(new_room))
                except:
                    room_list.append(np.nan)
            except self.requests.exceptions.RequestException as e:
                print('Connection Error: {}'.format(e))

        df = pd.DataFrame(
            {'full_address': full_address_list, 'full_description': full_desc_list, 'room': room_list})

        return df


if __name__ == "__main__":
    booking = BookingCrawler()
    max_page = booking.get_max_page()
    page_info = booking.loop_page_search(max_page)
    hotel_info = booking.loop_hotel_search(page_info)

    # 合併 Dataframe
    result = pd.concat([page_info, hotel_info], axis=1)

    # 結果筆數
    print('{} rows x {} columns'.format(result.shape[0], result.shape[1]))

    # 匯出檔案 (檔名: Hualien、Taitung、Kaohsiung、Nantou)
    result.to_csv('{}.csv'.format('Hualien'),
                  encoding='utf_8_sig', index=False)
    result.to_json('{}.json'.format('Hualien'), orient='records', indent=4)
