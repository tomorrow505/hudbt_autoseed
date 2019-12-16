# -*- coding: utf-8 -*-
# Author:tomorrow505

import shutil
import tkinter as tk
from tkinter import Label, StringVar, Button, ttk, W, E
import tkinter.filedialog
from tkinter.filedialog import askdirectory
import tkinter.scrolledtext
import re
import os
import common_methods
import get_douban_info
import get_media_info
import autoseed_task
import html_handler

TITLE_FONT = ("Helvetica", 18, "bold")


class DescrPanel(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # self.config_dl = commen_component.load_config_dl()

        self.var_link = StringVar()

        self.button_get_descr = Button(self, text="一键获取简介", command=self.get_descr)

        self.entry_link = tk.Entry(self, textvariable=self.var_link, width=80, borderwidth=3, font=('Helvetica', '10'))
        self.entry_link.bind('<Return>', self.enter_click)

        self.txtContent = tkinter.scrolledtext.ScrolledText(self, height=23, font=("Helvetica", 10), wrap=tkinter.WORD)

        self.btn_clear = Button(self, text="清空", command=self.clear_descr)

        self.label_remind = Label(self, text='温馨提示：链接包括原始站点链接，或者IMDB/豆瓣链接', fg='red', anchor=W)

        self.label_link = Label(self, text='链接', font=("Helvetica", 10), anchor=W)

        self.create_page()

    def create_page(self):

        self.label_link.place(x=30, y=20, width=50, height=30)

        self.entry_link.place(x=80, y=20, width=620, height=30)

        self.button_get_descr.place(x=30, y=65, width=120, height=30)

        self.btn_clear.place(x=170, y=65, width=60, height=30)

        self.label_remind.place(x=280, y=65, width=570, height=30)

        self.txtContent.place(x=32, y=110, width=680, height=450)

    def get_descr(self):

        # 获取链接
        url = self.var_link.get()
        link_type, url_for_descr = self.__judge_link_type(url)

        if link_type == 'douban_imdb':
            try:
                descr = get_douban_info.get_douban_descr(url_for_descr)
            except Exception as exc:
                tk.messagebox.showerror('错误', '获取豆瓣信息出错：%s' % exc)
        elif link_type == 'detail_link':
            origin_site = common_methods.find_origin_site(url_for_descr)
            if origin_site['abbr'] == 'FRDS':
                html = common_methods.get_response_by_firefox(url_for_descr)
            else:
                response = common_methods.get_response(url_for_descr, origin_site['cookie'])
                html = response.text
            try:
                htmlhandler = html_handler.HtmlHandler(origin_site['abbr'], html)
                raw_info_tmp = htmlhandler.get_raw_info()
                descr = raw_info_tmp['descr']
            except Exception as exc:
                tk.messagebox.showerror('Error', '从源链接获取简介错误：%s' % exc)
        else:
            descr = ''

        self.txtContent.insert(tkinter.INSERT, descr)

    def enter_click(self, event):
        self.get_descr()

    def __judge_link_type(self, url):

        url = self.var_link.get()
        if not url:
            return '', ''
        douban_link = get_douban_info.get_douban_link(url)
        if not douban_link:
            support_sign = common_methods.find_origin_site(url)
            if not support_sign:
                tk.messagebox.showerror('Error', '错误的链接！')
                return '', ''
            else:
                torrent_id = common_methods.get_id(url)
                if torrent_id == -1:
                    tk.messagebox.showerror('Error', '错误的链接！错误的链接！')
                    return '', ''
                else:
                    return 'detail_link', url
        else:
            return 'douban_imdb', douban_link

    def clear_descr(self):
        self.var_link.set('')
        self.txtContent.delete(0.0, tk.END)
