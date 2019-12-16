# -*- coding: utf-8 -*-
# Author:tomorrow505


import re
from common_info import extend_descr_after, Amer_Euro, domains, extend_descr_before, recommand_allow
import common_methods

dict_standard = {
    '1080p': 1, '1080i': 2, '720p': 3, 'SD': 4, '4K': 5
}


def get_post_data(raw_info):

    raw_info = get_info_from_raw_info(raw_info)
    extend_descr_after_1 = extend_descr_after.format(detail_link=raw_info['detail_link'],
                                                     version=common_methods.VERSION)
    if recommand_allow:
        for item in domains[0:3]:
            raw_info['recommand'] = raw_info['recommand'].replace(item, 'https://pt.m-team.cc//')
        raw_info['recommand'] = raw_info['recommand'].replace(' ', '%2F')
    else:
        raw_info['recommand'] = ''
    descr = extend_descr_before + raw_info['descr'] + raw_info['nfo'] + raw_info['recommand'] + extend_descr_after_1
    raw_info['ename'] = common_methods.refine_title(raw_info['ename'])
    data = {
        "name": raw_info['ename'],
        "small_descr": raw_info["small_descr"],
        "url": raw_info["url"],
        "descr": descr,
        "type": str(raw_info['type_']),
        "standard_sel": dict_standard[raw_info['standard']],
        "processing_sel": raw_info['processing_sel'],
        "team_sel": raw_info['team_sel'],
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

    raw_info['ename'] = name.strip()

    if not raw_info['standard']:
        if name.lower().find('1080p') >= 0:
            raw_info['standard'] = '1080p'
        elif name.lower().find('720p') >= 0:
            raw_info['standard'] = '720p'
        elif name.lower().find('2160p') >= 0 or name.lower().find('4k') >= 0:
            raw_info['standard'] = '4K'
        else:
            raw_info['standard'] = '720p'

    if not raw_info['media_type']:
        raw_info['media_type'] = 'Encode'

    raw_info['type_'] = 419
    if big_type == '电影':
        if raw_info['media_type'] == 'Blu-ray':
            raw_info['type_'] = 421
        elif raw_info['media_type'] == 'Encode':
            raw_info['type_'] = 419
        elif raw_info['media_type'] == 'Remux':
            raw_info['type_'] = 439
        elif raw_info['media_type'] == 'DVD':
            raw_info['type_'] = 420
        elif raw_info['media_type'] == 'SD':
            raw_info['type_'] = 401
    elif big_type in ['剧集', '综艺']:
        if raw_info['media_type'] == 'Blu-ray':
            raw_info['type_'] = 438
        elif raw_info['media_type'] == 'Encode':
            raw_info['type_'] = 402
        elif raw_info['media_type'] == 'DVD':
            raw_info['type_'] = 435
        elif raw_info['media_type'] == 'SD':
            raw_info['type_'] = 403
    elif big_type in ['纪录', '学习', '资料']:
        raw_info['type_'] = 404
    elif big_type in ['体育']:
        raw_info['type_'] = 407
    elif big_type in ['软件']:
        raw_info['type_'] = 422
    elif big_type in ['动漫']:
        raw_info['type_'] = 405
    else:
        raw_info['type_'] = 419

    raw_info['team_sel'] = ''

    CN = ['华语', '大陆', '中国', '国产']
    HKTW = ['香港', '台湾']
    JP = '日本'
    KR = '韩国'

    processing_sel = {
        1: CN, 2: Amer_Euro, 3: HKTW, 4: JP, 5: KR
    }

    flag = False
    raw_info['processing_sel'] = 6
    for item in processing_sel.keys():
        if flag:
            break
        country_list = processing_sel[item]
        for country in country_list:
            if type_info.find(country) >= 0:
                flag = True
                raw_info['processing_sel'] = item
                break

    dict_codec = {
        'H264': 1, 'VC-1': 2, 'MPEG-2': 4, 'MPEG-4': 15, 'H265': 16, 'other': 0
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

    # print(raw_info['codec_sel'])

    return raw_info

