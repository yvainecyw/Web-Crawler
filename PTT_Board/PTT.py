# -*- coding: utf-8 -*-

"""
針對批踢踢實業坊特定看板的文章爬蟲，執行方法: python PTTBoard.py Gossiping 5 3 gossiping
.. module:: 批踢踢實業坊網站爬蟲
.. moduleauthor:: Yvaine
"""

from bs4 import BeautifulSoup as bs
import json
import requests
import sys
import time
import urllib

# 將 cookies 加入 POST 請求中
payload = {'yes': 'yes'}


def get_all_articles(base_index, start_page, page):
    """取得特定頁面中的所有文章內容"""
    if page > start_page:
        print('params error')
        return None
    # 跨請求保持 cookies
    rs = requests.session()
    # 繞過 18 禁限制 (部分看板為 18 禁)
    if 'over18' in rs.get(base_index).url:
        rs.post('https://www.ptt.cc/ask/over18', data=payload)
    # 透過 requests 的 get 方法把網頁抓下來
    res = rs.get(base_index)
    # 解析網頁
    soup = bs(res.text, 'lxml')
    # 透過 '上頁' 按鈕得知當前 index
    prev_page = soup.find_all('a', 'btn wide')[1].get('href')
    prev_index = prev_page[(prev_page.find('index') + 5):prev_page.find('.html')]
    start_index = int(prev_index) + 1 - (start_page - 1)
    # '上頁' 剛好是最後一頁，起始頁面再減 1
    if bs(rs.get(base_index[:-5] + str(start_index) + '.html').text, 'lxml').find(text='500 - Internal Server Error'):
        start_index -= 1
    # 暫存看板的全部頁面 (.../index頁面.html)
    index_list = [i for i in range(start_index, start_index + page)]

    no = 1
    article_list = []
    comma = False
    for idx in index_list:
        cur_url = base_index[:-5] + str(idx) + '.html'
        print('Board Index {}'.format(cur_url))
        res = rs.get(cur_url)
        soup = bs(res.text, 'lxml')
        for article in soup.find_all('div', 'r-ent'):
            # 取得文章標題
            title_url = article.find('a')
            # 判斷不合規格的文章 (e.g. '本文已被刪除')
            if title_url:
                # 取得文章網址
                title_url = title_url.get('href')
                url = urllib.parse.urljoin(cur_url, title_url)
                # 建立 Dictionary
                article_data = get_article_content(rs.get(url))
                if article_data:
                    print('{:5}. {}'.format(no, url))
                    article_data['a_no'] = no
                    json_data = (',' if comma else '') + json.dumps(article_data,
                                                                    ensure_ascii=False, indent=4, sort_keys=True)
                    article_list.append(json_data)
                    if not comma:
                        comma = True
                    no += 1
            # 避免被當作攻擊網站
            time.sleep(0.5)
        time.sleep(0.5)
    rs.close()

    return article_list


def get_article_content(res):
    """取得單一篇文章內容"""
    soup = bs(res.text, 'lxml')
    metalines = soup.find_all('div', 'article-metaline')
    try:
        # 文章作者
        author = metalines[0].find('span', 'article-meta-value').get_text()
        # 文章標題
        title = metalines[1].find('span', 'article-meta-value').get_text()
        # 文章時間
        date = metalines[2].find('span', 'article-meta-value').get_text()
    except Exception as e:
        print('error infomation at {}\n{}'.format(res.url, repr(e)))
        return None
    try:
        # 文章內容
        main_content = soup.find('div', id='main-content')
        # 用 '文章結尾' 和 '時間' 來做分割
        content = main_content.get_text().split('--\n※ 發信站')[0].split(date)[1]
    except Exception as e:
        print('error content at {}\n{}'.format(res.url, repr(e)))
        return None

    good = 0
    boo = 0
    arrow = 0
    reviews = []
    if soup.find_all('div', 'push'):
        for push_tag in soup.find_all('div', 'push'):
            # 繞過 '檔案過大！部分文章無法顯示' warning-box
            if 'warning-box' in push_tag.get('class'):
                continue
            # 計算推噓文數量
            tag = push_tag.find('span', class_='push-tag').get_text().strip()
            if tag == '→':  # 註解
                arrow += 1
            elif tag == '推':  # 推
                good += 1
            elif tag == '噓':  # 噓
                boo += 1
            # 留言者
            userid = push_tag.find('span', class_='push-userid').get_text()
            # 留言內容
            push_content = push_tag.find(
                'span', class_='push-content').get_text().strip(': ')

            reviews.append({'a_id': userid, 'b_tag': tag,
                           'c_content': push_content})
    statistics = {'a_total': good + boo,
                  'b_good': good, 'c_boo': boo, 'd_arrow': arrow}
    data = {"b_title": title, "c_author": author, "d_content": content,
            "e_reviews": reviews, "f_statistics": statistics, "g_url": res.url}

    return data


def main(board, start_page, page, filename):
    # 看板的原始網址 (e.g. 'https://www.ptt.cc/bbs/Gossiping/index.html')
    base_index = 'https://www.ptt.cc/bbs/' + board + '/index.html'
    payload['form'] = '/bbs/' + board + '/index.html'
    # (base_index, 5, 3): 從倒數第 5 頁開始抓，總共抓 3 頁
    article_list = get_all_articles(base_index, start_page, page)
    # 匯出檔案 (json)
    with open('{}.json'.format(filename), 'w', encoding='UTF-8') as f:
        f.write('[\n')
        for article in article_list:
            f.write(article)
        f.write('\n]')


if __name__ == "__main__":
    sec = time.time()
    # 執行方法: python PTTBoard.py [看板名稱] [起始頁面] [抓取頁數] [檔名]
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    print('耗時 {:.2f} 秒'.format(time.time() - sec))
