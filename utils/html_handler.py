# -*- coding: utf-8 -*-
# Author:tomorrow505


import re
from bs4 import BeautifulSoup
import requests
from html2bbcode.parser import HTML2BBCode
import get_douban_info
from utils import common_methods

# 为了判断类似于quote里的东西要不要保留
judge_list = ['RELEASE NAME', 'RELEASE DATE', 'VIDEO CODE', 'FRAME RATE', 'AUDIO', 'SOURCE', 'BIT RATE',
              'RESOLUTION', 'SUBTITLES', 'FRAMERATE', 'BITRATE', '[IMG]', '视频编码', '帧　　率', '译　　名',
              '主　　演', '主演', '海报', '截图', '分辨率']
# [IMG]为了留下ourbits图片  视频编码, 帧　　率  保留HDChina， 译名防止把简介用quote框起来 海报是为了保留北邮人的海报

# 为了判断是不是包含了info 信息
mediainfo_judge = ['RELEASE NAME', 'RELEASE DATE', 'VIDEO CODE', 'FRAME RATE', 'AUDIO', 'SOURCE', 'BIT RATE',
                   'RESOLUTION', 'SUBTITLES', 'FRAMERATE', 'BITRATE', '视频编码', '帧　　率', '帧　率', '分辨率']

# 分大类为了下载到指定目录
type_dict_for_big_type = {
    "电影": '电影', "Movie": '电影', "剧集": '剧集', "电视剧": '剧集', "欧美剧": '剧集',
    "日剧": '剧集', "韩剧": '剧集', "大陆港台剧": '剧集', "TV series": '剧集',
    "TV-Episode": '剧集', "TV-Pack": '剧集', 'TV Series': '剧集',
    "综艺": '综艺', "TV-Show": '综艺', "TV Shows": '综艺', "音乐": '音乐', "Music": '音乐',
    "动漫": '动漫', "动画": '动漫', "Anime": '动漫', "Animation": '动漫', "剧场": '动漫',
    "软件": '软件',
    "游戏": '游戏',
    "资料": '资料',
    "学习": '学习',
    "Sports": '体育', "体育": '体育',
    "紀錄教育": '纪录', "Documentary": '纪录', "纪录": '纪录', "Doc": '纪录',
    "移动视频": '移动视频'
}

# site_support_code = ['nypt', 'tjupt', 'mteam', 'cmct', 'Pter']


