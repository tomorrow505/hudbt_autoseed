# -*- coding: utf-8 -*-
# Author:Chengli


# 欧美国家字段
Amer_Euro = ['欧洲', '北美', '美国', '法国', '瑞典', '英国', '德国', '意大利', '西班牙', '加拿大', '欧美', '比利时', '荷兰', '澳大利亚',
             '挪威', '丹麦', '芬兰', '爱尔兰', '卢森堡', '奥地利', '瑞士', '新西兰', 'US/EU', '俄罗斯', '俄国', '欧美', '波兰']

# 亚洲国家字段
Asia_Country = ['亚洲', '日本', '韩国', '日韩', '印度', '泰国', 'KR', 'JP', 'KR/韩', 'JP/日', '阿富汗', '伊拉克', '伊朗', '叙利亚', '约旦',
                '黎巴嫩', '以色列', '巴勒斯坦', '沙特阿拉伯', '阿曼', '也门', '格鲁吉亚', '亚美尼亚', '阿塞拜疆', '土耳其', '塞浦路斯',
                '菲律宾', '越南', '老挝', '柬埔寨', '缅甸', '泰国', '马来西亚', '文莱', '新加坡', '印度尼西亚', '东帝汶']

try:
    f = open('./conf/extend_before.txt')
    extend_descr_before = f.read()
    f.close()
except Exception:
    extend_descr_before = ''

try:
    f = open('./conf/recommand_allow.txt')
    recommand_allow = f.read()
    f.close()
except Exception:
    recommand_allow = ''

extend_descr_after = """
[quote=感谢]感谢发布者！！资源来自：{detail_link} [/quote]
"""

domains = [
    'https://hudbt.hust.edu.cn/', 'https://www.tjupt.org/', 'https://nanyangpt.com/', 'https://pt.m-team.cc//',
    'https://springsunday.net/', 'https://ourbits.club/', 'https://hdsky.me/', 'https://hdchina.org/',
    'https://totheglory.im/', 'https://pter.club/'
]
