# -*- coding: utf-8 -*-
# Author:tomorrow505

import tkinter as tk
from tkinter import Label, E, Entry, StringVar, Button
import os
from os.path import getsize, join
import time
import configparser
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import json
from time import sleep
import my_bencode
import re
import datetime
import win32api
import win32con
import threading

str_list = ['TiB', 'GiB', 'MiB', 'KB', 'B']
USER_DATA_PATH = './conf/config_chrome.json'
RESEED_INFO = ''


class ReseedPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.config_dl = self.controller.config_dl

        self.reseed_info = ''

        self.reseed_path = os.path.join(self.config_dl['cache_path'], 'Reseed')
        if not os.path.isdir(self.reseed_path):
            os.mkdir(self.reseed_path)
        self.config_path = join(self.reseed_path, 'reseed_test.ini')
        self.torrent_path = ''
        self.qb = ''

        # self.label_reseed_rule = Label(self, text='自定义规则：', anchor=E)
        # self.var_rule = StringVar()
        # if os.path.exists('./conf/reseed_re_rule.txt'):
        #     with open('./conf/reseed_re_rule.txt', 'r') as f:
        #         self.var_rule.set(f.read())
        # self.entry_rule = Entry(self, textvariable=self.var_rule, width=30)

        self.var_dir = StringVar()
        self.label_show_info = Label(self, text='方案1(从目录导入):', anchor=E)
        self.entry_dir = Entry(self, textvariable=self.var_dir, width=30)

        self.btn_create = Button(self, text='生成配置文件', command=self.mkconfig)

        self.label_show_plan = Label(self, text='方案2(客户端导入):', anchor=E)
        self.btn_load_from_client = Button(self, text='导入', command=self.mkconfig_from_client)

        self.txtContent = tk.scrolledtext.ScrolledText(self, height=23, font=("Helvetica", 10), wrap=tk.WORD)

        self.btn_save = Button(self, text='保存', command=self.saveconfig)

        self.btn_start = Button(self, text='开始', command=self.start_reseed_by_thread)

        self.var_range = StringVar()
        self.label_range = Label(self, text='区间：', anchor=E)
        self.entry_range = Entry(self, textvariable=self.var_range, width=8)

        self.create_page()

    def create_page(self):
        self.label_show_info.place(x=25, y=25, width=80, height=30)
        self.entry_dir.place(x=110, y=25, width=280, height=30)
        self.btn_create.place(x=405, y=25, width=80, height=28)
        self.btn_load_from_client.place(x=635, y=25, width=60, height=28)
        self.label_show_plan.place(x=550, y=25, width=80, height=30)
        self.txtContent.place(x=32, y=75, width=680, height=470)

        self.btn_save.place(x=80, y=555, width=80, height=30)
        self.btn_start.place(x=560, y=555, width=80, height=30)

        self.label_range.place(x=430, y=555, width=40, height=30)
        self.entry_range.place(x=480, y=557, width=60, height=26)

    def mkconfig(self):
        if not self.var_dir.get():
            return

        parser = configparser.ConfigParser()
        all_number = 0

        source_dirs = self.var_dir.get().split(";")
        for dir_ in source_dirs:
            all_number = get_item(dir_, parser, all_number)

        self.config_path = join(self.reseed_path, 'reseed_test.ini')
        with open(self.config_path, 'w', encoding='utf-8') as configfile:
            parser.write(configfile)

        with open(self.config_path, 'r', encoding='utf-8') as configfile:
            lines = configfile.read().replace('{', '').replace('}', '')
            self.txtContent.insert(tk.INSERT, lines)

    def mkconfig_from_client(self):
        self.qb = self.controller.qb
        parser = configparser.ConfigParser()
        torrent_list = []
        torrents = self.qb.torrents()
        dict_torrents = {}
        for item in torrents:
            time_added = item['added_on']
            datearray = datetime.datetime.fromtimestamp(time_added)
            otherstyletime = datearray.strftime("%Y-%m-%d %H:%M:%S")
            # print(otherstyletime, item['name'])
            dict_torrents[otherstyletime] = item
        sorted_dict_torrents = sorted(dict_torrents.items(), key=lambda d: d[1]["added_on"], reverse=True)
        all_number = 0
        for item in sorted_dict_torrents:
            if item[1]['name'] not in torrent_list:
                str_index = 0
                torrent_list.append(item[1]['name'])
                item_str = deal_keyword(item[1]['name'])
                size_of_item = item[1]['size'] / 1024 / 1024 / 1024 / 1024
                while size_of_item < 1:
                    size_of_item = size_of_item * 1024
                    str_index = str_index + 1
                save_path = item[1]['save_path']
                parser[all_number] = {
                    'full_name': item[1]['name'],
                    'search_keyword': item_str,
                    'size': '%.2f %s' % (size_of_item, str_list[str_index]),
                    'create_time': item[0],
                    'abs_path': save_path
                }
                all_number = all_number + 1
        self.config_path = join(self.reseed_path, 'reseed_test.ini')
        with open(self.config_path, 'w', encoding='utf-8') as configfile:
            parser.write(configfile)

        with open(self.config_path, 'r', encoding='utf-8') as configfile:
            lines = configfile.read().replace('{', '').replace('}', '')
            self.txtContent.insert(tk.INSERT, lines)

    def saveconfig(self):
        items = self.txtContent.get(0.0, tk.END)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            f.write(items)

    def start_reseed_by_thread(self):
        t = threading.Thread(target=self.start_reseed, args=())
        t.start()

    def start_reseed(self):
        if os.path.exists(USER_DATA_PATH):
            with open(USER_DATA_PATH, 'r') as config_file:
                reseed_info_ = json.load(config_file)
                if 'reseed_info' in reseed_info_.keys():
                    self.reseed_info = reseed_info_['reseed_info']
                else:
                    reseed_info_['reseed_info'] = ''
                    self.reseed_info = ''

        if not self.reseed_info:
            app = self.MyCollectApp()
            app.mainloop()
            return
        self.qb = self.controller.qb
        self.torrent_path = join(self.reseed_path, 'torrents').replace('/', '\\')
        if not os.path.isdir(self.torrent_path):
            os.mkdir(self.torrent_path)

        filelist = list(os.listdir(self.torrent_path))
        for file in filelist:
            if os.path.isfile(join(self.torrent_path, file)) and file.endswith('.torrent'):
                os.remove(join(self.torrent_path, file))

        driver_ = get_driver(self.torrent_path)
        parser = configparser.ConfigParser()
        parser.read(self.config_path, encoding='utf-8')

        sections = parser.sections()

        start = int(self.var_range.get().split('-')[0])
        end = int(self.var_range.get().split('-')[1])

        start_index = sections.index(str(start))
        end_index = sections.index(str(end))

        count = 0
        in_use_list = []
        for section in sections[start_index: end_index+1]:
            keyword = parser[section]['search_keyword']
            size = parser[section]['size'].split(' ')[0]
            abs_path = parser[section]['abs_path']
            full_name = parser[section]['full_name']
            download_torrent_by_keyword(reseed_info=self.reseed_info, keyword=keyword, driver=driver_, size=size)
            sleep(2)
            while True:
                torrents = os.listdir(self.torrent_path)
                if any(torrent.endswith('.torrent.crdownload') for torrent in torrents):
                    sleep(1)
                else:
                    break

            for torrent in torrents:
                abs_torrent_path = os.path.join(self.torrent_path, torrent)
                if abs_torrent_path.endswith('.torrent') and abs_torrent_path not in in_use_list:
                    if check_if_matched(full_name, abs_torrent_path):
                        os.rename(abs_torrent_path, os.path.join(self.torrent_path, str(count) + '.torrent'))
                        torrent = os.path.join(self.torrent_path, str(count) + '.torrent')
                        torrent_file = open(torrent, 'rb')
                        self.qb.download_from_file(torrent_file, savepath=abs_path, category='自动', skip_checking='true',
                                                   paused='true')
                        in_use_list.append(torrent)
                        torrent_file.close()
                        count = count + 1

        sleep(4)
        driver_.quit()

    class MyCollectApp(tk.Toplevel):  # 重点
        def __init__(self):
            super().__init__()  # 重点
            x = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            y = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            width = 400
            height = 100
            self.xls_text = tk.StringVar()
            self.wm_geometry('%dx%d+%d+%d' % (width, height, (x - width) / 2, (y - height) / 2))
            self.setupui()

        def setupui(self):
            l1 = tk.Label(self, text="扩展信息：", height=2, width=10)
            l1.place(x=30, y=20, width=60, height=30)
            entry_1 = tk.Entry(self, textvariable=self.xls_text)
            entry_1.place(x=90, y=20, width=280, height=28)

            btn = tk.Button(self, text="点击确认", command=self.on_click)
            btn.place(x=180, y=60, width=80, height=30)

        def on_click(self):
            global RESEED_INFO
            # print(self.xls_text.get().lstrip())
            reseed_info_ = self.xls_text.get().lstrip()
            if len(reseed_info_) == 0:
                # print("用户名必须输入!")
                tk.messagebox.showwarning(title='系统提示', message='请输入扩展信息!')
                return False
            with open(USER_DATA_PATH, 'r') as config_file:
                reseed_info_tmp = json.load(config_file)
                reseed_info_tmp['reseed_info'] = reseed_info_
            with open(USER_DATA_PATH, 'w') as config_file_2:
                json.dump(reseed_info_tmp, config_file_2)
            # print(ReseedPage.reseed_info)
            self.destroy()