class HtmlHandler:

    def __init__(self, abbr, html, torrent_id=0):
        self.site = abbr
        self.html = html
        self.torrent_id = torrent_id

        # 基本信息，能够从页面上获取到的——16个字段  full_title 类似于北邮人，北洋，麦田这样的包含很多信息的标题
        self.raw_info = {'title': '', 'full_title': '', 'small_descr': '', 'descr': '', 'url': '',  'dburl': '',
                         'douban_info': '', 'recommand': '', 'nfo': '', 'hash_info': '', 'type_info': '', 'cname': '',
                         'language': '', 'subinfo': '', 'region': '', 'format': '', 'episodes': '', 'big_type': '',
                         'publish_time': '', 'download_url': '', 'codec': '', 'standard': '', 'media_type': '',
                         'img_num': 1}  # 新增三个编码格式，清晰度，媒介类型

        self.soup = self.get_soup()

        self.ref_link = {
            'imdb_link': '',
            'url_imdb_for_desc': {},
            'douban_link': ''
        }

        self.parser_html()

    def get_soup(self):
        if self.site == 'ttg':
            self.html = self.html.encode('ISO-8859-1').decode()
        # if self.site == 'ourbits':
        #     self.html = self.html.replace('<br>', '<br> \t\n\n')
        self.capture_email_bug()
        soup = BeautifulSoup(self.html, 'lxml')
        return soup

    def capture_email_bug(self):
        def decodeemail(e):
            de = ""
            k = int(e[:2], 16)
            for i in range(2, len(e) - 1, 2):
                de += chr(int(e[i:i + 2], 16) ^ k)
            return de
        item = re.findall('data-cfemail="([\da-z]*)"', self.html)
        email_str = []
        for it in item:
            email_str.append(decodeemail(it))
        for ii in range(len(item)):
            email = re.search('(<[^<]*?\[email.*?protected\].*?>)', self.html)
            try:
                index = email.span()
                email = self.html[index[0]:index[1]]
                self.html = self.html.replace(email, email_str[ii], 1)
            except AttributeError:
                print('error')

    def parser_html(self):

        func_dict = {
            'byr': self.parser_html_byr,
            'tjupt': self.parser_html_tjupt,
            'npupt': self.parser_html_npupt,
            'stju': self.parser_html_sjtu,
            'ourbits': self.parser_html_ourbits,
            'cmct': self.parser_html_cmct,
            'nypt': self.parser_html_nypt,
            'mteam': self.parser_html_mteam,
            'hdchina': self.parser_html_hdchina,
            'ttg': self.parser_html_ttg,
            'FRDS': self.parser_html_frds,
            'HDHome': self.parser_html_hdhome,
            '麦田': self.parser_html_nwsuaf6,
            'hudbt': self.parser_html_hudbt,
            'Pter': self.parser_html_pter,
            'beitai': self.parser_html_beitai,
            'chd': self.parser_html_chd,
            'U2': self.parser_html_u2,
            'pthome': self.parser_html_pthome,
            'hdsky': self.parser_html_hdsky,
            'hdstreet': self.parser_html_hdstreet,
            'ptp': self.parser_html_ptp
        }
        func_dict[self.site]()
        self.fill_info_from_descr()
        self.raw_info['title'] = common_methods.refine_title(self.raw_info['title'])
        self.check_img()
        self.raw_info['small_descr'].replace('应求发布', '')
        self.raw_info['small_descr'].replace('应求', '')
        return self.raw_info

    def get_raw_info(self):
        return self.raw_info

    # 北邮人
    def parser_html_byr(self):

        # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr, mode=0)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr
        # print(descr)

        # 获取imdb链接和豆瓣信息
        self.get_imdb_douban_link_by_str(descr)
        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型相关信息很好获取
        type_1 = self.soup.select('#type')[0].get_text()
        type_2 = self.soup.select('#sec_type')[0].get_text()
        type_info = type_1 + type_2
        self.get_region()
        self.raw_info['type_info'] = type_info + self.raw_info['region']
        self.get_big_type(type_info)

        # 主、副标题
        small_descr = self.soup.select('#subtitle')[0].get_text()
        full_title = to_bbcode(str(self.soup.find('h1', id='share')))
        self.raw_info['full_title'] = full_title
        print(full_title)
        try:
            e = re.search('(E\d{1,3}-?E?\d{0,3})', full_title)
            episodes = e.group(1)
            self.raw_info['episodes'] = episodes
        except AttributeError:
            pass

        try:
            sub_infos = re.findall('\[(.*?)\]', full_title)
            if type_info.find('电影') >= 0:
                if not small_descr.find(sub_infos[1]) >= 0:
                    small_descr = sub_infos[1] + ' | ' + small_descr
            elif type_info.find('资料') >= 0 or type_info.find('剧集') >= 0:
                if not small_descr.find(sub_infos[2]) >= 0:
                    small_descr = sub_infos[2] + ' | ' + small_descr
            elif type_info.find('体育') >= 0 or type_info.find('综艺') >= 0 or type_info.find('纪录') >= 0 \
                    or type_info.find('软件') >= 0 or type_info.find('游戏') >= 0 or type_info.find('动漫') >= 0 \
                    or type_info.find('音乐') >= 0:
                if not small_descr.find(sub_infos[3]) >= 0:
                    small_descr = sub_infos[3] + ' | ' + small_descr
        except Exception:
            pass
        # if len(small_descr) == 0:
        #     sub_info_1 = re.sub('\[[^\u4e00-\u9fff]+\]|\[|\]', ' ', full_title)
        #     sub_info_1 = re.sub("国产|连载|华语|英文|大陆|欧美", "", sub_info_1).replace(' ', '')
        #     small_descr = sub_info_1

        # try:
        #     tran_name = re.search('◎译名(.*)', ''.join(self.raw_info['descr'].split()))
        #     tran_name = tran_name.group(1).strip()
        # except AttributeError:
        #     tran_name = ''
        # try:
        #     name = re.search('◎片名(.*)', ''.join(self.raw_info['descr'].split()))
        #     name = name.group(1).strip()
        # except AttributeError:
        #     name = ''
        # ch_name = ''
        #
        # for ch in tran_name:
        #     if u'\u4e00' <= ch <= u'\u9fff':
        #         ch_name = tran_name.rstrip()
        #         break
        # if ch_name == '':
        #     ch_name = name.rstrip()
        # tmp_list = ch_name.split('/')
        # if len(tmp_list) >= 2:
        #     cname = '/'.join(tmp_list[0:2])
        # else:
        #     cname = tmp_list[0]
        #
        # if self.raw_info['small_descr'].find(cname) < 0:
        #     self.raw_info['small_descr'] = cname + self.raw_info['small_descr']

        self.raw_info['small_descr'] = small_descr.replace('免费', '')
        print(self.raw_info['small_descr'])

        if self.raw_info['big_type'] in ['学习', '游戏']:
            sub_info_2 = re.sub('\[|\]', ' ', full_title)
            sub_info_2 = re.sub(' +', ' ', sub_info_2)
            self.raw_info['title'] = sub_info_2.strip().replace('免费', '')
        elif self.raw_info['big_type'] == '动漫':
            # sub_titles = re.findall('\[(.*?)\]', self.raw_info['full_title'])
            try:
                self.raw_info['title'] = ' '.join(sub_infos[4:-1]) + ' ' + sub_infos[2]
            except Exception:
                self.raw_info['title'] = ''

        # hash_info
        hash_info = ''
        no_border_wide = self.soup.select('td .no_border_wide')
        for item in no_border_wide:
            item_str = str(item)
            if item_str.find('Hash码') >= 0:
                hash_info = to_bbcode(item_str).split(':')[-1].strip()
                break
        self.raw_info['hash_info'] = hash_info

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])
        self.get_media_info()

    # CMCT
    def parser_html_cmct(self):

        # 主标题
        title = to_bbcode(str(self.soup.find('h1', id='top').get_text()))
        title = re.sub('\[.*?\]', '', title)
        self.raw_info['title'] = ' '.join(title.split('.')).strip()

        # 副标题
        small_descr = self.soup.select('.rowfollow')[1].get_text()
        self.raw_info['small_descr'] = small_descr

        # 类型
        type_info = self.soup.select('.rowfollow')[4].get_text()
        type_info = ' '.join(type_info.split())
        media_info = self.soup.select('.rowfollow')[5].get_text()
        media_info = ' '.join(media_info.split())
        type_info = type_info + media_info
        self.get_region()
        self.raw_info['type_info'] = type_info + self.raw_info['region']
        self.get_big_type(type_info)

        # 编码类
        if type_info.find('封装(容器)格式: Blu-ray(原盘)') >= 0:
            self.raw_info['media_type'] = 'Blu-ray'
        elif type_info.find('封装(容器)格式: Matroska') >= 0 or type_info.find('封装(容器)格式: MP4') >= 0:
            self.raw_info['media_type'] = 'Encode'
        elif type_info.find('封装(容器)格式: TS/REMUX') >= 0:
            self.raw_info['media_type'] = 'Rumux'

        if type_info.find('分辨率: 1080p') >= 0:
            self.raw_info['standard'] = '1080p'
        elif type_info.find('分辨率: 720p') >= 0:
            self.raw_info['standard'] = '720p'
        elif type_info.find('分辨率: UHD') >= 0:
            self.raw_info['standard'] = '4K'
        elif type_info.find('分辨率: 1080i') >= 0:
            self.raw_info['standard'] = '1080i'
        elif type_info.find('分辨率: SD') >= 0:
            self.raw_info['standard'] = 'SD'

        if type_info.find('主视频编码: VC-1') >= 0:
            self.raw_info['codec'] = 'VC-1'
        elif type_info.find('主视频编码: H.264') >= 0:
            self.raw_info['codec'] = 'H264'
        elif type_info.find('主视频编码: MPEG-2') >= 0:
            self.raw_info['codec'] = 'MPEG-2'
        elif type_info.find('主视频编码: MPEG-4') >= 0:
            self.raw_info['codec'] = 'MPEG-4'
        elif type_info.find('主视频编码: HEVC') >= 0:
            self.raw_info['codec'] = 'H265'

        # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr, mode=0)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        # 获取链接和豆瓣信息
        self.get_imdb_douban_link_by_str(descr)
        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])

    # HDChina  # 信任的站点
    def parser_html_hdchina(self):

        # 主标题
        title = to_bbcode(str(self.soup.find('h2', id='top').get_text()))
        title = re.sub('\[.*?\]', '', title)
        self.raw_info['title'] = ' '.join(title.split('.')).strip()

        # 副标题
        small_descr = ''
        for line in self.soup.h3.children:
            small_descr = small_descr + line
        self.raw_info['small_descr'] = small_descr

        # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        # 获取链接和豆瓣信息
        kimdb = to_bbcode(str(self.soup.find('div', id='kimdb')))
        kdouban = to_bbcode(str(self.soup.find('div', id='kdouban')))
        self.get_imdb_douban_link_by_list([descr, kimdb, kdouban])

        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        img_url = '[img]https://hdchina.org/attachments/201705/20170526101902f426542dd6d0d44825b0f2baae30639b.jpg.' \
                  'pagespeed.ce.9CZULdbQ1E.jpg[/img]'
        self.raw_info['descr'] = self.raw_info['descr'].replace(img_url, '')

        # 类型
        self.get_region()
        type_info = to_bbcode(str(self.soup.select('li[class="right bspace"]')[0]))
        type_info = type_info + self.raw_info['region']
        self.raw_info['type_info'] = type_info
        self.get_big_type(type_info)

        # 编码类
        if type_info.find('类型：原盘(Full BD)') >= 0 or type_info.find('类型：4K UltraHD') >= 0:
            self.raw_info['media_type'] = 'Blu-ray'
        elif type_info.find('媒介: Encode') >= 0:
            self.raw_info['media_type'] = 'Encode'
        elif type_info.find('媒介: Remux') >= 0:
            self.raw_info['media_type'] = 'Rumux'
        elif type_info.find('媒介: DVD') >= 0:
            self.raw_info['media_type'] = 'DVD'

        if type_info.find('格式：1080P') >= 0:
            self.raw_info['standard'] = '1080p'
        elif type_info.find('格式：720p') >= 0:
            self.raw_info['standard'] = '720p'
        elif type_info.find('格式：4K') >= 0:
            self.raw_info['standard'] = '4K'
        elif type_info.find('格式：1080i') >= 0:
            self.raw_info['standard'] = '1080i'
        elif type_info.find('格式：SD') >= 0:
            self.raw_info['standard'] = 'SD'

        if type_info.find('编码：VC-1') >= 0:
            self.raw_info['codec'] = 'VC-1'
        elif type_info.find('编码：x264') >= 0 or type_info.find('编码: x264') >= 0:
            self.raw_info['codec'] = 'H264'
        elif type_info.find('编码：MPEG-2') >= 0:
            self.raw_info['codec'] = 'MPEG-2'
        elif type_info.find('编码：MPEG-4') >= 0:
            self.raw_info['codec'] = 'MPEG-4'
        elif type_info.find('编码：x265/HEVC') >= 0 or type_info.find('编码：x265/HEVC') >= 0:
            self.raw_info['codec'] = 'H265'

        # hash_info
        hash_info = to_bbcode(str(self.soup.select('td .file_hash')[0]))
        hash_info = hash_info.split('：')[-1].strip()
        self.raw_info['hash_info'] = hash_info

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])

    # HDSky    # 信任的站点
    def parser_html_hdsky(self):

        # 主标题
        all_title = to_bbcode(str(self.soup.find('h1', id='top').get_text()))
        title = re.sub('\[.*?\]', '', all_title)
        self.raw_info['title'] = ' '.join(title.split('.')).strip()

        # # 副标题
        small_descr = self.soup.select('.rowfollow')[2].get_text()
        self.raw_info['small_descr'] = small_descr

        # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr)
        descr = self.format_descr(descr)
        descr = descr.replace('[img]https://hdsky.me/adv/hds_logo.png[/img]', '')
        self.raw_info['descr'] = descr

        kimdb = to_bbcode(str(self.soup.find('div', id='kimdb')))
        kdouban = to_bbcode(str(self.soup.find('div', id='kdouban')))
        # 获取链接和豆瓣信息
        self.get_imdb_douban_link_by_list([descr, kimdb, kdouban])

        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型
        self.get_region()
        type_info = self.soup.select('.rowfollow')[3].get_text()
        type_info = type_info + self.raw_info['region']
        self.raw_info['type_info'] = type_info
        self.get_big_type(type_info)

        # 编码类
        if type_info.find('媒介: Blu-ray') >= 0 or type_info.find('媒介: UHD Blu-ray') >= 0:
            self.raw_info['media_type'] = 'Blu-ray'
        elif type_info.find('媒介: Encode') >= 0:
            self.raw_info['media_type'] = 'Encode'
        elif type_info.find('媒介: Remux') >= 0:
            self.raw_info['media_type'] = 'Rumux'

        if type_info.find('分辨率: 2K/1080p') >= 0:
            self.raw_info['standard'] = '1080p'
        elif type_info.find('分辨率: 720p') >= 0:
            self.raw_info['standard'] = '720p'
        elif type_info.find('分辨率: 4K/2160p') >= 0:
            self.raw_info['standard'] = '4K'
        elif type_info.find('分辨率: 1080i') >= 0:
            self.raw_info['standard'] = '1080i'

        if type_info.find('编码: VC-1') >= 0:
            self.raw_info['codec'] = 'VC-1'
        elif type_info.find('编码: H.264/AVC') >= 0:
            self.raw_info['codec'] = 'H264'
        elif type_info.find('编码: MPEG-2') >= 0:
            self.raw_info['codec'] = 'MPEG-2'
        elif type_info.find('编码: MPEG-4') >= 0:
            self.raw_info['codec'] = 'MPEG-4'
        elif type_info.find('编码: x265') >= 0 or type_info.find('编码: HEVC') >= 0:
            self.raw_info['codec'] = 'H265'

        # hash_info
        hash_info = ''
        no_border_wide = self.soup.select('td .no_border_wide')
        for item in no_border_wide:
            item_str = str(item)
            if item_str.find('Hash码') >= 0:
                hash_info = to_bbcode(item_str).split(':')[-1].strip()
                break
        self.raw_info['hash_info'] = hash_info

        # print(hash_info)
        # print(self.raw_info['descr'])
        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])

    # Mteam    # 信任的站点
    def parser_html_mteam(self):

        # 主标题
        title = to_bbcode(str(self.soup.find('h1', id='top').get_text()))
        title = title.split('[免費]')[0]
        title = re.sub('\[.*?\]', '', title).strip()
        self.raw_info['title'] = ' '.join(title.split('.'))

        # 副标题
        small_descr = self.soup.select('.rowfollow')[1].get_text()
        self.raw_info['small_descr'] = small_descr

        # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr, mode=0)
        descr = self.format_descr(descr)
        descr = descr.replace('[img]https://tp.m-team.cc/logo.png[/img]', '')
        descr = descr.replace('[img]https://img.m-team.cc/images/2016/12/05/d3be0d6f0cf8738edfa3b8074744c8e8.png[/img]'
                              , '')
        self.raw_info['descr'] = descr

        kimdb = to_bbcode(str(self.soup.find('div', id='kimdb')))
        kdouban = to_bbcode(str(self.soup.find('div', id='kdouban')))
        # 获取链接和豆瓣信息
        self.get_imdb_douban_link_by_list([descr, kimdb, kdouban])

        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型
        type_info_1 = (self.soup.select('.rowfollow')[2].get_text())
        type_info_2 = (self.soup.select('.rowfollow')[3].get_text())
        type_info = type_info_1 + type_info_2
        self.get_region()
        self.raw_info['type_info'] = type_info + self.raw_info['region']
        # print(type_info)
        self.get_big_type(type_info)

        # hash_info
        hash_info = ''
        no_border_wide = self.soup.select('td .no_border_wide')
        for item in no_border_wide:
            item_str = str(item)
            if item_str.find('Hash碼') >= 0:
                hash_info = to_bbcode(item_str).split(':')[-1].strip()
                break
        self.raw_info['hash_info'] = hash_info

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])

    # 蒲公英  # 信任的站点
    def parser_html_npupt(self):

        title = self.soup.find('div', class_='jtextfill')
        title = title.get_text().split('    ')[0]
        title = ' '.join(title.split('.')).strip()
        self.raw_info['title'] = title

        # 副标题
        small_descr = self.soup.find('span', class_='large').get_text()
        self.raw_info['small_descr'] = small_descr

        # 简介
        ads = self.soup.find_all('div', class_='well small')
        try:
            for ad in ads:
                ad.decompose()
        except Exception:
            pass
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr, mode=2)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        # 获取链接和豆瓣信息
        self.get_imdb_douban_link_by_str(descr)

        # 类型
        info_1 = self.soup.find(class_='label label-success').get_text()
        info_2 = self.soup.find(class_='label label-info').get_text()
        type_info = info_1 + info_2
        self.get_region()
        type_info = type_info + self.raw_info['region']
        self.raw_info['type_info'] = type_info
        self.get_big_type(type_info)

        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])
        self.get_media_info()

    # 南洋
    def parser_html_nypt(self):

        # 主标题
        title = self.soup.find('h1', id='top').get_text()
        title = title.split(' ')[0]
        self.raw_info['title'] = ' '.join(title.split('.')).strip()

        # # 副标题
        small_descr = self.soup.select('.rowfollow')[1].get_text()
        self.raw_info['small_descr'] = small_descr

        # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr, mode=0)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        kimdb = to_bbcode(str(self.soup.find('div', id='kimdb')))
        kdouban = to_bbcode(str(self.soup.find('div', id='kdouban')))

        # 获取链接和豆瓣信息
        no_url_in_descr = False
        self.get_imdb_douban_link_by_str(descr)
        if not self.ref_link['douban_link'] and not self.ref_link['imdb_link']:
            no_url_in_descr = True
        if no_url_in_descr and descr.find('◎主     演') < 0:
            self.get_imdb_douban_link_by_list([kimdb, kdouban])

        if no_url_in_descr:
            douban_info = self.get_douban_info()
        else:
            douban_info = ''

        self.raw_info['descr'] = douban_info + '\n' + self.raw_info['descr']

        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型
        self.get_region()
        type_info = (self.soup.select('.rowfollow')[2].get_text())
        type_info = ' '.join(type_info.split()) + self.raw_info['region']
        self.raw_info['type_info'] = type_info
        self.get_big_type(type_info)

        # hash_info
        hash_info = ''
        no_border_wide = self.soup.select('td .no_border_wide')
        for item in no_border_wide:
            item_str = str(item)
            if item_str.find('Hash码') >= 0:
                hash_info = to_bbcode(item_str).split(':')[-1].strip()
                break
        self.raw_info['hash_info'] = hash_info

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])
        self.get_media_info()

    # OurBits
    def parser_html_ourbits(self):
        # 主标题
        title = self.soup.find('h1', id='top').get_text()
        title = title.split('[免费]')[0]
        title = re.sub('\[.*?\]', '', title)
        self.raw_info['title'] = title.strip()

        # 副标题
        small_descr = self.soup.select('.rowfollow')[1].get_text()
        self.raw_info['small_descr'] = small_descr

        # 简介 返回来的是经过转换的bbcode，直接str就可以了
        descr = self.soup.find('div', id='kdescr')
        descr = str(descr)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        # 获取链接和豆瓣信息
        self.get_imdb_douban_link_by_str(descr)

        if not self.ref_link['douban_link'] and not self.ref_link['imdb_link']:
            if not self.ref_link['imdb_link']:
                kimdb = to_bbcode(str(self.soup.find('div', id='kimdb')))
                try:
                    imdb_link = re.search('.*imdb.com/title/(tt\d{5,9})', kimdb)
                    url_imdb_for_desc = {'site': 'douban', 'sid': imdb_link.group(1)}
                    imdb_link = 'https://www.imdb.com/title/' + imdb_link.group(1) + '/'
                    self.raw_info['recommand'] = recommand_for_imdb(imdb_link)
                    self.ref_link['imdb_link'] = imdb_link
                    self.ref_link['url_imdb_for_desc'] = url_imdb_for_desc
                except AttributeError:
                    pass
            if not self.ref_link['douban_link']:
                doubanid = re.search('data-doubanid=(\d{3,10})', self.html)
                try:
                    doubanid = doubanid.group(1)
                except AttributeError:
                    doubanid = ''
                if doubanid:
                    self.ref_link['douban_link'] = 'https://movie.douban.com/subject/%s/' % doubanid
            if self.ref_link['douban_link'] or self.ref_link['imdb_link']:
                douban_info = self.get_douban_info()
            else:
                douban_info = ''
        else:
            actor = re.search('(主演)|◎导演', ''.join(descr.split()))
            if not actor:
                douban_info = self.get_douban_info()
            else:
                douban_info = ''

        self.raw_info['descr'] = douban_info + descr
        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型
        type_info = (self.soup.select('.rowfollow')[2].get_text())
        type_info = ' '.join(type_info.split())
        self.get_region()
        self.raw_info['type_info'] = type_info + self.raw_info['region']
        self.get_big_type(type_info)

        # 编码类
        if type_info.find('媒介: FHD Blu-ray') >= 0 or type_info.find('媒介: UHD Blu-ray') >= 0:
            self.raw_info['media_type'] = 'Blu-ray'
        elif type_info.find('媒介: Encode') >= 0:
            self.raw_info['media_type'] = 'Encode'
        elif type_info.find('媒介: Remux') >= 0:
            self.raw_info['media_type'] = 'Rumux'

        if type_info.find('分辨率: 1080p') >= 0:
            self.raw_info['standard'] = '1080p'
        elif type_info.find('分辨率: 720p') >= 0:
            self.raw_info['standard'] = '720p'
        elif type_info.find('分辨率: 2160p') >= 0:
            self.raw_info['standard'] = '4K'
        elif type_info.find('分辨率: 1080i') >= 0:
            self.raw_info['standard'] = '1080i'

        if type_info.find('编码: VC-1') >= 0:
            self.raw_info['codec'] = 'VC-1'
        elif type_info.find('编码: H.264') >= 0:
            self.raw_info['codec'] = 'H264'
        elif type_info.find('编码: MPEG-2') >= 0:
            self.raw_info['codec'] = 'MPEG-2'
        elif type_info.find('编码: MPEG-4') >= 0:
            self.raw_info['codec'] = 'MPEG-4'
        elif type_info.find('编码: H.265') >= 0 or type_info.find('编码: HEVC') >= 0:
            self.raw_info['codec'] = 'H265'

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])

        # print(self.raw_info['descr'])

    # 葡萄  # 信任的站点
    def parser_html_sjtu(self):

        # 主标题
        title = self.soup.find('h1').get_text()
        title = re.sub(r'\[.*?\]', '', title).strip()
        title = re.sub(r'\(.*?\)', '', title).strip()
        self.raw_info['title'] = title.strip()

        # 副标题
        small_descr = to_bbcode(str(self.soup.select('td .rowfollow')[2]))
        self.raw_info['small_descr'] = small_descr

        # # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr,mode=0)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        # 获取链接信息
        self.get_imdb_douban_link_by_str(descr)
        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型
        type_info = str(self.soup.select('td .rowfollow')[3].get_text())
        type_info = type_info.split()[3]
        self.get_region()
        self.raw_info['type_info'] = type_info + self.raw_info['region']
        self.get_big_type(type_info)

        # hash_info
        hash_info = ''
        no_border_wide = self.soup.select('td .no_border_wide')
        for item in no_border_wide:
            item_str = str(item)
            if item_str.find('Hash码') >= 0:
                hash_info = to_bbcode(item_str).split(':')[-1].strip()
                break
        self.raw_info['hash_info'] = hash_info

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])
        self.get_media_info()

    # 北洋园 # 信任的站点
    def parser_html_tjupt(self):

        # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr, mode=0)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        kimdb = to_bbcode(str(self.soup.find('div', id='kimdb')))
        kdouban = to_bbcode(str(self.soup.find('div', id='kdouban')))
        # 获取链接信息
        self.get_imdb_douban_link_by_list([descr, kimdb, kdouban])
        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型
        type_info = ''.join(to_bbcode(str(self.soup.select('td .rowfollow')[3])).split())
        self.get_region()
        type_info = type_info + self.raw_info['region']
        self.raw_info['type_info'] = type_info
        self.get_big_type(type_info)

        # 副标题
        small_descr = self.soup.select('td .rowfollow')[2].get_text()
        try:
            tran_name = re.search('◎译.*?名(.*)', self.raw_info['descr'])
            tran_name = tran_name.group(1).strip()
        except AttributeError:
            tran_name = ''
        try:
            name = re.search('◎片.*?名(.*)', self.raw_info['descr'])
            name = name.group(1).strip()
        except AttributeError:
            name = ''
        ch_name = ''

        for ch in tran_name:
            if u'\u4e00' <= ch <= u'\u9fff':
                ch_name = tran_name.rstrip()
                break
        if ch_name == '':
            ch_name = name.rstrip()
        tmp_list = ch_name.split('/')
        if len(tmp_list) >= 2:
            cname = '/'.join(tmp_list[0:2])
        else:
            cname = tmp_list[0]
        if self.raw_info['small_descr'].find(cname) < 0:
            self.raw_info['small_descr'] = cname + self.raw_info['small_descr']

        full_title = to_bbcode(str(self.soup.find('h1', id='top')))
        self.raw_info['full_title'] = full_title
        try:
            e = re.search('(E\d{1,3}-?E?\d{0,3})', full_title)
            episodes = e.group(1)
            self.raw_info['episodes'] = episodes
        except AttributeError:
            pass
        self.raw_info['small_descr'] = small_descr

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])

        # hash_info
        hash_info = ''
        no_border_wide = self.soup.select('td .no_border_wide')
        for item in no_border_wide:
            item_str = str(item)
            if item_str.find('Hash码') >= 0:
                hash_info = to_bbcode(item_str).split(':')[-1].strip()
                break
        self.raw_info['hash_info'] = hash_info
        self.get_media_info()

    # TTG  # 信任的站点
    def parser_html_ttg(self):

        # 主标题
        all_title = to_bbcode(str(self.soup.find('h1').get_text()))
        title = all_title.split('[')[0]
        self.raw_info['title'] = ' '.join(title.split('.')).strip()

        # 副标题
        small_descr = all_title.replace(title, '')
        small_descr = small_descr.replace('[', '')
        small_descr = small_descr.replace(']', '')
        self.raw_info['small_descr'] = small_descr.strip()

        # 简介
        descr = self.soup.find('div', id='kt_d')
        quotos = descr.find_all('p', class_='sub')
        try:
            for quoto in quotos:
                quoto.decompose()
        except Exception:
            pass

        descr = format_mediainfo(self.soup, descr, mode=3)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr
        # print(descr)

        # 获取链接和豆瓣信息
        self.get_imdb_douban_link_by_str(descr)
        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型——可以提取出来
        self.get_region()
        type_info = to_bbcode(str(self.soup.select('td[valign="top"]')[8].next_sibling.get_text()))
        type_info = type_info + self.raw_info['region']
        self.raw_info['type_info'] = type_info
        self.get_big_type(type_info)

        # 编码类
        if type_info.find('BluRay原盘') >= 0:
            self.raw_info['media_type'] = 'Blu-ray'
        if title.find('Remux') >= 0:
            self.raw_info['media_type'] = 'Rumux'
        else:
            self.raw_info['media_type'] = 'Encode'

        if title.find('1080p') >= 0:
            self.raw_info['standard'] = '1080p'
        elif title.find('720p') >= 0:
            self.raw_info['standard'] = '720p'
        elif title.find('2160p') >= 0:
            self.raw_info['standard'] = '4K'
        elif title.find('1080i') >= 0:
            self.raw_info['standard'] = '1080i'

        self.raw_info['codec'] = 'H264'

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])

    # FRDS  # 信任的站点
    def parser_html_frds(self):
        # 主标题

        all_title = to_bbcode(str(self.soup.select('.rowfollow')[1].get_text()))
        self.raw_info['title'] = all_title.strip()

        # 发布时间
        td_publish_time = self.soup.select('.rowfollow')[0]
        spans = td_publish_time.find_all('span')
        span = spans[-1]
        publish_time = span.get_attribute_list('title')[0]
        # print(publish_time)
        self.raw_info['publish_time'] = publish_time

        # 副标题
        sub_title = to_bbcode(str(self.soup.find('h1').get_text()))
        sub_title = re.sub('【|】| \[.*\]', ' ', sub_title)
        sub_title = sub_title.strip()
        self.raw_info['small_descr'] = sub_title

        # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr)
        descr = self.format_descr(descr)
        descr = descr.replace('[img]static/pic/smilies/92.gif[/img]', '')
        self.raw_info['descr'] = descr

        # 获取链接和豆瓣信息
        self.get_imdb_douban_link_by_str(descr)

        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        try:
            nfo = to_bbcode(str(self.soup.find('div', id='knfo').get_text()))
            if nfo:
                self.raw_info['nfo'] = '\n\n[quote=iNFO][font=Courier New]%s[/font][/quote]\n' % nfo
        except Exception:
            pass

        # 类型
        type_info = to_bbcode(str(self.soup.select('.rowfollow')[2].get_text()))
        self.get_region()
        type_info = type_info + self.raw_info['region']
        self.raw_info['type_info'] = type_info
        self.get_big_type(type_info)

        self.raw_info['media_type'] = 'Encode'

        if type_info.find('分辨率: 1080p') >= 0:
            self.raw_info['standard'] = '1080p'
        elif type_info.find('分辨率: 720p') >= 0:
            self.raw_info['standard'] = '720p'
        elif type_info.find('分辨率: 2160p(4k)') >= 0:
            self.raw_info['standard'] = '4K'
        elif type_info.find('分辨率: 1080i') >= 0:
            self.raw_info['standard'] = '1080i'

        if type_info.find('编码: AVC(x264)') >= 0:
            self.raw_info['codec'] = 'H264'
        else:
            self.raw_info['codec'] = 'H265'

        # hash_info
        hash_info = ''
        no_border_wide = self.soup.select('td .no_border_wide')
        for item in no_border_wide:
            item_str = str(item)
            if item_str.find('Hash码') >= 0:
                hash_info = to_bbcode(item_str).split(':')[-1].strip()
                break
        self.raw_info['hash_info'] = hash_info

        if not self.raw_info['nfo']:
            self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])
        # print(self.raw_info['descr'])

    # hdhome  # 信任的站点
    def parser_html_hdhome(self):
        # 主标题
        title = to_bbcode(str(self.soup.find('h1', id='top').get_text()))
        title = title.split('[免费]')[0]
        title = re.sub('\[.*?\]', '', title)
        self.raw_info['title'] = ' '.join(title.split('.')).strip()

        # # 副标题
        sub_title = to_bbcode(str(self.soup.select('.rowfollow')[1].get_text()))
        sub_title = re.sub('\[|\]', ' ', sub_title)
        sub_title = re.sub(' +', ' ', sub_title)
        self.raw_info['small_descr'] = sub_title.strip()

        # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr, mode=0)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        # 获取链接信息
        self.get_imdb_douban_link_by_str(descr)
        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型
        type_info = to_bbcode(str(self.soup.select('.rowfollow')[2].get_text()))
        self.get_region()
        type_info = type_info + self.raw_info['region']
        self.raw_info['type_info'] = type_info
        self.get_big_type(type_info)

        # 编码类
        if type_info.find('媒介: Blu-ray') >= 0 or type_info.find('媒介: UHD Blu-ray') >= 0:
            self.raw_info['media_type'] = 'Blu-ray'
        elif type_info.find('媒介: Encode') >= 0:
            self.raw_info['media_type'] = 'Encode'
        elif type_info.find('媒介: Remux') >= 0:
            self.raw_info['media_type'] = 'Remux'

        if type_info.find('分辨率: 1080p') >= 0:
            self.raw_info['standard'] = '1080p'
        elif type_info.find('分辨率: 720p') >= 0:
            self.raw_info['standard'] = '720p'
        elif type_info.find('分辨率: 2160p/4K') >= 0:
            self.raw_info['standard'] = '4K'
        elif type_info.find('分辨率: 1080i') >= 0:
            self.raw_info['standard'] = '1080i'

        if type_info.find('编码: VC-1') >= 0:
            self.raw_info['codec'] = 'VC-1'
        elif type_info.find('编码: H.264/AVC') >= 0:
            self.raw_info['codec'] = 'H264'
        elif type_info.find('编码: MPEG-2') >= 0:
            self.raw_info['codec'] = 'MPEG-2'
        elif type_info.find('编码: MPEG-4') >= 0:
            self.raw_info['codec'] = 'MPEG-4'
        elif type_info.find('编码: H.265') >= 0:
            self.raw_info['codec'] = 'H265'

        if not self.raw_info['nfo']:
            self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])

    # 麦田  # 信任的站点
    def parser_html_nwsuaf6(self):

        # 类型很好获取
        type_info = self.soup.select('.rowfollow')[3].get_text()
        self.get_region()
        self.raw_info['type_info'] = type_info + self.raw_info['region']
        self.get_big_type(type_info)

        # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr, mode=0)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        # 获取imdb链接和豆瓣信息
        self.get_imdb_douban_link_by_str(descr)
        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 主、副标题
        small_descr = self.soup.select('.rowfollow')[2].get_text()
        full_title = to_bbcode(str(self.soup.find('h1', id='top')))
        self.raw_info['full_title'] = full_title
        try:
            e = re.search('(E\d{1,3}-?E?\d{0,3})', full_title)
            episodes = e.group(1)
            self.raw_info['episodes'] = episodes
        except AttributeError:
            pass
        if len(small_descr) == 0:
            sub_info_1 = re.sub('\[[^\u4e00-\u9fff]+\]|\[|\]', ' ', full_title)
            sub_info_1 = re.sub("国产|连载|华语|英文|大陆|欧美", "", sub_info_1).replace(' ', '')
            small_descr = sub_info_1
        try:
            tran_name = re.search('◎译.*?名(.*)', self.raw_info['descr'])
            tran_name = tran_name.group(1).strip()
        except AttributeError:
            tran_name = ''
        try:
            name = re.search('◎片.*?名(.*)', self.raw_info['descr'])
            name = name.group(1).strip()
        except AttributeError:
            name = ''
        ch_name = ''

        for ch in tran_name:
            if u'\u4e00' <= ch <= u'\u9fff':
                ch_name = tran_name.rstrip()
                break
        if ch_name == '':
            ch_name = name.rstrip()
        tmp_list = ch_name.split('/')
        if len(tmp_list) >= 2:
            cname = '/'.join(tmp_list[0:2])
        else:
            cname = tmp_list[0]
        if self.raw_info['small_descr'].find(cname) < 0:
            self.raw_info['small_descr'] = cname + self.raw_info['small_descr']

        self.raw_info['small_descr'] = small_descr.replace('免费', '')

        if self.raw_info['type_'] in ['学习', '纪录', '游戏']:
            sub_info_2 = re.sub('\[|\]', ' ', full_title)
            sub_info_2 = re.sub(' +', ' ', sub_info_2)
            self.raw_info['title'] = sub_info_2.strip()

        # print(self.raw_info['descr'])

        # hash_info
        hash_info = ''
        no_border_wide = self.soup.select('td .no_border_wide')
        for item in no_border_wide:
            item_str = str(item)
            if item_str.find('Hash码') >= 0:
                hash_info = to_bbcode(item_str).split(':')[-1].strip()
                break
        self.raw_info['hash_info'] = hash_info

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])
        self.get_media_info()

    # hudbt
    def parser_html_hudbt(self):
        # 主标题
        title = self.soup.find('h1', id='page-title').get_text()
        self.raw_info['title'] = title.strip()

        # 副标题
        small_descr = self.soup.find_all('dd')[1].get_text()
        self.raw_info['small_descr'] = small_descr

        # 简介 返回来的是经过转换的bbcode，直接str就可以了
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        # 获取链接和豆瓣信息
        self.get_imdb_douban_link_by_str(descr)
        self.get_imdb_douban_link_by_str(descr)
        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型
        type_info = (self.soup.find_all('dd')[2].get_text())
        type_info = ' '.join(type_info.split())
        self.get_region()
        self.raw_info['type_info'] = type_info + self.raw_info['region']
        self.get_big_type(type_info)

        # hash_info
        hash_info = ''
        minor_list = self.soup.find_all('dl', class_='minor-list properties')
        for item in minor_list:
            item_str = str(item)
            if item_str.find('Hash码') >= 0:
                hash_info = to_bbcode(item_str)
                hash_info = re.search('[0-9a-z]{40}', hash_info)
                try:
                    hash_info = hash_info.group()
                except AttributeError:
                    hash_info = ''
        self.raw_info['hash_info'] = hash_info

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])
        self.get_media_info()

    # 猫站
    def parser_html_pter(self):
        # 主标题
        title = self.soup.find('h1', id='top').get_text()
        # self.raw_info['title'] = title.split('[免费]')[0].strip()
        self.raw_info['title'] = re.sub('\[2?X?免费\].*', '', title).strip()

        # 副标题
        small_descr = self.soup.select('.rowfollow')[5].get_text()
        self.raw_info['small_descr'] = small_descr

        # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr, mode=0)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        # 获取链接和豆瓣信息
        self.get_imdb_douban_link_by_str(descr)
        self.get_imdb_douban_link_by_str(descr)
        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型
        type_info = self.soup.select('.rowfollow')[7].get_text()
        type_info = ' '.join(type_info.split())
        self.get_region()
        self.raw_info['type_info'] = type_info + self.raw_info['region']
        self.get_big_type(type_info)

        # 编码类
        if type_info.find('质量: UltraHD(4K)') >= 0 or type_info.find('质量: Blu-ray') >= 0:
            self.raw_info['media_type'] = 'Blu-ray'
        elif type_info.find('质量: Encode') >= 0:
            self.raw_info['media_type'] = 'Encode'
        elif type_info.find('质量: Remux') >= 0:
            self.raw_info['media_type'] = 'Rumux'
        elif type_info.find('质量: DVD') >= 0:
            self.raw_info['media_type'] = 'DVD'

        if title.find('1080p') >= 0:
            self.raw_info['standard'] = '1080p'
        elif title.find('720p') >= 0:
            self.raw_info['standard'] = '720p'
        elif title.find('4K') >= 0:
            self.raw_info['standard'] = '4K'
        elif title.find('1080i') >= 0:
            self.raw_info['standard'] = '1080i'

        if title.upper().find('VC-1') >= 0:
            self.raw_info['codec'] = 'VC-1'
        elif title.upper().find('H264') >= 0 or title.upper().find('X264') >= 0:
            self.raw_info['codec'] = 'H264'
        elif title.upper().find('MPEG-2') >= 0:
            self.raw_info['codec'] = 'MPEG-2'
        elif title.upper().find('MPEG-4') >= 0:
            self.raw_info['codec'] = 'MPEG-4'
        elif title.upper().find('H265') >= 0 or title.upper().find('X265') >= 0 or title.upper().find('HEVC') >= 0:
            self.raw_info['codec'] = 'H265'

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])

    # PThome
    def parser_html_pthome(self):
        # 主标题
        title = self.soup.find('h1', id='top').get_text()
        self.raw_info['title'] = re.sub('\[.*\].*', '', title).strip()

        # 副标题
        small_descr = self.soup.select('.rowfollow')[1].get_text()
        self.raw_info['small_descr'] = small_descr

        # 简介 返回来的是经过转换的bbcode，直接str就可以了
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr, mode=0)
        descr = self.format_descr(descr)
        descr = descr.replace('[b]在此页面截图请注意passkey链接部分打码以防passkey泄露！[/b]', '')
        self.raw_info['descr'] = descr

        # 获取链接和豆瓣信息
        self.get_imdb_douban_link_by_str(descr)
        self.get_imdb_douban_link_by_str(descr)
        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型
        type_info = self.soup.select('.rowfollow')[2].get_text()
        type_info = ' '.join(type_info.split())
        self.get_region()
        type_info = type_info + self.raw_info['region']
        self.raw_info['type_info'] = type_info
        self.get_big_type(type_info)

        # 编码类
        if type_info.find('媒介: UHD Blu-ray') >= 0 or type_info.find('媒介: Blu-ray(原盘)') >= 0:
            self.raw_info['media_type'] = 'Blu-ray'
        elif type_info.find('媒介: encode') >= 0:
            self.raw_info['media_type'] = 'Encode'
        elif type_info.find('媒介: REMUX') >= 0:
            self.raw_info['media_type'] = 'Rumux'

        if type_info.find('分辨率: 1080p') >= 0:
            self.raw_info['standard'] = '1080p'
        elif type_info.find('分辨率: 720p') >= 0:
            self.raw_info['standard'] = '720p'
        elif type_info.find('分辨率: 4K') >= 0:
            self.raw_info['standard'] = '4K'
        elif type_info.find('分辨率: 1080i') >= 0:
            self.raw_info['standard'] = '1080i'

        if type_info.find('编码: VC-1') >= 0:
            self.raw_info['codec'] = 'VC-1'
        elif type_info.find('编码: H.264') >= 0:
            self.raw_info['codec'] = 'H264'
        elif type_info.find('编码: MPEG-2') >= 0:
            self.raw_info['codec'] = 'MPEG-2'
        elif type_info.find('编码: MPEG-4') >= 0:
            self.raw_info['codec'] = 'MPEG-4'
        elif type_info.find('编码: H.265') >= 0:
            self.raw_info['codec'] = 'H265'

        print('codec', self.raw_info['codec'])
        print(type_info)

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])

    # beitai
    def parser_html_beitai(self):
        # 主标题
        title = self.soup.find('h1', id='top').get_text()
        self.raw_info['title'] = re.sub('\[2?X?免费\].*', '', title).strip()

        # 副标题
        small_descr = self.soup.select('.rowfollow')[1].get_text()
        self.raw_info['small_descr'] = small_descr

        # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr, mode=0)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        # 获取链接和豆瓣信息
        self.get_imdb_douban_link_by_str(descr)
        self.get_imdb_douban_link_by_str(descr)
        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型
        type_info = self.soup.select('.rowfollow')[2].get_text()
        type_info = ' '.join(type_info.split())
        self.get_region()
        type_info = type_info + self.raw_info['region']
        self.raw_info['type_info'] = type_info
        self.get_big_type(type_info)

        # 编码类
        if descr.find('DISC INFO') >= 0:
            self.raw_info['media_type'] = 'Blu-ray'
        elif type_info.find('媒介: Encode') >= 0:
            self.raw_info['media_type'] = 'Encode'
        elif type_info.find('媒介: Remux') >= 0:
            self.raw_info['media_type'] = 'Rumux'

        if type_info.find('分辨率: 1080p') >= 0:
            self.raw_info['standard'] = '1080p'
        elif type_info.find('分辨率: 720p') >= 0:
            self.raw_info['standard'] = '720p'
        elif type_info.find('分辨率: 4K') >= 0:
            self.raw_info['standard'] = '4K'
        elif type_info.find('分辨率: 1080i') >= 0:
            self.raw_info['standard'] = '1080i'

        if type_info.find('编码: VC-1') >= 0:
            self.raw_info['codec'] = 'VC-1'
        elif type_info.find('编码: H.264') >= 0:
            self.raw_info['codec'] = 'H264'
        elif type_info.find('编码: MPEG-2') >= 0:
            self.raw_info['codec'] = 'MPEG-2'
        elif type_info.find('编码: MPEG-4') >= 0:
            self.raw_info['codec'] = 'MPEG-4'
        elif type_info.find('编码: H.265') >= 0:
            self.raw_info['codec'] = 'H265'

        # hash_info
        hash_info = ''
        no_border_wide = self.soup.select('td .no_border_wide')
        for item in no_border_wide:
            item_str = str(item)
            if item_str.find('Hash码') >= 0:
                hash_info = to_bbcode(item_str).split(':')[-1].strip()
                break
        self.raw_info['hash_info'] = hash_info

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])

    # chd
    def parser_html_chd(self):
        # 主标题
        title = self.soup.find('h1', id='top').get_text()
        title = re.sub('\(.*\)', '', title)
        title = title.replace('x265.', 'x265 ')
        self.raw_info['title'] = re.sub('Free', '', title).strip()

        # 副标题
        small_descr = self.soup.select('.rowfollow')[1].get_text()
        self.raw_info['small_descr'] = small_descr

        # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr, mode=0)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        # 获取链接和豆瓣信息
        self.get_imdb_douban_link_by_str(descr)
        self.get_imdb_douban_link_by_str(descr)
        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型
        type_info = self.soup.select('.rowfollow')[2].get_text()
        type_info = ' '.join(type_info.split())
        self.get_region()
        type_info = type_info + self.raw_info['region']
        self.raw_info['type_info'] = type_info
        self.get_big_type(type_info)
        # print(self.raw_info['region'])

        # 编码类
        if type_info.find('媒介: Blu-ray') >= 0:
            self.raw_info['media_type'] = 'Blu-ray'
        elif type_info.find('媒介: Encode') >= 0:
            self.raw_info['media_type'] = 'Encode'
        elif type_info.find('媒介: Remux') >= 0:
            self.raw_info['media_type'] = 'Rumux'

        if type_info.find('分辨率: 1080p') >= 0:
            self.raw_info['standard'] = '1080p'
        elif type_info.find('分辨率: 720p') >= 0:
            self.raw_info['standard'] = '720p'
        elif type_info.find('分辨率: 4K') >= 0:
            self.raw_info['standard'] = '4K'
        elif type_info.find('分辨率: 1080i') >= 0:
            self.raw_info['standard'] = '1080i'

        if type_info.find('编码: VC-1') >= 0:
            self.raw_info['codec'] = 'VC-1'
        elif type_info.find('编码: H.264/AVC') >= 0:
            self.raw_info['codec'] = 'H264'
        elif type_info.find('编码: MPEG-2') >= 0:
            self.raw_info['codec'] = 'MPEG-2'
        elif type_info.find('编码: MPEG-4') >= 0:
            self.raw_info['codec'] = 'MPEG-4'
        elif type_info.find('编码: H.265') >= 0:
            self.raw_info['codec'] = 'H265'

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])

    # U2
    def parser_html_u2(self):
        # 主标题
        title = self.soup.find('h1', id='top').get_text()
        self.raw_info['full_title'] = title
        sub_title = re.findall('\[(.*?)\]', title)
        title = ' '.join(sub_title[1:])
        self.raw_info['title'] = re.sub(' +', ' ', title).strip()
        # print(title)

        # 副标题
        small_descr = sub_title[0]
        self.raw_info['small_descr'] = small_descr
        # print(small_descr)

        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr, mode=4)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        # 类型
        tds = self.soup.find_all('td', class_='rowhead nowrap')
        td_row = self.soup.find_all('td', class_='rowfollow')
        for i, td in enumerate(tds):
            txt = td.get_text()
            if txt.find('基本信息') >= 0:
                td_row_find = td_row[i+1]
                self.raw_info['type_info'] = td_row_find.get_text()
                # print(self.raw_info['type_info'])

        self.raw_info['big_type'] = '动漫'

        hash_info = ''
        no_border_wide = self.soup.select('td .no_border_wide')
        for item in no_border_wide:
            item_str = str(item)
            if item_str.find('种子散列值') >= 0:
                hash_info = to_bbcode(item_str).split(':')[-1].strip()
                break
        self.raw_info['hash_info'] = hash_info
        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])

        # print(self.raw_info['descr'])

    # hdstreet
    def parser_html_hdstreet(self):
        # 主标题
        title = self.soup.find('h1', id='top').get_text()
        title = re.sub('\[2?X?免费.*\]', '', title).strip()
        title = re.sub('[^-\.~@￡A-Za-z0-9]', ' ', title)
        title = re.sub(' +', ' ', title)
        self.raw_info['title'] = title

        # 副标题
        small_descr = self.soup.select('.rowfollow')[3].get_text()
        self.raw_info['small_descr'] = small_descr

        # 简介
        descr = self.soup.find('div', id='kdescr')
        descr = format_mediainfo(self.soup, descr, mode=0)
        descr = self.format_descr(descr)
        self.raw_info['descr'] = descr

        # 获取链接和豆瓣信息
        self.get_imdb_douban_link_by_str(descr)
        self.get_imdb_douban_link_by_str(descr)
        self.raw_info['url'] = self.ref_link['imdb_link']
        self.raw_info['dburl'] = self.ref_link['douban_link']

        # 类型
        type_info = self.soup.select('.rowfollow')[5].get_text()
        type_info = ' '.join(type_info.split())
        self.get_region()
        type_info = type_info + self.raw_info['region']
        self.raw_info['type_info'] = type_info
        self.get_big_type(type_info)

        # hash_info
        hash_info = ''
        no_border_wide = self.soup.select('td .no_border_wide')
        for item in no_border_wide:
            item_str = str(item)
            if item_str.find('Hash码') >= 0:
                hash_info = to_bbcode(item_str).split(':')[-1].strip()
                break
        self.raw_info['hash_info'] = hash_info

        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])
        self.get_media_info()

    # ptp
    def parser_html_ptp(self):
        table = self.soup.find('table', id='torrent-table')

        str_1 = 'torrent_%s' % self.torrent_id

        torrent = table.find('tr', id=str_1)
        torrent_info = torrent.find('div', class_='bbcode-table-guard')
        # self.soup.get_attribute_list()
        # 主标题
        aas = torrent_info.find_all('a')
        for a in aas:
            href = a.get_attribute_list('onclick')[0]
            if href == 'BBCode.MediaInfoToggleShow( this );':
                title = a.get_text()
                break
        title = title.replace('[', ' ')
        title = title.replace(']', ' ')
        title = title.replace('(', ' ')
        title = title.replace(')', ' ')
        title = ' '.join(title.split('.')[0:-1])
        title = re.sub(' +', ' ', title)
        # print(title)
        self.raw_info['title'] = title
        # print(self.raw_info['title'])

        # 获取imdb链接
        rating_table = self.soup.find('table', id='movie-ratings-table')
        imdb_link = rating_table.find('a')
        imdb_link = imdb_link.get_attribute_list('href')[0]
        self.raw_info['url'] = imdb_link
        self.get_imdb_douban_link_by_str(imdb_link)
        self.raw_info['dburl'] = ''

        # 简介-----豆瓣信息+mediainfo+图片信息
        douban_info = self.get_douban_info()  # 豆瓣信息
        mediainfo = torrent_info.find('blockquote').get_text()
        descr = douban_info + '[quote=iNFO][font=Courier New]%s[/font][/quote]' % mediainfo
        pictures = torrent_info.find_all('img')
        for item in pictures:
            url = item.get_attribute_list('src')[0]
            descr = descr + '\n[img]%s[/img]' % url
        self.raw_info['descr'] = descr
        # print(descr)

        # # 副标题
        self.fill_info_from_descr()
        self.raw_info['small_descr'] = self.raw_info['cname']
        # print(self.raw_info['small_descr'])

        # # 类型
        self.get_region()
        self.raw_info['type_info'] = self.raw_info['region'] + '电影'
        self.raw_info['big_type'] = '电影'

        # 获取下载链接
        str_2 = 'group_torrent_header_%s' % self.torrent_id
        tr_of_download_info = self.soup.find('tr', id=str_2)
        a_of_download_url = tr_of_download_info.find('a', title='Download')
        prex_str = 'https://passthepopcorn.me/'
        self.raw_info['download_url'] = prex_str + a_of_download_url.get_attribute_list('href')[0]
        # print(self.raw_info['download_url'])
        title_of_torrent = tr_of_download_info.find('img').get_attribute_list('title')[0]
        if title_of_torrent == 'High quality torrent':
            self.raw_info['small_descr'] = self.raw_info['small_descr'] + '| PTP Golden Popcorn '
        else:
            self.raw_info['small_descr'] = self.raw_info['small_descr'] + '| 转自PTP '

        # print(self.raw_info['small_descr'])
        self.raw_info['nfo'] = judge_nfo_existed(self.raw_info['descr'])
        self.get_media_info()

    def get_imdb_douban_link_by_str(self, check_str):
        if not self.ref_link['imdb_link']:
            try:
                imdb_link = re.search('(tt\d{5,9})', check_str)
                url_imdb_for_desc = {'site': 'douban', 'sid': imdb_link.group(1)}
                imdb_link = 'https://www.imdb.com/title/' + imdb_link.group(1) + '/'
                self.raw_info['recommand'] = recommand_for_imdb(imdb_link)
                self.ref_link['imdb_link'] = imdb_link
                self.ref_link['url_imdb_for_desc'] = url_imdb_for_desc
            except AttributeError:
                pass
        if not self.ref_link['douban_link']:
            try:
                douban_link = re.search('.*douban.com/subject/(\d{5,9})', check_str)
                douban_link = 'https://movie.douban.com/subject/' + douban_link.group(1) + '/'
                self.ref_link['douban_link'] = douban_link
            except AttributeError:
                pass

    def get_imdb_douban_link_by_list(self, check_list):
        for check_str in check_list:
            if check_str:
                self.get_imdb_douban_link_by_str(check_str)

    def get_douban_info(self):
        if self.ref_link['douban_link']:
            try:
                douban_info = get_douban_info.get_douban_descr(self.ref_link['douban_link'])
                if not self.ref_link['imdb_link']:
                    self.get_imdb_douban_link_by_str(douban_info)
            except Exception:
                douban_info = ''
        else:
            if self.ref_link['url_imdb_for_desc']:
                try:
                    douban_info = get_douban_info.get_douban_descr(self.ref_link['url_imdb_for_desc'])
                except Exception:
                    douban_info = ''
            else:
                douban_info = ''

        return douban_info

    def get_region(self):
        try:
            district = re.search('产地(.*)', ''.join(self.raw_info['descr'].split()))
            district = district.group(1).strip()
        except AttributeError:
            try:
                district = re.search('国家(.*)', ''.join(self.raw_info['descr'].split()))
                district = district.group(1).strip()
            except AttributeError:
                district = ''
        if not district:
            try:
                district = re.search('地区(.*)', ''.join(self.raw_info['descr'].split()))
                district = district.group(1).strip()
            except AttributeError:
                district = ''
        self.raw_info['region'] = district.split('/')[0].strip()
        # print(district)

        if self.raw_info['region'].find('中国香港') >= 0:
            self.raw_info['region'] = '香港'
        elif self.raw_info['region'].find('中国台湾') >= 0:
            self.raw_info['region'] = '台湾'

        if self.site == 'chd':
            if self.raw_info['small_descr'].find('台綜') >= 0 or self.raw_info['small_descr'].find('台劇') >= 0:
                self.raw_info['region'] = '台湾'
            elif self.raw_info['small_descr'].find('港綜') >= 0 or self.raw_info['small_descr'].find('港劇') >= 0:
                self.raw_info['region'] = '香港'
            elif self.raw_info['small_descr'].find('韩剧') >= 0 or self.raw_info['small_descr'].find('韩綜') >= 0:
                self.raw_info['region'] = '韩国'
            elif self.raw_info['small_descr'].find('新加坡') >= 0:
                self.raw_info['region'] = '新加坡'
            elif self.raw_info['small_descr'].find('马来西亚') >= 0:
                self.raw_info['region'] = '马来西亚'
            elif self.raw_info['small_descr'].find('中国') >= 0:
                self.raw_info['region'] = '中国'

    def get_language(self):
        try:
            language = re.search('◎语.*?言(.*)', self.raw_info['descr'])
            language = language.group(1).strip()
        except AttributeError:
            language = ''
        self.raw_info['language'] = language

    def get_cname(self):

        try:
            tran_name = re.search('◎译.*?名(.*)', self.raw_info['descr'])
            tran_name = tran_name.group(1).strip()
        except AttributeError:
            tran_name = ''
        try:
            name = re.search('◎片.*?名(.*)', self.raw_info['descr'])
            name = name.group(1).strip()
        except AttributeError:
            name = ''
        ch_name = ''

        for ch in tran_name:
            if u'\u4e00' <= ch <= u'\u9fff':
                ch_name = tran_name.rstrip()
                break
        if ch_name == '':
            ch_name = name.rstrip()
        tmp_list = ch_name.split('/')
        if len(tmp_list) >= 2:
            self.raw_info['cname'] = '/'.join(tmp_list[0:2])
        else:
            self.raw_info['cname'] = tmp_list[0]

    def get_ename(self):
        pass

    def format_descr(self, descr):
        tmp = []
        descr = descr.split('\n')
        for line in descr:
            if len(line.strip()) == 0:
                pass
            else:
                tmp.append(line)
        descr = '\n'.join(tmp)
        if self.site == 'byr':
            descr = re.sub('Info Format Powered By @Rhilip', '', descr)
        elif self.site == 'ourbits':
            a = '<div id="kdescr"><div class="ubbcode">'
            b = '</div></div>'
            c = '[size=3][color=RoyalBlue][b] MediaInfo[/b][/color]'
            descr = descr.replace(a, '')
            descr = descr.replace(b, '')
            descr = descr.replace(c, '')

            quoto = re.findall('(\[quote\][\s\S]*?\[/quote\])', descr, re.M, )
            for item in quoto:
                code = item.upper()
                if not any(i in code for i in judge_list):
                    descr = descr.replace(item, '')
            hide_info = re.findall('(\[hide\][\s\S]*?\[/hide\])', descr, re.M, )
            for item in hide_info:
                descr = descr.replace(item, '')

            descr = descr.replace('[img]attachments', '[img]https://ourbits.club/attachments')
        elif self.site == 'npupt':
            descr = descr.replace(
                '[img]attachments',
                '[img]https://npupt.com/attachments')
            descr = descr.replace(
                '[img]torrents/image/',
                '[img]https://npupt.com/torrents/image/')
        elif self.site == 'tjupt':
            # 图片补链接
            descr = descr.replace(
                '[img]attachments',
                '[img]https://www.tjupt.org/attachments')
            descr = descr.replace(
                'https://www.tjupt.org/jump_external.php?ext_url=', '')
            descr = descr.replace('jump_external.php?ext_url=', '')
            descr = re.sub('jump_external.php?[\s\S]+?ext_url=', '', descr)
            descr = descr.replace('%3A', ':')
            descr = descr.replace('%2F', '/')
        elif self.site == 'nwsuaf6':
            # 图片补链接
            descr = descr.replace(
                '[img]attachments',
                '[img]https://pt.nwsuaf6.edu.cn/attachments')
            descr = descr.replace('%3A', ':')
            descr = descr.replace('%2F', '/')
        elif self.site == 'chd':
            # 图片补链接
            descr = descr.replace(
                '[img]attachments',
                '[img]https://chdbits.co/attachments')
            descr = descr.replace('%3A', ':')
            descr = descr.replace('%2F', '/')
            descr = descr.replace('%3D', '=')
            descr = descr.replace('%3F', '?')
        elif self.site == 'hdchina':
            descr = descr.replace('%3A', ':')
            descr = descr.replace('%2F', '/')
            descr = descr.replace('%3F', '?')
            descr = descr.replace('%3D', '=')
            descr = descr.replace('本资源仅限会员测试带宽之用，严禁用于商业用途！', '')
            descr = descr.replace('对用于商业用途所产生的法律责任，由使用者自负！', '')
            descr = descr.replace('[img]attachments/', '[img]https://hdchina.org/attachments/')
        elif self.site == 'mteam':
            descr = descr.replace('[img]attachments', '[img]https://pt.m-team.cc/attachments')
            descr = descr.replace('imagecache.php?url=', '')
            descr = descr.replace('%3A', ':')
            descr = descr.replace('%2F', '/')
            descr = descr.replace('%3F', '?')
            descr = descr.replace('%3D', '=')
        elif self.site == 'hdsky':
            descr = descr.replace('[img]attachments', '[img]https://hdsky.me/attachments')
            descr = descr.replace('imagecache.php?url=', '')
            descr = descr.replace('%3A', ':')
            descr = descr.replace('%2F', '/')
            descr = descr.replace('%3F', '?')
            descr = descr.replace('%3D', '=')
        elif self.site == '6V':
            descr = descr.replace('[img]static/image/common/none.gif[/img]', '')
        return descr

    def get_big_type(self, info: str or list):
        if isinstance(info, list):
            info = ''.join(info)
        big_type = '其他'
        # flag = False

        for item in type_dict_for_big_type.keys():
            if info.find(item) >= 0:
                big_type = type_dict_for_big_type[item]
                # flag = True
                break

        self.raw_info['big_type'] = big_type

        if self.site in ['hdsky', 'FRDS', 'HDHome']:
            if big_type == '动漫':
                self.raw_info['big_type'] = '电影'
        # print(big_type)

    def fill_info_from_descr(self):
        if not self.raw_info['region']:
            self.get_region()
        self.get_language()
        self.get_cname()

        # print(self.raw_info['region'])

    def get_media_info(self):

        title = self.raw_info['title'] + self.raw_info['full_title']
        descr = self.raw_info['descr']

        # 编码类
        if descr.find('DISC INFO') >= 0:
            self.raw_info['media_type'] = 'Blu-ray'
        else:
            if title.upper().find('BLURAY') >= 0:
                self.raw_info['media_type'] = 'Encode'
            elif title.upper().find('REMUX') >= 0:
                self.raw_info['media_type'] = 'Rumux'
            elif title.upper().find('DVD') >= 0:
                self.raw_info['media_type'] = 'DVD'

        if title.upper().find('1080p') >= 0:
            self.raw_info['standard'] = '1080p'
        elif title.upper().find('720p') >= 0:
            self.raw_info['standard'] = '720p'
        elif title.upper().find('4K') >= 0:
            self.raw_info['standard'] = '4K'
        elif title.upper().find('1080i') >= 0:
            self.raw_info['standard'] = '1080i'

        if title.upper().find('VC-1') >= 0:
            self.raw_info['codec'] = 'VC-1'
        elif title.upper().find('H264') >= 0 or title.upper().find('X264') >= 0:
            self.raw_info['codec'] = 'H264'
        elif title.upper().find('MPEG-2') >= 0:
            self.raw_info['codec'] = 'MPEG-2'
        elif title.upper().find('MPEG-4') >= 0:
            self.raw_info['codec'] = 'MPEG-4'
        elif title.upper().find('H265') >= 0 or title.upper().find('X265') >= 0 or title.upper().find('HEVC') >= 0:
            self.raw_info['codec'] = 'H265'

    def check_img(self):

        # print('here')
        reject_str = ['byr', 'mteam', 'hdchina']
        flag = False
        descr = self.raw_info['descr']

        url_to_delete = re.findall('(\[url.*?\])(\[img\].*?\[/img\])(\[/url\])', descr)
        if url_to_delete:
            for item in url_to_delete:
                full_str = item[0]+item[1]+item[2]
                descr = descr.replace(full_str, item[1])

        img_first = re.search('^.{0,10}\[img\](.*?)\[/img\]', descr)
        if img_first:
            img_first = img_first.group(1)
            if any(img_first.lower().find(item) >= 0 for item in reject_str):
                flag = True
                descr = descr.replace('[img]%s[/img]' % img_first, '')
            else:
                code = check_url(img_first)
                if code != 200:
                    flag = True
                    descr = descr.replace('[img]%s[/img]' % img_first, '')
                else:
                    # if poster == 1:
                    descr = descr.replace(img_first+'[/img]', img_first+'[/img]\n')
        else:
            flag = True

        if flag:
            try:
                douban_info = self.get_douban_info()
                douban_url = re.search('^.{0,5}\[img\](.*?)\[/img\]', douban_info)
                douban_url = douban_url.group(1)
                if img_first != douban_url:
                    descr = '[img]%s[/img]\n\n' % douban_url + descr
            except Exception:
                pass

        img_other = re.findall('(\[img\].*?\[/img\])', descr)
        if len(img_other) > 1:
            self.raw_info['img_num'] = len(img_other)
            img_other = img_other[1:]
            for item in img_other:
                if item.find('totheglory') < 0:
                    if any(item.lower().find(dd) >= 0 for dd in reject_str):

                        self.raw_info['img_num'] = self.raw_info['img_num'] - 1
                        descr = descr.replace(item, '')
                    else:
                        url_of_item = item.replace('[img]', '').replace('[/img]', '')
                    # print(url_of_item)
                        code = check_url(url_of_item)
                        if code != 200:
                            self.raw_info['img_num'] = self.raw_info['img_num'] - 1

        self.raw_info['descr'] = descr
        # print(self.raw_info['descr'])


