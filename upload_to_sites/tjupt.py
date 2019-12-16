# -*- coding: utf-8 -*-
# Author:tomorrow505

from common_info import extend_descr_after, domains, recommand_allow, extend_descr_before
import re
import common_methods

type_dict_for_tjupt = {
    "电影": 401, "Movie": 401, "剧集": 402, "电视剧": 402, "欧美剧": 402,
    "日剧": 402, "韩剧": 402, "大陆港台剧": 402, "TV series": 402, "TV Series": 402,
    "TV-Episode": 402, "TV-Pack": 402,
    "综艺": 403, "TV-Show": 403, "音乐": 406, "Music": 406,
    "动漫": 405, "动画": 405, "Anime": 405, "Animation": 405, "剧场": 405,
    "软件": 408,
    "游戏": 409,
    "资料": 404,
    "学习": 404,
    "Sports": 407, "体育": 407,
    "紀錄教育": 411, "Documentary": 411, "纪录": 411,
    "移动视频": 412
}

district = ['大陆', '香港', '台湾', '日本', '韩国', '美国', '英国', '法国', '德国', '澳大利亚']

au = ['格陵兰', '加拿大', '墨西哥', '危地马拉共和国', '伯里兹', '萨尔瓦多共和国', '洪都拉斯共和国', '尼加拉瓜共和国',
      '哥斯达黎加共和国', '巴拿马共和国', '巴哈马国', '特克斯', '凯科斯群岛', '古巴', '开曼群岛', '牙买加',
      '海地共和国', '多米尼加共和国', '波多黎各自由邦', '美属维尔京群岛', '英属维尔京群岛', '圣基茨和尼维斯联邦',
      '安圭拉', '安提瓜', '巴布达', '蒙特塞拉特', '多米尼克国', '马提尼克', '圣卢西亚', '圣文森特',
      '格林纳丁斯', '巴巴多斯', '格林纳达',  '荷属安的列斯', '阿鲁巴']

eu = ['英国', '爱尔兰', '荷兰', '比利时', '卢森堡',  '摩纳哥', '塞尔维亚', '黑山', '克罗地亚', '斯洛文尼亚',
      '波斯尼亚', '黑塞哥维那', '马其顿', '罗马尼亚', '保加利亚', '阿尔巴尼亚', '希腊', '意大利', '梵蒂冈', '圣马力诺',
      '马耳他', '西班牙', '葡萄牙', '安道尔', '波兰', '捷克', '斯洛伐克', '匈牙利', '奥地利', '瑞士',
      '列支敦士登', '冰岛', '丹麦', '挪威', '瑞典', '芬兰', '爱沙尼亚', '拉脱维亚', '立陶宛', '白俄罗斯', '乌克兰',
      '摩尔多瓦', '俄罗斯']


def get_post_data(raw_info):

    raw_info['type_'] = get_type_tjupt(raw_info['type_info'])
    raw_info = add_info_for_tjupt(raw_info)

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

    if name.upper().find('MP4') >= 0 and raw_info['type_'] == 405:
        raw_info['format'] = 'MP4/'
    else:
        raw_info['format'] = raw_info['video_format'].upper()

    raw_info['ename'] = name.strip().replace(' ', '.')

    if name.lower().find('1080p') >= 0:
        raw_info['standard_sel'] = '1080p'
    elif name.lower().find('720p') >= 0:
        raw_info['standard_sel'] = '720p'
    if name.upper().endswith(("PAD", 'IHD')) or name.upper().find('IPAD') >= 0:
        upload_type = 412
    else:
        upload_type = raw_info['type_']

    if raw_info['descr_rss']:
        raw_info['descr'] = raw_info['descr_rss']
    else:
        if raw_info['douban_info']:
            raw_info['descr'] = raw_info['douban_info'] + raw_info['nfo'] + raw_info['picture_info']

    extend_descr_after_1 = extend_descr_after.format(detail_link=raw_info['detail_link'],
                                                     version=common_methods.VERSION)
    if recommand_allow:
        for item in domains[0:1]:
            raw_info['recommand'] = raw_info['recommand'].replace(item, 'https://www.tjupt.org/')
        raw_info['recommand'] = raw_info['recommand'].replace(' ', '%2F')
    else:
        raw_info['recommand'] = ''
    descr = extend_descr_before + raw_info['descr'] + raw_info['nfo'] + raw_info['recommand'] + extend_descr_after_1
    raw_info['ename'] = common_methods.refine_title(raw_info['ename'])
    data = {
        "dl-url": "",
        "ename": raw_info['ename'],
        "cname": raw_info['cname'],
        "small_descr": raw_info["small_descr"],
        "url": raw_info["url"],
        "descr": descr,
        "type": str(upload_type),
        "language": raw_info['language'],
        "district": get_distric_by_region(raw_info['region']),
        "specificcat": raw_info['tjupt_specificcat'],
        "subinfo": str(6),
        "hqname": "Unknown",
        "artist": "Unknown",
        "resilution": raw_info['standard_sel'],
        "platform": "PC",
        "format": raw_info['format'],
        "uplver": raw_info['uplver'],
    }

    return data


