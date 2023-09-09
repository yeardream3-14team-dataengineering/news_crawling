import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime
import time
import os
from tqdm import tqdm
import re


##오늘날짜얻기
today = datetime.today().strftime('%Y%m%d')
#print(today)

##data 폴더 생성
try:
    if not os.path.exists("data"):
        os.mkdir("data")
except OSError:
    print ('Error: Creating directory. ' +  "data")

"""
100 : 정치
101 : 경제
102 : 사회
103 : 생활/문화
104 : 세계
105 : IT/과학
"""


def convert_datetime_format(get_time):
    """
    2023.08.31. 오후 3:51
    to
    YYYY-MM-DD HH:MI:SS
    """
    if '오후' in get_time:
        # 오후인 경우, 시간에 12를 더해서 24시간 형식으로 변환
        tmp_time = datetime.strptime(get_time, "%Y.%m.%d. 오후 %I:%M")
        tmp_time = tmp_time.replace(hour=tmp_time.hour + 12)
    else:
        # 오전인 경우, 그대로 24시간 형식으로 변환
        tmp_time = datetime.strptime(get_time, "%Y.%m.%d. 오전 %I:%M")

    return tmp_time.strftime("%Y-%m-%d %H:%M:%S")






def make_urllist(code, date):
    urllist= []
    
    url = 'https://news.naver.com/main/list.nhn?mode=LSD&mid=sec&sid1='+str(code)+'&date='+str(date)+'&page=1'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.90 Safari/537.36'}
    news = requests.get(url, headers=headers)

    # BeautifulSoup의 인스턴스 생성합니다. 파서는 html.parser를 사용합니다.
    soup = BeautifulSoup(news.content, 'html.parser')

    # CASE 1
    news_list = soup.select('.newsflash_body .type06_headline li dl')
    # CASE 2
    news_list.extend(soup.select('.newsflash_body .type06 li dl'))
    
    # 각 뉴스로부터 a 태그인 <a href ='주소'> 에서 '주소'만을 가져옵니다.
    for line in news_list:
        urllist.append(line.a.get('href'))

    time.sleep(1)

    return urllist
    

cat = [100, 101, 102, 103 ,104, 105]

url_lists = {}
for i in tqdm(cat):
    url_lists[i] = make_urllist(i, today)


# cat 값에 따라 url_list에 접근
for i in tqdm(cat):
    #print(f"cat {i}: {url_lists[i]}")


    #빈 데이터프레임 생성
    columns = {
        '뉴스URL': [],
        '뉴스업체': [],
        '기사제목': [],
        '작성일자': [],
        '수정일자': [],
        '본문내용': [],
        '이미지URL': [],
        '작성기자&이메일': []
    }
    df = pd.DataFrame(columns)
    #print(df)

    for url in url_lists[i]:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"}

        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'lxml')


        #print(soup)
        #newslist = soup.select(".office_header")
        #print(len(newslist))
        
        ##뉴스업체
        #ofhd_float_title_text
        try:

            siteName = soup.find(class_="c_inner")
            siteName_val = siteName.text.split("ⓒ")[1].strip().split('.')[0].strip()
        except:
            continue
            #siteName_val = None
            #print(url)

        ##기사제목
        #media_end_head_headline
        try:
            title = soup.find(class_="media_end_head_headline")
            title_val = title.text
        except:
            continue
            #title_val = None
            #print(url)

        ##작성일자
        #media_end_head_info_datestamp_time _ARTICLE_DATE_TIME
        try:
            createDate = soup.find(class_="media_end_head_info_datestamp_time _ARTICLE_DATE_TIME")
            createDate_val = convert_datetime_format(createDate.text)
        except:
            continue
            #createDate_val = None
            #print(url)

        ##수정일자
        #media_end_head_info_datestamp_time _ARTICLE_MODIFY_DATE_TIME
        try:
            modifyDate = soup.find(class_="media_end_head_info_datestamp_time _ARTICLE_MODIFY_DATE_TIME")
            modifyDate_val = convert_datetime_format(modifyDate.text)
        except:
            modifyDate_val = None


        ##본문내용
        #dic_area 안 br카테고리 txt
        try:
            #text_list = ""

            brs = soup.find(id="dic_area")
            #print(len(brs))
            #brs = lis.findAll("br")
            #brs.findAll("br")

            text_list = brs.get_text(strip=True)
            #for br in brs:
            #    text_list.append(br.get_text(strip=True))
            #print(text_list)
        except:
            print(url)


        ##이미지 URL
        #end_photo_org
        try:
            img_url_list = []

            urs = soup.findAll(class_="end_photo_org")
            #print(len(urs))
            for ur in urs:
                img_url_list.append(ur.img['data-src'])
            #print(img_url_list)
        except:
            print(url)

        ##작성기자 기자 이메일
        #byline_s
        try:
            author_list = []

            authors = soup.findAll(class_="byline_s")
            #print(len(authors))
            for au in authors:
                author_list.append(au.text)
            #print(author_list)
        except:
            print(url)



        new_row = {
            '뉴스URL': url,
            '뉴스업체': siteName_val,
            '기사제목': title_val,
            '작성일자': createDate_val,
            '수정일자': modifyDate_val,
            '본문내용': text_list,
            '이미지URL': str(' '.join(img_url_list)),
            '작성기자&이메일': ' '.join(author_list),
        }
        new_row_df = pd.DataFrame([new_row], columns=columns)

        df = pd.concat([df,new_row_df], ignore_index=True)
        time.sleep(3)


    df.to_csv(f"./data/{i}-{today}_naver_news_crawling.csv", encoding="utf-8-sig")
















