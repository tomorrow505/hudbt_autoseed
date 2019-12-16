# -*- coding: utf-8 -*-
# Author:tomorrow505

import tkinter as tk
from tkinter import ttk, StringVar, Frame, Scrollbar, LEFT, RIGHT, Y, Entry, Button

import bencoder
import os
from tkinter.filedialog import askdirectory
import shutil
import common_methods


class ResumePage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.qb = ''
        self.config_dl = self.controller.config_dl

        self.var_dir = StringVar()
        # self.label_show_info = Label(self, text='', anchor=E)
        self.entry_dir = Entry(self, textvariable=self.var_dir, width=60)
        self.btn_open = Button(self, text='打开Resume.dat目录', command=self.select_folder)

        self.btn_parser = Button(self, text='解析', command=self.parse_resume)

        self.parser_frame = Frame(self)
        self.scrollBar = Scrollbar(self.parser_frame)
        self.tree = ttk.Treeview(self.parser_frame, columns=('c1', 'c2', 'c3'), show="headings",
                                 yscrollcommand=self.scrollBar.set)

        self.label_info = tk.Label(self, text='状态码说明——0：正常; 1：种子文件缺失; 2：资源文件缺失', fg='red')
        self.btn_start = Button(self, text='开始', command=self.start_reseed)

        self.create_page()

    def create_page(self):
        self.btn_open.place(x=510, y=25, width=140, height=30)
        self.entry_dir.place(x=20, y=25, width=480, height=30)
        # self.btn_open.place(x=635, y=25, width=20, height=30)
        self.btn_parser.place(x=665, y=25, width=50, height=30)

        self.label_info.place(x=30, y=555, width=480, height=30)
        self.btn_start.place(x=560, y=555, width=80, height=30)

        self.scrollBar.pack(side=RIGHT, fill=Y)

        # 在Frame容器中使用Treeview组件实现表格功能
        # Treeview组件，三列，显示表头，带垂直滚动条

        # 设置每列宽度和对齐方式
        self.tree.column('c1', width=420, anchor='w')
        self.tree.column('c2', width=200, anchor='w')
        self.tree.column('c3', width=60, anchor='center')

        # 设置每列表头标题文本
        self.tree.heading('c1', text='种子名称', command=lambda: self.treeview_sort_column(self.tree, 'c1', False))
        self.tree.heading('c2', text='保存目录', command=lambda: self.treeview_sort_column(self.tree, 'c2', False))
        self.tree.heading('c3', text='状态码', command=lambda: self.treeview_sort_column(self.tree, 'c3', False))
        # self.tree.insert('', 0, values=['蝴蝶', 'https://hudbt.hust.edu.cn', ''])

        # 左对齐，纵向填充
        self.tree.pack(side=LEFT, fill=Y)
        # self.tree.bind('<Double-1>', self.treeviewclick)

        # Treeview组件与垂直滚动条结合
        self.scrollBar.config(command=self.tree.yview)
        self.parser_frame.place(x=20, y=80, width=730, height=460)

    def select_folder(self):
        path_ = askdirectory()
        self.var_dir.set(path_.replace('/', '\\'))

    def parse_resume(self):
        path = r"%s\resume.dat" % self.var_dir.get()
        #  Reading of the file for decoding
        if not os.path.exists(path):
            tk.messagebox.showerror('Error', 'Resume.dat文件不存在')
            return
        f = open(path, "rb")
        d = bencoder.decode(f.read())
        for key in d:
            if key == b'.fileguard':
                pass
            elif key == b'rec':
                pass
            else:
                filename = key.decode()
                path = d[key][b'path'].decode()
                # if os.path.exists(path):
                #     yes_or_no = '否'
                # else:
                #     yes_or_no = '是'
                code = self.get_statu_code(filename, path)
                save_dir = '\\'.join(path.split('\\')[0:-1])
                values = [filename, save_dir, code]
                self.tree.insert('', 0, values=values)

    def start_reseed(self):
        self.qb = self.controller.qb
        task_all = self.tree.get_children()
        for task in task_all:
            torrent_name = self.tree.item(task, 'values')[0]
            save_path = self.tree.item(task, 'values')[1]
            code = int(self.tree.item(task, 'values')[2])
            if code == 0:
                torrent_path = self.var_dir.get() + '\\%s' % torrent_name
                tmp_path = self.var_dir.get() + '\\tmp.torrent'
                shutil.copy(torrent_path, tmp_path)
                torrent_file = open(tmp_path, 'rb')
                self.qb.download_from_file(torrent_file, savepath=save_path, category='自动', skip_checking='true',
                                           paused='true')
                torrent_file.close()
                os.remove(tmp_path)
                self.tree.item(task, values=(torrent_name, save_path, '完成'))

    def treeview_sort_column(self, tv, col, reverse):  # Treeview、列名、排列方式
        ll = [(tv.set(k, col), k) for k in tv.get_children('')]
        ll.sort(reverse=reverse)  # 排序方式
        for index, (val, k) in enumerate(ll):  # 根据排序后索引移动
            tv.move(k, '', index)
        tv.heading(col, command=lambda: self.treeview_sort_column(tv, col, not reverse))

    def get_statu_code(self, torrent_name, file_path):
        code = 0
        torrent_path = self.var_dir.get() + '\\%s' % torrent_name
        if not os.path.exists(torrent_path):
            code = 1
        else:
            if not common_methods.check_for_file_exists(torrent_path, file_path):
                code = code + 2

        return code
