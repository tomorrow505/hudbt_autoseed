# -*- coding: utf-8 -*-
# Author:tomorrow505
from bs4 import BeautifulSoup
import os
import re
import json
import inspect
import requests
import ctypes
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import my_bencode
import psutil
import subprocess
from qbittorrent import Client
import pickle
import webbrowser


AUTHOR = 'tomorrow505'
VERSION = 'V3.2'
THANK_LIST = 'Rach & Lancesaber & Rhilip'
USER_INFO_PATH = './conf/user_info.pickle'


def load_config_dl():

    judge_if_conf_exists()

    config_dl_path = './conf/config_dl.json'
    if not os.path.exists(config_dl_path):
        config_dl_tmp = {
            'Max_Size': 15,
            'study_path': '',
            'movie_path': '',
            'carton_path': '',
            'others_path': '',
            'img_path': '',
            'cache_path': '',
            'rss_open': 0,
            'refresh_time': '10',
            'server_open': 0,
            'anony_close': 0,
            'up_to_hudbt': 1,
            'up_to_nypt': 1,
            'up_to_hdsky': 1,
            'up_to_tjupt': 1,
            'up_to_mteam': 1,
            'up_to_cmct': 1,
            'up_to_ourbits': 1,
            'up_to_hdchina': 1,
            'up_to_ttg': 1,
            'up_to_pter': 1,
            'server_port': '',
            'server_ip': ''
        }
        with open(config_dl_path, 'w') as f:
            json.dump(config_dl_tmp, f)
    else:
        try:
            with open(config_dl_path, 'r') as config_file:
                flag = True
                config_dl_tmp = json.load(config_file)
                if 'up_to_pter' not in config_dl_tmp.keys():
                    config_dl_tmp['up_to_pter'] = 0
                    flag = False
            if not flag:
                with open(config_dl_path, 'w') as f:
                    json.dump(config_dl_tmp, f)
        except Exception as exc:
            config_dl_tmp = ''
            print("config_dl.json load failed: %s" % exc)

    return config_dl_tmp


def judge_if_conf_exists():
    if os.path.exists('./conf'):
        pass
    else:
        os.mkdir('./conf')


# 定义用来删除线程
def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
    raise SystemError("PyThreadState_SetAsyncExc failed")


# 结合删除线程的函数对线程进行删除操作
def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


def show_info():

    show_str = '''
            help                    呼出帮助菜单
            post detail_link        提交详情页链接进行下载/发布
            get detail_link         提交详情页链接获取下载状态
            cancle detail_link      提交详情页链接取消下载
            exit                    退出
    '''
    return show_str


def load_pt_sites():
    pt_sites = {}
    try:
        with open('./conf/config_sites.json', 'r') as pt_file:
            pt_sites = json.load(pt_file)
    except (FileNotFoundError, Exception):
        pass
    finally:
        return pt_sites


def find_origin_site(url):
    match_site = ''
    pt_sites = load_pt_sites()
    for site in pt_sites.keys():
        domain = pt_sites[site]['domain']
        if ''.join(url.split(' ')).find(domain) >= 0:
            match_site = site
            break
    if match_site == '':
        return 0
    pt_site = pt_sites[match_site]
    return pt_site


def get_id(url):
    if url.find('totheglory.im') >= 0:
        id_ = re.search(r'(\d{2,10})', url)
    elif url.find('passthepopcorn') >= 0:
        id_ = re.search(r'torrentid=(\d{2,10})', url)
    else:
        id_ = re.search(r'id=(\d{2,10})', url)
    try:
        my_id = id_.group(1)
        # id_info.append('获取id成功')
        # print('获取id成功')
    except Exception as exc:
        # id_info.append('获取id失败！%s' % exc)
        # print('获取id失败！%s' % exc)
        my_id = -1

    return my_id


def get_response(url, cookie):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/'
                      '537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    }
    session = requests.session()

    session.keep_alive = False

    session.headers = headers

    response = session.get(url, cookies=cookie)

    return response


