# -*- coding: utf-8 -*-
# Author:tomorrow505

import tkinter as tk
from tkinter import Label, E, Entry, StringVar, Button, Frame, Scrollbar, ttk, RIGHT, Y, LEFT
import os
import requests
from bs4 import BeautifulSoup
import json
import re
import webbrowser


class InvitePage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.config_path = './conf/hudbt.json'
        self.data = self.load_data()

        self.var_email = StringVar()
        self.label_email = Label(self, text='邀请邮箱：', anchor=E)
        self.entry_email = Entry(self, textvariable=self.var_email, width=30, font=("Helvetica", 12))

        self.btn_send = Button(self, text='发送邀请', command=self.send_invite)
        self.btn_take = Button(self, text='收回邀请', command=self.take_invite)
        self.btn_sear = Button(self, text='获取链接', command=self.get_hashlink)

        self.btn_fetch = Button(self, text='未验证邮箱', command=self.unco_email)
        self.btn_confirm = Button(self, text='进行验证', command=self.con_email)

        self.txtContent = tk.scrolledtext.ScrolledText(self, height=23, font=("Helvetica", 12), wrap=tk.WORD)

        self.invite_frame = Frame(self)
        self.scrollBar = Scrollbar(self.invite_frame)
        self.tree = ttk.Treeview(self.invite_frame, columns=('c1', 'c2', 'c3'), show="headings",
                                 yscrollcommand=self.scrollBar.set)

        self.menu = tk.Menu(self, tearoff=0)
        # self.menulink = tk.Menu(self.menu, tearoff=0)
        # self.menucopylink = tk.Menu(self.menu, tearoff=0)

        # self.frame = tk.LabelFrame(self, text='各站邀请楼')
        # self.btn_hudbt = Button(self.frame, text='蝴蝶', command=open_hudbt)
        # self.btn_byr = Button(self.frame, text='北邮人', command=open_byr)
        # self.btn_nypt = Button(self.frame, text='南洋', command=open_nypt)
        # self.btn_tjupt = Button(self.frame, text='北洋', command=open_tjupt)
        # self.btn_npupt = Button(self.frame, text='蒲公英', command=open_npupt)
        # self.btn_maitian = Button(self.frame, text='麦田', command=open_maitian)
        # self.btn_whupt = Button(self.frame, text='珞樱', command=open_whupt)

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/'
                          '537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        }

        self.unco_user = {}

        self.create_page()

    def create_page(self):
        self.label_email.place(x=20, y=25, width=80, height=30)
        self.entry_email.place(x=105, y=25, width=280, height=30)
        self.btn_send.place(x=400, y=25, width=80, height=28)
        self.btn_take.place(x=500, y=25, width=80, height=28)
        self.btn_sear.place(x=600, y=25, width=80, height=28)
        self.txtContent.place(x=32, y=75, width=680, height=200)

        self.btn_fetch.place(x=33, y=300, width=80, height=28)
        self.btn_confirm.place(x=133, y=300, width=80, height=28)

        self.scrollBar.pack(side=RIGHT, fill=Y)

        # 设置每列宽度和对齐方式
        self.tree.column('c1', width=200, anchor='center')
        self.tree.column('c2', width=240, anchor='center')
        self.tree.column('c3', width=260, anchor='center')

        # 设置每列表头标题文本
        self.tree.heading('c1', text='Name', command=lambda: self.treeview_sort_column(self.tree, 'c1', False))
        self.tree.heading('c2', text='eMail', command=lambda: self.treeview_sort_column(self.tree, 'c2', False))
        self.tree.heading('c3', text='added', command=lambda: self.treeview_sort_column(self.tree, 'c3', False))
        # self.tree.insert('', 0, values=['蝴蝶', 'https://hudbt.hust.edu.cn', ''])

        # 左对齐，纵向填充
        self.tree.pack(side=LEFT, fill=Y)
        # self.tree.bind('<Double-1>', self.treeviewclick)

        # Treeview组件与垂直滚动条结合
        self.scrollBar.config(command=self.tree.yview)
        self.invite_frame.place(x=32, y=350, width=680, height=200)

        self.menu.add_command(label='蝴蝶邀请区', command=open_hudbt)
        self.menu.add_command(label='北邮邀请区', command=open_byr)
        self.menu.add_command(label='南洋邀请区', command=open_nypt)
        self.menu.add_command(label='北洋邀请区', command=open_tjupt)
        self.menu.add_command(label='麦田邀请区', command=open_maitian)
        self.menu.add_command(label='珞樱邀请区', command=open_whupt)
        self.menu.add_command(label='蒲公英邀请区', command=open_npupt)

        self.bind('<ButtonRelease-3>', self.onrightbuttonup)
        self.tree.bind('<ButtonRelease-3>', self.onrightbuttonup)
        self.txtContent.bind('<ButtonRelease-3>', self.onrightbuttonup)

        # self.frame.place(x=32, y=478, width=670, height=90)
        # self.btn_hudbt.place(x=30, y=15, width=60, height=30)
        # self.btn_byr.place(x=120, y=15, width=60, height=30)
        # self.btn_nypt.place(x=210, y=15, width=60, height=30)
        # self.btn_tjupt.place(x=300, y=15, width=60, height=30)
        # self.btn_npupt.place(x=390, y=15, width=60, height=30)
        # self.btn_maitian.place(x=480, y=15, width=60, height=30)
        # self.btn_whupt.place(x=570, y=15, width=60, height=30)

    def treeview_sort_column(self, tv, col, reverse):  # Treeview、列名、排列方式
        ll = [(tv.set(k, col), k) for k in tv.get_children('')]
        ll.sort(reverse=reverse)  # 排序方式
        for index, (val, k) in enumerate(ll):  # 根据排序后索引移动
            tv.move(k, '', index)
        tv.heading(col, command=lambda: self.treeview_sort_column(tv, col, not reverse))

    def onrightbuttonup(self, event):
        self.menu.post(event.x_root, event.y_root)

    def send_invite(self):
        send_str = '''Hi,

我邀请你加入 蝴蝶-HUDBT, 这是一个拥有丰富资源的非开放社区. 
如果你有兴趣加入我们请阅读规则并确认邀请.最后,请确保维持一个良好的分享率 
并分享允许的资源.

欢迎到来! :)
{name}'''.format(name=self.data['name'])

        send_url = 'https://hudbt.hust.edu.cn/takeinvite.php?id=%d' % self.data['id']

        email = self.var_email.get()
        if not email:
            return
        email_check = re.search('[a-zA-Z0-9].*@.*\..*', email)
        if email_check:
            try:
                data = {
                    'email': email,
                    'body': send_str
                }
                response = requests.post(url=send_url, data=data, cookies=self.data['cookie'])
                # print(response.text)
                if response.status_code == 200:
                    print('邀请发送成功')
                    value = self.get_hash_value(email)
                    link = 'https://hudbt.hust.edu.cn/signup.php?type=invite&invitenumber=' + value
                    info = '私信内容：\n%s\n邀请链接如上，请及时注册，验证出现问题请PM或加群：105548142，' \
                           '验证消息：HUDBT。\n\n回帖内容：\n邀请链接已经PM，请查看收件箱信息，及时注册。' % link
                    self.txtContent.delete(0.0, tk.END)
                    self.txtContent.insert(tk.INSERT, info)
                else:
                    print('失败')
            except Exception as exc:
                print('发送邀请失败：%s' % exc)

    def take_invite(self):
        take_url = 'https://hudbt.hust.edu.cn/invite.php'
        email = self.var_email.get()
        if not email:
            return
        email_check = re.search('[a-zA-Z0-9].*@.*\..*', email)
        if email_check:
            try:
                hash_value = self.get_hash_value(email)
                data = {
                    'type': 'recover',
                    'id': self.data['id'],
                    'invitee': email,
                    'hash': hash_value
                }
                response = requests.post(url=take_url, data=data, cookies=self.data['cookie'], headers=self.headers)
                # print(response.text)
                if response.status_code == 200:
                    print('邀请回收成功')
                else:
                    print('邀请回收失败')
            except Exception as exc:
                print('回收邀请出现错误：%s' % exc)

    def load_data(self):
        config_tmp = {}
        if not os.path.exists(self.config_path):
            pass
        else:
            try:
                with open(self.config_path, 'r') as config_file:
                    config_tmp = json.load(config_file)
            except Exception as exc:
                print("config_dl.json load failed: %s" % exc)
        return config_tmp

    def get_hash_value(self, email):
        session = requests.session()
        session.headers = self.headers
        req_url = 'https://hudbt.hust.edu.cn/invite.php?id=%d' % self.data['id']
        html = session.get(req_url, cookies=self.data['cookie']).text
        soup = BeautifulSoup(html, 'lxml')
        table = soup.find_all('table')[-1]
        tbody = table.find('tbody')
        if not tbody:
            print('当前没有被邀请者')
            return
        try:
            trs = tbody.find_all('tr')
            for tr in trs:
                tds = tr.find_all('td')
                if tds[0].get_text().find(email) >= 0:
                    td = tds[2]
                    form = td.find('form')
                    inputs = form.find_all('input')
                    value = inputs[-2].get_attribute_list('value')[0]
                    return value
        except Exception as exc:
            print('获取hash链接错误：%s' % exc)

    def get_hashlink(self):
        email = self.var_email.get()
        if not email:
            return
        email_check = re.search('[a-zA-Z0-9].*@.*\..*', email)
        if email_check:
            hash_value = self.get_hash_value(email)
            info = '\n\n邀请链接如上，请及时注册，验证出现问题请PM或加群：105548142,验证消息：HUDBT。'
            hash_link = 'https://hudbt.hust.edu.cn/signup.php?type=invite&invitenumber=' + hash_value + info
            self.txtContent.delete(0.0, tk.END)
            self.txtContent.insert(tk.INSERT, hash_link)

    def unco_email(self):
        session = requests.session()
        session.headers = self.headers
        req_url = 'https://hudbt.hust.edu.cn/unco.php'
        html = session.get(req_url, cookies=self.data['cookie']).text
        soup = BeautifulSoup(html, 'lxml')

        table = soup.find('table')

        if table:
            try:
                # tbody = table.find('tbody')
                trs = table.find_all('tr')[1:]
                for tr in trs:
                    user = []
                    inputs = tr.find_all('input')
                    user_id = inputs[1].get_attribute_list('value')[0]
                    # print(input_value)

                    user.append(user_id)

                    tds = tr.find_all('td')[0:3]
                    for td in tds:
                        info = td.get_text().strip()
                        user.append(info)
                    values = [user[1], user[2], user[3]]
                    self.tree.insert('', 0, values=values)
                    self.unco_user[user[1]] = user
            except Exception as exc:
                print('查询未验证用户出错： %s' % exc)
        else:
            print('当前没有未验证用户……')

    def con_email(self):
        req_url = 'https://hudbt.hust.edu.cn/modtask.php'
        if not self.tree.selection():
            tk.messagebox.showerror('抱歉', '请至少选择一个用户')
            return
        item = self.tree.selection()[0]
        value_name = self.tree.item(item, 'values')[0]
        user = self.unco_user[value_name]
        user_id = user[0]
        try:
            data = {
                'action': 'confirmuser',
                'userid': user_id,
                'confirm': 'confirmed'
            }
            response = requests.post(url=req_url, data=data, cookies=self.data['cookie'], headers=self.headers)
            # print(response.text)
            if response.text.find('The user account has been updated.') >= 0:
                print('用户验证成功！！')
                self.tree.delete(item)
            else:
                print('用户验证失败！！')
        except Exception as exc:
            print('用户验证出现错误：%s' % exc)


def open_hudbt():
    webbrowser.open('https://hudbt.hust.edu.cn/forums.php?action=viewforum&forumid=16')


def open_byr():
    webbrowser.open('https://bt.byr.cn/forums.php?action=viewtopic&forumid=29&topicid=11105')


def open_nypt():
    webbrowser.open('https://nanyangpt.com/forums.php?action=viewtopic&forumid=33&topicid=2468')


def open_tjupt():
    webbrowser.open('https://www.tjupt.org/forums.php?action=viewtopic&forumid=34&topicid=15935')


def open_npupt():
    webbrowser.open('https://npupt.com/forums.php?action=viewtopic&topicid=1944&page=0')


def open_maitian():
    webbrowser.open('https://pt.nwsuaf6.edu.cn/forums.php?action=viewtopic&forumid=8&topicid=8568')


def open_whupt():
    webbrowser.open('https://bt.byr.cn/forums.php?action=viewtopic&forumid=29&topicid=11105')