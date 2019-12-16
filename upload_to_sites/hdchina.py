# -*- coding: utf-8 -*-
# Author:Chengli


import re
from common_info import extend_descr_after, Amer_Euro, domains, extend_descr_before, recommand_allow
import common_methods

# 多了一个2K? 不知道啥玩意儿。原盘特殊处理
dict_standard = {
    '1080p': 11, '1080i': 12, '720p': 13, 'SD': 15, '4K': 17, 'other': 10, '2K': 18, '原盘': 2
}


def get_post_data(raw_info):

    raw_info = get_info_from_raw_info(raw_info)
    extend_descr_after_1 = extend_descr_after.format(detail_link=raw_info['detail_link'],
                                                     version=common_methods.VERSION)
    if recommand_allow:
        for item in domains[0:7]:
            raw_info['recommand'] = raw_info['recommand'].replace(item, 'https://hdchina.org/')
        raw_info['recommand'] = raw_info['recommand'].replace(' ', '%2F')
    else:
        raw_info['recommand'] = ''
    descr = extend_descr_before + raw_info['descr'] + raw_info['nfo'] + raw_info['recommand'] + extend_descr_after_1

    cover = re.search('\[img\](.*?)\[/img\]', descr)
    try:
        cover = cover.group(1)
    except AttributeError:
        cover = ''

    raw_info['ename'] = common_methods.refine_title(raw_info['ename'])
    data = {
        "name": raw_info['ename'],
        "small_descr": raw_info["small_descr"],
        "url": raw_info["url"],
        "descr": descr,
        "type": str(raw_info['type_']),
        "standard_sel": dict_standard[raw_info['standard']],
        "audiocodec_sel": raw_info['audiocodec_sel'],
        "medium_sel": raw_info['medium_sel'],
        "team_sel": raw_info['team_sel'],
        "cover": cover,
        "codec_sel": raw_info['codec_sel'],
        "uplver": raw_info['uplver'],
    }

    return data


