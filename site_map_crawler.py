import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from secondary_page import get_introduce
import time
import re

"""
爬虫主文件
"""

headers = {'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"}
# 浏览器请求头（大部分网站没有这个请求头会报错、请务必加上哦）
domain_name = 'https://lessonslearned.faa.gov/'
mongo_url = "mongodb://localhost:27017/"
db_name = "Accident"
my_set = "Transport_Airplane_Site_Map"
sleep_n = 10


def get_accidents_soups(all_url):
    """
    获取信息表HTML
    :param all_url:表所在页面的URL
    :return:
    """
    all_url = all_url  # 开始的URL地址
    start_html = requests.get(all_url,  headers=headers)
    all_Soup = BeautifulSoup(start_html.text, 'lxml')  # 解析html

    accident_soups = all_Soup.find('table', summary='Lessons Learned From Transport Airplane Accidents Site Map').find_all('tr')
    accident_soups.pop(0)
    return accident_soups


def get_ralated_video_download_url(related_video_url):
    """
    获取视频下载URL
    :param related_video_url:
    :return: 视频下载URL
    """
    time.sleep(sleep_n)
    videoe_html = requests.get(related_video_url, headers=headers)
    video_soup = BeautifulSoup(videoe_html.text, 'lxml')
    related_video_download_url = related_video_url[:related_video_url.rfind('/', ) + 1] + video_soup.find('param', {'name': 'movie'})['value']
    return related_video_download_url


def get_related_videos(related_videos_html_soup):
    """
    解析动画td（格子）
    其中一个td中可能含多条动画，每层label1中存放一条动画相关信息，label1中的text中存放动画名称
    label1中的label2标签中存放动画的url（此时的url还只是能链接到该动画页面，并不能直接下载）
    :param related_videos_html: 存放相关动画的td的soup
    :return: 返回该td的列表
    """
    related_videos_list = []  # 可能有多条，用字典存储
    for related_video in related_videos_html_soup.find_all('a'):
        related_video_name = related_video.get_text()  # 获取视频名称
        related_video_url = domain_name + re.findall(r"window.open\('[\.\.\/]*(.*htm)'", related_video['onclick'])[0]
        related_video_download_url = get_ralated_video_download_url(related_video_url)
        related_videos_list.append({'name':related_video_name,'url':related_video_url,'download url':related_video_download_url})
    return related_videos_list


def insert_accident_dict(db_name, my_set, data_dict, mongo_url):
    """
    存储单个事故到MongoDB中，该事故为一个document，
    :param db_name:
    :param data_dict: 单个事故字典
    :param mongo_url:
    :return:
    """
    conn = MongoClient(mongo_url)
    db = conn[db_name]
    my_set = db[my_set]
    data_dict['_id'] = data_dict['name']
    print("存储中:", data_dict['name'])
    my_set.insert(data_dict)
    print("end")


def get_accident_info(accidents_soups):
    """
    :param all_tr: 事故html的列表 [事故1html，事故2html，事故3html，...]
    :param domain_name: 域名，用于链接地址的恢复
    """
    t1 = time.time()
    i = 0
    for tr in accidents_soups:  # 每行分两部分，前一部分的td是事故的名字和对应描述的URL，第二部分td是该事故对应的相关动画
        time.sleep(sleep_n)
        print(i)
        td_list = tr.find_all('td')  # 表的第一列为事故的name和url，第二列为相关动画（可能为多条）
        accident_dict = {} # 存放事故A的信息
        accident_dict['name'] = td_list[0].get_text()
        print(accident_dict['name'] + "开始抽取")
        accident_dict['url'] = domain_name + td_list[0].find('a')['href'].replace('amp;','')  # 将解析多出来的&amp;还原为&
        accident_dict['descriptions'] = get_introduce(accident_dict['url'])  # 获取事故页面的详细信息，是字典
        # 存放事故A的相关动画信息
        accident_dict['Related Videos and Animations'] = get_related_videos(td_list[1])  # 可能有多条，用列表存储
        print(accident_dict['name'] + "开始存储")
        insert_accident_dict(db_name, my_set, accident_dict, mongo_url)
        print(accident_dict['name'] + "存储完毕")
        print(time.time() - t1)
        i += 1


if __name__ == '__main__':
    all_url = 'https://lessonslearned.faa.gov/ll_site_map.cfm'
    accidents_soups = get_accidents_soups(all_url)
    get_accident_info(accidents_soups)  # 在此处可以设定爬取特定事故