def to_bbcode(descr):
    parser = HTML2BBCode()
    bbcode = parser.feed(descr)
    return bbcode


def to_bbcode_use_api(data_html):

    url = 'https://www.garyshood.com/htmltobb/'
    data = {
        'baseurl': '',
        'html': data_html.encode()
    }
    try:
        des_post = requests.post(url=url, data=data)
        return_html = des_post.content.decode()
        mysoup = BeautifulSoup(return_html, 'lxml')
        code = mysoup.find('textarea').get_text()
    except Exception:
        # code = to_bbcode(data_html)
        code = to_bbcode_use_api_2(data_html)

    return code


def to_bbcode_use_api_2(data_html):
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/74.0.3729.169 Safari/537.36",
        'Cookie': 'csrftoken=11pSdyiaWLoC54kGmeEeNrbpynMayd5NRzxz2kiV99Qc5zXFQMkwzPn7hMPpv7nU'
    }
    session = requests.session()
    session.headers = headers

    url = 'https://html2bbcode.ru/converter/'
    data = {
        'csrfmiddlewaretoken': 'QxD85IWlX2yiTWBwytXpuAszocEarpRhG5LPUuW6aq0STrev21DHgYEh7BHpoj9o',
        'html': data_html
    }
    try:
        des_post = session.post(url=url, data=data)
        return_html = des_post.content.decode()
        soup = BeautifulSoup(return_html, 'lxml')
        code = soup.find('textarea', id='bbcode').get_text()
    except Exception:
        code = to_bbcode_use_api_3(data_html)
    return code


