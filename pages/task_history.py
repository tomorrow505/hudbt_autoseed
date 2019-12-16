# -*- coding: utf-8 -*-
# Author:Chengli

import tkinter as tk
from tkinter import ttk, Frame, Scrollbar, LEFT, RIGHT, Y, Button
import webbrowser


class TaskPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.qb = None
        self.task_loaded = False
        self.config_dl = self.controller.config_dl
        self.cu = self.controller.cu
        self.cx = self.controller.cx
        self.btn_load = Button(self, text='导入任务', command=self.load_task)
        self.btn_copy = Button(self, text='打开链接', command=self.copy_links)
        self.btn_readd = Button(self, text='重新添加', command=self.task_readd)
        self.btn_delete = Button(self, text='永久删除', command=self.task_delete)

        self.task_frame = Frame(self)
        self.scrollBar = Scrollbar(self.task_frame)
        self.tree = ttk.Treeview(self.task_frame, columns=('c1', 'c2'), show="headings",
                                 yscrollcommand=self.scrollBar.set)

        self.create_page()

    def create_page(self):
        self.btn_load.place(x=110, y=20, width=80, height=30)
        self.btn_copy.place(x=250, y=20, width=80, height=30)
        self.btn_readd.place(x=390, y=20, width=80, height=30)
        self.btn_delete.place(x=530, y=20, width=80, height=30)

        self.scrollBar.pack(side=RIGHT, fill=Y)

        # 在Frame容器中使用Treeview组件实现表格功能
        # Treeview组件，三列，显示表头，带垂直滚动条

        # 设置每列宽度和对齐方式
        self.tree.column('c1', width=540, anchor='w')
        self.tree.column('c2', width=160, anchor='center')
        # self.tree.column('c3', width=60, anchor='center')

        # 设置每列表头标题文本
        self.tree.heading('c1', text='种子链接', command=lambda: self.treeview_sort_column(self.tree, 'c1', False))
        self.tree.heading('c2', text='添加时间', command=lambda: self.treeview_sort_column(self.tree, 'c2', False))
        # self.tree.heading('c3', text='状态码', command=lambda: self.treeview_sort_column(self.tree, 'c3', False))
        # self.tree.insert('', 0, values=['蝴蝶', 'https://hudbt.hust.edu.cn', ''])

        # 左对齐，纵向填充
        self.tree.pack(side=LEFT, fill=Y)
        self.tree.bind('<Double-1>', self.treeviewclick)

        # Treeview组件与垂直滚动条结合
        self.scrollBar.config(command=self.tree.yview)
        self.task_frame.place(x=20, y=70, width=720, height=500)

    def treeview_sort_column(self, tv, col, reverse):  # Treeview、列名、排列方式
        ll = [(tv.set(k, col), k) for k in tv.get_children('')]
        ll.sort(reverse=reverse)  # 排序方式
        for index, (val, k) in enumerate(ll):  # 根据排序后索引移动
            tv.move(k, '', index)
        tv.heading(col, command=lambda: self.treeview_sort_column(tv, col, not reverse))

    def copy_links(self):
        if not self.tree.selection():
            tk.messagebox.showerror('抱歉', '请至少选择一个任务')
            return
        urls = []
        for item in self.tree.selection():
            value_link = self.tree.item(item, 'values')[0]
            urls.append(value_link)
            webbrowser.open(value_link)
        self.controller.clipboard_clear()
        self.controller.clipboard_append('\n'.join(urls))

    def load_task(self):
        if self.task_loaded:
            task_all = self.tree.get_children()
            for item in task_all:
                self.tree.delete(item)
        self.cu.execute("select * from task")
        res = self.cu.fetchall()
        for item in res:
            values = [item[1], item[2]]
            self.tree.insert('', 0, values=values)
        self.task_loaded = True

    def task_readd(self):
        if not self.tree.selection():
            tk.messagebox.showerror('抱歉', '请至少选择一个任务')
            return
        for item in self.tree.selection():
            value_link = self.tree.item(item, 'values')[0]
            self.controller.frames['AutoUploadPage'].add_task_by_link(value_link)

    def task_delete(self):
        if not self.tree.selection():
            tk.messagebox.showerror('抱歉', '请至少选择一个任务')
            return
        for item in self.tree.selection():
            value_link = self.tree.item(item, 'values')[0]
            self.cu.execute("delete from task where link = '%s'" % value_link)
            self.cx.commit()
            self.tree.delete(item)

    def treeviewclick(self, event):
        task = self.tree.selection()[0]
        value_link = self.tree.item(task, 'values')[0]
        self.cu.execute("select * from task where link = '%s'" % value_link)
        res = self.cu.fetchall()
        for item in res:
            values = item[3].replace('tomorrow505', '\'')
            tk.messagebox.showinfo('详情', values)
            break
