# -*- coding: utf-8 -*-
# Author:Chengli


from time import sleep
import re
import html_handler
import my_bencode
import requests
import os
from utils import common_methods
import get_media_info
import threading
import shutil
from urllib.parse import unquote
import time
# import datetime
from upload_to_sites import hudbt, tjupt, nypt, mteam, cmct, ourbits, hdsky, hdchina, ttg, pter

CONFIG_SITE_PATH = './conf/config_sites.json'


reject_keywords = ['禁转', '禁止转载', '謝絕提取壓制轉載', '情色', '色情']

time_transfer = {
    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
    'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
}


class AutoSeed (threading.Thread):

    pt_sites = common_methods.load_pt_sites()

    def __init__(self, qb, origin_url: str or dict or tuple, config_dl):
        super(AutoSeed, self).__init__()
        self.qb = qb

        self.raw_info = {
            'up_mode': 'HAND_MODE', 'detail_link': '', 'title': '', 'small_descr': '', 'descr': '', 'filename': '',
            'url': '', 'douban_info': '', 'type_': 0, 'uplver': 'yes', 'standard_sel': 0, 'origin_site': '',
            'recommand': '', 'nfo': '', 'hash_info': '', 'des_site': 'hudbt', 'descr_rss': '', 'picture_info': '',
            'video_info': '', 'video_format': '',
        }
        self.abs_file_dir = ''
        if isinstance(origin_url, str):
            self.raw_info['detail_link'] = origin_url
            self.entrie = {}
        elif isinstance(origin_url, tuple):
            self.raw_info['detail_link'] = origin_url[1]
            self.raw_info['up_mode'] = 'REMOTE_MODE'
            self.entrie = {}
        else:
            self.raw_info['up_mode'] = 'RSS_MODE'
            self.entrie = origin_url
            self.raw_info['detail_link'] = self.entrie['link']

        self.torrent_id = common_methods.get_id(self.raw_info['detail_link'])
        self.statu = ['准备中…']
        self.process_info = []
        self.config_dl = config_dl
        self.torrent_info = {}

        self.task_confirmed = False

        if self.config_dl['anony_close']:
            self.raw_info['uplver'] = 'no'

    def run(self):
        '''
        大致上分为5个阶段——
            1、获取网页并解析基本信息
            2、获取种子并进行下载
            3、根据下载文件进行解析
            4、合并信息并进行发布
        :return:
        '''

        #  ------------------------------------------Part1：获取网页并解析基本信息------------------------------------------
        # 根据链接获取原始站点信息
        origin_site = common_methods.find_origin_site(self.raw_info['detail_link'])
        self.raw_info['origin_site'] = origin_site['abbr']
        try:
            self.update_process_info('正在获取源网页……')
            response = common_methods.get_response(self.raw_info['detail_link'], origin_site['cookie'])
            html = response.text
        except Exception as exc:
            self.update_process_info('获取网页错误……%s' % exc)
            return exc

        # 认怂，自动转载检查是不是禁转
        if any([html.find(item) >= 0 for item in reject_keywords]):
            if self.raw_info['up_mode'] == "RSS_MODE":
                self.statu.append("禁转？请检查")
                self.update_process_info('禁转？请检查是否禁转或包含敏感信息。')
                sleep(3)
                return
        if html.find('[quote=感谢]感谢发布者！！资源来自') >= 0:
            if self.raw_info['up_mode'] == "RSS_MODE":
                self.statu.append("机器人转发")
                self.update_process_info('同类机器人转发，跳过！')
                sleep(3)
                return
        # 开始解析网页，主要是为了获取类型然后分目录下载；获取hash_info判断下载情况
        try:
            self.statu.append('解析源网页……')
            self.update_process_info('正在解析源网页……')
            htmlhandler = html_handler.HtmlHandler(self.raw_info['origin_site'], html, self.torrent_id)
            raw_info_tmp = htmlhandler.get_raw_info()
            for key in raw_info_tmp.keys():
                self.raw_info[key] = raw_info_tmp[key]
            self.raw_info['descr'] = self.raw_info['descr'].replace('img3.doubanio.com/view/photo',
                                                                    'img1.doubanio.com/view/photo')

        except Exception as exc:
            self.statu.append('网页解析出错')
            self.update_process_info('网页解析错误：%s' % exc)
            return exc

        # return
        # ------------------------------------------Part2: 获取种子并进行下载------------------------------------------
        # 根据基本类型获取存文件储路径
        self.abs_file_dir = self.get_abs_file_dir()

        # 获取种子下载路径并下载，返回种子存放路径，备份路径，以及下载信息
        self.statu.append("下载源种子")
        self.update_process_info('正在下载源种子……')

        if self.raw_info['download_url']:
            download_url = self.raw_info['download_url']
        else:
            download_url = common_methods.get_download_url(html, origin_site, self.torrent_id)

        origin_torrent_path, dl_info = self.download_torrent(origin_site, self.torrent_id, download_url)
        if 'Error' in dl_info:
            self.statu.append('源种子下载失败')
            self.update_process_info('源种子下载失败！！')
            return

        # 根据备份种子获取下载的文件的相对路径以及hash值
        self.statu.append('解析源种子')
        self.update_process_info('正在解析源种子……')

        try:
            self.torrent_info = common_methods.parser_torrent(origin_torrent_path)
            file_path = self.torrent_info['file_path']
            file_dir = self.torrent_info['file_dir']
            self.raw_info['video_format'] = file_path.split('.')[-1].strip()
            if not self.raw_info['hash_info']:
                self.raw_info['hash_info'] = my_bencode.get_hash(origin_torrent_path)
            self.update_process_info('hash值:%s\n                          名称:%s\n                          大小:%s'
                                     % (self.raw_info['hash_info'], self.torrent_info['name'], self.torrent_info['size']))

        except Exception as exc:
            self.statu.append('种子解析错误：%s' % exc)
            self.update_process_info('源种子解析错误……')
            return

        if origin_site['abbr'] in ['mteam']:
            my_bencode.change_tracker(origin_torrent_path)

        # 获取文件的绝对路径
        # abs_file_path = os.path.join(self.abs_file_dir, file_path)

        abs_file_dir_full = os.path.join(self.abs_file_dir, file_dir)
        self.raw_info['abs_file_path'] = abs_file_dir_full

        # 根据下载的种子，下载文件到指定路径
        self.start_download(origin_torrent_path, self.abs_file_dir, 'false')
        self.statu.append('下载中……')
        self.update_process_info('正在下载资源……')

        if self.wait_for_download(self.raw_info['hash_info']):
            self.statu.append('下载成功')
            self.update_process_info('资源下载成功，等待发布……')
        else:
            return

        upload_str = ["up_to_hudbt", "up_to_nypt", "up_to_tjupt", "up_to_mteam", "up_to_cmct", "up_to_ourbits",
                      "up_to_hdsky", "up_to_hdchina", "up_to_ttg", "up_to_pter"]
        if any(self.config_dl[item] for item in upload_str):
            pass
        else:
            self.update_process_info('无需发布，直接跳过……')
            self.statu.append('任务完成')
            return
        self.statu.append('准备发布')

        # ------------------------------------------Part3：根据下载文件进行解析------------------------------------------

        if self.raw_info['origin_site'] == 'FRDS':
            self.statu.append('朋友等待')
            if self.check_for_upload():
                pass
            else:
                return

        abs_file_path = os.path.join(self.abs_file_dir, file_path)
        try:
            video_info = get_media_info.get_video_info(abs_file_path.replace('/', '\\'))
            self.raw_info['video_info'] = video_info
        except Exception:
            pass

        if not self.raw_info['nfo'] and self.raw_info['video_info']:
            self.raw_info['descr'] = self.raw_info['descr'] + '\n\n[quote=iNFO][font=Courier New]'
            item_list = ['general', 'Video', 'Audio']
            for item in item_list:
                self.raw_info['descr'] = self.raw_info['descr'] + '\n\n' + self.raw_info['video_info'][item]
            self.raw_info['descr'] = self.raw_info['descr'] + '[/font][/quote]\n'

        pic_num = self.find_num_of_pics()
        if pic_num <= 1:
            try:
                video_name = abs_file_path.split('\\')[-1]
                img_name = '%s.jpg' % video_name
                img_name = re.sub('^\[.*?\]\.|[\u4e00-\u9fff]', '', img_name)
                abs_img_path = self.config_dl['img_path'] + '/' + img_name
                picture_info = get_media_info.get_picture_2(abs_file_path, abs_img_path)
            except Exception as exc:
                self.update_process_info('上传图片失败：%s' % exc)
                picture_info = ''
            self.raw_info['picture_info'] = picture_info
            self.raw_info['descr'] = self.raw_info['descr'] + picture_info

        # ------------------------------------------Part4：合并信息进行发布------------------------------------------

        # return

        self.raw_info['descr'] = re.sub('\n+', '\n', self.raw_info['descr'])
        self.upload_to_sites(origin_torrent_path)

    def find_num_of_pics(self):
        pics = re.findall('\[img\].*?\[/img\]', self.raw_info['descr'])
        # print(len(pics))
        return self.raw_info['img_num']

    # 针对朋友需要等待的
    @staticmethod
    def check_for_upload():
        # if self.entrie:
        #     date = self.entrie['published']
        #     date = date.split(',')[1]
        #     date = date.split('+')[0].strip()
        #     part_of_date = date.split(' ')
        #
        #     full_date = '%s-%s-%s %s' % (part_of_date[2], time_transfer[part_of_date[1]], part_of_date[0], part_of_date[-1])
        # else:
        #     full_date = self.raw_info['publish_time']
        #
        # # print(full_date)
        # timearray = time.strptime(full_date, "%Y-%m-%d %H:%M:%S")
        #
        # publish_time = int(time.mktime(timearray))
        #
        # timestamp = int(publish_time) + 60 * 60 * 8

        timestamp = time.time()

        time_to_upload = timestamp + 24*60*60

        # datearray = datetime.datetime.fromtimestamp(time_to_upload)
        # otherstyletime = datearray.strftime("%Y-%m-%d %H:%M:%S")
        # print(otherstyletime)

        while True:
            time_now = int(time.time())
            # print(time_now)
            if time_to_upload <= time_now:
                return True
            else:
                if time_to_upload - time_now >= 1200:
                    sleep(1200)
                else:
                    sleep(time_to_upload - time_now)

    def judge_for_tjupt(self):
        if not self.config_dl['up_to_tjupt']:
            return False
        if self.raw_info['title'].upper().endswith('CMCT'):
            if self.raw_info['title'].find('720p') >= 0:
                return False
            else:
                return True
        elif self.raw_info['title'].upper().endswith('FRDS'):
            if self.raw_info['title'].upper().find('MNHD') >= 0:
                return False
            else:
                return True
        else:
            return True

    def judge_for_cmct(self):
        reject_list = ['CnSCG', 'FRDS', 'SmY', 'SeeHD', 'VeryPSP', 'DWR', 'XLMV', 'XJCTV', 'Mp4Ba', 'FGT']
        if not self.config_dl['up_to_cmct']:
            return False
        if any(self.raw_info['title'].find(item) >= 0 for item in reject_list):
            return False
        else:
            return True

    def judge_for_ourbits(self):
        reject_list = ['CNSCG', 'FRDS', 'SMY', 'SEEHD', 'VERYPSP', 'DWR', 'XLMV', 'XJCTV', 'MP4BA', 'FGT', 'YYETS',
                       'WEBRIP']
        if not self.config_dl['up_to_ourbits']:
            return False
        if any(self.raw_info['title'].upper().find(item) >= 0 for item in reject_list):
            return False
        else:
            return True

    def judge_for_hdsky(self):
        reject_list = ['CnSCG', 'SmY', 'SeeHD', 'VeryPSP', 'DWR', 'XLMV', 'XJCTV', 'Mp4Ba', 'FGT',  'YYeTs']
        if not self.config_dl['up_to_hdsky']:
            return False
        if any(self.raw_info['title'].find(item) >= 0 for item in reject_list):
            return False
        else:
            return True

    def judge_for_hdchina(self):
        reject_list = ['CnSCG', 'SmY', 'SeeHD', 'VeryPSP', 'DWR', 'XLMV', 'XJCTV', 'Mp4Ba', 'FGT', 'CHD', 'EPiC',
                       'RARBG', 'HQC', 'YYeTs']
        if not self.config_dl['up_to_hdchina']:
            return False
        if any(self.raw_info['title'].find(item) >= 0 for item in reject_list):
            return False
        else:
            if self.raw_info['title'].upper().find('X265') >= 0 or self.raw_info['title'].upper().find('HEVC') >= 0:
                if self.raw_info['title'].upper().find('2160p') < 0 and self.raw_info['title'].upper().find('2160p') < 0:
                    return False
            else:
                return True

    def judge_for_ttg(self):
        reject_list = ['CnSCG',  'SmY', 'SeeHD', 'VeryPSP', 'DWR', 'XLMV', 'Mp4Ba', 'YYeTs']
        if not self.config_dl['up_to_ttg']:
            return False
        if any(self.raw_info['title'].find(item) >= 0 for item in reject_list):
            return False
        else:
            return True

    def get_origin_url(self):
        if self.entrie:
            return self.entrie
        else:
            return self.raw_info['detail_link']

    def get_statu(self):
        return self.statu[-1]

    def get_all_statu(self):
        return self.statu

    def get_all_info(self):
        return self.process_info

    def get_abs_file_path(self):
        if 'abs_file_path' in self.raw_info.keys():
            return self.raw_info['abs_file_path']
        else:
            return ''

    def get_torrent_id(self):
        return common_methods.get_id(self.raw_info['detail_link'])

    def wait_for_download(self, hash_info):
        try:
            torrent = self.qb.get_torrent(infohash=hash_info)
            if torrent['completion_date'] != -1:
                save_path = torrent['save_path']
                if save_path.strip() != self.abs_file_dir.strip():
                    self.abs_file_dir = save_path
                return True
        except Exception as exc:
            if str(exc).find('Not Found for url') >= 0:
                torrents = self.qb.torrents()
                for torrent in torrents:
                    if torrent['name'] == self.torrent_info['file_dir']:
                        self.raw_info['hash_info'] = torrent['hash']
                        hash_info = torrent['hash']
                        break
            sleep(5)
        try:
            limit = 1024*1024*12
            if self.raw_info['origin_site'] == 'FRDS':
                self.qb.set_torrent_download_limit(infohash_list=hash_info, limit=limit)
        except Exception as exc:
            print('朋友限速失败：%s' % exc)

        while True:
            try:
                torrent = self.qb.get_torrent(infohash=hash_info)
                if torrent['completion_date'] != -1:
                    return True
                else:
                    self.task_confirmed = True
            except Exception as exc:
                if not self.task_confirmed:
                    self.update_process_info('任务出错：%s' % exc)
                    self.statu.append('任务丢失')
                    return False
            sleep(5)

    def download_torrent(self, pt_site, tid, download_url):

        dl_info = []

        response = common_methods.get_response(download_url, pt_site['cookie'])
        try:
            content = response.headers['Content-Disposition']
            content = content.encode('ISO-8859-1').decode().replace('"', '')
            if pt_site['domain'] == 'https://npupt.com' or pt_site['domain'] == 'https://totheglory.im':
                content = (unquote(content, 'utf-8'))
            origin_filename = re.search('filename=(.*?).torrent', content).group(1)
            # print(origin_filename)
        except Exception as exc:
            dl_info.append('Error')
            print('下载种子错误', exc)
            return '', dl_info

        # 处理种子名称
        filename = re.sub(r'^\[.{1,10}?\]|.mp4$|.mkv$|[\(\)]|\[|\]|[\u4e00-\u9fff]|[^-\.(A-Za-z0-9)]', ' ',
                          origin_filename)
        filename = ' '.join(filename.split('.'))
        filename = re.sub(' +', ' ', filename).lstrip()
        if pt_site['domain'] == 'https://pt.sjtu.edu.cn' or pt_site['domain'] == 'https://ourbits.club':
            filename = re.sub('^\d{3,10}', '', filename)
        else:
            pass

        self.raw_info['abbr'] = pt_site['abbr']
        if not filename:
            filename = '%s_%s' % (pt_site['abbr'], tid)
        else:
            filename = '%s_%s_%s' % (filename, pt_site['abbr'], tid)

        self.raw_info['filename'] = filename

        origin_file_path = self.config_dl['cache_path'] + '\\%s.torrent' % filename

        # back_file_path = self.config_dl['cache_path'] + '\\%s_back.torrent' % filename

        try:
            response.raise_for_status()
            f = open(origin_file_path, 'wb')
            for chunk in response.iter_content(100000):
                f.write(chunk)
            f.close()
            dl_info.append('Torrent Downloded')
        except Exception:
            # print('种子下载失败: %s' % exc)
            dl_info.append('Error')

        return origin_file_path, dl_info

    def get_abs_file_dir(self):
        big_type = self.raw_info['big_type']

        if big_type in ['电影', '剧集', '综艺']:
            self.raw_info['category'] = big_type
            abs_file_dir = self.config_dl['movie_path']
        elif big_type in ['学习', '资料']:
            abs_file_dir = self.config_dl['study_path']
            self.raw_info['category'] = '学习'
        elif big_type in ['动漫']:
            abs_file_dir = self.config_dl['carton_path']
            self.raw_info['category'] = '动漫'
        else:
            if big_type == '体育':
                self.raw_info['category'] = '体育'
            elif big_type in ['音乐']:
                self.raw_info['category'] = '音乐'
            else:
                self.raw_info['category'] = '其他'
            abs_file_dir = self.config_dl['others_path']

        return abs_file_dir

    def start_download(self, torrent_path, dl_path, flag):
        torrent_file = open(torrent_path, 'rb')
        try:
            self.qb.download_from_file(torrent_file, savepath=dl_path, category=self.raw_info['category'],
                                       skip_checking=flag, )
        except Exception as exc:
            # print(exc)
            torrent_file.close()
            if self.statu[-1] != '重新加载':
                self.statu.append('重新加载')
            self.qb = common_methods.relogin()
            sleep(3)
            torrent_file = open(torrent_path, 'rb')
            self.qb.download_from_file(torrent_file, savepath=dl_path, category=self.raw_info['category'],
                                       skip_checking=flag)
        torrent_file.close()

    def upload_to_hudbt(self, raw_info, origin_torrent_path, params=None, files=None):

        log_info = []
        site_hudbt = AutoSeed.pt_sites['蝴蝶']
        des_url = "https://{host}/takeupload.php".format(host=site_hudbt['domain'])

        torrent_file = open(origin_torrent_path, "rb")
        try:
            files = [("file", (raw_info['filename'], torrent_file, "application/x-bittorrent")),
                     ("nfo", ("", "", "application/octet-stream")), ]
        except Exception as exc:
            self.update_process_info('上传种子打开错误：%s' % exc)
            log_info.append('Error')

        data = hudbt.get_post_data(raw_info)
        flag = self.post_data_reseed_torrent(des_url, params, data, files, site_hudbt, raw_info)
        log_info.append(flag)
        torrent_file.close()
        # os.remove(origin_torrent_path)
        return log_info

    def upload_to_tjupt(self, raw_info, origin_torrent_path, params=None, files=None):

        log_info = []
        site_tjupt = AutoSeed.pt_sites['北洋园']
        des_url = "https://{host}/takeupload.php".format(host=site_tjupt['domain'])

        torrent_file = open(origin_torrent_path, "rb")
        try:
            files = [("file", (raw_info['filename'] + '.torrent', torrent_file, "application/x-bittorrent")),
                     ("nfo", ("", "", "application/octet-stream")), ]
        except Exception as exc:
            self.update_process_info('上传种子打开错误：%s' % exc)
            log_info.append('Error')

        data = tjupt.get_post_data(raw_info)
        flag = self.post_data_reseed_torrent(des_url, params, data, files, site_tjupt, raw_info)
        log_info.append(flag)
        torrent_file.close()
        # os.remove(origin_torrent_path)
        return log_info

    def upload_to_nypt(self, raw_info, origin_torrent_path, params=None, files=None):
        log_info = []
        site_nypt = AutoSeed.pt_sites['南洋']

        des_url = "https://{host}/takeupload.php".format(host=site_nypt['domain'])

        torrent_file = open(origin_torrent_path, "rb")
        try:
            files = [("file", (raw_info['filename'] + '.torrent', torrent_file, "application/x-bittorrent")),
                     ("nfo", ("", "", "application/octet-stream")), ]
        except Exception as exc:
            self.update_process_info('上传种子打开错误：%s' % exc)
            log_info.append('Error')

        data = nypt.get_post_data(raw_info)
        flag = self.post_data_reseed_torrent(des_url, params, data, files, site_nypt, raw_info)
        log_info.append(flag)
        torrent_file.close()
        # os.remove(origin_torrent_path)
        # os.remove(origin_file_path)
        return log_info

    def upload_to_mteam(self, raw_info, origin_torrent_path, params=None, files=None):
        # my_bencode.change_tracker_2_mteam(origin_torrent_path)
        log_info = []
        site_mteam = AutoSeed.pt_sites['M-team']
        des_url = "https://{host}/takeupload.php".format(host=site_mteam['domain'])

        try_time = 5
        while try_time > 0:
            torrent_file = open(origin_torrent_path, "rb")
            try:
                files = [("file", (raw_info['filename'] + '.torrent', torrent_file, "application/x-bittorrent")), ]
            except Exception as exc:
                self.update_process_info('上传种子打开错误：%s' % exc)
                log_info.append('Error')

            data = mteam.get_post_data(raw_info)

            flag = self.post_data_reseed_torrent(des_url, params, data, files, site_mteam, raw_info)
            if flag != '馒头上传失败':
                break
            try_time = try_time - 1
            torrent_file.close()
        log_info.append(flag)
        # os.remove(origin_torrent_path)
        return log_info

    def upload_to_cmct(self, raw_info, origin_torrent_path, params=None, files=None):
        # my_bencode.change_tracker_2_mteam(origin_torrent_path)
        log_info = []
        site_cmct = AutoSeed.pt_sites['CMCT']
        des_url = "https://{host}/takeupload.php".format(host=site_cmct['domain'])

        # try_time = 5
        # while try_time > 0:
        torrent_file = open(origin_torrent_path, "rb")
        try:
            files = [("file", (raw_info['filename'] + '.torrent', torrent_file, "application/x-bittorrent")), ]
        except Exception as exc:
            self.update_process_info('上传种子打开错误：%s' % exc)
            log_info.append('Error')

        data = cmct.get_post_data(raw_info)

        flag = self.post_data_reseed_torrent(des_url, params, data, files, site_cmct, raw_info)

        torrent_file.close()
        log_info.append(flag)
        # os.remove(origin_torrent_path)
        return log_info

    def upload_to_ourbits(self, raw_info, origin_torrent_path, params=None, files=None):
        # my_bencode.change_tracker_2_mteam(origin_torrent_path)
        log_info = []
        site_ourbits = AutoSeed.pt_sites['OurBits']
        des_url = "https://{host}/takeupload.php".format(host=site_ourbits['domain'])

        torrent_file = open(origin_torrent_path, "rb")
        try:
            files = [("file", (raw_info['filename'] + '.torrent', torrent_file, "application/x-bittorrent")), ]
        except Exception as exc:
            self.update_process_info('上传种子打开错误：%s' % exc)
            log_info.append('Error')

        data = ourbits.get_post_data(raw_info)

        flag = self.post_data_reseed_torrent(des_url, params, data, files, site_ourbits, raw_info)

        torrent_file.close()
        log_info.append(flag)
        return log_info

    def upload_to_hdsky(self, raw_info, origin_torrent_path, params=None, files=None):

        log_info = []
        site_hdsky = AutoSeed.pt_sites['天空']
        des_url = "https://{host}/takeupload.php".format(host=site_hdsky['domain'])

        torrent_file = open(origin_torrent_path, "rb")
        try:
            files = [("file", (raw_info['filename'] + '.torrent', torrent_file, "application/x-bittorrent")), ]
        except Exception as exc:
            self.update_process_info('上传种子打开错误：%s' % exc)
            log_info.append('Error')

        data = hdsky.get_post_data(raw_info)

        flag = self.post_data_reseed_torrent(des_url, params, data, files, site_hdsky, raw_info)

        torrent_file.close()
        log_info.append(flag)
        # os.remove(origin_torrent_path)
        return log_info

    def upload_to_hdchina(self, raw_info, origin_torrent_path, params=None, files=None):

        log_info = []
        site_hdchina = AutoSeed.pt_sites['瓷器']
        des_url = "https://{host}/takeupload.php".format(host=site_hdchina['domain'])

        torrent_file = open(origin_torrent_path, "rb")
        try:
            files = [("file", (raw_info['filename'] + '.torrent', torrent_file, "application/x-bittorrent")), ]
        except Exception as exc:
            self.update_process_info('上传种子打开错误：%s' % exc)
            log_info.append('Error')

        data = hdchina.get_post_data(raw_info)

        flag = self.post_data_reseed_torrent(des_url, params, data, files, site_hdchina, raw_info)

        torrent_file.close()
        log_info.append(flag)
        # os.remove(origin_torrent_path)
        return log_info

    def upload_to_ttg(self, raw_info, origin_torrent_path, params=None, files=None):

        log_info = []
        site_ttg = AutoSeed.pt_sites['TTG']
        des_url = "https://{host}/takeupload.php".format(host=site_ttg['domain'])

        torrent_file = open(origin_torrent_path, "rb")
        try:
            files = [("file", (raw_info['filename'].split('_')[0] + '.torrent', torrent_file,
                               "application/x-bittorrent")), ]
        except Exception as exc:
            self.update_process_info('上传种子打开错误：%s' % exc)
            log_info.append('Error')

        data = ttg.get_post_data(raw_info)

        flag = self.post_data_reseed_torrent(des_url, params, data, files, site_ttg, raw_info)

        torrent_file.close()
        log_info.append(flag)
        # os.remove(origin_torrent_path)
        return log_info

    def upload_to_pter(self, raw_info, origin_torrent_path, params=None, files=None):

        log_info = []
        site_pter = AutoSeed.pt_sites['猫站']
        des_url = "https://{host}/takeupload.php".format(host=site_pter['domain'])

        torrent_file = open(origin_torrent_path, "rb")
        try:
            files = [("file", (raw_info['filename'].split('_')[0] + '.torrent', torrent_file,
                               "application/x-bittorrent")), ]
        except Exception as exc:
            self.update_process_info('上传种子打开错误：%s' % exc)
            log_info.append('Error')

        data = pter.get_post_data(raw_info)

        flag = self.post_data_reseed_torrent(des_url, params, data, files, site_pter, raw_info)

        torrent_file.close()
        log_info.append(flag)
        # os.remove(origin_torrent_path)
        return log_info

    def post_data_reseed_torrent(self, des_url, params, data, files, site, raw_info):
        post_time = 3
        seed_torrent_download_id = -1
        des_post = requests.post(url=des_url, params=params, data=data, files=files, cookies=site['cookie'])
        if site['abbr'] == 'nypt':
            while post_time > 0:
                seed_torrent_download_id = common_methods.get_id(des_post.url)
                if seed_torrent_download_id != -1:
                    break
                post_time = post_time - 1
                des_post = requests.post(url=des_url, params=params, data=data, files=files, cookies=site['cookie'])

        else:
            seed_torrent_download_id = common_methods.get_id(des_post.url)
            if seed_torrent_download_id == -1:
                content = des_post.content.decode()
                # print(content)
                if content.find('<h1>上傳失敗！</h1>') >= 0:
                    # print('馒头上传失败！')
                    return '馒头上传失败'
                try:
                    seed_torrent_download_id = re.search('该种子已存在！.*id=(\d{2,8})', content)
                    seed_torrent_download_id = seed_torrent_download_id.group(1)
                except Exception as exc:
                    print('获取种子链接出错了！%s' % exc)
                    seed_torrent_download_id = -1

        if seed_torrent_download_id == -1:
            return 'Error'
        else:
            if site['abbr'] == 'hdchina':
                url = 'https://hdchina.org/details.php?id={tid}&hit=1'.format(tid=seed_torrent_download_id)
                response = common_methods.get_response(url, site['cookie'])
                html = response.text
                download_url = common_methods.get_hdchina_download_url(html)
            elif site['abbr'] == 'ttg':
                download_url = "https://{host}/dl/{tid}/{passkey}".format(
                    host=site['domain'], tid=seed_torrent_download_id, passkey=site['passkey'])
            else:
                download_url = "https://{host}/download.php?id={tid}".format(host=site['domain'],
                                                                             tid=seed_torrent_download_id)
                if site['abbr'] in ['hdsky']:
                    download_url = download_url + '&passkey=' + site['passkey']

            try_time = 10
            dl_info = ''
            while try_time > 0:
                origin_file_path, dl_info = self.download_torrent(site, seed_torrent_download_id, download_url)
                if 'Error' in dl_info:
                    pass
                else:
                    if 'download_path' in raw_info.keys():
                        abs_file_dir = raw_info['download_path']
                        raw_info['category'] = self.raw_info['category']
                    if site['abbr'] in ['mteam', 'cmct', 'ourbits', 'hdsky', 'hdchina']:
                        my_bencode.change_tracker(origin_file_path)
                        hash_info = self.raw_info['hash_info']
                        self.start_download(origin_file_path, self.abs_file_dir, 'true')
                        t = threading.Thread(target=self.reannounce_torrent, args=(hash_info,))
                        t.start()
                    else:
                        self.start_download(origin_file_path, self.abs_file_dir, 'true')
                    if site['abbr'] == 'ttg':
                        self.update_process_info(
                            '发布成功：https://totheglory.im/t/%s/' % seed_torrent_download_id)
                    else:
                        self.update_process_info(
                            '发布成功：https://%s/details.php?id=%s&hit=1' % (site['domain'], seed_torrent_download_id))
                    if os.path.exists(origin_file_path):
                        os.remove(origin_file_path)
                    break
                try_time = try_time - 1
            if 'Error' in dl_info:
                self.update_process_info('辅种失败！！')
                return 'Error'
            else:
                return 'Succeed'

    def get_hash_info(self):
        return self.raw_info['hash_info']

    def fak_upload(self):
        torrent_path = self.entrie['torrent_path']
        # print(torrent_path)
        log_info = self.upload_to_hudbt(self.entrie, torrent_path)
        return log_info

    def backup_torrent(self, origin_torrent_path):

        origin_torrent_name = origin_torrent_path.split('\\')[-1]
        new_filename = re.sub('\.torrent', '', origin_torrent_name)
        new_filename = re.sub(r'^\[.{1,10}?\]|.mp4$|.mkv$|\[|\]|[\u4e00-\u9fff]|[^-\.@￡(A-Za-z0-9)]', '',
                              new_filename)
        new_filename = ' '.join(new_filename.split('.')).strip()
        back_up_path = self.config_dl['cache_path']+'\\%sback.torrent' % new_filename
        shutil.copyfile(origin_torrent_path, back_up_path)

        return back_up_path

    def update_process_info(self, string):
        now = time.strftime("%m/%d %H:%M:%S", time.localtime())
        info = '%s  %s' % (now, string)
        self.process_info.append(info.ljust(50, ' '))

    def upload_to_sites(self, origin_torrent_path):
        if self.raw_info['nfo'] == 'true':
            self.raw_info['nfo'] = ''

        new_torrent_paths = []
        for i in range(10):
            torrent_tmp = '%s.%d.torrent' % (origin_torrent_path, i)
            shutil.copy(origin_torrent_path, torrent_tmp)
            new_torrent_paths.append(torrent_tmp)

        try:
            if self.raw_info['origin_site'] != 'hudbt' and self.config_dl['up_to_hudbt']:
                self.update_process_info('正在发布到蝴蝶……')
                log_info = self.upload_to_hudbt(self.raw_info, new_torrent_paths[0])
                if 'Succeed' in log_info:
                    pass
                else:
                    self.update_process_info('发布到蝴蝶失败！！')
            else:
                self.update_process_info('不符合蝴蝶发布条件，跳过发布……')
        except Exception as exc:
            self.update_process_info('错误： %s' % exc)
        finally:
            try:
                os.remove(new_torrent_paths[0])
            except Exception:
                pass

        try:
            if self.raw_info['origin_site'] not in ['tjupt', 'U2'] and self.judge_for_tjupt():
                self.update_process_info('正在发布到北洋园……')
                log_info_2 = self.upload_to_tjupt(self.raw_info, new_torrent_paths[1])
                if 'Succeed' in log_info_2:
                    pass
                else:
                    self.update_process_info('发布到北洋园失败！！')
            else:
                self.update_process_info('不符合北洋园发布条件，跳过发布……')
        except Exception as exc:
            self.update_process_info('错误： %s' % exc)
        finally:
            try:
                os.remove(new_torrent_paths[1])
            except Exception:
                pass

        try:
            if self.raw_info['origin_site'] not in ['nypt', 'U2'] and self.config_dl['up_to_nypt']:
                self.update_process_info('正在发布到南洋……')
                log_info_1 = self.upload_to_nypt(self.raw_info, new_torrent_paths[2])
                if 'Succeed' in log_info_1:
                    pass
                else:
                    self.update_process_info('发布到南洋失败！！')
            else:
                self.update_process_info('不符合南洋发布条件，跳过发布……')
        except Exception as exc:
            self.update_process_info('错误： %s' % exc)
        finally:
            try:
                os.remove(new_torrent_paths[2])
            except Exception:
                pass

        try:
            if self.raw_info['origin_site'] not in ['mteam', 'U2'] and self.config_dl['up_to_mteam']:
                self.update_process_info('正在发布到馒头……')
                log_info = self.upload_to_mteam(self.raw_info, new_torrent_paths[3])
                if 'Succeed' in log_info:
                    pass
                else:
                    self.update_process_info('发布到馒头失败！！')
            else:
                self.update_process_info('不符合馒头发布条件，跳过发布……')
        except Exception as exc:
            self.update_process_info('错误： %s' % exc)
        finally:
            try:
                os.remove(new_torrent_paths[3])
            except Exception:
                pass

        try:
            if self.raw_info['origin_site'] not in ['cmct', 'U2'] and self.judge_for_cmct():
                self.update_process_info('正在发布到SSD……')
                log_info = self.upload_to_cmct(self.raw_info, new_torrent_paths[4])
                if 'Succeed' in log_info:
                    pass
                else:
                    self.update_process_info('发布到SSD失败！！')
            else:
                self.update_process_info('不符合SSD发布条件，跳过发布……')
        except Exception as exc:
            self.update_process_info('错误： %s' % exc)
        finally:
            try:
                os.remove(new_torrent_paths[4])
            except Exception:
                pass

        try:
            if self.raw_info['origin_site'] not in ['ourbits', 'U2'] and self.judge_for_ourbits():
                self.update_process_info('正在发布到OurBits……')
                log_info = self.upload_to_ourbits(self.raw_info, new_torrent_paths[5])
                if 'Succeed' in log_info:
                    pass
                else:
                    self.update_process_info('发布到OurBits失败！！')
            else:
                self.update_process_info('不符合OurBits发布条件，跳过发布……')
        except Exception as exc:
            self.update_process_info('错误： %s' % exc)
        finally:
            try:
                os.remove(new_torrent_paths[5])
            except Exception:
                pass

        try:
            if self.raw_info['origin_site'] not in ['hdsky', 'U2'] and self.judge_for_hdsky():
                self.update_process_info('正在发布到hdsky……')
                log_info = self.upload_to_hdsky(self.raw_info, new_torrent_paths[6])
                if 'Succeed' in log_info:
                    pass
                else:
                    self.update_process_info('发布到hdsky失败！！')
            else:
                self.update_process_info('不符合hdsky发布条件，跳过发布……')
        except Exception as exc:
            self.update_process_info('错误： %s' % exc)
        finally:
            try:
                os.remove(new_torrent_paths[6])
            except Exception:
                pass

        try:
            if self.raw_info['origin_site'] not in ['hdchina', 'U2'] and self.judge_for_hdchina():
                self.update_process_info('正在发布到HDChina……')
                log_info = self.upload_to_hdchina(self.raw_info, new_torrent_paths[7])
                if 'Succeed' in log_info:
                    pass
                else:
                    self.update_process_info('发布到HDChina失败！！')
            else:
                self.update_process_info('不符合HDChina发布条件，跳过发布……')
        except Exception as exc:
            self.update_process_info('错误： %s' % exc)
        finally:
            try:
                os.remove(new_torrent_paths[7])
            except Exception:
                pass

        try:
            if self.raw_info['origin_site'] not in ['ttg', 'U2'] and self.judge_for_ttg():
                self.update_process_info('正在发布到TTG……')
                log_info = self.upload_to_ttg(self.raw_info, new_torrent_paths[8])
                if 'Succeed' in log_info:
                    pass
                else:
                    self.update_process_info('发布到TTG失败！！')
            else:
                self.update_process_info('不符合TTG发布条件，跳过发布……')
        except Exception as exc:
            self.update_process_info('错误： %s' % exc)
        finally:
            try:
                os.remove(new_torrent_paths[8])
            except Exception:
                pass

        try:
            if self.raw_info['origin_site'] != 'pter' and self.config_dl['up_to_pter']:
                self.update_process_info('正在发布到猫站……')
                log_info = self.upload_to_pter(self.raw_info, new_torrent_paths[9])
                if 'Succeed' in log_info:
                    pass
                else:
                    self.update_process_info('发布到猫站失败！！')
            else:
                self.update_process_info('不符合猫站发布条件，跳过发布……')
        except Exception as exc:
            self.update_process_info('错误： %s' % exc)
        finally:
            try:
                os.remove(new_torrent_paths[9])
            except Exception:
                pass
        self.statu.append('任务完成')
        self.update_process_info('任务已经完成！！')

    def reannounce_torrent(self, hash_info):
        time_passed = 0
        while time_passed < 600:
            sleep(30)
            self.qb.reannounce(hash_info)
            # print('announce freshed')
            sleep(10)
            time_passed = time_passed + 10