def get_download_url(html, pt_site, tid):
    if pt_site['domain'] == 'totheglory.im':
        download_url = "https://{host}/dl/{tid}/{passkey}".format(host=pt_site['domain'],
                                                                  tid=tid, passkey=pt_site['passkey'])
    elif pt_site['domain'] == 'hdsky.me':
        download_url = "https://{host}/download.php?id={tid}&passkey={passkey}".format(
            host=pt_site['domain'], tid=tid, passkey=pt_site['passkey'])
    elif pt_site['domain'] == 'hdchina.org':
        download_url = get_hdchina_download_url(html)
    elif pt_site['domain'] == 'www.beitai.pt':
        download_url = "http://{host}/download.php?id={tid}".format(host=pt_site['domain'], tid=tid)
    else:
        download_url = "https://{host}/download.php?id={tid}".format(host=pt_site['domain'], tid=tid)
    return download_url


def get_hdchina_download_url(html):
    soup = BeautifulSoup(html, 'lxml')
    download_link = soup.find('a', id='clip_target').get_text()
    return download_link


def check_for_file_exists(torrent_path, file_path):
    with open(torrent_path, 'rb') as fh:
        torrent_data = fh.read()
    torrent = my_bencode.decode(torrent_data)
    info = torrent[0][b'info']
    if b'files' in info.keys():
        files = info[b'files']
        for file in files:
            new_path = []
            for path in file[b'path']:
                new_path.append(path.decode('utf-8'))
            append_file_path = '\\'.join(new_path)
            new_file_path = file_path + '\\' + append_file_path
            # print(new_file_path)
            if not os.path.exists(new_file_path):
                return False
    else:
        if os.path.exists(file_path):
            return True

    return True


def parser_torrent(file_path):

    torrent_info = {}
    with open(file_path, 'rb') as fh:
        torrent_data = fh.read()
    torrent = my_bencode.decode(torrent_data)
    info = torrent[0][b'info']

    file_dir = info[b'name'].decode('utf-8')
    torrent_info['name'] = file_dir

    if b'files' in info.keys():
        file_length = 0
        biggest = 0
        file_path = ''
        files = info[b'files']
        for file in files:
            file_length = file_length + file[b'length']
            new_path = []
            if file[b'length'] > biggest:
                for path in file[b'path']:
                    new_path.append(path.decode('utf-8'))
                if new_path[-1].endswith(('.mp4', '.mkv', '.avi', '.mov', '.rmvb', '.ts')):
                    biggest = file[b'length']
                    file_path = '\\'.join(new_path)
        file_path = file_dir + '\\' + file_path
        torrent_info['file_path'] = file_path
        torrent_info['file_dir'] = file_dir
        torrent_info['size'] = length2size(file_length)

    else:
        torrent_info['size'] = length2size(info[b'length'])
        torrent_info['file_path'] = file_dir
        torrent_info['file_dir'] = ''

    return torrent_info


def length2size(length):
    str_list = ['TiB', 'GiB', 'MiB', 'KB', 'B']
    power = 1024
    str_index = 0
    size = length / (power**4)
    while size < 1:
        size = size * 1024
        str_index = str_index + 1
    return '%.2f %s' % (size, str_list[str_index])


def kill_myself():

    exe = 'HUDBT-UPLOADER-%s.exe' % VERSION

    pids = psutil.pids()

    for pid in pids:
        p = psutil.Process(pid)
        # print('pid-%s,pname-%s' % (pid, p.name()))
        if p.name() == exe:
            cmd = 'taskkill /F /IM %s' % exe
            # os.system(cmd)
            subprocess.call(cmd, shell=True)
            break