def get_info_from_raw_info(raw_info):

    big_type = raw_info['big_type']
    type_info = raw_info['type_info']

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

    # 清晰度
    if not raw_info['standard']:
        if name.lower().find('2K') >= 0:
            raw_info['standard'] = '2K'
        elif name.lower().find('1080p') >= 0:
            raw_info['standard'] = '1080p'
        elif name.lower().find('720p') >= 0:
            raw_info['standard'] = '720p'
        elif name.lower().find('2160p') >= 0 or name.lower().find('4k') >= 0:
            raw_info['standard'] = '4K'
        else:
            raw_info['standard'] = '720p'

    if not raw_info['media_type']:
        raw_info['media_type'] = 'Encode'

    # 地区
    # 地区
    cn = ['华语', '大陆', '中国', '国产', '香港', '台湾']
    jp = ['日本']
    kr = ['韩国']

    processing_sel = {
        1: cn, 2: Amer_Euro, 3: jp, 4: kr
    }
    flag = False
    raw_info['source_sel'] = 2
    for item in processing_sel.keys():
        if flag:
            break
        country_list = processing_sel[item]
        for country in country_list:
            if type_info.find(country) >= 0:
                flag = True
                raw_info['source_sel'] = item
                break

    # 类型
    raw_info['type_'] = 409
    if big_type == '电影':
        if raw_info['standard'] == '1080p':
            raw_info['type_'] = 17
        elif raw_info['standard'] == '1080i':
            raw_info['type_'] = 16
        elif raw_info['standard'] == '720p':
            raw_info['type_'] = 9

    elif big_type in ['剧集']:
        if raw_info['source_sel'] == 1:
            if raw_info['title'].lower().find('complete') >= 0:
                raw_info['type'] = 22
            else:
                raw_info['type_'] = 25
        elif raw_info['source_sel'] == 2:
            if raw_info['title'].lower().find('complete') >= 0:
                raw_info['type'] = 21
            else:
                raw_info['type_'] = 13
        elif raw_info['source_sel'] == 3:
            if raw_info['title'].lower().find('complete') >= 0:
                raw_info['type'] = 23
            else:
                raw_info['type_'] = 24
        elif raw_info['source_sel'] == 4:
            if raw_info['title'].lower().find('complete') >= 0:
                raw_info['type'] = 23
            else:
                raw_info['type_'] = 26

    elif big_type in ['纪录']:
        raw_info['type_'] = 5
    elif big_type in ['综艺']:
        raw_info['type_'] = 401
    elif big_type in ['体育']:
        raw_info['type_'] = 15
    elif big_type in ['音乐']:
        raw_info['type_'] = 408
    elif big_type in ['软件']:
        raw_info['type_'] = 422
    elif big_type in ['动漫']:
        raw_info['type_'] = 14
    else:
        raw_info['type_'] = 419
    if raw_info['standard'] == '4K':
        raw_info['type_'] = 410
    if raw_info['media_type'] == 'Blu-ray':
        raw_info['standard'] = '原盘'
        raw_info['type_'] = 20

    if name.upper().endswith(("PAD", 'IHD')) or name.upper().find('IPAD') >= 0:
        raw_info['type_'] = 27

    # 媒介——封装格式
    raw_info['medium_sel'] = 15

    if raw_info['media_type'] == 'Blu-ray':
        raw_info['medium_sel'] = 11
    if raw_info['media_type'] == 'Encode':
        raw_info['medium_sel'] = 5
    elif raw_info['media_type'] == 'Remux':
        raw_info['medium_sel'] = 6
    elif raw_info['media_type'] == 'DVD':
        raw_info['medium_sel'] = 14

    if raw_info['title'].upper().find('HDTV') >= 0:
        raw_info['medium_sel'] = 13
    if raw_info['title'].upper().find('MINIBD') >= 0:
        raw_info['medium_sel'] = 2
    if raw_info['title'].upper().find('WEB-DL') >= 0:
        raw_info['medium_sel'] = 21

    raw_info['team_sel'] = ''

    # 视频编码
    dict_codec = {
        'H264': 1, 'VC-1': 2, 'MPEG-2': 4, 'H265': 10, 'other': 5, 'x264': 6, 'xvid': 3
    }
    if not raw_info['codec']:
        title = raw_info['title']
        if title.upper().find('VC-1') >= 0:
            raw_info['codec'] = 'VC-1'
        elif title.upper().find('H264') >= 0:
            raw_info['codec'] = 'H264'
        elif title.upper().find('X264') >= 0:
            raw_info['codec'] = 'x264'
        elif title.upper().find('MPEG-2') >= 0:
            raw_info['codec'] = 'MPEG-2'
        elif title.upper().find('XVID') >= 0:
            raw_info['codec'] = 'xvid'
        elif title.upper().find('H265') >= 0 or title.upper().find('X265') >= 0 or title.upper().find('HEVC') >= 0:
            raw_info['codec'] = 'H265'
        else:
            raw_info['codec'] = 'other'
    raw_info['codec_sel'] = dict_codec[raw_info['codec']]

    # 音频编码
    dict_audiocodec = {
        'DTS X': 14, 'DTS-HD': 12, 'TrueHD': 13, 'LPCM': 11, 'DTS': 3, 'AC-3': 8, 'AAC': 6, 'FLAC': 1, 'APE': 2,
        'WAV': 9, 'other': 7, 'Atmos': 15
    }
    title = raw_info['title']
    if title.upper().find('DTS-HD') >= 0:
        raw_info['audiocodec'] = 'DTS-HD'
    elif title.upper().find('DTS-X') >= 0:
        raw_info['audiocodec'] = 'DTS X'
    elif title.upper().find('DTS') >= 0:
        raw_info['audiocodec'] = 'DTS'
    elif title.upper().find('TRUEHD') >= 0:
        raw_info['audiocodec'] = 'TrueHD'
    elif title.upper().find('LPCM') >= 0:
        raw_info['audiocodec'] = 'LPCM'
    elif title.upper().find('AC-3') >= 0:
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

