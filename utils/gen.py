# -*- coding: utf-8 -*-
# Author:tomorrow505


import re
import json
import requests
import random
from bs4 import BeautifulSoup
from html2bbcode.parser import HTML2BBCode


douban_format = [
    # (key name in dict. the format of key, string format) with order
    ("poster", "[img]{}[/img]\n\n"),
    ("trans_title", "◎译　　名　{}\n"),
    ("this_title", "◎片　　名　{}\n"),
    ("year", "◎年　　代　{}\n"),
    ("region", "◎产　　地　{}\n"),
    ("genre", "◎类　　别　{}\n"),
    ("language", "◎语　　言　{}\n"),
    ("playdate", "◎上映日期　{}\n"),
    ("imdb_rating", "◎IMDb评分  {}\n"),
    ("imdb_link", "◎IMDb链接  {}\n"),
    ("douban_rating", "◎豆瓣评分　{}\n"),
    ("douban_link", "◎豆瓣链接　{}\n"),
    ("episodes", "◎集　　数　{}\n"),
    ("duration", "◎片　　长　{}\n"),
    ("director", "◎导　　演　{}\n"),
    ("writer", "◎编　　剧　{}\n"),
    ("cast", "◎主　　演　{}\n\n"),
    ("tags", "\n◎标　　签　{}\n"),
    ("introduction", "\n◎简　　介  \n\n　　{}\n"),
    ("awards", "\n◎获奖情况  \n\n{}\n"),
]

imdb_format = [
    ('poster', '[img]{}[/img]\n\n'),
    ('name', 'Title: {}\n'),
    ('keywords', 'Keywords: {}\n'),
    ('datePublished', 'Date Published: {}\n'),
    ('imdb_rating', 'IMDb Rating: {}\n'),
    ('imdb_link', 'IMDb Link: {}\n'),
    ('directors', 'Directors: {}\n'),
    ('creators', 'Creators: {}\n'),
    ('actors', 'Actors: {}\n'),
    ('description', '\nIntroduction\n    {}\n')
]


support_list = [
    ("douban", re.compile("(https?://)?((movie|www)\.)?douban\.com/(subject|movie)/(?P<sid>\d+)/?")),
    ("imdb", re.compile("(https?://)?www\.imdb\.com/title/(?P<sid>tt\d+)")),
]

support_site_list = list(map(lambda x: x[0], support_list))

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/61.0.3163.100 Safari/537.36 ',
    'Cookie': '',
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8"
}


def get_page(url: str, json_=False, jsonp_=False, bs_=False, text_=False, **kwargs):
    kwargs.setdefault("headers", headers)
    page = requests.get(url, **kwargs)
    page.encoding = "utf-8"
    page_text = page.text
    if json_:
        return page.json()
    elif jsonp_:
        start_idx = page_text.find('(')
        end_idx = page_text.rfind(')')
        return json.loads(page_text[start_idx + 1:end_idx])
    elif bs_:
        return BeautifulSoup(page.text, "lxml")
    elif text_:
        return page_text
    else:
        return page


def html2ubb(html: str) -> str:
    return str(HTML2BBCode().feed(html))


def get_num_from_string(raw):
    return int(re.search('[\d,]+', raw).group(0).replace(',', ''))