def get_response_by_firefox(url):
    # 配置文件路径
    profile_path = r'C:\Users\CL\AppData\Roaming\Mozilla\Firefox\Profiles\dwj2youj.default'
    # 加载配置数据
    profile = webdriver.FirefoxProfile(profile_path)

    options = webdriver.FirefoxOptions()

    options.headless = True

    options.add_argument('--disable-gpu')  # 这里是禁用GPU加速

    driver = webdriver.Firefox(firefox_profile=profile, options=options)

    driver.get(url)

    WebDriverWait(driver, 30, 0.5).until(EC.presence_of_element_located((By.ID, 'kdescr')))

    html = driver.page_source

    driver.quit()

    return html


def relogin():
    try:
        with open(USER_INFO_PATH, "rb") as usr_file:
            usrs_info = pickle.load(usr_file)
            ip = usrs_info['ip']
            port = usrs_info['port']
            name = usrs_info['name']
            pwd = usrs_info['pwd']
            qb = Client('http://{ip}:{port}/'.format(ip=ip, port=port))
            qb.login(name, pwd)
            return qb
    except Exception as exc:
        print('重新认证出错： %s' % exc)
   
        
def refine_title(title):
    title = title.replace('DD2 0', 'DD 2.0')
    title = title.replace('DD 2 0', 'DD 2.0')
    title = title.replace('DD5 1', 'DD 5.1')
    title = title.replace('DD 5 1', 'DD 5.1')
    title = title.replace('DD+5 1', 'DD+5.1')
    title = title.replace('DD+ 5 1', 'DD+5.1')
    title = title.replace('DDP5 1', 'DDP 5.1')
    title = title.replace('DDP 5 1', 'DDP 5.1')
    title = title.replace('DDP7 1', 'DDP 7.1')
    title = title.replace('DDP 7 1', 'DDP 7.1')
    title = title.replace('DDP+7 1', 'DDP+ 7.1')
    title = title.replace('DDP2 0', 'DDP2.0')
    title = title.replace('DDP 2 0', 'DDP 2.0')
    title = title.replace('DDP+2 0', 'DDP+2.0')

    title = title.replace('MA2 0', 'MA 2.0')
    title = title.replace('MA 2 0', 'MA 2.0')
    title = title.replace('MA5 1', 'MA 5.1')
    title = title.replace('MA 5 1', 'MA 5.1')
    title = title.replace('MA6 1', 'MA 6.1')
    title = title.replace('MA 6 1', 'MA 6.1')
    title = title.replace('MA7 1', 'MA 7.1')
    title = title.replace('MA 7 1', 'MA 7.1')
    title = title.replace('HDMA', 'HD MA')
    title = title.replace('TrueHD7 1', 'TrueHD 7.1')
    title = title.replace('TrueHD 7 1', 'TrueHD 7.1')
    title = title.replace('Atmos7 1', 'Atmos 7.1')
    title = title.replace('Atmos 7 1', 'Atmos 7.1')

    title = title.replace('DTS-X 7 1', 'DTS-X 7.1')
    title = title.replace('DTS HD', 'DTS-HD')

    title = title.replace('AAC2 0', 'AAC 2.0')
    title = title.replace('AAC 2 0', 'AAC 2.0')
    title = title.replace('AAC1 0', 'AAC 1.0')
    title = title.replace('AAC 1 0', 'AAC 1.0')

    return title

# if __name__ == "__main__":
#     url = 'https://pt.keepfrds.com/details.php?id=9589'
#     get_response_by_firefox(url)


# if __name__ == "__main__":
#     my_path = r'C:\Users\CL\Desktop\种子\ut\utorrent\Android 带服务端IM即时通讯App 全程MVP手把手打造.torrent'
#     # path = r'E:\test\cache\Kaabil 2017 NF WEB-DL 1080p DD 5 1 - DDP 5 1 ESub _tjupt_182704.torrent'
#     my_file_path = r'J:\HUDBT\Android 带服务端IM即时通讯App 全程MVP手把手打造'
#     print(check_for_file_exists(my_path, my_file_path))