def get_type_tjupt(info):
    code = 410
    if isinstance(info, list):
        info = ''.join(info)
    for item in type_dict_for_tjupt.keys():
        if info.find(item) >= 0:
            code = type_dict_for_tjupt[item]
            break
    return code


def add_info_for_tjupt(raw_info):

    raw_info['tjupt_specificcat'] = '其他'

    if raw_info['type_'] == 401:
        for item in raw_info['region'].split('/'):
            if item.find('大陆') >= 0 or raw_info['region'].find('中国') >= 0:
                raw_info['region'] = '大陆'
                break
            elif item.strip() in ['香港', '台湾', '日本', '韩国', '美国', '英国', '法国', '德国', '澳大利亚', '欧洲', '北美']:
                raw_info['region'] = item
                break
        if not raw_info['region']:
            raw_info['region'] = '其他'

    if raw_info['type_'] == 402:
        if raw_info['region'].find('大陆') >= 0 or raw_info['region'].find('中国') >= 0:
            raw_info['tjupt_specificcat'] = '大陆'
        elif raw_info['region'].find('香港') >= 0 or raw_info['region'].find('台湾') >= 0:
            raw_info['tjupt_specificcat'] = '港台'
        elif raw_info['region'].find('美国') >= 0:
            raw_info['tjupt_specificcat'] = '美剧'
        elif raw_info['region'].find('英国') >= 0:
            raw_info['tjupt_specificcat'] = '英剧'
        elif raw_info['region'].find('日本') >= 0:
            raw_info['tjupt_specificcat'] = '日剧'
        elif raw_info['region'].find('韩国') >= 0:
            raw_info['tjupt_specificcat'] = '韩剧'
        else:
            raw_info['tjupt_specificcat'] = '其他'

    if raw_info['type_'] == 405:
        if raw_info['full_title'].find('连载') >= 0:
            raw_info['tjupt_specificcat'] = '连载'
        elif raw_info['full_title'].find('OVA') >= 0:
            raw_info['tjupt_specificcat'] = 'OVA'
        elif raw_info['full_title'].find('[TV]') >= 0:
            raw_info['tjupt_specificcat'] = 'TV'
        elif raw_info['full_title'].find('剧场') >= 0:
            raw_info['tjupt_specificcat'] = '剧场'
        else:
            raw_info['tjupt_specificcat'] = '其他'
        if raw_info['region'].find('日本') >= 0:
            raw_info['region'] = '日漫'
        elif raw_info['region'].find('美国') >= 0:
            raw_info['region'] = '美漫'
        elif raw_info['region'].find('大陆') >= 0 or raw_info['region'].find('中国') >= 0:
            raw_info['region'] = '国产'
        else:
            raw_info['region'] = '其他'

    if raw_info['type_'] in [406, 407, 411]:
        raw_info['tjupt_specificcat'] = '其他/'

    if raw_info['type_'] in [407, 409]:
        raw_info['tjupt_cname'] = 'Unknown'
    if raw_info['type_'] == 409:
        raw_info['format'] = '其他/'

    if raw_info['type_'] == 410:
        raw_info['tjupt_specificcat'] = '其他资源'

    return raw_info


def get_distric_by_region(region):
    for item in district:
        if region.find(item) >= 0:
            district_ = item
            return district_

    for dd in au:
        if region.find(dd) >= 0:
            district_ = '北美'
            return district_

    for tt in eu:
        if region.find(tt) >= 0:
            district_ = '欧洲'
            return district_

    return '其他'
