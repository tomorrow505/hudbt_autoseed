

from utils import common_methods
from pages import auto_upload, reseed_panel, config_sites, login, config_rss, config_dl, descr_panel, hand_upload, \
    resume_page, picture_shot, task_history, invite_page, tracker_manage
import tkinter as tk
import os
import threading
from time import sleep
import time
from tkinter import messagebox
from PIL import Image, ImageTk
import win32api
import win32con
import socketserver
import windnd
import sqlite3
# from TkinterDnD2 import TkinterDnD
import random
# from TkinterDnD2 import *
import get_media_info


X = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
Y = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)


# class MainPage(TkinterDnD.Tk):
class MainPage(tk.Tk):

    auto_page = ''

    def __init__(self, *args, **kwargs):
        # TkinterDnD.Tk.__init__(self, *args, **kwargs)

        tk.Tk.__init__(self, *args, **kwargs)

        self.author = common_methods.AUTHOR
        self.version = common_methods.VERSION
        self.thanks_list = common_methods.THANK_LIST

        self.qb = None
        self.login_statu = False

        self.is_server_open = False
        self.t = 'recorder_server'
        self.geometry('%dx%d+%d+%d' % (750, 600, (X - 750) / 2, (Y - 650) / 2))  # 设置窗口大小
        self.resizable(False, False)
        self.title('HUDBT-TJUPT-UPLOADER-%s' % self.version)
        try:
            self.img_path = './docs/bitbug_favicon.ico'
            self.iconbitmap('', self.img_path)
        except Exception:
            pass
        self.frames = {}
        self.config_dl = common_methods.load_config_dl()

        path = './docs/task_list.db'
        self.cx = sqlite3.connect(path, check_same_thread=False)
        # 定义一个游标
        self.cu = self.cx.cursor()
        self.cu.execute('create table if not exists task (id integer primary key,link varchar(200) UNIQUE,'
                        'tasktime varchar(30), statu varchar(1200))')

        self.create_page()

    def create_page(self):
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        for F in (config_sites.ConfigSitesPage, config_dl.ConfigDlPage, auto_upload.AutoUploadPage,
                  hand_upload.HandUploadPage, login.LoginPage, config_rss.RssPage, reseed_panel.ReseedPage,
                  descr_panel.DescrPanel, resume_page.ResumePage, picture_shot.VideoInfoPage, task_history.TaskPage,
                  invite_page.InvitePage, tracker_manage.TrackerPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            ''' 
            put all of the utils in the same location;
            the one on the top of the stacking order
            will be the one that is visible.
            '''
            frame.grid(row=0, column=0, sticky="nsew")

        # 设置主菜单
        menu = tk.Menu(self)

        # 发布模式子菜单
        submenu = tk.Menu(menu, tearoff=0)
        submenu.add_command(label='自动转载', command=self.show_auto_upload)
        submenu.add_command(label='手动发布', command=self.show_hand_upload)
        submenu.add_command(label='历史任务', command=self.show_task_history)
        menu.add_cascade(label='发布模式', menu=submenu)

        # 配置子菜单
        submenu = tk.Menu(menu, tearoff=0)
        submenu.add_command(label='站点配置', command=self.show_config_sites)
        submenu.add_command(label='软件配置', command=self.show_config_dl)
        submenu.add_command(label='清除缓存', command=self.clear_cache)
        menu.add_cascade(label='配置选项', menu=submenu)

        # RSS子菜单
        submenu = tk.Menu(menu, tearoff=0)
        submenu.add_command(label='RSS管理', command=self.show_rss)
        menu.add_cascade(label='RSS选项', menu=submenu)

        # Reseed子菜单
        submenu = tk.Menu(menu, tearoff=0)
        submenu.add_command(label='辅种工具', command=self.show_reseed)
        submenu.add_command(label='获取简介', command=self.show_get_descr)
        submenu.add_command(label='UT移植', command=self.show_resume_page)
        submenu.add_command(label='视频信息', command=self.show_media_page)
        submenu.add_command(label='伺服管理', command=self.show_tracker_page)
        menu.add_cascade(label='MORE', menu=submenu)

        # 蝴蝶管理菜单
        if os.path.exists('./conf/hudbt.json'):
            submenu = tk.Menu(menu, tearoff=0)
            submenu.add_command(label='邀请管理', command=self.show_invite_page)
            submenu.add_command(label='促销管理', command=self.show_promotion)
            menu.add_cascade(label='蝴蝶管理', menu=submenu)

        # 帮助子菜单
        submenu = tk.Menu(menu, tearoff=0)
        submenu.add_command(label='关于', command=self.about)
        submenu.add_command(label='宣传', command=self.publicity)
        menu.add_cascade(label='帮助', menu=submenu)

        self.config(menu=menu)

        MainPage.auto_page = self.frames['AutoUploadPage']

        # self.check_remote_server()

        # 调试
        # self.show_frame("RssPage")
        # self.show_frame("HandUploadPage")
        # self.show_frame("AutoUploadPage")
        # self.show_frame("ConfigDlPage")
        # self.show_frame("ConfigSitesPage")
        # self.show_frame("LoginPage")

        # 起始界面
        self.show_frame("LoginPage")
        t1 = threading.Thread(target=self.check, args=())
        t1.start()

    def check_remote_server(self):
        if not self.is_server_open:
            if self.config_dl['server_open']:
                try:
                    ip = self.config_dl['server_ip']
                    port = self.config_dl['server_port']
                    self.t = threading.Thread(target=self.open_server, args=(ip, int(port)))
                    self.t.start()
                    self.is_server_open = True

                    # tk.messagebox.showinfo('提示', '服务器开启成功')
                except Exception as exc:
                    tk.messagebox.showerror('错误', '服务器模式开启失败%s ' % exc)
        else:
            if not self.config_dl['server_open']:
                try:
                    common_methods.stop_thread(self.t)
                except ValueError:
                    pass
                except SystemError:
                    pass
                # tk.messagebox.showinfo('提示', '服务器模式已经关闭')
                self.is_server_open = False

    def check(self):
        while True:
            sleep(1)
            if self.login_statu:
                self.show_auto_upload()
                self.check_remote_server()
                self.frames['AutoUploadPage'].init_qb()
                self.delete_torrents_over_time()
                break

    def show_frame(self, page_name):
        '''
        Show a frame for the given page name
        '''
        frame = self.frames[page_name]
        frame.tkraise()

    def show_media_page(self):
        if self.login_statu:
            self.show_frame('VideoInfoPage')

    def show_auto_upload(self):
        if self.login_statu:
            self.show_frame('AutoUploadPage')

    def show_hand_upload(self):
        if self.login_statu:
            self.show_frame('HandUploadPage')

    def show_config_sites(self):
        if self.login_statu:
            self.show_frame('ConfigSitesPage')

    def show_resume_page(self):
        if self.login_statu:
            self.show_frame('ResumePage')

    def show_config_dl(self):
        if self.login_statu:
            self.show_frame('ConfigDlPage')

    def show_rss(self):
        if self.login_statu:
            self.show_frame('RssPage')

    def show_reseed(self):
        if self.login_statu:
            self.show_frame('ReseedPage')

    def show_get_descr(self):
        if self.login_statu:
            self.show_frame('DescrPanel')

    def show_task_history(self):
        if self.login_statu:
            self.show_frame('TaskPage')

    def show_invite_page(self):
        if self.login_statu:
            self.show_frame('InvitePage')

    def show_promotion(self):
        messagebox.showinfo(title='提示', message='功能尚未集成')

    def show_tracker_page(self):
        if self.login_statu:
            self.show_frame('TrackerPage')

    def call_back(self):
        self.cx.close()
        self.frames['AutoUploadPage'].bak_task()
        self.config_dl['server_open'] = False
        self.check_remote_server()
        self.frames['AutoUploadPage'].close_rss()
        try:
            common_methods.stop_thread(self.frames['AutoUploadPage'].refresh_t)
        except ValueError:
            pass
        except SystemError:
            pass
        except Exception:
            pass
        self.destroy()

    def open_server(self, ip, port):
        # 创建一个多线程TCP服务器
        server = socketserver.ThreadingTCPServer((ip, port), self.MyServer)
        # print("启动socketserver服务器！")
        # 启动服务器，服务器将一直保持运行状态
        server.serve_forever()

    def clear_cache(self):

        if not os.path.exists(self.config_dl['cache_path']):
            tk.messagebox.showerror('错误', '尚未配置缓存文件目录！！')
            return
        try:
            for pathdir in [self.config_dl['img_path'], self.config_dl['cache_path']]:
                os.chdir(pathdir)
                filelist = list(os.listdir())
                for file in filelist:
                    if os.path.isfile(file) and file.endswith(('.torrent', '.jpg', '.log')):
                        os.remove(file)
        except Exception as exc:
            tk.messagebox.showerror('失败', exc)

    class MyServer(socketserver.BaseRequestHandler):
        """
        必须继承socketserver.BaseRequestHandler类
        """

        def handle(self):
            """
            必须实现这个方法！
            :return:
            """
            conn = self.request  # request里封装了所有请求的数据
            conn.sendall('欢迎使用蝴蝶种鸡服务器！'.encode())
            while True:
                data = conn.recv(1024).decode().strip()
                if data == "exit":
                    # print("断开与%s的连接！" % (self.client_address,))
                    break
                elif data == 'help':
                    result = common_methods.show_info()
                else:
                    try:
                        data_ = data.split(' ')
                        if len(data_) > 2 or len(data_) < 2:
                            result = '参数提示：\n%s' % common_methods.show_info()
                        else:
                            method = data_[0]
                            detail_link = data_[1]
                            support_sign = common_methods.find_origin_site(detail_link)
                            if support_sign == 0:
                                result = '不支持的链接！！'
                            else:
                                torrent_id = common_methods.get_id(detail_link)
                                if torrent_id == -1:
                                    result = '不支持的链接！！'
                                else:
                                    if method == 'post':
                                        result = MainPage.auto_page.add_task_by_link(detail_link, 'remote')
                                    elif method == 'get':
                                        result = MainPage.auto_page.get_statu_by_link(detail_link)
                                    elif method == 'cancle':
                                        result = MainPage.auto_page.cancle_task_by_link(detail_link)
                                    else:
                                        result = '参数提示：\n%s' % common_methods.show_info()
                    except IndexError:
                        result = '参数提示：\n%s' % common_methods.show_info()

                # print("来自%s的客户端向你发来信息：%s" % (self.client_address, data))
                conn.sendall(('客户端指令：%s\n服务器结果：%s' % (data, result)).encode())

    def about(self):
        if self.login_statu:
            messagebox.showinfo(title='About', message='Author：{author}\n鸣谢：{thanks}'.format(
                author=self.author, thanks=self.thanks_list))

    def publicity(self):
        if self.login_statu:
            top1 = tk.Toplevel(self)
            xuanchuan = './docs/xuanchuan.png'
            image = Image.open(xuanchuan)
            img = ImageTk.PhotoImage(image)
            canvas1 = tk.Canvas(top1, width=image.width, height=image.height, bg='white')
            canvas1.create_image(0, 0, image=img, anchor="nw")
            canvas1.pack()
            label = tk.Label(top1, text='微信扫一扫吧@_@.', font=("Helvetica", 11))
            label.pack()
            top1.wm_geometry(
                '%dx%d+%d+%d' % (image.width, image.height + 30, (X - image.width) / 2, (Y - image.height - 30) / 2))
            top1.wm_attributes('-topmost', 1)
            top1.mainloop()

    def delete_torrents_over_time(self):
        hash_list = []
        now = int(time.time())
        torrents = self.qb.torrents()
        for torrent in torrents:
            d = torrent['completion_on']
            if now - int(d) > 60*60*24*30 and torrent['tags'] != '保留':
                hash_list.append(torrent['hash'])
        if len(hash_list):
            result = tk.messagebox.askokcancel('提示', '是否删除超时的%d个种子?' % len(hash_list))
            if result:
                self.qb.delete_permanently(hash_list)
            else:
                pass

    # windnd方案
    def thread_handle_drage(self, files):
        t = threading.Thread(target=self.drag_picture, args=(files,))
        t.start()

    def drag_picture(self, files):
        self.show_media_page()
        for item in files:
            file = item.decode('gbk')
            if file.endswith(('.jpg', '.png')):
                funcs = [0, 1, 2, 3]
                func = random.choice(funcs)
                if func == 0:
                    pic_url = get_media_info.send_picture(img_loc=file)
                elif func == 1:
                    pic_url = get_media_info.send_picture_2(img_loc=file)
                elif func == 2:
                    pic_url = get_media_info.send_picture_3(img_loc=file)
                else:
                    pic_url = get_media_info.send_picture_4(img_loc=file)

                if pic_url:
                    info_ = '[img]%s[/img]\n' % pic_url
                    self.frames['VideoInfoPage'].txtContent.insert(tk.INSERT, info_)
                else:
                    pass
            break

    def drag_picture_2(self, files):
        self.show_media_page()
        for item in files:
            file = item.decode('gbk')
            if file.endswith(('.jpg', '.png')):
                funcs = [0, 1, 2, 3]
                func = random.choice(funcs)
                if func == 0:
                    pic_url = get_media_info.send_picture(img_loc=file)
                elif func == 1:
                    pic_url = get_media_info.send_picture_2(img_loc=file)
                elif func == 2:
                    pic_url = get_media_info.send_picture_3(img_loc=file)
                else:
                    pic_url = get_media_info.send_picture_4(img_loc=file)

                if pic_url:
                    info_ = '[img]%s[/img]\n' % pic_url
                    self.frames['VideoInfoPage'].txtContent.insert(tk.INSERT, info_)
                else:
                    pass
            break

    # tkdnd方案
    # def thread_handle_drage(self, event):
    #     t = threading.Thread(target=self.drag_picture, args=(event,))
    #     t.start()
    #
    # def drag_picture(self, event):
    #     print('开始上传图片……')
    #     self.show_media_page()
    #     file = event.data
    #     if file.endswith(('.jpg', '.png')):
    #         funcs = [0, 1, 2, 3]
    #         func = random.choice(funcs)
    #         if func == 0:
    #             pic_url = get_media_info.send_picture(img_loc=file)
    #         elif func == 1:
    #             pic_url = get_media_info.send_picture_2(img_loc=file)
    #         elif func == 2:
    #             pic_url = get_media_info.send_picture_3(img_loc=file)
    #         else:
    #             pic_url = get_media_info.send_picture_4(img_loc=file)
    #
    #         if pic_url:
    #             info_ = '[img]%s[/img]\n' % pic_url
    #             self.frames['VideoInfoPage'].txtContent.insert(tk.INSERT, info_)
    #         else:
    #             pass


if __name__ == "__main__":
    app = MainPage()

    # 为了能够拖拽，方案1
    windnd.hook_dropfiles(app, func=app.thread_handle_drage)

    # 方案2：
    # app.drop_target_register(DND_FILES)
    # app.dnd_bind('<<Drop>>', app.thread_handle_drage)

    app.protocol("WM_DELETE_WINDOW", app.call_back)
    app.mainloop()
    try:
        common_methods.kill_myself()
    except Exception as exc:
        print(exc)
        pass