def to_bbcode_use_api_3(data_html):
    url = 'http://skeena.net/htmltobb/index.pl'
    data = {
        'html': data_html.encode()
    }

    try:
        des_post = requests.post(url=url, data=data)
        return_html = des_post.content.decode()
        mysoup = BeautifulSoup(return_html, 'lxml')
        code = mysoup.find('textarea').get_text()

        # 这个网站解析出来很多是http:/bt 而不是http://bt的形式，替换掉

        def change_str(str_):
            str_ = '//'.join(str_.group().split('/'))
            return str_

        code = re.sub('(https?:/[^/])', change_str, code)
    except Exception:
        code = to_bbcode(data_html)

    return code


def recommand_for_imdb(url):

    base_command = 'https://api.douban.com/v2/movie/imdb/{tt}?&apikey=02646d3fb69a52ff072d47bf23cef8fd'

    recommand_list = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/'
                      '537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    }
    session = requests.session()

    session.headers = headers

    try:

        session.keep_alive = False

        response = session.get(url)

        html = response.text
        # print(html)

        before = '[url=https://hudbt.hust.edu.cn/torrents.php?search='

        # links = re.findall('alt="(.*)" title=.*loadlate="(.*)_AL_.jpg', html)

        links = re.findall('href="/title/(.*)\/\?ref.*\n.*alt="(.*)" title=.*loadlate="(.*)_AL_.jpg', html)

        for link in links:
            if link[2].find('UY190') >= 0 or link[2].find('UX128') >= 0:
                url = base_command.format(tt=link[0])
                response = session.get(url)
                page = response.json()
                # print(page)
                if 'msg' not in page.keys():
                    title = page['title']
                    alt_tit1e = page['alt_title']
                    useful_title = ''
                    for ch in title:
                        if u'\u4e00' <= ch <= u'\u9fff':
                            useful_title = title.split('/')[0].strip()
                            break
                    if useful_title == '':
                        useful_title = alt_tit1e.split('/')[0].strip()

                else:
                    useful_title = link[1]
                # print(useful_title)
                str_ = '%s%s][img]%s_AL_.jpg[/img][/url]' % (before, useful_title, link[2])
                recommand_list.append(str_)
    except Exception as exc:
        print(exc)
        return ''
    if not recommand_list:
        return ''
    else:
        return '\n[quote=相关推荐]' + ''.join(recommand_list) + '[/quote]'