def getdirsize(dir_):
    size = 0
    for root, dirs, files in os.walk(dir_):
        size += sum([getsize(join(root, name)) for name in files])
    return size


def get_item(base_dir, parser, all_number):
    items = os.listdir(base_dir)

    # print('当前目录下有%d个项目：' % len(items))
    for item in items:
        # print(all_number, item)
        str_index = 0
        path = os.path.join(base_dir, item)
        if os.path.isdir(path):
            if not os.listdir(path):
                item_str = ''
            else:
                item_str = deal_keyword(item)
                try:
                    size_of_item = getdirsize(path)/1024/1024/1024/1024
                except FileNotFoundError:
                    size_of_item = float('inf')
                while size_of_item < 1:
                    size_of_item = size_of_item * 1024
                    str_index = str_index + 1
        else:
            item_str = item[0: item.rfind('.')].replace('.', ' ')
            item_str = deal_keyword(item_str)
            size_of_item = getsize(path)/1024/1024/1024/1024
            while size_of_item < 1:
                size_of_item = size_of_item * 1024
                str_index = str_index + 1
        timearray = time.localtime(os.path.getatime(path))
        otherstyletime = time.strftime("%Y-%m-%d %H:%M:%S", timearray)

        if item_str:
            parser[all_number] = {
                'full_name': item,
                'search_keyword': item_str,
                'size': '%.2f %s' % (size_of_item, str_list[str_index]),
                'create_time': otherstyletime,
                'abs_path': base_dir
            }
            all_number = all_number + 1

    return all_number


