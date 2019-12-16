# -*- coding: utf-8 -*-
# Author:Chengli

import tkinter as tk
from tkinter.ttk import Treeview
from tkinter import Scrollbar, Frame, StringVar, LEFT, RIGHT, Y, messagebox
import datetime
import webbrowser
from utils import common_methods
import threading
import time
from time import sleep
import autoseed_task
import get_rss_info
import pickle
import subprocess
from math import ceil


CONFIG_DL_PATH = './conf/config_dl.json'
USER_BAK_TASK_PATH = './conf/bak_task.pickle'


class AutoUploadPage(tk.Frame):  # 继承Frame类
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # 存储任务列表
        self.task_dict = {}
        self.complete_task = {}
        self.task_list = []
        self.onduty_list = []

        self.qb = None

        self.cu = self.controller.cu
        self.cx = self.controller.cx

        self.is_rss_mode = False
        self.t = 'Recorde_rss'
        self.refresh_t = 'Recorde_task_list'

        # 布局组件的定义
        self.var_link = StringVar()

        self.entry_link = tk.Entry(self, textvariable=self.var_link, width=58, borderwidth=2, font=('Helvetica', '12'))
        self.entry_link.bind('<Return>', self.enter_add)
        self.button_add = tk.Button(self, text='Add', font=('Helvetica', '12'), width=6, command=self.add_task_by_click)

        self.frame_m = Frame(self)
        self.scrollBar = Scrollbar(self.frame_m)
        self.tree = Treeview(self.frame_m, columns=('c1', 'c2', 'c3'), show="headings", yscrollcommand=self.scrollBar.set)

        self.btnDelete = tk.Button(self, text='删除任务', command=self.delete_task)
        self.btnRefresh = tk.Button(self, text='备份任务', command=self.bak_task)

        self.rsshandler = get_rss_info.RssLinkHandler()

        self.config_dl = self.controller.config_dl

        self.menu = tk.Menu(self, tearoff=0)
        self.menulink = tk.Menu(self.menu, tearoff=0)
        self.menucopylink = tk.Menu(self.menu, tearoff=0)
        self.create_page()

    def create_page(self):

        # 添加种子部分
        # LEFT
        self.entry_link.place(x=30, y=30, width=600, height=30)
        self.var_link.set('请输入种子详情链接：')
        self.entry_link.bind('<FocusIn>', self.on_entry_click)
        self.entry_link.bind('<FocusOut>', self.on_focus_out)
        self.entry_link.config(fg='grey')

        self.button_add.place(x=640, y=28, width=80, height=30)

        # 管理种子部分
        self.frame_m.place(x=28, y=80, width=700, height=450)

        # 在Frame容器中创建滚动条
        self.scrollBar.pack(side=RIGHT, fill=Y)

        # 在Frame容器中使用Treeview组件实现表格功能
        # Treeview组件，三列，显示表头，带垂直滚动条

        # 设置每列宽度和对齐方式
        self.tree.column('c1', width=400, anchor='w')
        self.tree.column('c2', width=140, anchor='center')
        self.tree.column('c3', width=120, anchor='center')

        # 设置每列表头标题文本
        self.tree.heading('c1', text='种子链接', command=lambda: self.treeview_sort_column(self.tree, 'c1', False))
        self.tree.heading('c2', text='添加时间', command=lambda: self.treeview_sort_column(self.tree, 'c2', False))
        self.tree.heading('c3', text='状态', command=lambda: self.treeview_sort_column(self.tree, 'c3', False))

        # 左对齐，纵向填充
        self.tree.pack(side=LEFT, fill=Y)
        self.tree.bind('<Double-1>', self.treeviewclick)
        self.tree.bind('<ButtonRelease-3>', self.onrightbuttonup)

        # Treeview组件与垂直滚动条结合
        self.scrollBar.config(command=self.tree.yview)

        # 删除按钮
        self.btnDelete.place(x=160, y=550, width=120, height=30)

        # 刷新按钮
        self.btnRefresh.place(x=460, y=550, width=120, height=30)

        self.menu.add_command(label='查看进度', command=self.check_progress)
        self.menu.add_command(label='删除任务', command=self.del_task)
        self.menu.add_command(label='暂停下载', command=self.pause)
        self.menu.add_command(label='继续下载', command=self.resume)
        self.menu.add_separator()

        self.menulink.add_command(label='进入源站', command=self.open_link)
        self.menulink.add_command(label='进入蝴蝶', command=self.open_hudbt)
        self.menulink.add_command(label='进入北洋', command=self.open_tjupt)
        self.menulink.add_command(label='进入南洋', command=self.open_nypt)
        self.menulink.add_command(label='进入馒头', command=self.open_mteam)
        self.menulink.add_command(label='进入SSD', command=self.open_ssd)
        self.menulink.add_command(label='进入OurBits', command=self.open_ourbits)
        self.menulink.add_command(label='进入HDSky', command=self.open_hdsky)
        self.menulink.add_command(label='进入HDChina', command=self.open_hdchina)
        self.menulink.add_command(label='进入TTG', command=self.open_ttg)
        self.menulink.add_command(label='进入猫站', command=self.open_pter)
        self.menulink.add_command(label='以上全部', command=self.open_all)
        self.menu.add_cascade(label='打开链接', menu=self.menulink)

        self.menucopylink.add_command(label='源站链接', command=self.copy_link)
        self.menucopylink.add_command(label='蝴蝶链接', command=self.copy_hudbt)
        self.menucopylink.add_command(label='北洋链接', command=self.copy_tjupt)
        self.menucopylink.add_command(label='南洋链接', command=self.copy_nypt)
        self.menucopylink.add_command(label='馒头链接', command=self.copy_mteam)

        self.menucopylink.add_command(label='SSD链接', command=self.copy_ssd)
        self.menucopylink.add_command(label='OurBits链接', command=self.copy_ourbits)
        self.menucopylink.add_command(label='HDSky链接', command=self.copy_hdsky)
        self.menucopylink.add_command(label='HDChina链接', command=self.copy_hdchina)
        self.menucopylink.add_command(label='TTG链接', command=self.copy_ttg)
        self.menucopylink.add_command(label='猫站链接', command=self.copy_pter)
        self.menucopylink.add_command(label='以上全部', command=self.copy_all)
        self.menu.add_cascade(label='复制链接', menu=self.menucopylink)
        self.menu.add_separator()
        self.menu.add_command(label='显示详情', command=self.show_info)
        self.menu.add_command(label='打开文件夹', command=self.open_folder)

    def on_entry_click(self, event):
        """function that gets called whenever entry is clicked"""
        if self.var_link.get() == '请输入种子详情链接：':
            self.var_link.set('')  # delete all the text in the entry
            self.entry_link.config(fg='black')

    def on_focus_out(self, event):
        if self.var_link.get() == '':
            self.var_link.set('请输入种子详情链接：')
            self.entry_link.config(fg='grey')

    # 添加下载任务
    def add_task_by_click(self):
        detail_link = self.var_link.get()
        self.add_task_by_link(detail_link)
        # 重置界面
        self.var_link.set('')
        self.entry_link.config(fg='grey')

    def all_time_refresh(self):
        while True:
            if len(self.onduty_list) == 0:
                break
            else:
                time.sleep(2)
                self.refresh_task()

    def enter_add(self, event):
        self.add_task_by_click()

    # 删除选中项的按钮
    def delete_task(self):
        if not self.tree.selection():
            tk.messagebox.showerror('抱歉', '你还没有选择，不能删除')
            return
        for item in self.tree.selection():
            detail_link = self.tree.item(item, 'values')[0]
            statu = self.tree.item(item, 'values')[2]
            if statu not in ['任务完成', '任务丢失']:
                chosen_task = self.task_dict[detail_link]

                hash_info = chosen_task.get_hash_info()
                if chosen_task.get_statu() != '任务完成' and hash_info:
                    try:
                        torrent = self.qb.get_torrent(infohash=hash_info)
                        if torrent['completion_date'] == -1:
                            self.qb.delete_permanently(hash_info)
                    except Exception:
                        pass
                try:
                    common_methods.stop_thread(chosen_task)
                except ValueError:
                    pass
                except SystemError:
                    pass
                self.task_dict.pop(detail_link)
            self.task_list.remove(detail_link)

            if len(self.onduty_list) == 0:
                try:
                    common_methods.stop_thread(self.refresh_t)
                except ValueError:
                    pass
                except SystemError:
                    pass

            if detail_link in self.onduty_list:
                self.onduty_list.remove(detail_link)
            self.tree.delete(item)

    # 更新所有种子的下载状态
    def refresh_task(self):
        task_all = self.tree.get_children()
        for item in task_all:
            value_link = self.tree.item(item, 'values')[0]
            value_addtime = self.tree.item(item, 'values')[1]
            value_statu = self.tree.item(item, 'values')[2]
            if value_link in self.task_dict.keys():
                value_statu_now = self.task_dict[value_link].get_statu()
                if not value_statu == value_statu_now:
                    self.tree.item(item, values=(value_link, value_addtime, value_statu_now))
                    if value_statu_now == '任务完成' or value_statu_now == '任务丢失':
                        if value_statu_now == '任务完成':
                            self.format_dict_for_completed_task(value_link)
                            task = self.complete_task[value_link]
                            all_statu = task['progress_info']
                            all_statu = '\n'.join(all_statu)
                            try:
                                cmd = 'insert into task(link,tasktime,statu) values("{link}", "{addtime}", "{statu}")'\
                                    .format(link=value_link, addtime=value_addtime,
                                            statu=all_statu.replace('\'', 'tomorrow505'))
                                self.cu.execute(cmd)
                                self.cx.commit()
                            except Exception as exc:
                                print('任务添加至历史记录失败：%s' % exc)
                        try:
                            common_methods.stop_thread(self.task_dict[value_link])
                        except ValueError:
                            pass
                        except SystemError:
                            pass
                        self.onduty_list.remove(value_link)
                        self.task_dict.pop(value_link)
                        if len(self.onduty_list) == 0:
                            try:
                                common_methods.stop_thread(self.refresh_t)
                            except ValueError:
                                pass
                            except SystemError:
                                pass
                elif value_statu_now == '重新加载':
                    self.controller.qb = common_methods.relogin()
                    self.qb = self.controller.qb

    def treeviewclick(self, event):
        selected_item = self.tree.selection()[0]
        link = self.tree.item(selected_item, 'values')[0]
        webbrowser.open(link)

    def treeview_sort_column(self, tv, col, reverse):  # Treeview、列名、排列方式
        ll = [(tv.set(k, col), k) for k in tv.get_children('')]
        ll.sort(reverse=reverse)  # 排序方式
        for index, (val, k) in enumerate(ll):  # 根据排序后索引移动
            tv.move(k, '', index)
        tv.heading(col, command=lambda: self.treeview_sort_column(
            tv, col, not reverse))  # 重写标题，使之成为再点倒序的标题

    def add_rss_task(self):
        while True:
            self.rsshandler.change_refresh_time(self.config_dl['refresh_time'])
            self.rsshandler.now_time = ''
            entries_list = self.rsshandler.get_entries(self.config_dl['Max_Size'])
            for item in entries_list:
                detail_link = item['link']
                if detail_link in self.task_list:
                    continue
                add_time = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                values = [detail_link, add_time, '准备下载']
                self.tree.insert('', 'end', values=values)
                new_task = autoseed_task.AutoSeed(self.qb, item, self.config_dl)
                new_task.start()
                self.task_dict[detail_link] = new_task
                self.task_list.append(detail_link)
                self.onduty_list.append(detail_link)
                if len(self.onduty_list) == 1:
                    self.refresh_t = threading.Thread(target=self.all_time_refresh, args=())
                    self.refresh_t.start()
            if int(self.config_dl['refresh_time']) == 0:
                sleep(600)
            else:
                try:
                    common_methods.stop_thread(self.t)
                except ValueError:
                    pass
                except SystemError:
                    pass
                sleep(int(self.config_dl['refresh_time']-1) * 60 + 30)
                self.t = threading.Thread(target=self.add_rss_task, args=())
                self.t.start()
                self.is_rss_mode = True

    def reopen_rss(self):
        try:
            common_methods.stop_thread(self.t)
        except ValueError:
            pass
        except SystemError:
            pass
        self.t = threading.Thread(target=self.add_rss_task, args=())
        self.t.start()
        self.is_rss_mode = True
        tk.messagebox.showinfo('提示', 'RSS模式已经重启')

    def init_qb(self):

        self.qb = self.controller.qb
        self.get_bak_task()
        self.check_rss_mode()

    def check_rss_mode(self):
        if self.config_dl['rss_open']:
            if not self.is_rss_mode:
                self.t = threading.Thread(target=self.add_rss_task, args=())
                self.t.start()
                self.is_rss_mode = True
                return 'opened'
            else:
                return 'opened_already'
        else:
            if self.is_rss_mode:
                try:
                    common_methods.stop_thread(self.t)
                except ValueError:
                    pass
                except SystemError:
                    pass
                self.is_rss_mode = False
                return 'closed'
            else:
                return 'closed_already'

    def bak_task(self):
        self.refresh_task()
        bak_task = []  # 以列表的形式保存未完成的种子
        task_all = self.tree.get_children()
        for item in task_all:
            value_link = self.tree.item(item, 'values')[0]
            value_statu = self.tree.item(item, 'values')[2]
            if value_statu not in ['任务完成', '任务丢失', '机器人转发']:
                task = self.task_dict[value_link]
                bak_task.append(task.get_origin_url())
                try:
                    common_methods.stop_thread(task)
                except ValueError:
                    pass
                except SystemError:
                    pass
        with open(USER_BAK_TASK_PATH, "wb") as bak_file:  # with open with语句可以自动关闭资源
            pickle.dump(bak_task, bak_file)

    def get_bak_task(self):
        try:
            with open(USER_BAK_TASK_PATH, "rb") as bak_file:
                bak_task = pickle.load(bak_file)
                if not bak_task:
                    return
                for item in bak_task:
                    if isinstance(item, dict):
                        link = item['link']
                    else:
                        link = item
                    add_time = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                    values = [link, add_time, '准备下载']
                    self.tree.insert('', 'end', values=values)
                    new_task = autoseed_task.AutoSeed(self.qb, item, self.config_dl)
                    self.task_dict[link] = new_task
                    self.onduty_list.append(link)
                    self.task_list.append(link)
                    new_task.start()
                    if len(self.onduty_list) == 1:
                        self.refresh_t = threading.Thread(target=self.all_time_refresh, args=())
                        self.refresh_t.start()
        except FileNotFoundError:
            pass

    def add_task_by_link(self, string, mode=0, *args):
        detail_link = string
        # 禁止空或者误操作
        if not detail_link or detail_link == '请输入种子详情链接：':
            return
        # 禁止重复添加的链接
        if detail_link in self.task_list:
            messagebox.showerror('错误', '重复添加的链接！')
            return
        # 禁止不支持的网站
        support_sign = common_methods.find_origin_site(detail_link)
        if support_sign == 0:
            messagebox.showerror('错误', '不支持的网站！')
            return

        torrent_id = common_methods.get_id(detail_link)
        if torrent_id == -1:
            messagebox.showerror('错误', '不是种子详情链接！')
            return
        # 显示任务到列表
        add_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S').replace('-', '/')
        values = [detail_link, add_time, '准备下载']
        # 添加到尾部
        if mode == 0:
            self.tree.insert('', 'end', values=values)
        # 添加到首部
        # self.tree.insert('', 0, values=values)

        # 添加任务到后台并开启
        # 构造元祖实现远程判断
        if args:
            detail_link_tuple = (args[0], detail_link)
        else:
            detail_link_tuple = detail_link
        new_task = autoseed_task.AutoSeed(self.qb, detail_link_tuple, self.config_dl)
        new_task.start()
        self.task_dict[detail_link] = new_task
        self.task_list.append(detail_link)
        self.onduty_list.append(detail_link)
        if len(self.onduty_list) == 1:
            self.refresh_t = threading.Thread(target=self.all_time_refresh, args=())
            self.refresh_t.start()
        return '任务已经添加'

    def get_statu_by_link(self, link):
        task_all = self.tree.get_children()
        for item in task_all:
            value_link = self.tree.item(item, 'values')[0]
            if value_link == link:
                value_statu = self.tree.item(item, 'values')[2]
                return value_statu
        return 'no result'

    def cancle_task_by_link(self, detail_link):

        find = False
        task_all = self.tree.get_children()
        for item in task_all:
            link = self.tree.item(item, 'values')[0]
            if link == detail_link:
                self.tree.delete(item)
                find = True
                break
        if find:
            chosen_task = self.task_dict[detail_link]
            hash_info = chosen_task.get_hash_info()
            if chosen_task.get_statu() != '任务完成' and hash_info:
                self.qb.delete_permanently(hash_info)
            else:
                return '任务还未开始或已经完成'
            try:
                common_methods.stop_thread(chosen_task)
            except ValueError:
                pass
            except SystemError:
                pass
            self.task_list.remove(detail_link)
            self.task_dict.pop(detail_link)
            if detail_link in self.onduty_list:
                self.onduty_list.remove(detail_link)

            return '取消成功'
        else:
            return '没找到任务'

    def close_rss(self):
        self.config_dl['rss_open'] = False
        self.check_rss_mode()

    def open_link(self):
        selected_item = self.tree.selection()[0]
        link = self.tree.item(selected_item, 'values')[0]
        webbrowser.open(link)

    def open_hudbt(self):
        link = self.get_uploaded_link()
        if link['hudbt']:
            webbrowser.open(link['hudbt'])

    def open_tjupt(self):
        link = self.get_uploaded_link()
        if link['tjupt']:
            webbrowser.open(link['tjupt'])
        # else:
        #     webbrowser.open('https://www.tjupt.org/torrents.php')

    def open_nypt(self):
        link = self.get_uploaded_link()
        if link['nypt']:
            webbrowser.open(link['nypt'])
        # else:
        #     webbrowser.open('https://www.tjupt.org/torrents.php')

    def open_mteam(self):
        link = self.get_uploaded_link()
        if link['mteam']:
            webbrowser.open(link['mteam'])

    def open_ssd(self):
        link = self.get_uploaded_link()
        if link['ssd']:
            webbrowser.open(link['ssd'])
        # else:
        #     webbrowser.open('https://www.tjupt.org/torrents.php')

    def open_ourbits(self):
        link = self.get_uploaded_link()
        if link['ourbits']:
            webbrowser.open(link['ourbits'])

    def open_hdsky(self):
        link = self.get_uploaded_link()
        if link['hdsky']:
            webbrowser.open(link['hdsky'])

    def open_hdchina(self):
        link = self.get_uploaded_link()
        if link['hdchina']:
            webbrowser.open(link['hdchina'])

    def open_ttg(self):
        link = self.get_uploaded_link()
        if link['ttg']:
            webbrowser.open(link['ttg'])

    def open_pter(self):
        link = self.get_uploaded_link()
        if link['pter']:
            webbrowser.open(link['pter'])

    def open_all(self):

        all_link = []
        selected_item = self.tree.selection()[0]
        origin_link = self.tree.item(selected_item, 'values')[0]
        all_link.append(origin_link)
        link = self.get_uploaded_link()
        if link['hudbt']:
            all_link.append(link['hudbt'])
        else:
            pass
        if link['tjupt']:
            all_link.append(link['tjupt'])
        else:
            pass
        if link['nypt']:
            all_link.append(link['nypt'])
        else:
            pass
        if link['mteam']:
            all_link.append(link['mteam'])
        else:
            pass

        if link['ssd']:
            all_link.append(link['ssd'])
        else:
            pass
        if link['ourbits']:
            all_link.append(link['ourbits'])
        else:
            pass
        if link['hdsky']:
            all_link.append(link['hdsky'])
        else:
            pass
        if link['hdchina']:
            all_link.append(link['hdchina'])
        else:
            pass
        if link['ttg']:
            all_link.append(link['ttg'])
        else:
            pass
        if link['pter']:
            all_link.append(link['pter'])
        else:
            pass

        for item in all_link:
            webbrowser.open(item)

    def show_info(self):
        selected_item = self.tree.selection()[0]
        link = self.tree.item(selected_item, 'values')[0]
        statu = self.tree.item(selected_item, 'values')[2]
        if not statu == '任务完成':
            if statu == '任务丢失':
                tk.messagebox.showerror('错误', '任务已丢失！')
            else:
                task = self.task_dict[link]
                all_statu = task.get_all_info()
                tk.messagebox.showinfo('详情', '\n'.join(all_statu))
        else:
            task = self.complete_task[link]
            all_statu = task['progress_info']
            tk.messagebox.showinfo('详情', '\n'.join(all_statu))

    def pause(self):
        task = self.get_task()
        if task:
            if isinstance(task, dict):
                hash_info = task['hash_info']
            else:
                hash_info = task.get_hash_info()
            if hash_info:
                try:
                    self.qb.pause(hash_info)
                    task.statu.append('已暂停')
                except Exception as exc:
                    tk.messagebox.showinfo('提示', '出现错误：%s' % exc)
            else:
                tk.messagebox.showerror('错误', '尚未开始下载！！')

    def resume(self):
        task = self.get_task()
        if task:
            if isinstance(task, dict):
                hash_info = task['hash_info']
            else:
                hash_info = task.get_hash_info()
            if hash_info:
                try:
                    self.qb.resume(hash_info)
                    task.statu.append('下载中……')
                except Exception as exc:
                    tk.messagebox.showinfo('提示', '出现错误：%s' % exc)

    def check_progress(self):
        task = self.get_task()
        if task:
            if isinstance(task, dict):
                hash_info = task['hash_info']
            else:
                hash_info = task.get_hash_info()
            if hash_info:
                try:
                    torrent = self.qb.get_torrent(hash_info)
                    if 'progress' in torrent.keys():
                        progress = torrent['progress']*100
                    else:
                        progress = float(torrent['total_downloaded'])/float(torrent['total_size'])*1000
                        progress = ceil(progress)/10.0
                    tk.messagebox.showinfo('已完成', '完成进度：%.1f %s' % (progress, '%'))
                except Exception as exc:
                    tk.messagebox.showinfo('提示', '出现错误：%s' % exc)
        else:
            tk.messagebox.showinfo('错误', '任务已丢失！！')

    def open_folder(self):
        task = self.get_task()
        if task:
            if isinstance(task, dict):
                path = task['path']
            else:
                path = task.get_abs_file_path()
            path = path.replace('/', '\\')
            if path:
                subprocess.call("explorer.exe %s" % path, shell=True)
                # os.system("explorer.exe %s" % path)
            else:
                tk.messagebox.showinfo('提示', '尚未下载……')
        else:
            tk.messagebox.showinfo('错误', '任务已丢失！！')

    def del_task(self):
        self.delete_task()

    def copy_link(self):
        selected_item = self.tree.selection()[0]
        link = self.tree.item(selected_item, 'values')[0]
        self.controller.clipboard_clear()
        self.controller.clipboard_append(link)

    def copy_hudbt(self):
        link = self.get_uploaded_link()
        if link['hudbt']:
            self.controller.clipboard_clear()
            self.controller.clipboard_append(link['hudbt'])

    def copy_tjupt(self):
        link = self.get_uploaded_link()
        if link['tjupt']:
            self.controller.clipboard_clear()
            self.controller.clipboard_append(link['tjupt'])

    def copy_nypt(self):
        link = self.get_uploaded_link()
        if link['nypt']:
            self.controller.clipboard_clear()
            self.controller.clipboard_append(link['nypt'])

    def copy_mteam(self):
        link = self.get_uploaded_link()
        if link['mteam']:
            self.controller.clipboard_clear()
            self.controller.clipboard_append(link['mteam'])

    def copy_ssd(self):
        link = self.get_uploaded_link()
        if link['ssd']:
            self.controller.clipboard_clear()
            self.controller.clipboard_append(link['ssd'])

    def copy_ourbits(self):
        link = self.get_uploaded_link()
        if link['ourbits']:
            self.controller.clipboard_clear()
            self.controller.clipboard_append(link['ourbits'])

    def copy_hdsky(self):
        link = self.get_uploaded_link()
        if link['hdsky']:
            self.controller.clipboard_clear()
            self.controller.clipboard_append(link['hdsky'])

    def copy_hdchina(self):
        link = self.get_uploaded_link()
        if link['hdchina']:
            self.controller.clipboard_clear()
            self.controller.clipboard_append(link['hdchina'])

    def copy_ttg(self):
        link = self.get_uploaded_link()
        if link['ttg']:
            self.controller.clipboard_clear()
            self.controller.clipboard_append(link['ttg'])

    def copy_pter(self):
        link = self.get_uploaded_link()
        if link['pter']:
            self.controller.clipboard_clear()
            self.controller.clipboard_append(link['pter'])

    def copy_all(self):
        all_link = []
        selected_item = self.tree.selection()[0]
        origin_link = self.tree.item(selected_item, 'values')[0]
        all_link.append(origin_link)
        link = self.get_uploaded_link()
        if link['hudbt']:
            all_link.append(link['hudbt'])
        else:
            pass
        if link['tjupt']:
            all_link.append(link['tjupt'])
        else:
            pass
        if link['nypt']:
            all_link.append(link['nypt'])
        else:
            pass
        if link['mteam']:
            all_link.append(link['mteam'])
        else:
            pass
        if link['ssd']:
            all_link.append(link['ssd'])
        else:
            pass
        if link['ourbits']:
            all_link.append(link['ourbits'])
        else:
            pass
        if link['hdsky']:
            all_link.append(link['hdsky'])
        else:
            pass
        if link['hdchina']:
            all_link.append(link['hdchina'])
        else:
            pass
        if link['ttg']:
            all_link.append(link['ttg'])
        else:
            pass

        if link['pter']:
            all_link.append(link['pter'])
        else:
            pass
        
        self.controller.clipboard_clear()
        self.controller.clipboard_append('\n'.join(all_link))

    def onrightbuttonup(self, event):
        if not self.tree.selection():
            pass
        else:
            selected_item = self.tree.selection()[0]
            statu_now = self.tree.item(selected_item, 'values')[2]
            if statu_now not in ['已暂停', '下载中……']:
                self.menu.entryconfig('暂停下载', state='disabled')
                self.menu.entryconfig('继续下载', state='disabled')
            else:
                if statu_now == '已暂停':
                    self.menu.entryconfig('暂停下载', state='disabled')
                    self.menu.entryconfig('继续下载', state='normal')
                if statu_now == '下载中……':
                    self.menu.entryconfig('暂停下载', state='normal')
                    self.menu.entryconfig('继续下载', state='disabled')
            
            link = self.get_uploaded_link()

            if link['hudbt']:
                self.menulink.entryconfig('进入蝴蝶', state='normal')
                self.menucopylink.entryconfig('蝴蝶链接', state='normal')
            else:
                self.menulink.entryconfig('进入蝴蝶', state='disabled')
                self.menucopylink.entryconfig('蝴蝶链接', state='disabled')

            if link['tjupt']:
                self.menulink.entryconfig('进入北洋', state='normal')
                self.menucopylink.entryconfig('北洋链接', state='normal')
            else:
                self.menulink.entryconfig('进入北洋', state='disabled')
                self.menucopylink.entryconfig('北洋链接', state='disabled')

            if link['nypt']:
                self.menulink.entryconfig('进入南洋', state='normal')
                self.menucopylink.entryconfig('南洋链接', state='normal')
            else:
                self.menulink.entryconfig('进入南洋', state='disabled')
                self.menucopylink.entryconfig('南洋链接', state='disabled')

            if link['mteam']:
                self.menulink.entryconfig('进入馒头', state='normal')
                self.menucopylink.entryconfig('馒头链接', state='normal')
            else:
                self.menulink.entryconfig('进入馒头', state='disabled')
                self.menucopylink.entryconfig('馒头链接', state='disabled')

            if link['ssd']:
                self.menulink.entryconfig('进入SSD', state='normal')
                self.menucopylink.entryconfig('SSD链接', state='normal')
            else:
                self.menulink.entryconfig('进入SSD', state='disabled')
                self.menucopylink.entryconfig('SSD链接', state='disabled')

            if link['ourbits']:
                self.menulink.entryconfig('进入OurBits', state='normal')
                self.menucopylink.entryconfig('OurBits链接', state='normal')
            else:
                self.menulink.entryconfig('进入OurBits', state='disabled')
                self.menucopylink.entryconfig('OurBits链接', state='disabled')

            if link['hdsky']:
                self.menulink.entryconfig('进入HDSky', state='normal')
                self.menucopylink.entryconfig('HDSky链接', state='normal')
            else:
                self.menulink.entryconfig('进入HDSky', state='disabled')
                self.menucopylink.entryconfig('HDSky链接', state='disabled')

            if link['ttg']:
                self.menulink.entryconfig('进入TTG', state='normal')
                self.menucopylink.entryconfig('TTG链接', state='normal')
            else:
                self.menulink.entryconfig('进入TTG', state='disabled')
                self.menucopylink.entryconfig('TTG链接', state='disabled')

            if link['hdchina']:
                self.menulink.entryconfig('进入HDChina', state='normal')
                self.menucopylink.entryconfig('HDChina链接', state='normal')
            else:
                self.menulink.entryconfig('进入HDChina', state='disabled')
                self.menucopylink.entryconfig('HDChina链接', state='disabled')

            if link['pter']:
                self.menulink.entryconfig('进入猫站', state='normal')
                self.menucopylink.entryconfig('猫站链接', state='normal')
            else:
                self.menulink.entryconfig('进入猫站', state='disabled')
                self.menucopylink.entryconfig('猫站链接', state='disabled')
            
            self.menu.post(event.x_root, event.y_root)

    def format_dict_for_completed_task(self, detail_link):

        tmp_dict = {}
        task = self.task_dict[detail_link]
        tmp_dict['hash_info'] = task.get_hash_info()
        tmp_dict['path'] = task.get_abs_file_path()
        tmp_dict['progress_info'] = task.get_all_info()
        self.complete_task[detail_link] = tmp_dict

    def get_task(self):
        selected_item = self.tree.selection()[0]
        link = self.tree.item(selected_item, 'values')[0]
        statu = self.tree.item(selected_item, 'values')[2]
        if not statu == '任务完成':
            if statu == '任务丢失':
                return ''
            else:
                task = self.task_dict[link]
        else:
            task = self.complete_task[link]
        return task

    def get_uploaded_link(self):
        link = {
            'hudbt': '', 'tjupt': '', 'nypt': '', 'mteam': '', 'ssd': '', 'ourbits': '', 'hdsky': '',
            'hdchina': '', 'ttg': '', 'pter': ''
        }
        task = self.get_task()
        if task:
            if isinstance(task, dict):
                all_statu = task['progress_info']
            else:
                all_statu = task.get_all_info()
            for item in all_statu:
                if item.find('https://hudbt.hust.edu.cn/') >= 0:
                    hudbt_link = item.split('：')[-1]
                    link['hudbt'] = hudbt_link
                if item.find('https://www.tjupt.org/') >= 0:
                    tjupt_link = item.split('：')[-1]
                    link['tjupt'] = tjupt_link
                if item.find('https://nanyangpt.com/') >= 0:
                    nypt_link = item.split('：')[-1]
                    link['nypt'] = nypt_link
                if item.find('https://pt.m-team.cc') >= 0:
                    mteam_link = item.split('：')[-1]
                    link['mteam'] = mteam_link

                if item.find('https://springsunday.net') >= 0:
                    ssd_link = item.split('：')[-1]
                    link['ssd'] = ssd_link
                if item.find('https://ourbits.club') >= 0:
                    ourbits_link = item.split('：')[-1]
                    link['ourbits'] = ourbits_link
                if item.find('https://hdsky.me/') >= 0:
                    hdsky_link = item.split('：')[-1]
                    link['hdsky'] = hdsky_link
                if item.find('https://hdchina.org/') >= 0:
                    hdchina_link = item.split('：')[-1]
                    link['hdchina'] = hdchina_link
                if item.find('https://totheglory.im/') >= 0:
                    ttg_link = item.split('：')[-1]
                    link['ttg'] = ttg_link
                if item.find('https://pterclub.com/') >= 0:
                    ttg_link = item.split('：')[-1]
                    link['pter'] = ttg_link

        return link


