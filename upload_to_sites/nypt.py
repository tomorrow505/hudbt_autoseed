# -*- coding: utf-8 -*-
# Author:tomorrow505


from common_info import extend_descr_after, domains, extend_descr_before, recommand_allow
from utils import common_methods
import re


type_dict_for_nypt = {
    "电影": 401, "Movie": 401, "剧集": 402, "电视剧": 402, "欧美剧": 402,
    "日剧": 402, "韩剧": 402, "大陆港台剧": 402, "TV series": 402, "TV Series": 402,
    "TV-Episode": 402, "TV-Pack": 402,
    "综艺": 404, "TV-Show": 404, "音乐": 407, "Music": 407,
    "动漫": 403, "动画": 403, "Anime": 403, "Animation": 403, "剧场": 403,
    "软件": 409,
    "游戏": 410,
    "资料": 408,
    "学习": 408,
    "Sports": 407, "体育": 407,
    "紀錄教育": 406, "Documentary": 406, "纪录": 406,
    "移动视频": 411
}


def get_post_data(raw_info):

    raw_info['nypt_type'] = get_type_nypt(raw_info['type_info'])

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

    if raw_info['descr_rss']:
        raw_info['descr'] = raw_info['descr_rss']
    else:
        if raw_info['douban_info']:
            raw_info['descr'] = raw_info['douban_info'] + raw_info['nfo'] + raw_info['picture_info']

    extend_descr_after_1 = extend_descr_after.format(detail_link=raw_info['detail_link'],
                                                     version=common_methods.VERSION)
    for item in domains[0:2]:
        raw_info['recommand'] = raw_info['recommand'].replace(item, 'https://nanyangpt.com/')
    raw_info['recommand'] = raw_info['recommand'].replace(' ', '%2F')
    descr = extend_descr_before + raw_info['descr'] + raw_info['nfo'] + raw_info['recommand'] + extend_descr_after_1

    data = {
        "cite_site": '',
        "name": raw_info['ename'],
        "small_descr": raw_info["small_descr"],
        "url": raw_info["url"],
        "dburl": raw_info["dburl"],
        "descr": descr,
        "type": str(raw_info['nypt_type']),
        "uplver": raw_info['uplver'],
    }

    if raw_info['nypt_type'] == 401:
        data['movie_enname'] = raw_info['ename']
    elif raw_info['nypt_type'] == 402:
        data['series_enname'] = raw_info['ename']
    elif raw_info['nypt_type'] == 403:
        data['anime_enname'] = raw_info['ename']
    elif raw_info['nypt_type'] == 404:
        data['show_enname'] = raw_info['ename']
    elif raw_info['nypt_type'] == 406:
        data['doc_enname'] = raw_info['ename']

    if raw_info['nypt_type'] not in [401, 402, 403, 404, 406]:
        return ''
    else:
        return data


def add_info_for_nypt():
    pass


def get_type_nypt(info: str or list):
    code = 410
    if isinstance(info, list):
        info = ''.join(info)
    flag = False
    for item in type_dict_for_nypt.keys():
        if info.find(item) >= 0:
            code = type_dict_for_nypt[item]
            flag = True
            break
    if not flag:
        code = 410

    return code