def deal_keyword(string):
    item_str = string.replace('.', ' ')
    # item_str = item_str.replace('-', ' ')
    item_str = item_str.replace('DD5 1', ' ')
    item_str = item_str.replace('DD 5 1', ' ')
    item_str = item_str.replace('BluRay', ' ')
    item_str = item_str.replace('x264', ' ')
    item_str = item_str.replace('AAC', ' ')
    item_str = re.sub(
        '\[|\]|,|\(|\)|_|(1080[pP])|(DTS)|!|([Ff][Ll][Aa][Cc])|(\d{2,3}0[xX]\d{2,3}0)|([Bb][Dd][Rr][Ii][Pp])'
        '|\+|&|([xXHh]26[45])|(\d{1,3}-\d{1,3}Fin)|(OVA)|(OAD)|(10bit)|(TrueHD)|(Hi10P)|(DTS-HD)'
        '|(Ma10p_1080p)|(Audio)', ' ', item_str)
    item_str = re.sub(' +', ' ', item_str)

    item_strs = item_str.split(' ')
    back_item_strs = list(item_strs)
    for item in item_strs:
        if len(item) <= 3 and item.isalnum():
            back_item_strs.remove(item)

    item_str = ' '.join(back_item_strs)
    item_str = item_str.replace('-', ' ')
    item_str = re.sub(' +', ' ', item_str).strip()
    if len(item_str) == 0:
        item_str = string
    return item_str


