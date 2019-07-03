import requests
import re
import time
from bs4 import BeautifulSoup

"""
单个事故页面解析代码，由site_map_crawler调用
"""

domain_name = 'https://lessonslearned.faa.gov/'
headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"}
sleep_n = 10

def get_home_page_info(home_page_url):
    """
    主页和其他描述页面的不同之处在于多了右下角一个表
    :param home_page_url: 主页url
    :return: 主页元素字典 dict
    """
    home_page = {}
    home_page['url'] = home_page_url
    home_page_html = requests.get(home_page['url'], headers=headers)
    home_page_soup = BeautifulSoup(home_page_html.text, 'lxml').find('div', id='vNavContent')
    # 该soup中包含了右侧表结构，提取description时要将该部分抛去
    home_page['description'] = get_descriptions(home_page_soup)
    home_page['pictures'] = get_pictures(home_page_soup)  # 图片和pdf直接采用home_page_soup即可
    home_page['pdfs'] = get_pdfs(home_page_soup)
    home_page['Accident Perspectives:'] = get_home_page_table(home_page_soup)  # 表结构soup
    return home_page


def get_home_page_table(home_page_soup):
    """
    获取主页右下角表的内容，共四个部分，返回表内容字典
    :param home_page_soup: 主页的soup
    :return:返回表内容的字典，dict
    """
    tds_soup = home_page_soup.find('div', class_='imgNorm_Per').find_all('td')
    table = {}
    table['Airplane Life Cycle'] = '; '.join([text for text in tds_soup[0].stripped_strings])
    table['Accident Threat Categories'] = '; '.join([text for text in tds_soup[1].stripped_strings])
    table['Groupings'] = '; '.join([text for text in tds_soup[2].stripped_strings])
    table['Accident Common Themes'] = '; '.join([text for text in tds_soup[3].stripped_strings])
    return table


def get_attribute(attribute_url):
    """
    获得非home_page页面的页面解析结果字典，含'url','description','pictures','pdfs'
    :param attribute_url: 除主页外的其他属性页面的url
    :return: 返回该属性页的字典 dict
    """
    attribute = {}
    attribute['url'] = attribute_url
    attribute_html = requests.get(attribute['url'], headers=headers)
    attribute_html_soup = BeautifulSoup(attribute_html.text, 'lxml').find('div', id='vNavContent')
    attribute['description'] = get_descriptions(attribute_html_soup)
    attribute['pictures'] = get_pictures(attribute_html_soup)
    attribute['pdfs'] = get_pdfs(attribute_html_soup)
    return attribute


def get_descriptions(html_soup):
    """
    获取抓取页面的描述信息，会对段落进行分段，返回字符串
    :return: descriptions Str
    """
    descriptions = []  # 先建立列表，存储特定段落，之后再将其拼接为str
    # 对子孙节点进行遍历，获取descriptions
    for sibling in html_soup.descendants:
        if sibling.name in ['p', 'ul', 'ol', 'h1,', 'h2', 'h3']:
            descriptions.append(sibling.get_text())
    if descriptions[-1] == 'Back to top':
        descriptions.pop(-1)  # 删除最后一个Back to top
    descriptions = '\n'.join(descriptions)  # 转字符串
    return descriptions


def get_pictures(html_soup):
    """
    获取抓取页面的图片类表，列表中每个图片元素为一个字典，包含'name'和'url'两部分
    :return: pictures List
    """
    pictures = []
    for img in html_soup.find_all('img'):
        picture_url = domain_name + re.findall(r"[\.\.\/]*(\..*)", img['src'])[0]  # 有jpg和gif两种
        picture_name = img.get_text()
        pictures.append({'name': picture_name, 'url': picture_url})
    return pictures


def get_pdfs(html_soup):
    """
    获取抓取页面的pdf类表，列表中每个pdf元素为一个字典，包含'name'和'url'两部分
    :return: pictures List
    """
    pdfs = []
    for pdf in html_soup.find_all(href=has_pdf):
        pdf_url = domain_name + re.findall(r"[\.\.\/]*(.*pdf)", pdf['href'])[0]
        pdf_name = pdf.get_text()
        pdfs.append({'name': pdf_name, 'url': pdf_url})
    return pdfs


def has_pdf(href):
    """
    提取PDF 标签
    :param href:
    :return:
    """
    return href and re.compile("pdf").search(href)


def get_introduce(accident_url):
    """
    获取单个事故的具体信息，共包括13项：Home page, Accident Overview,Accident Board Findings ...
    每项单独为一个字典，都包括'url','description','pictures', 'pdfs'四个键，前两个为字符串，后两个为字典，
    Home page还多一个Accident Common Themes字典，是主页特有的表格解析结果
    :param accident_url:事故主页url
    :return:事故详细信息介绍字典
    """
    accident_html = requests.get(accident_url, headers=headers)
    accident_soup = BeautifulSoup(accident_html.text, 'lxml')
    attributes = accident_soup.find('li', class_='isLB').find_all('a')  # 属性列表
    accident_introduce = {}
    accident_introduce['Home page'] = get_home_page_info(domain_name+attributes.pop(0)['href'])  # 第一个是主页，采用不同的解析方式
    for attribute_tag in attributes:
        time.sleep(sleep_n)
        accident_introduce.update({attribute_tag.get_text():get_attribute(domain_name + attribute_tag['href'])})
    return accident_introduce


if __name__ == '__main__':
    print(get_introduce('https://lessonslearned.faa.gov/ll_main.cfm?TabID=1&LLID=26&LLTypeID=0'))
