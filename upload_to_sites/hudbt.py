# -*- coding: utf-8 -*-
# Author:Chengli


from common_info import Asia_Country, Amer_Euro, extend_descr_after
from utils import common_methods
import re

type_dict_hudbt = {
    "电影": [(['华语', '大陆', '中国', '国产'], 401), (Amer_Euro, 415),
           (Asia_Country, 414), (['香港', '台湾'], 413)],
    "Movie": [(['大陆', 'CN', '台湾'], 401), (Amer_Euro, 415),
              (Asia_Country, 414),
              (['港台', 'HK/TW', '香港', '台湾'], 413)],
    "剧集": [(['大陆'], 402), (['美剧', '英剧'] + Amer_Euro, 418),
           (['日韩', '日剧', '韩剧', '日本', '韩国'], 416), (['港台', '香港', '台湾'], 417)],
    "Drama": [(['韩剧', '日剧'], 416)],
    "电视剧": [(['大陆', '中国'], 402), (Amer_Euro, 418), (['亚洲', '日本', '韩国', '韩剧', '日剧'], 416), (['港台', '香港', '台湾'], 417)],
    "欧美剧": [(['欧美剧'], 418)],
    "日剧": [(['高清日剧', '日剧包'], 416)],
    "韩剧": [(['高清韩剧', '韩剧包'], 416)],
    "大陆港台剧": [(['大陆港台剧'], 402)],
    "TV series": [(['大陆', 'CN'], 402), (Amer_Euro, 418),
                  (['Kor Drama', 'KR', 'JP', 'Jpn Drama'], 416), (['香港', '台湾', 'HK/TW'], 417)],
    "TV Series": [(['大陆', 'CN'], 402), (Amer_Euro, 418),
                  (['Kor Drama', 'KR', 'JP', 'Jpn Drama'], 416), (['香港', '台湾', 'HK/TW'], 417)],
    "TV-Episode": [(['大陆', 'CN'], 402), (['欧美'], 418), (['KR/韩', 'JP/日', 'KR', 'JP'], 416), (['港台'], 417)],
    "TV-Pack": [(['大陆', 'CN'], 402), (['欧美'], 418), (['KR/韩', 'JP/日', 'KR', 'JP'], 416), (['港台'], 417)],
    "综艺": [(['大陆', '中国'], 403), (['欧美'] + Amer_Euro, 421), (['日韩', '日本', '韩国'], 420), (['港台','香港', '台湾'], 419)],
    "TV-Show": [(['大陆'], 403), (['欧美'], 421), (['KR/韩', 'JP/日'], 420), (['港台'], 419)],
    "音乐": [(['大陆', '港台', '华语'], 408), (['欧美'], 423), (['日韩'], 422),  (['古典'], 424), (['原声'], 425)],
    "Music": [(['CN', 'HK/TW', '华语'], 408), (['US/EU', '欧美'], 423), (['KR', 'JP', '日韩'], 422),
              (['古典'], 424), (['原声'], 425)],
    "MV": [(['CN', 'HK/TW', '华语'], 408), (['US/EU', '欧美'], 423), (['KR', 'JP', '日韩'], 422),
           (['古典'], 424), (['原声'], 425)],
    "动漫": [(['周边'], 429), (['动漫'], 427)],
    "动画": [(['动画'], 427)],
    "剧场": [(['剧场'], 428)],
    "Anime": [(['Anime'], 427)],
    "Animation": [(['Animation'], 427)],
    "软件": [(['软件'], 411)],
    "游戏": [(['游戏'], 410)],
    "资料": [(['资料'], 412)],
    "学习": [(['学习'], 412)],
    "Sports": [(['Sports'], 407)],
    "体育": [(['体育'], 407)],
    "紀錄教育": [(['紀錄教育'], 404)],
    "Documentary": [(['Documentary'], 404)],
    "纪录": [(['纪录'], 404)],
    "移动视频": [(['移动视频'], 430)]
}


def get_post_data(raw_info):
    extend_descr_before = """
[quote][*]这是一个自动发布的种子，转自{site}。一切信息以种子源站点为准，有误或误转请举报。另：如有违规请管理员自主删除。
[*]部分种子长期保种，其余保种约[color=red][20-30][/color]天，断种恕不补种。[/quote]
"""

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

    if name.lower().find('1080p') >= 0:
        raw_info['standard_sel'] = 1
    elif name.lower().find('720p') >= 0:
        raw_info['standard_sel'] = 3

    if raw_info['origin_site'] == 'U2':
        if raw_info['full_title'].upper().find('FIN') >= 0:
            raw_info['type_'] = 405
        elif raw_info['full_title'].upper().find('MOVIE') >= 0:
            raw_info['type_'] = 428
        elif raw_info['full_title'].upper().find('OVA') >= 0:
            raw_info['type_'] = 428
        else:
            raw_info['type_'] = 427
        if raw_info['type_info'].find('类型: Lossless Music') >= 0:
            raw_info['type_'] = 429
    elif raw_info['origin_site'] == 'byr' and raw_info['big_type'] == '动漫':
        sub_titles = re.findall('\[(.*?)\]', raw_info['full_title'])
        try:

            if raw_info['small_descr'].find(sub_titles[3]) < 0:
                raw_info['small_descr'] = sub_titles[3] + raw_info['small_descr']
                # print(raw_info['small_descr'])
            if sub_titles[1] in ['连载', '长篇']:
                raw_info['type_'] = 427
            elif sub_titles[1] in ['剧场']:
                raw_info['type_'] = 428
            elif sub_titles[1] in ['TV'] or raw_info['full_title'].find('Fin') >= 0:
                raw_info['type_'] = 405
            else:
                raw_info['type_'] = 429
        except Exception:
            raw_info['type_'] = ''

    if not raw_info['type_']:
        raw_info['type_'] = get_type_from_type_info(raw_info['type_info'])

    if name.upper().endswith(("PAD", 'IHD')) or name.upper().find('IPAD') >= 0:
        upload_type = 430
    else:
        upload_type = raw_info['type_']

    if raw_info['descr_rss']:
        raw_info['descr'] = raw_info['descr_rss']
    else:
        if raw_info['douban_info']:
            raw_info['descr'] = raw_info['douban_info'] + raw_info['nfo'] + raw_info['picture_info']

    extend_descr_before_1 = extend_descr_before.format(site=raw_info['origin_site'])
    extend_descr_after_1 = extend_descr_after.format(detail_link=raw_info['detail_link'],
                                                     version=common_methods.VERSION)

    descr = extend_descr_before_1 + raw_info['descr'] + raw_info['nfo'] + raw_info['recommand'] + extend_descr_after_1
    name = common_methods.refine_title(name)
    data = {
        "dl-url": "",
        "name": name.strip(),
        "small_descr": raw_info["small_descr"],
        "url": raw_info["url"],
        "descr": descr,
        "type": str(upload_type),
        "data[Tcategory][Tcategory][]": "",
        "standard_sel": str(raw_info["standard_sel"]),
        "uplver": raw_info['uplver'],
    }

    return data


def get_type_from_type_info(type_info):
    code = 409
    if isinstance(type_info, list):
        type_info = ''.join(type_info)
    flag = False
    for item in type_dict_hudbt.keys():
        if flag:
            break
        if type_info.find(item) >= 0:
            sub_type_info = type_dict_hudbt[item]
            for sub_item in sub_type_info:
                if flag:
                    break
                for sub_item2 in sub_item[0]:
                    if type_info.find(sub_item2) >= 0:
                        code = sub_item[1]
                        flag = True
                        break
    return code