class Gen(object):
    site = sid = url = ret = None
    img_list = []  # 临时存储图片信息

    def __init__(self, url: str or dict):
        self.clear()
        self.pat(url)

    def pat(self, url: str or dict):
        if isinstance(url, dict):
            self.site = url.get('site', '')
            self.sid = url.get('sid', '')

        else:
            for site, pat in support_list:
                search = pat.search(url)
                if search:
                    self.sid = search.group("sid")
                    self.site = site
                    # print(self.site, self.sid)
                    return
        if not self.site or self.site not in support_site_list:
            self.ret["error"] = "No support link."

    def clear(self):
        self.site = self.sid = self.url = None
        self.img_list = []  # 临时存储图片信息
        self.ret = {
            "success": False,
            "error": None,
            "format": "",
        }

    def gen(self, _debug=False):
        if not self.ret.get("error"):
            try:
                getattr(self, "_gen_{}".format(self.site))()
                self.ret["img"] = self.img_list
                self.ret["success"] = True if not self.ret.get("error") else False
            except Exception as err:
                raw_error = self.ret["error"]
                self.ret["error"] = "Internal error"
                if _debug:
                    raise Exception("Internal error").with_traceback(err.__traceback__)
        return self.ret

    def _gen_douban(self):
        api_keys = ["0dad551ec0f84ed02907ff5c42e8ec70", "02646d3fb69a52ff072d47bf23cef8fd",
                    "07c78782db00a121175696889101e363"]
        # 处理source为douban，但是sid是tt开头的imdb信息 （这种情况只有使用 {'site':'douban','sid':'tt1234567'} 才可能存在）
        if isinstance(self.sid, str) and self.sid.startswith('tt'):
            # 根据tt号先在豆瓣搜索，如果有则直接使用豆瓣解析结果

            api_key = random.choice(api_keys)
            douban_imdb_api = get_page("https://api.douban.com/v2/movie/imdb/{id}?"
                                       "&apikey={apikey}".format(id=self.sid, apikey=api_key), json_=True)
            if douban_imdb_api.get("alt"):
                self.pat(douban_imdb_api["alt"])
            else:  # 该imdb号在豆瓣上不存在
                self.ret["error"] = "Can't find this imdb_id({}) in Douban.".format(self.sid)
                # print("Can't find this imdb_id")
                return

        douban_link = "https://movie.douban.com/subject/{}/".format(self.sid)
        douban_page = get_page(douban_link, bs_=True)
        douban_api_json = get_page('https://api.douban.com/v2/movie/{}?'
                                   '&apikey=02646d3fb69a52ff072d47bf23cef8fd'.format(self.sid), json_=True)

        if "msg" in douban_api_json:
            self.ret["error"] = douban_api_json["msg"]
        elif str(douban_page).find("检测到有异常请求") > -1:
            self.ret["error"] = "GenHelp was banned by Douban."
        elif douban_page.title.text == "页面不存在":
            self.ret["error"] = "The corresponding resource does not exist."
        else:
            data = {"douban_link": douban_link}

            def fetch(node):
                return node.next_element.next_element.strip()

            # 对主页面进行解析
            data["chinese_title"] = (douban_page.title.text.replace("(豆瓣)", "").strip())
            data["foreign_title"] = (douban_page.find("span", property="v:itemreviewed").text
                                     .replace(data["chinese_title"], '').strip())

            aka_anchor = douban_page.find("span", class_="pl", text=re.compile("又名"))
            data["aka"] = sorted(fetch(aka_anchor).split(' / ')) if aka_anchor else []

            if data["foreign_title"]:
                trans_title = data["chinese_title"] + (('/' + "/".join(data["aka"])) if data["aka"] else "")
                this_title = data["foreign_title"]
            else:
                trans_title = "/".join(data["aka"]) if data["aka"] else ""
                this_title = data["chinese_title"]

            data["trans_title"] = trans_title.split("/")
            data["this_title"] = this_title.split("/")

            region_anchor = douban_page.find("span", class_="pl", text=re.compile("制片国家/地区"))
            language_anchor = douban_page.find("span", class_="pl", text=re.compile("语言"))
            episodes_anchor = douban_page.find("span", class_="pl", text=re.compile("集数"))
            imdb_link_anchor = douban_page.find("a", text=re.compile("tt\d+"))
            year_anchor = douban_page.find("span", class_="year")

            data["year"] = douban_page.find("span", class_="year").text[1:-1] if year_anchor else ""  # 年代
            data["region"] = fetch(region_anchor).split(" / ") if region_anchor else []  # 产地
            data["genre"] = list(map(lambda l: l.text.strip(), douban_page.find_all("span", property="v:genre")))  # 类别
            data["language"] = fetch(language_anchor).split(" / ") if language_anchor else []  # 语言
            data["playdate"] = sorted(map(lambda l: l.text.strip(),  # 上映日期
                                          douban_page.find_all("span", property="v:initialReleaseDate")))
            data["imdb_link"] = imdb_link_anchor.attrs["href"] if imdb_link_anchor else ""  # IMDb链接
            data["imdb_id"] = imdb_link_anchor.text if imdb_link_anchor else ""  # IMDb号
            data["episodes"] = fetch(episodes_anchor) if episodes_anchor else ""  # 集数

            duration_anchor = douban_page.find("span", class_="pl", text=re.compile("单集片长"))
            runtime_anchor = douban_page.find("span", property="v:runtime")

            duration = ""  # 片长
            if duration_anchor:
                duration = fetch(duration_anchor)
            elif runtime_anchor:
                duration = runtime_anchor.text.strip()
            data["duration"] = duration

            # 请求其他资源
            if data["imdb_link"]:  # 该影片在豆瓣上存在IMDb链接
                imdb_source = ("https://p.media-imdb.com/static-content/documents/v1/title/{}/ratings%3Fjsonp="
                               "imdb.rating.run:imdb.api.title.ratings/data.json".format(data["imdb_id"]))
                try:
                    imdb_json = get_page(imdb_source, jsonp_=True)  # 通过IMDb的API获取信息，（经常超时555555）
                    imdb_average_rating = imdb_json["resource"]["rating"]
                    imdb_votes = imdb_json["resource"]["ratingCount"]
                    if imdb_average_rating and imdb_votes:
                        data["imdb_rating"] = "{}/10 from {} users".format(imdb_average_rating, imdb_votes)
                except Exception as err:
                    pass

            # 获取获奖情况
            awards = ""
            awards_page = get_page("https://movie.douban.com/subject/{}/awards".format(self.sid), bs_=True)
            for awards_tag in awards_page.find_all("div", class_="awards"):
                _temp_awards = ""
                _temp_awards += "　　" + awards_tag.find("h2").get_text(strip=True) + "\n"
                for specific in awards_tag.find_all("ul"):
                    _temp_awards += "　　" + specific.get_text(" ", strip=True) + "\n"

                awards += _temp_awards + "\n"

            data["awards"] = awards

            # 豆瓣评分，简介，海报，导演，编剧，演员，标签
            data["douban_rating_average"] = douban_average_rating = douban_api_json["rating"]["average"] or 0
            data["douban_votes"] = douban_votes = douban_api_json["rating"]["numRaters"] or 0
            data["douban_rating"] = "{}/10 from {} users".format(douban_average_rating, douban_votes)
            data["introduction"] = re.sub("^None$", "暂无相关剧情介绍", douban_api_json["summary"])
            data["poster"] = poster = re.sub("s(_ratio_poster|pic)", r"l\1", douban_api_json["image"])
            self.img_list.append(poster)

            data["director"] = douban_api_json["attrs"]["director"] if "director" in douban_api_json["attrs"] else []
            data["writer"] = douban_api_json["attrs"]["writer"] if "writer" in douban_api_json["attrs"] else []
            data["cast"] = douban_api_json["attrs"]["cast"] if "cast" in douban_api_json["attrs"] else ""
            data["tags"] = list(map(lambda member: member["name"], douban_api_json["tags"]))

            # -*- 组合数据 -*-
            descr = ""
            for key, ft in douban_format:
                _data = data.get(key)
                if _data:
                    if isinstance(_data, list):
                        join_fix = " / "
                        if key == "cast":
                            join_fix = "\n　　　　　　"
                        elif key == "tags":
                            join_fix = " | "
                        _data = join_fix.join(_data)
                    descr += ft.format(_data)
            self.ret["format"] = descr

            # 将清洗的数据一并发出
            self.ret.update(data)

    def _gen_imdb(self):
        # 处理imdb_id格式，self.sid 可能为 tt\d{7,8} 或者 \d{0,8}，
        # 存库的应该是 tt\d{0,8} 而用户输入两种都有可能，但向imdb请求的应统一为 tt\d{7,8}
        self.sid = str(self.sid)
        if self.sid.startswith('tt'):
            self.sid = self.sid[2:]

        # 不足7位补齐到7位，如果是7、8位则直接使用
        imdb_id = 'tt{}'.format(self.sid if len(self.sid) >= 7 else self.sid.rjust(7, '0'))

        # 请求对应页面
        imdb_url = "https://www.imdb.com/title/{}/".format(imdb_id)
        imdb_page = get_page(imdb_url, bs_=True)
        if imdb_page.title.text == '404 Error - IMDb':
            self.ret["error"] = "The corresponding resource does not exist."
        else:
            data = {}
            # 首先解析页面中的json信息，并从中获取数据  `<script type="application/ld+json">...</script>`
            page_json_another = imdb_page.find('script', type='application/ld+json')
            page_json = json.loads(page_json_another.text)

            data['imdb_id'] = imdb_id
            data['imdb_link'] = imdb_url

            # 处理可以直接从page_json中复制过来的信息
            for v in ['@type', 'name', 'genre', 'contentRating', "datePublished", 'description', 'duration']:
                data[v] = page_json.get(v)

            data['poster'] = page_json.get('image')
            if page_json.get('image'):
                self.img_list.append(page_json.get('image'))

            if data.get('datePublished'):
                data["year"] = data.get('datePublished')[0:4]

            def filter_person(d):
                return d['@type'] == 'Person'

            def del_type_def(d):
                del d['@type']
                return d

            for p in ['actor', 'director', 'creator']:
                raw = page_json.get(p)
                if raw:
                    if isinstance(raw, dict):
                        raw = [raw]
                    data[p + 's'] = list(map(del_type_def, filter(filter_person, raw)))

            data['keywords'] = page_json.get("keywords", '').split(',')
            aggregate_rating = page_json.get("aggregateRating", {})
            data['imdb_votes'] = aggregate_rating.get("ratingCount", 0)
            data['imdb_rating_average'] = aggregate_rating.get("ratingValue", 0)
            data['imdb_rating'] = '{}/10 from {} users'.format(data['imdb_rating_average'], data['imdb_votes'])

            # 解析页面元素
            # 第一部分： Metascore，Reviews，Popularity
            mrp_bar = imdb_page.select('div.titleReviewBar > div.titleReviewBarItem')
            for bar in mrp_bar:
                if bar.text.find('Metascore') > -1:
                    metascore_another = bar.find('div', class_='metacriticScore')
                    data['metascore'] = metascore_another.get_text(strip=True) if metascore_another else None
                elif bar.text.find('Reviews') > -1:
                    reviews_another = bar.find('a', href=re.compile(r'^reviews'))
                    critic_another = bar.find('a', href=re.compile(r'^externalreviews'))
                    data['reviews'] = get_num_from_string(reviews_another.get_text()) if reviews_another else 0
                    data['critic'] = get_num_from_string(critic_another.get_text()) if critic_another else 0
                elif bar.text.find('Popularity') > -1:
                    data['popularity'] = get_num_from_string(bar.text)

            # 第二部分： Details
            details_another = imdb_page.find('div', id='titleDetails')
            title_anothers = details_another.find_all('div', class_='txt-block')

            def get_title(raw):
                title_raw = raw.get_text(' ', strip=True).replace('See more »', '').strip()
                title_split = title_raw.split(': ', 1)
                return {title_split[0]: title_split[1]} if len(title_split) > 1 else None

            details_dict = {}
            details_list_raw = list(filter(lambda x: x is not None, map(get_title, title_anothers)))
            for d in details_list_raw:
                for k,v in d.items():
                    details_dict[k] = v

            data['details'] = details_dict

            # 请求附属信息
            # 第一部分： releaseinfo
            imdb_releaseinfo_page = get_page('https://www.imdb.com/title/{}/releaseinfo'.format(imdb_id), bs_=True)

            release_date_items = imdb_releaseinfo_page.find_all('tr', class_='release-date-item')
            release_date = []
            for item in release_date_items:
                country = item.find('td', class_='release-date-item__country-name')
                date = item.find('td', class_='release-date-item__date')
                if country and date:
                    release_date.append({'country': country.get_text(strip=True), 'date': date.get_text(strip=True)})
            data['release_date'] = release_date

            aka_items = imdb_releaseinfo_page.find_all('tr', class_='aka-item')
            aka = []
            for item in aka_items:
                country = item.find('td', class_='aka-item__name')
                name = item.find('td', class_='aka-item__title')
                if country and name:
                    aka.append({'country': country.get_text(strip=True), 'title': name.get_text(strip=True)})
            data['aka'] = aka

            # TODO full cast to replace infoformation from page_json

            # -*- 组合数据 -*-
            descr = ""
            for key, ft in imdb_format:
                _data = data.get(key)
                if _data:
                    if key in ['directors', 'creators', 'actors']:
                        _data = list(map(lambda x: x.get('name'), _data))
                    if isinstance(_data, list):
                        join_fix = " / "
                        if key == "keywords":
                            join_fix = ", "
                        _data = join_fix.join(_data)

                    descr += ft.format(_data)
            self.ret["format"] = descr

            # 将清洗的数据一并发出
            self.ret.update(data)

    def _gen_steam(self):
        steam_chs_url = "https://store.steampowered.com/app/{}/?l=schinese".format(self.sid)
        steam_page = requests.get(steam_chs_url,
                                  # 使用cookies避免 Steam 年龄认证
                                  cookies={"mature_content": "1", "birthtime": "157737601",
                                           "lastagecheckage": "1-January-1975", "wants_mature_content": "1"})
        if re.search("(欢迎来到|Welcome to) Steam", steam_page.text):  # 不存在的资源会被302到首页，故检查标题或r.history
            self.ret["error"] = "The corresponding resource does not exist."
        else:
            data = {'steam_id': self.sid, 'steam_link': steam_chs_url}
            steam_bs = BeautifulSoup(steam_page.text, "lxml")
            # 从网页中定位数据
            name_anchor = steam_bs.find("div", class_="apphub_AppName") or steam_bs.find("span", itemprop="name")  # 游戏名
            cover_anchor = steam_bs.find("img", class_="game_header_image_full")  # 游戏封面图
            detail_anchor = steam_bs.find("div", class_="details_block")  # 游戏基本信息
            linkbar_anchor = steam_bs.find("a", class_="linkbar")  # 官网
            language_anchor = steam_bs.select("table.game_language_options > tr")[1:]  # 已支持语言
            tag_anchor = steam_bs.find_all("a", class_="app_tag")  # 标签
            rate_anchor = steam_bs.find_all("div", class_="user_reviews_summary_row")  # 游戏评价
            descr_anchor = steam_bs.find("div", id="game_area_description")  # 游戏简介
            sysreq_anchor = steam_bs.select("div.sysreq_contents > div.game_area_sys_req")  # 系统需求
            screenshot_anchor = steam_bs.select("div.screenshot_holder a")  # 游戏截图

            # 请求第三方中文名信息
            try:  # Thanks @Deparsoul with his Database
                steamcn_json = get_page("https://steamdb.steamcn.com/app/{}/data.js?v=38".format(self.sid), jsonp_=True)
            except Exception:
                pass
            else:
                if "name_cn" in steamcn_json:
                    data["name_chs"] = steamcn_json["name_cn"]

            # 数据清洗
            def reviews_clean(tag):
                return tag.get_text(" ", strip=True).replace("：", ":")

            def sysreq_clean(tag):
                os_dict = {"win": "Windows", "mac": "Mac OS X", "linux": "SteamOS + Linux"}
                os_type = os_dict[tag["data-os"]]
                sysreq_content = re.sub("([^配置]):\n", r"\1: ", tag.get_text("\n", strip=True))

                return "{}\n{}".format(os_type, sysreq_content)

            def lag_clean(tag):
                lag_checkcol_list = ["界面", "完全音频", "字幕"]
                tag_td_list = tag.find_all("td")
                lag_support_checkcol = []
                lag = tag_td_list[0].get_text(strip=True)
                if re.search("不支持", tag.text):
                    lag_support_checkcol.append("不支持")
                else:
                    for i, j in enumerate(tag_td_list[1:]):
                        if j.find("img"):
                            lag_support_checkcol.append(lag_checkcol_list[i])

                return lag + ("({})".format(", ".join(lag_support_checkcol)) if lag_support_checkcol else "")

            data["cover"] = re.sub("^(.+?)(\?t=\d+)?$", r"\1", (cover_anchor or {"src": ""})["src"])
            data["name"] = name_anchor.get_text(strip=True)
            data["detail"] = detail_anchor.get_text("\n", strip=True).replace(":\n", ": ").replace("\n,\n", ", ")
            data["tags"] = list(map(lambda t: t.get_text(strip=True), tag_anchor)) or []
            data["review"] = list(map(reviews_clean, rate_anchor)) or []
            if linkbar_anchor and re.search("访问网站", linkbar_anchor.text):
                data["linkbar"] = re.sub("^.+?url=(.+)$", r"\1", linkbar_anchor["href"])
            data["language"] = list(filter(lambda s: s.find("不支持") == -1, map(lag_clean, language_anchor)))[:3] or []

            base_info = "中文名: {}\n".format(data["name_chs"]) if data.get("name_chs") else ""
            base_info += (data["detail"] + "\n") if data.get("detail") else ""
            base_info += "官方网站: {}\n".format(data["linkbar"]) if data.get("linkbar") else ""
            base_info += "Steam页面: https://store.steampowered.com/app/{}/\n".format(data['steam_id'])
            base_info += ("游戏语种: " + " | ".join(data["language"]) + "\n") if data.get("language") else ""
            base_info += ("标签: " + " | ".join(data["tags"]) + "\n") if data.get("tags") else ""
            base_info += ("\n".join(data["review"]) + "\n") if data.get("review") else ""

            data["baseinfo"] = base_info
            data["descr"] = html2ubb(str(descr_anchor)).replace("[h2]关于这款游戏[/h2]", "").strip()
            data["screenshot"] = list(map(lambda dic: re.sub("^.+?url=(http.+?)\.[\dx]+(.+?)(\?t=\d+)?$",
                                                             r"\1\2", dic["href"]), screenshot_anchor))
            data["sysreq"] = list(map(sysreq_clean, sysreq_anchor))

            # 主介绍生成
            descr = ""
            for key, ft in steam_format:
                _data = data.get(key)
                if _data:
                    if isinstance(_data, list):
                        join_fix = "\n"
                        if key == "screenshot":
                            _data = map(lambda d: "[img]{}[/img]".format(d), _data)
                        if key == "sysreq":
                            join_fix = "\n\n"
                        _data = join_fix.join(_data)
                    descr += ft.format(_data)
            self.ret["format"] = descr

            # 将清洗的数据一并发出
            self.ret.update(data)

    def _gen_bangumi(self):
        bangumi_link = "https://bgm.tv/subject/{}".format(self.sid)
        bangumi_characters_link = "https://bgm.tv/subject/{}/characters".format(self.sid)

        bangumi_page = get_page(bangumi_link, bs_=True)
        if str(bangumi_page).find("出错了") > -1:
            self.ret["error"] = "The corresponding resource does not exist."
        else:
            data = {"id": self.sid, "alt": bangumi_link}

            # 对页面进行划区
            cover_staff_another = bangumi_page.find("div", id="bangumiInfo")
            cover_another = cover_staff_another.find("img")
            staff_another = cover_staff_another.find("ul", id="infobox")
            story_another = bangumi_page.find("div", id="subject_summary")
            # cast_another = bangumi_page.find("ul", id="browserItemList")

            data["cover"] = re.sub("/cover/[lcmsg]/", "/cover/l/", "https:" + cover_another["src"])  # Cover
            data["story"] = story_another.get_text() if story_another else ""  # Story
            data["staff"] = list(map(lambda tag: tag.get_text(), staff_another.find_all("li")[4:4 + 15]))  # Staff

            bangumi_characters_page = get_page(bangumi_characters_link, bs_=True)

            cast_actors = bangumi_characters_page.select("div#columnInSubjectA > div.light_odd > div.clearit")

            def cast_clean(tag):
                h2 = tag.find("h2")
                char = (h2.find("span", class_="tip") or h2.find("a")).get_text().replace("/", "").strip()
                cv = "、".join(map(lambda p: (p.find("small").get_text() or p.find("a").get_text()).strip(),
                                  tag.select("div.clearit > p")))
                return "{}:{}".format(char, cv)

            data["cast"] = list(map(cast_clean, cast_actors))[:9]  # Cast

            descr = ""
            for key, ft in bangumi_format:
                _data = data.get(key)
                if _data:
                    if isinstance(_data, list):
                        _data = "\n".join(_data)
                    descr += ft.format(_data)
            data["format"] = descr

            self.ret.update(data)


# if __name__ == "__main__":
#     link = 'https://movie.douban.com/subject/27098632/'
#     # link = {'site':'douban','sid':'tt3072482'}
#     gen = Gen(link).gen(_debug=True)
#     if gen["success"]:
#         print("Format text:\n", gen["format"])
#         print(json.dumps(gen, ensure_ascii=False, sort_keys=True))
#     else:
#         print("Error : {}".format(gen["error"]))
#     # print("--------------------")