def get_driver(savepath):
    with open(USER_DATA_PATH, 'r') as config_file:
        user_data = json.load(config_file)['user_data']
        user_data = '/'.join(user_data.split('\\'))
        user_data = '--user-data-dir=' + user_data
        # print(user_data)
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': savepath}
        options.add_experimental_option('prefs', prefs)
        options.add_argument(user_data)

        if os.path.exists('./bin/chromedriver.exe'):
            driver = webdriver.Chrome(executable_path='./bin/chromedriver.exe', chrome_options=options)
        else:
            driver = webdriver.Chrome(executable_path='chromedriver.exe', chrome_options=options)

    return driver


def download_torrent_by_keyword(reseed_info, keyword, driver, size):

    url_ = 'chrome-extension://{info}/index.html#/search-torrent/{keyword}'.\
        format(info=reseed_info, keyword=keyword)

    driver.get(url_)
    driver.refresh()
    print('正在打印关键字【%s】的搜索结果：' % keyword)
    while True:
        try:
            tag = driver.find_element_by_xpath('//*[@id="inspire"]/div[5]/main/div/div/div/div[1]/div')
            if tag.text.find('Search completed') >= 0:
                try:
                    number = re.findall('found (\d{1,4}) results', tag.text)
                    number = number[0]
                    print('找到%d条结果' % number)
                except Exception as exc:
                    pass
                break
            elif tag.text.find('搜索完成') >= 0:
                try:
                    number = re.findall('共找到 (\d{1,3}) 条结果', tag.text)
                    number = number[0]
                    print('找到%d条结果' % number)
                except Exception:
                    pass
                break
        except NoSuchElementException:
            pass
    # driver.find_element_by_xpath('//*[@id="inspire"]/div[4]/main/div/div/div/div[2]/div[2]/div[1]/table/thead/tr[1]'
    #                              '/th[4]/i').click()

    table = driver.find_element_by_xpath('//*[@id="inspire"]/div[5]/main/div/div/div/div[2]/div[2]/div[1]/table')
    table = table.find_element_by_tag_name('tbody')

    trs = table.find_elements_by_tag_name('tr')
    for tr in trs:
        td_list = []
        tds = tr.find_elements_by_tag_name('td')
        for td in tds:
            td_list.append(td.text)
        try:
            if abs(float(td_list[3].split(' ')[0])-float(size)) < 0.011:
                a = tds[1].find_element_by_tag_name('a')
                print(a.get_attribute('href'))
                try:
                    a = tds[8].find_element_by_tag_name('a')
                    a.click()
                except NoSuchElementException:
                    try:
                        li = tds[8].find_elements_by_tag_name('i')
                        li[2].click()
                    except WebDriverException:
                        driver.execute_script("arguments[0].scrollIntoView(true);", li[2])
                        li[2].click()
                except WebDriverException:
                    driver.execute_script("arguments[0].scrollIntoView(true);", a)
                    driver.execute_script("window.scrollBy(0, -100)")
                    a.click()
                except Exception as exc:
                    pass
                    # print('错误：', exc)
            else:
                pass
        except IndexError:
            pass
        # td_list.append(a_href)
        # print([td_list[0], td_list[1], td_list[3], td_list[9]])


def check_if_matched(name, torrent_path):
    with open(torrent_path, 'rb') as fh:
        torrent_data = fh.read()
    torrent = my_bencode.decode(torrent_data)
    info = torrent[0][b'info']
    file_dir = info[b'name'].decode('utf-8')

    if file_dir == name:
        return True
    else:
        return False
