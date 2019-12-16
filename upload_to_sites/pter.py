# -*- coding: utf-8 -*-
# Author:Chengli


import re
from common_info import extend_descr_after, Amer_Euro, recommand_allow
import common_methods

# dict_standard = {
#     '1080p': 1, '1080i': 2, '720p': 3, 'SD': 4, '4K': 5
# }


def get_post_data(raw_info):

    raw_info = get_info_from_raw_info(raw_info)
    extend_descr_after_1 = extend_descr_after.format(detail_link=raw_info['detail_link'],
                                                     version=common_methods.VERSION)
    descr = raw_info['descr'] + raw_info['nfo'] + extend_descr_after_1

    raw_info['ename'] = common_methods.refine_title(raw_info['ename'])

    descr = descr.replace('img3.doubanio.com', 'img1.doubanio.com')
    descr = descr.replace('https://img1.doubanio.com', 'http://img1.doubanio.com')

    data = {
        "name": raw_info['ename'],
        "small_descr": raw_info["small_descr"],
        "url": raw_info["url"],
        "douban": raw_info["dburl"],
        "descr": descr,
        "type": str(raw_info['type_']),
        "source_sel": str(raw_info['source_sel']),
        "team_sel": str(raw_info['team_sel']),
        "uplver": raw_info['uplver'],
    }

    try:
        if '国语' in raw_info['video_info']['language']:
            data['guoyu'] = 'yes'
        if '粤语' in raw_info['video_info']['language']:
            data['yueyu'] = 'yes'
        if '中字' in raw_info['video_info']['subtitle']:
            data['zhongzi'] = 'yes'
    except Exception:
        pass

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

    raw_info['ename'] = name.strip()

    if not raw_info['media_type']:
        raw_info['media_type'] = 'Encode'

    raw_info['type_'] = 412
    if big_type == '电影':
        raw_info['type_'] = 401
    elif big_type in ['综艺']:
        raw_info['type_'] = 405
    elif big_type in ['剧集']:
        raw_info['type_'] = 404
    elif big_type in ['纪录']:
        raw_info['type_'] = 402
    elif big_type in ['学习', '资料']:
        raw_info['type_'] = 411
    elif big_type in ['体育']:
        raw_info['type_'] = 407
    elif big_type in ['软件']:
        raw_info['type_'] = 410
    elif big_type in ['动漫']:
        raw_info['type_'] = 403

    raw_info['team_sel'] = ''

    CN = ['华语', '大陆', '中国', '国产']
    HK = ['香港']
    TW = ['台湾']
    JP = ['日本']
    KR = ['韩国']
    HI = ['印度']

    processing_sel = {
        1: CN, 4: Amer_Euro, 2: HK, 3: TW, 6: JP, 5: KR, 7: HI
    }

    flag = False
    raw_info['team_sel'] = 8
    for item in processing_sel.keys():
        if flag:
            break
        country_list = processing_sel[item]
        for country in country_list:
            if type_info.find(country) >= 0:
                flag = True
                raw_info['team_sel'] = item
                break

    raw_info['source_sel'] = 15
    if raw_info['title'].upper().find('FLAC') >= 0:
        raw_info['source_sel'] = 8
    if raw_info['title'].upper().find('WAV') >= 0:
        raw_info['source_sel'] = 9
    if raw_info['title'].upper().find('ISO') >= 0:
        raw_info['source_sel'] = 10
    if raw_info['title'].upper().find('PDF') >= 0:
        raw_info['source_sel'] = 11
    if raw_info['title'].upper().find('PUB') >= 0:
        raw_info['source_sel'] = 12
    if raw_info['title'].upper().find('AZW') >= 0:
        raw_info['source_sel'] = 13
    if raw_info['title'].upper().find('MOBI') >= 0:
        raw_info['source_sel'] = 14
    if raw_info['media_type'] == 'Blu-ray':
        raw_info['source_sel'] = 2
    elif raw_info['media_type'] == 'Remux':
        raw_info['source_sel'] = 3
    elif raw_info['media_type'] == 'Encode':
        raw_info['source_sel'] = 6
    elif raw_info['media_type'] == 'DVD':
        raw_info['source_sel'] = 7
    if raw_info['title'].upper().find('HDTV') >= 0:
        raw_info['source_sel'] = 4
    if raw_info['title'].upper().find('WEB-DL') >= 0:
        raw_info['source_sel'] = 5
    if raw_info['title'].upper().find('4K') >= 0 or raw_info['title'].upper().find('2160P') >= 0:
        raw_info['source_sel'] = 1
    return raw_info

