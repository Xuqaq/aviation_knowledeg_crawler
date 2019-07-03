import requests
import pymongo
import os
import time

"""
媒体文件下载代码，通过遍历MongoDB进行下载
"""

headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"}
sleep_n = 5


def creat_file(download_url):
        """
        下载单个media文件，并存储在本地，media文件的名字从其下载url中提取
        :param download_url: media的下载url
        :return:
        """
        name = download_url[download_url.rfind('/',) + 1:]
        file = requests.get(download_url, headers=headers)
        f = open(name, 'ab')  # 写入多媒体文件必须要 b 这个参数
        f.write(file.content)  # 多媒体文件要用conctent
        f.close()


def creat_chenge_dir(path):
        """
        创建文件夹并转到该文件夹，若之前存在，则直接转到该文件夹
        :param path:要创建的文件夹路径
        """
        isExists = os.path.exists(path)
        if not isExists:
                os.makedirs(path)
        os.chdir(path)


def accident_media_downloader(accident,root):
        """
        对单个accident的medias进行下载
        :param accident:accident dict
        :param root:该accident存储根目录
        """
        accident_name = accident['name'].strip()  # 去掉开头或结尾的空格！！！
        accident_root = os.path.join(root, accident_name)
        creat_chenge_dir(accident_root)  # 切换至事故文件夹

        # 创建Related Videos and Animations文件夹并存储动画
        accident_video_root = os.path.join(accident_root, 'Related Videos and Animations')
        creat_chenge_dir(accident_video_root)
        for video in accident['Related Videos and Animations']:
                creat_file(video['download url'])
                time.sleep(sleep_n)

        # 创建descriptions文件
        accident_descriptions_root = os.path.join(accident_root, 'descriptions')
        creat_chenge_dir(accident_descriptions_root)
        for description_key,description in  accident['descriptions'].items():
                # 转到13个描述文件中
                description_root = os.path.join(accident_descriptions_root, description_key.replace(r'/',''))
                # 部分属性名中含有'/',使用''代替
                creat_chenge_dir(description_root)
                # 依次转到pictures,pdfs
                for key in ['pictures','pdfs']:
                        key_root = os.path.join(description_root, key)
                        creat_chenge_dir(key_root)
                        for file_dic in description[key]:
                                creat_file(file_dic['url'])
                                time.sleep(sleep_n)


def read_donload(root,db_url,db_name,collection_name,):
        """
        读取数据库accidents col数据，并对每个accident的media下载并存储到本地
        :param root: 存储根目录
        :param db_url:
        :param db_name:
        :param collection_name:
        """
        t1 = time.time()
        conn = pymongo.MongoClient(db_url)
        db = conn[db_name]
        table = db[collection_name]
        root = os.path.join(root,collection_name)
        data = list(table.find())
        for accident in data:  # 在此处可以设定特定事故
                print(accident['name']+' Start')
                accident_media_downloader(accident,root)
                print(accident['name']+' Over')
                print(time.time() - t1)


if __name__ == '__main__':
    root = "D:\\"
    collection_name = 'Transport_Airplane_Site_Map'
    db_name = 'Accident'
    db_url = 'mongodb://localhost:27017/'
    read_donload(root, db_url, db_name, collection_name, )