def format_mediainfo(soup, descr, mode=1):
    if mode == 1:
        fieldset = descr.find_all('fieldset')
        for field in fieldset:
            code = field.get_text().upper()
            if not any(i in code for i in judge_list):
                field.decompose()
            else:
                try:
                    legend = field.find('legend')
                    legend.decompose()
                except Exception as exc:
                    # print(exc)
                    pass
                if code.find('海报') >= 0 or code.find('◎译　　名　') >= 0 or code.find('◎主　　演　') >= 0 \
                        or code.find('[img]') >= 0 or code.find('主演') >= 0 or code.find('截图') >= 0:
                    pass
                else:
                    new_string_toinsert = soup.new_string("[quote=iNFO][font=Courier New]")
                    new_string_toappend = soup.new_string("[/font][/quote]")
                    field.insert(0, new_string_toinsert)
                    field.append(new_string_toappend)

    elif mode == 0:  # 馒头和北洋园,南洋的官方种子
        try:
            code_top = descr.find_all('div', class_='codetop')
            for item in code_top:
                item.decompose()
        except Exception:
            pass
        try:
            hide_part = descr.find_all('div', class_='hide')
            for item in hide_part:
                item.decompose()
        except Exception:
            pass
        fieldset = descr.find_all('fieldset')
        for field in fieldset:
            code = field.get_text().upper()
            if not any(i in code for i in judge_list):
                field.decompose()
            else:
                try:
                    legend = field.find('legend')
                    legend.decompose()
                except Exception:
                    pass
                if code.find('海报') >= 0 or code.find('◎译　　名　') >= 0 or code.find('◎主　　演　') >= 0 \
                        or code.find('[img]') >= 0 or code.find('主演') >= 0 or code.find('截图') >= 0:
                    pass
                else:
                    new_string_toinsert = soup.new_string("[quote=iNFO][font=Courier New]")
                    field.insert(0, new_string_toinsert)
                    new_string_toappend = soup.new_string("[/font][/quote]")
                    field.append(new_string_toappend)
        try:
            codemain = descr.find('div', class_='codemain')
            new_string_toinsert = soup.new_string("[quote=iNFO][font=Courier New]")
            codemain.insert(0, new_string_toinsert)
            new_string_toappend = soup.new_string("[/font][/quote]")
            codemain.append(new_string_toappend)
        except Exception:
            pass
    elif mode == 2:  # 蒲公英,竟然也有[code][/code]
        fieldset = descr.find_all('blockquote', class_='quote')
        for field in fieldset:
            code = field.get_text().upper()
            if not any(i in code for i in judge_list):
                field.decompose()
            else:
                try:
                    p = field.find('p')
                    b = field.find('b')
                    p.decompose()
                    b.decompose()
                except Exception:
                    pass
                new_string_toinsert = soup.new_string("[quote=iNFO][font=Courier New]")
                field.insert(0, new_string_toinsert)
                new_string_toappend = soup.new_string("[/font][/quote]")
                field.append(new_string_toappend)
        try:
            code_top = descr.find_all('div', class_='codetop')
            for item in code_top:
                item.decompose()
        except Exception:
            pass
        try:
            codemain = descr.find('div', class_='codemain')
            new_string_toinsert = soup.new_string("[quote=iNFO][font=Courier New]")
            codemain.insert(0, new_string_toinsert)
            new_string_toappend = soup.new_string("[/font][/quote]")
            codemain.append(new_string_toappend)
        except Exception:
            pass
    elif mode == 3:  # mode = 3 TTG
        try:
            imgs = descr.find_all('img', class_='topic')
            for img_2_remove in imgs:
                src = img_2_remove.get_attribute_list('src')[0]
                if src.find('pic/ico') >= 0:
                    img_2_remove.decompose()
            fonts = descr.find_all('font', color='red')
            for font in fonts:
                text = font.get_text()
                if text.find('本种子') >= 0:
                    font.decompose()
        except Exception:
            pass

        tables = descr.find_all('table', class_='main')
        for table in tables:
            code = table.get_text().upper()
            if not any(i in code for i in judge_list):
                table.decompose()
            else:
                new_string_toinsert = soup.new_string("[quote=iNFO][font=Courier New]")
                table.insert(0, new_string_toinsert)
                new_string_toappend = soup.new_string("[/font][/quote]")
                table.append(new_string_toappend)

    elif mode == 4:  # 动漫花园
        fieldset = descr.find_all('fieldset')
        for field in fieldset:
            new_string_toinsert = soup.new_string("[quote]")
            field.insert(0, new_string_toinsert)
            new_string_toappend = soup.new_string("[/quote]")
            field.append(new_string_toappend)

        colheads = descr.find_all('td', class_='colhead')
        for colhead in colheads:
            colhead.decompose()

    descr = to_bbcode_use_api(str(descr))
    return descr


def judge_nfo_existed(descr):
    if any(i in descr.upper() for i in mediainfo_judge):
        nfo = 'true'
    else:
        nfo = ''
    return nfo


def check_url(url):
    try:
        req = requests.get(url)
        code = req.status_code
    except Exception:
        code = 0

    return code


def get_img(url):
    img_url = ''
    if url.find('douban') > 0:
        req = requests.get(url)
        html = req.text
        img_url = re.search('<img src="(.*?)" title="点击看更多海报"', html)
        img_url = img_url.group(1)
        img_url = img_url.replace('img3.doubanio.com', 'img1.doubanio.com')
        img_url = img_url.replace('s_ratio_poster', 'l_ratio_poster')
    elif url.find('imdb') > 0:
        req = requests.get(url)
        html = req.text
        img_url = re.search('<img src="(.*?)" title="点击看更多海报"', html)
        img_url = img_url.group(1)
        img_url = img_url.replace('img3.doubanio.com', 'img1.doubanio.com')
        img_url = img_url.replace('s_ratio_poster', 'l_ratio_poster')
    else:
        pass

    return img_url
