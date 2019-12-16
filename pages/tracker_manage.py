# -*- coding: utf-8 -*-
# Author:Chengli


import tkinter as tk
from tkinter import Label, Entry, Button, StringVar


CONFIG_DL_PATH = './conf/config_dl.json'


class TrackerPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.config_dl = self.controller.config_dl
        self.qb = None

        self.subtitute_frame = tk.LabelFrame(self, text='批量替换', height=200, width=200)
        self.label_o = Label(self.subtitute_frame, text="源始tracker：", font=("Helvetica", 10))
        self.label_d = Label(self.subtitute_frame, text="修改tracker：", font=("Helvetica", 10))
        self.var_o = StringVar()
        self.var_d = StringVar()
        self.entry_o = Entry(self.subtitute_frame, textvariable=self.var_o, width=70, borderwidth=2, font=('Helvetica', '12'))
        self.entry_d = Entry(self.subtitute_frame, textvariable=self.var_d, width=70, borderwidth=2, font=('Helvetica', '12'))
        self.button_change = Button(self.subtitute_frame, text="替换", command=self.change_tracker)

        self.add_frame = tk.LabelFrame(self, text='批量增加', height=200, width=200)
        self.label_ao = Label(self.add_frame, text="源始tracker：", font=("Helvetica", 10))
        self.label_ad = Label(self.add_frame, text="新增tracker：", font=("Helvetica", 10))
        self.var_ao = StringVar()
        self.var_ad = StringVar()
        self.entry_ao = Entry(self.add_frame, textvariable=self.var_ao, width=70, borderwidth=2, font=('Helvetica', '12'))
        self.entry_ad = Entry(self.add_frame, textvariable=self.var_ad, width=70, borderwidth=2, font=('Helvetica', '12'))
        self.button_add = Button(self.add_frame, text="增加", command=self.add_tracker)

        self.delete_frame = tk.LabelFrame(self, text='批量删除(1、tracker；2、种子——模糊匹配)', height=200, width=200)

        self.label_do = Label(self.delete_frame, text="源始tracker：", font=("Helvetica", 10))
        self.label_dd = Label(self.delete_frame, text="种子消息值 ：", font=("Helvetica", 10))
        self.var_do = StringVar()
        self.var_dd = StringVar()
        self.entry_do = Entry(self.delete_frame, textvariable=self.var_ao, width=70, borderwidth=2,
                              font=('Helvetica', '12'))
        self.entry_dd = Entry(self.delete_frame, textvariable=self.var_ad, width=70, borderwidth=2,
                              font=('Helvetica', '12'))
        self.button_delete = Button(self.delete_frame, text="删除", command=self.delete_tracker)

        self.create_page()

    def create_page(self):

        self.subtitute_frame.place(x=40, y=20, width=660, height=160)

        self.label_o.place(x=20, y=20, width=80, height=30)
        self.label_d.place(x=20, y=60, width=80, height=30)
        self.entry_o.place(x=120, y=20, width=500, height=30)
        self.entry_d.place(x=120, y=60, width=500, height=30)
        self.button_change.place(x=310, y=100, width=60, height=30)

        self.add_frame.place(x=40, y=210, width=660, height=160)
        self.label_ao.place(x=20, y=20, width=80, height=30)
        self.label_ad.place(x=20, y=60, width=80, height=30)
        self.entry_ao.place(x=120, y=20, width=500, height=30)
        self.entry_ad.place(x=120, y=60, width=500, height=30)
        self.button_add.place(x=310, y=100, width=60, height=30)

        self.delete_frame.place(x=40, y=400, width=660, height=160)
        self.label_do.place(x=20, y=20, width=80, height=30)
        self.label_dd.place(x=20, y=60, width=80, height=30)
        self.entry_do.place(x=120, y=20, width=500, height=30)
        self.entry_dd.place(x=120, y=60, width=500, height=30)
        self.button_delete.place(x=310, y=100, width=60, height=30)

    def change_tracker(self):
        self.qb = self.controller.qb
        torrents = self.qb.torrents()

        origin_tracker = self.var_o.get()
        new_tracker = self.var_d.get()

        for torrent in torrents:
            if torrent['tracker'] == origin_tracker:
                hash_value = torrent['hash']
                self.qb.edit_tracker(hash_value, origin_tracker, new_tracker)

    def add_tracker(self):
        self.qb = self.controller.qb
        torrents = self.qb.torrents()

        origin_tracker = self.var_ao.get()
        new_tracker = self.var_ad.get()

        for torrent in torrents:
            if torrent['tracker'] == origin_tracker:
                hash_value = torrent['hash']
                self.qb.add_trackers(hash_value, new_tracker)

    def delete_tracker(self):
        self.qb = self.controller.qb
        torrents = self.qb.torrents()

        origin_tracker = self.var_do.get()
        message = self.var_dd.get()

        if message:
            for torrent in torrents:
                hash_value = torrent['hash']
                tackers = self.qb.get_torrent_trackers(hash_value)
                for tracker in tackers:
                    if tracker['msg'].find(message) >= 0:
                        self.qb.delete(hash_value)
                        break

        if origin_tracker:
            for torrent in torrents:
                hash_value = torrent['hash']
                tackers = self.qb.get_torrent_trackers(hash_value)
                for tracker in tackers:
                    if tracker['url'].find(origin_tracker) >= 0:
                        self.qb.remove_trackers(hash_value, tracker['url'])
                        break

