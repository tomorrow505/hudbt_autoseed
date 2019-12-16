# -*- coding: utf-8 -*-
# Author:Chengli

import tkinter as tk
from tkinter import Label, Entry, StringVar, Button, scrolledtext
import os
import get_media_info
import thumbnails_try as pvs
from tkinter.filedialog import askdirectory
import webbrowser
import subprocess
import random
import threading
from time import sleep
# import json
# import re

USER_DATA_PATH = './conf/config_chrome.json'
RESEED_INFO = ''


class VideoInfoPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.config_dl = self.controller.config_dl
        self.img_path = os.path.join(self.config_dl['cache_path'], 'imgs')
        self.qb = None

        self.video_path = ''
        self.full_pic_path = ''

        self.label_info = Label(self, text='根据视频文件绝对地址或种子hash值即可获取视频mediainfo、截图到cache目录',
                                fg='red')
        self.pic_pth = StringVar()
        self.label_pic_path = Label(self, textvariable=self.pic_pth, fg='red')
        self.var_dir = StringVar()

        self.entry_dir = Entry(self, textvariable=self.var_dir, width=30)
        self.btn_open = Button(self, text='视频地址', command=self.open_file)

        self.btn_get_mediainfo = Button(self, text='获取MediaInfo', command=self.get_media_info)
        self.btn_get_picture = Button(self, text='获取截图', command=self.get_image)
        self.btn_send_picture = Button(self, text='一键上传', command=self.upload_pic)

        self.txtContent = scrolledtext.ScrolledText(self, height=23, font=("Helvetica", 10), wrap=tk.WORD)

        # self.label_host_img = Label(self, text='发布到备选图床：')
        # self.btn_1 = Button(self, text='图床1', command=open_luguo)
        # self.btn_2 = Button(self, text='图床2', command=open_smms)
        # self.btn_3 = Button(self, text='图床3', command=open_imgbb)
        # self.btn_4 = Button(self, text='图床4', command=open_imgurl)
        # self.btn_5 = Button(self, text='图床5', command=open_xiaojian)
        # self.btn_6 = Button(self, text='图床6', command=open_psb)
        # self.btn_7 = Button(self, text='图床7', command=open_pter)
        # self.btn_8 = Button(self, text='图床8', command=open_catbox)

        self.create_page()

    def create_page(self):
        self.label_info.place(x=95, y=10, width=480, height=30)
        self.entry_dir.place(x=25, y=50, width=580, height=30)
        self.btn_open.place(x=625, y=50, width=80, height=28)
        self.btn_get_mediainfo.place(x=25, y=95, width=100, height=28)
        self.btn_get_picture.place(x=135, y=95, width=80, height=28)
        self.btn_send_picture.place(x=625, y=95, width=80, height=28)
        self.label_pic_path.place(x=220, y=95, width=430, height=28)
        self.txtContent.place(x=25, y=135, width=700, height=415)
        # self.label_host_img.place(x=25, y=550, width=100, height=28)
        # self.btn_1.place(x=135, y=550, width=50, height=28)
        # self.btn_2.place(x=210, y=550, width=50, height=28)
        # self.btn_3.place(x=285, y=550, width=50, height=28)
        # self.btn_4.place(x=360, y=550, width=50, height=28)
        # self.btn_5.place(x=435, y=550, width=50, height=28)
        # self.btn_6.place(x=510, y=550, width=50, height=28)
        # self.btn_7.place(x=585, y=550, width=50, height=28)
        # self.btn_8.place(x=660, y=550, width=50, height=28)

    def open_file(self):
        self.video_path = tk.filedialog.askopenfilename(title='Open file', filetypes=[('video files', '*')])
        self.var_dir.set(self.video_path.replace('/', '\\'))

    def mkthumbnails(self, action):
        pic_path = ''
        self.video_path = self.var_dir.get()

        if self.video_path.find(':') >= 0:
            video_name = os.path.basename(self.video_path)
            pic_path = os.path.join(self.img_path, video_name + '.jpg')
        else:
            choosen_path = ''
            if len(self.video_path) == 40:
                self.qb = self.controller.qb
                torrents = self.qb.torrents()
                for item in torrents:
                    if item['hash'] == self.video_path:
                        path = item['save_path'] + item['name']
                        if os.path.isfile(path):
                            choosen_path = path
                        else:
                            filelist = list(os.listdir(path))
                            biggest_file_size = 0
                            for file in filelist:
                                file_path = os.path.join(path, file)
                                if file_path.endswith(('.mkv', '.mp4', '.ts', '.avi', 'rmvb', 'vob', 'mpeg')):
                                    file_size = os.path.getsize(file_path)
                                    if file_size > biggest_file_size:
                                        choosen_path = file_path
                if choosen_path:
                    pic_path = self.img_path + '\\' + os.path.basename(choosen_path) + '.jpg'
                    self.video_path = choosen_path
            else:
                return

        if not pic_path:
            self.full_pic_path = 'Error'
            return
        self.pic_pth.set(os.path.basename(pic_path))
        # print(pic_path.replace('/', '\\'))
        vid = pvs.Video(self.video_path)
        vsheet = pvs.Sheet(vid)

        numbers = [12, 8]
        numer = random.choice(numbers)
        vsheet.make_sheet_by_number(numer)
        vsheet.sheet.save(pic_path)
        self.full_pic_path = pic_path.replace('/', '\\')

        # 单纯截图
        if action == 1:
            if os.path.exists(self.full_pic_path):
                func_list = ['luguo', 'imgurl', 'imgbb', 'xiaojian', 'psb', 'smms', 'pter', 'catbox']
                func_str = 'open_' + random.choice(func_list)
                globals().get(func_str)()
                subprocess.call("explorer.exe %s" % os.path.dirname(self.full_pic_path), shell=True)
        # 上传图片
        else:
            if os.path.exists(self.full_pic_path):
                send_choices = [0, 1, 2, 3]
                send_choice = random.choice(send_choices)
                if send_choice == 0:
                    url = get_media_info.send_picture(self.full_pic_path)
                elif send_choice == 1:
                    url = get_media_info.send_picture_2(self.full_pic_path)
                elif send_choice == 2:
                    url = get_media_info.send_picture_3(self.full_pic_path)
                else:
                    url = get_media_info.send_picture_4(self.full_pic_path)
                if url:
                    url = '[img]' + url + '[/img]\n'
                self.txtContent.insert(tk.INSERT, url)

    def get_image(self):
        self.thread_of_thumbnails_1()

    def upload_pic(self):
        self.thread_of_thumbnails_2()

    def get_media_info(self):
        self.video_path = self.var_dir.get()
        if self.video_path.find(':') >= 0:
            pass
        else:
            choosen_path = ''
            if len(self.video_path) == 40:
                self.qb = self.controller.qb
                torrents = self.qb.torrents()
                for item in torrents:
                    if item['hash'] == self.video_path:
                        path = item['save_path'] + item['name']
                        if os.path.isfile(path):
                            choosen_path = path
                        else:
                            filelist = list(os.listdir(path))
                            biggest_file_size = 0
                            for file in filelist:
                                file_path = os.path.join(path, file)
                                if file_path.endswith(('.mkv', '.mp4', '.ts', '.avi', 'rmvb', 'vob', 'mpeg')):
                                    file_size = os.path.getsize(file_path)
                                    if file_size > biggest_file_size:
                                        choosen_path = file_path
                if choosen_path:
                    self.video_path = choosen_path
            else:
                return
        if self.video_path:
            info = get_media_info.get_video_info(self.video_path)
            info_ = '[quote=iNFO][font=Courier New]\n' + info['general'] + '\n\n' + info['Video'] + '\n\n' + \
                    info['Audio'] + '\n[/font][/quote]'
            self.txtContent.insert(tk.INSERT, info_)

    def thread_of_thumbnails_1(self):
        t = threading.Thread(target=self.mkthumbnails, args=(1,))
        t.start()

    def thread_of_thumbnails_2(self):
        t = threading.Thread(target=self.mkthumbnails, args=(2,))
        t.start()


def open_luguo():
    url = 'https://imgchr.com/'
    open_url(url)


def open_imgbb():
    url = 'https://zh-cn.imgbb.com/'
    open_url(url)


def open_imgurl():
    url = 'https://imgurl.org/'
    open_url(url)


def open_xiaojian():
    url = 'https://pic.xiaojianjian.net/'
    open_url(url)


def open_psb():
    url = 'http://www.tc.pepsilovely.cn/'
    open_url(url)


def open_pter():
    url = 'https://img.pter.club/'
    open_url(url)


def open_smms():
    url = 'https://sm.ms/'
    open_url(url)


def open_catbox():
    url = 'http://www.qpic.ws'
    open_url(url)


def open_url(url):
    webbrowser.open(url)


