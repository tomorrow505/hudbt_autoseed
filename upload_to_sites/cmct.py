# -*- coding: utf-8 -*-
# Author:tomorrow505


import re
from common_info import extend_descr_after, Amer_Euro, domains, extend_descr_before, recommand_allow
import common_methods

dict_standard = {
    '4K': 1, '1080p': 2, '1080i': 3, '720p': 4, 'SD': 5,
}


def get_post_data(raw_info):

    raw_info = get_info_from_raw_info(raw_info)
    extend_descr_after_1 = extend_descr_after.format(detail_link=raw_info['detail_link'],
                                                     version=common_methods.VERSION)
    if recommand_allow:
        for item in domains[0:4]:
            raw_info['recommand'] = raw_info['recommand'].replace(item, 'https://springsunday.net/')
        raw_info['recommand'] = raw_info['recommand'].replace(' ', '%2F')
    else:
        raw_info['recommand'] = ''
    descr = extend_descr_before + raw_info['descr'] + raw_info['nfo'] + raw_info['recommand'] + extend_descr_after_1

    data = {
        "name": raw_info['ename'],
        "small_descr": raw_info["small_descr"],
        "url": raw_info["url"],
        "descr": descr,
        "type": str(raw_info['type_']),
        "standard_sel": dict_standard[raw_info['standard']],
        "source_sel": raw_info['source_sel'],
        "audiocodec_sel": raw_info['audiocodec_sel'],
        "codec_sel": raw_info['codec_sel'],
        "medium_sel": raw_info['medium_sel'],
        "uplver": raw_info['uplver'],
    }

    return data


def get_info_from_raw_info(raw_info):

    big_type = raw_info['big_type']

    type_info = raw_info['type_info']

    # 主标题
    if raw_info['title'] != '':
        name = raw_info['title']
    else:
        name = raw_info['filename'].split('_')[0]
        if raw_info['episodes']:
            index = name.upper().find('COMPLETE')
            if index >= 0:
                name = name.replace(name[index: index + 8], raw_info['episodes'])
            else:
                try:
                    year = re.search('(19\d{2}|20\d{2})', name)
                    index = year.span()
                    name = name[0:index[1]] + ' ' + raw_info['episodes'] + name[index[1]:]
                except Exception:
                    pass

    raw_info['ename'] = name.strip().replace(' ', '.')

    # 分辨率
    if not raw_info['standard']:
        if name.lower().find('1080p') >= 0:
            raw_info['standard'] = '1080p'
        elif name.lower().find('720p') >= 0:
            raw_info['standard'] = '720p'
        elif name.lower().find('2160p') >= 0 or name.lower().find('4k') >= 0:
            raw_info['standard'] = '4K'
        else:
            raw_info['standard'] = '720p'

    # 类型
    raw_info['type_'] = 509
    if big_type == '电影':
        raw_info['type_'] = 501
    elif big_type == '剧集':
        raw_info['type_'] = 502
    elif big_type == '纪录':
        raw_info['type_'] = 503
    elif big_type == '动漫':
        raw_info['type_'] = 504
    elif big_type == '综艺':
        raw_info['type_'] = 505
    elif big_type == '体育':
        raw_info['type_'] = 506
    elif big_type == '音乐':
        raw_info['type_'] = 508

    # 封装格式
    raw_info['medium_sel'] = 0
    # print(raw_info['video_format'])
    if raw_info['video_format'] == 'mp4':
        raw_info['medium_sel'] = 7
    elif raw_info['video_format'] == 'mkv':
        raw_info['medium_sel'] = 6

    if raw_info['media_type'] == 'Blu-ray':
        raw_info['medium_sel'] = 1
    elif raw_info['media_type'] == 'Remux':
        raw_info['medium_sel'] = 4
    elif raw_info['media_type'] == 'DVD':
        raw_info['medium_sel'] = 3

    if raw_info['title'].upper().find('HDTV') >= 0:
        raw_info['medium_sel'] = 5

    # 地区
    cn = ['华语', '大陆', '中国', '国产']
    hktw = ['香港', '台湾']
    jpkr = ['日本', '韩国']

    processing_sel = {
        1: cn, 9: Amer_Euro, 2: hktw, 10: jpkr
    }
    flag = False
    raw_info['source_sel'] = 3
    for item in processing_sel.keys():
        if flag:
            break
        country_list = processing_sel[item]
        for country in country_list:
            if type_info.find(country) >= 0:
                flag = True
                raw_info['source_sel'] = item
                break

    # 主视频编码
    dict_codec = {
        'H264': 2, 'VC-1': 3, 'MPEG-2': 4, 'MPEG-4': 4, 'H265': 1, 'other': 0
    }
    if not raw_info['codec']:
        title = raw_info['title']
        if title.upper().find('VC-1') >= 0:
            raw_info['codec'] = 'VC-1'
        elif title.upper().find('H264') >= 0 or title.upper().find('X264') >= 0:
            raw_info['codec'] = 'H264'
        elif title.upper().find('MPEG-2') >= 0:
            raw_info['codec'] = 'MPEG-2'
        elif title.upper().find('MPEG-4') >= 0:
            raw_info['codec'] = 'MPEG-4'
        elif title.upper().find('H265') >= 0 or title.upper().find('X265') >= 0 or title.upper().find('HEVC') >= 0:
            raw_info['codec'] = 'H265'
        else:
            raw_info['codec'] = 'other'
    raw_info['codec_sel'] = dict_codec[raw_info['codec']]

    # 主音频编码
    dict_audiocodec = {
        'DTS-HD': 1, 'TrueHD': 2, 'LPCM': 6, 'DTS': 3, 'AC-3': 4, 'AAC': 5, 'FLAC': 7, 'APE': 8, 'WAV': 9, 'other': 0
    }
    title = raw_info['title']
    if title.upper().find('DTS-HD') >= 0:
        raw_info['audiocodec'] = 'DTS-HD'
    elif title.upper().find('DTS') >= 0:
        raw_info['audiocodec'] = 'DTS'
    elif title.upper().find('TRUEHD') >= 0:
        raw_info['audiocodec'] = 'TrueHD'
    elif title.upper().find('LPCM') >= 0:
        raw_info['audiocodec'] = 'LPCM'
    elif title.upper().find('AC-3') >= 0 or title.upper().find('AC3') >= 0:
        raw_info['audiocodec'] = 'AC-3'
    elif title.upper().find('AAC') >= 0:
        raw_info['audiocodec'] = 'AAC'
    elif title.upper().find('FLAC') >= 0:
        raw_info['audiocodec'] = 'FLAC'
    elif title.upper().find('WAV') >= 0:
        raw_info['audiocodec'] = 'WAV'
    elif title.upper().find('APE') >= 0:
        raw_info['audiocodec'] = 'APE'
    else:
        raw_info['audiocodec'] = 'other'
    raw_info['audiocodec_sel'] = dict_audiocodec[raw_info['audiocodec']]

    return raw_info
