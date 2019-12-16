# -*- coding: utf-8 -*-
# Author:Chengli


import os
import subprocess
import requests
import json
import re
import random
from bs4 import BeautifulSoup
import thumbnails_try as pvs
from pymediainfo import MediaInfo


def get_video_info(video_file):
    mediainfo = {
        'general': '',
        'Video': '',
        'Audio': '',
        'language': [],
        'subtitle': [],
        'full_info': ''
    }

    text_info = ''

    media_info = MediaInfo.parse(video_file)
    data = media_info.to_json()
    data = json.loads(data)['tracks']
    audio_num = 0
    text_num = 0
    for key in data:
        if key['track_type'] == 'General':
            general = get_general(key)
            mediainfo['general'] = general
        elif key['track_type'] == 'Video':
            video = get_video(key)
            mediainfo['Video'] = video
        elif key['track_type'] == 'Audio':
            audio_num = audio_num + 1
            audio = get_audio(key, audio_num)
            mediainfo['Audio'] = mediainfo['Audio'] + audio

            if 'title' in key.keys():
                title = key['title']
                if title.find('粤语') >= 0:
                    mediainfo['language'].append('粤语')
                elif title.find('国语') >= 0:
                    mediainfo['language'].append('国语')
                    # else:
                    #     mediainfo['language'].append('国语')
            else:
                if'other_language' in key.keys():
                    language = key['other_language'][0]
                    if language.lower() == 'chinese':
                        mediainfo['language'].append('国语')

        elif key['track_type'] == 'Text':

            text_num = text_num + 1
            text = get_text(key, text_num)
            text_info = text_info + text

            if 'other_language' in key.keys():
                subtitle = key['other_language'][0]
                if subtitle.lower() == 'chinese':
                    mediainfo['subtitle'].append('中字')
                if subtitle.lower() == 'english':
                    mediainfo['subtitle'].append('英字')
            else:
                if 'title' in key.keys():
                    subtitle = key['title']
                    if subtitle.find('中字') >= 0 or subtitle.find('简体') >= 0 or subtitle.find('繁体') >= 0:
                        mediainfo['subtitle'].append('中字')
    if mediainfo['Audio']:
        mediainfo['Audio'] = 'Audio' + mediainfo['Audio']
    if text_info:
        mediainfo['Audio'] = mediainfo['Audio'] + '\n\nText' + text_info

    mediainfo['full_info'] = get_video_info_1(video_file)
    return mediainfo


def get_general(key):

    general = []
    general.append(key['track_type'])
    # general.append(check('UniqueID/String------------------: ', key, 'other_unique_id'))
    general.append(check('Name..............: ', key, 'file_name'))
    general.append(check('Container.........: ', key, 'format'))
    # general.append(check('Format_Version-------------------: ', key, 'format_version'))
    general.append(check('Size..............: ', key, 'other_file_size'))
    general.append(check('Duration..........: ', key, 'other_duration'))
    general.append(check('BitRate...........: ', key, 'other_overall_bit_rate'))
    # general.append(check('Encoded_Date---------------------: ', key, 'encoded_date'))
    # general.append(check('Other_writing_application--------: ', key, 'other_writing_application'))
    # general.append(check('Encoded_Application/String-------: ', key, 'writing_library'))

    general = '\n'.join(part for part in general if part)
    return general


def get_audio(key, audio_num):

    audio_string = '\nAudio # %s............: ' % audio_num
    if 'format' in key.keys():
        audio_string = audio_string + key['format']
    if 'channel_s' in key.keys():
        num = int(key['channel_s'])
        if num == 2:
            audio_string = audio_string + ' ' + '2.0ch'
        elif num == 6:
            audio_string = audio_string + ' ' + '5.1ch'
        elif num == 8:
            audio_string = audio_string + ' ' + '7.1ch'
    if 'other_bit_rate' in key.keys():
        audio_string = audio_string + ' @ ' + key['other_bit_rate'][0]
    if 'title' in key.keys():
        audio_string = audio_string + ' ' + key['title']

    return audio_string


def get_text(key, text_num):

    text_string = '\nText # %s.............: ' % text_num
    if 'format' in key.keys():
        text_string = text_string + key['format']
    if 'title' in key.keys():
        text_string = text_string + ' ' + key['title']

    return text_string


def get_video(key):

    general = []
    general.append(key['track_type'])
    if 'format' in key.keys():
        if key['format'] == 'AVC':
            key['format'] = 'X264'
    general.append(check('Codec.............: ', key, 'format'))
    general.append(check('BitRate...........: ', key, 'other_bit_rate'))
    if 'width' in key.keys() and 'height' in key.keys():
        width = key['width']
        height = key['height']
        string = '{width}x{height} pixels'.format(width=width, height=height)
        # print(string)
        general.append('Resolution........: %s' % string)
    general.append(check('Aspect Ratio......: ', key, 'other_display_aspect_ratio'))
    general.append(check('Frame Rate........: ', key, 'other_frame_rate'))
    general.append(check('Title.............: ', key, 'title'))
    general = '\n'.join(part for part in general if part)
    return general


def check(str1, key, str2):
    if str2 in key.keys():
        if str2.find('other') >= 0:
            r_part = key[str2][0]
        else:
            r_part = key[str2]
        return str1 + r_part
    else:
        return ''


def get_frame(video_file):
    media_info = MediaInfo.parse(video_file)
    data = media_info.to_json()
    data = json.loads(data)['tracks']
    frame_rate = 1
    frame_count = 0
    for key in data:
        if key['track_type'] == 'Video':
            frame_rate = key['frame_rate']
            frame_count = key['frame_count']
            break
    return frame_rate, frame_count


# def get_picture(file_loc, img_loc):
#     time = []
#     ratio, total = get_frame(file_loc)
#
#     total_num = int(total) / (int(ratio.split('.')[0]))
#     start = total_num * 0.1
#     step = total_num * 0.8 / 11
#     time.append(change_to_ss(start))
#     for i in range(1, 12):
#         midle = start + i * step
#         time.append(change_to_ss(midle))
#     for i in range(12):
#         base_command = 'ffmpeg -ss {time} -i "{file}" -vframes 1 -y -vf "scale=500:-1" "out-{i}".jpg 2> NUL'
#         ffmpeg_sh = base_command.format(time=time[i], file=file_loc, i=i)
#         subprocess.call(ffmpeg_sh, shell=True)
#     set_par = 'tile=3x4:nb_frames=0:padding=5:margin=5:color=random'
#     base_command = 'ffmpeg -i "out-%d.jpg" -y -filter_complex "{set}" "{img_loc}" 2> NUL'.format(
#         set=set_par, img_loc=img_loc,)
#     subprocess.call(base_command, shell=True)
#     # os.system(base_command)
#
#     for i in range(12):
#         os.remove('out-{i}.jpg'.format(i=i))
#
#     data = {
#         'smfile': open(img_loc, "rb"),
#         'file_id': ' '
#     }
#     # print('准备发送图片……')
#     pic_url = send_picture(files=data)
#
#     thanks = '[quote="截图"]自动随机截图，不喜勿看。——>该部分感谢@[url=https://hudbt.hust.edu.cn/userdetails.php?id=107055]' \
#              '[color=Red]rach[/color][/url]的指导[/quote]\n'
#
#     return thanks + '[img]' + pic_url + '[/img]'


def get_picture_2(file_loc, img_loc):
    if not os.path.exists(img_loc):
        vid = pvs.Video(file_loc)
        vsheet = pvs.Sheet(vid)
        numbers = [12, 8]
        number = random.choice(numbers)
        vsheet.make_sheet_by_number(number)
        vsheet.sheet.save(img_loc)

    funcs = [0, 1, 2, 3]
    func = random.choice(funcs)

    if func == 0:
        pic_url = send_picture(img_loc=img_loc)
    elif func == 1:
        pic_url = send_picture_2(img_loc=img_loc)
    elif func == 2:
        pic_url = send_picture_3(img_loc=img_loc)
    else:
        pic_url = send_picture_4(img_loc=img_loc)
    if pic_url:
        return '\n\n[img]' + pic_url + '[/img]\n\n'
    else:
        return ''


# sm.ms
def send_picture(img_loc=None):
    print('正在上传到SM.MS……')
    files = {
        'smfile': open(img_loc, "rb"),
        'file_id': ' '
    }
    # print('准备发送图片……')

    des_url = 'https://sm.ms/api/upload'
    try:
        des_post = requests.post(
            url=des_url,
            files=files)

        data = json.loads(des_post.content.decode())['data']

        url_to_descr = data['url']

        print(url_to_descr)
    except Exception as exc:
        url_to_descr = ''
        print('上传到sm.ms失败: %s' % exc)

    # print('获取图片链接成功。')
    return url_to_descr


# img_url
def send_picture_2(img_loc=None):
    print('正在上传到imgurl……')
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/74.0.3729.169"}

    des_url = 'https://imgurl.org/upload/backblaze'
    img = open(img_loc, 'rb')
    try:
        files = [('file', (img_loc.split('\\')[-1], img, 'image/jpeg'))]
        des_post = requests.post(headers=headers, url=des_url, files=files)
        response = des_post.content.decode()
        url = re.search('"thumbnail_url":"(.*?)"', response)
        url = url.group(1).replace('/', '')
        url = url.replace('\\', '/')
        url = url.replace('_thumb', '')
        print(url)
    except Exception as exc:
        print('上传到imgurl错误：%s' % exc)
        url = ''

    return url


# catbox
def send_picture_3(img_loc=None):
    # cookie = {
    #     "PHPSESSID": "8o8v85dtpg91v6tj6kugniue53"
    # }
    print('正在上传到catbox……')
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/74.0.3729.169",
               'Referer': 'https: // catbox.moe /?tdsourcetag = s_pctim_aiomsg'
               }
    des_url = 'https://catbox.moe/user/api.php'
    img = open(img_loc, 'rb')
    try:
        files = [('fileToUpload', (img_loc.split('\\')[-1], img, 'image/jpeg'))]
        data = {
            'reqtype': 'fileupload',
            'userhash': ''
        }
        des_post = requests.post(headers=headers, url=des_url, data=data, files=files)
        url = des_post.content.decode()
        print(url)
    except Exception as exc:
        print('上传到catbox错误: %s' % exc)
        url = ''

    return url


# lightshot
def send_picture_4(img_loc=None):

    print('正在上传图片至lightshot')
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/74.0.3729.169",
               }
    des_url = 'https://prntscr.com/upload.php'
    img = open(img_loc, 'rb')
    try:
        files = [('image', (img_loc.split('\\')[-1], img, 'image/jpeg'))]
        des_post = requests.post(headers=headers, url=des_url, files=files)
        html_ = des_post.content.decode()
        # print(html_)
        url = re.search('"data":"(.*)"', html_)
        url = url.group(1).replace('\\', '')
        html_ = requests.get(url, headers=headers).text
        # print(html_)
        soup = BeautifulSoup(html_, 'lxml')
        div = soup.find('div', class_="image-container image__pic js-image-pic")
        img = div.find('img')
        url = img.get_attribute_list('src')[0]
        url = url.replace('https', 'http')
        print(url)
    except Exception as exc:
        print('上传图片错误%s :' % exc)
        url = ''

    return url


def change_to_ss(number):
    hh = int(number / 3600)
    number_ = number - 3600 * hh
    mm = int(number_ / 60)
    ss = int(number_ - 60 * mm)
    hh = str(hh).zfill(2)
    mm = str(mm).zfill(2)
    ss = str(ss).zfill(2)
    time = '%s:%s:%s' % (hh, mm, ss)
    return time


def get_video_info_1(video_file):

    mediainfo = ''
    media_info = MediaInfo.parse(video_file)
    data = media_info.to_json()
    data = json.loads(data)['tracks']
    # audio_num = 0
    for key in data:
        if key['track_type'] == 'General':
            general = get_general_1(key)
            mediainfo = general + '\n'
        elif key['track_type'] == 'Video':
            video = get_video_1(key)
            mediainfo = mediainfo + '\n' + video + '\n'
        elif key['track_type'] == 'Audio':
            # audio_num = audio_num + 1
            # if audio_num > 2:
            #     continue
            audio = get_audio_1(key)
            mediainfo = mediainfo + '\n' + audio + '\n'

    mediainfo = mediainfo

    return mediainfo


def get_general_1(key):

    general = []
    general.append(key['track_type'])
    general.append(check('UniqueID/String------------------: ', key, 'other_unique_id'))
    general.append(check('Format/String--------------------: ', key, 'format'))
    general.append(check('Format_Version-------------------: ', key, 'format_version'))
    general.append(check('FileSize/String------------------: ', key, 'other_file_size'))
    general.append(check('Duration/String------------------: ', key, 'other_duration'))
    general.append(check('OverallBitRate/String------------: ', key, 'other_overall_bit_rate'))
    general.append(check('Encoded_Date---------------------: ', key, 'encoded_date'))
    general.append(check('other_writing_application--------: ', key, 'other_writing_application'))
    general.append(check('Encoded_Application/String-------: ', key, 'writing_library'))

    general = '\n'.join(part for part in general if part)
    return general


def get_audio_1(key):

    general = []
    general.append(key['track_type'])
    general.append(check('ID/String------------------------: ', key, 'count_of_stream_of_this_kind'))
    general.append(check('Format/String--------------------: ', key, 'other_format'))
    general.append(check('Format/Info----------------------: ', key, 'format_info'))
    general.append(check('CodecID--------------------------: ', key, 'codec_id'))
    general.append(check('Duration/String------------------: ', key, 'other_duration'))
    general.append(check('BitRate/String-------------------: ', key, 'other_bit_rate'))
    general.append(check('Channel(s)/String----------------: ', key, 'other_channel_s'))
    general.append(check('ChannelLayout--------------------: ', key, 'channel_layout'))
    general.append(check('SamplingRate/String--------------: ', key, 'other_sampling_rate'))
    general.append(check('FrameRate/String-----------------: ', key, 'other_frame_rate'))
    general.append(check('Compression_Mode/String----------: ', key, 'compression_mode'))
    general.append(check('Video_Delay/String---------------: ', key, 'other_delay_relative_to_video'))
    general.append(check('StreamSize/String----------------: ', key, 'other_stream_size'))
    general.append(check('Title----------------------------: ', key, 'title'))
    general.append(check('Language/String------------------: ', key, 'other_language'))
    general.append(check('Default/String-------------------: ', key, 'default'))
    general.append(check('Forced/String--------------------: ', key, 'forced'))

    general = '\n'.join(part for part in general if part)
    return general


def get_video_1(key):

    general = []
    general.append(key['track_type'])

    general.append(check('ID/String------------------------: ', key, 'count_of_stream_of_this_kind'))
    general.append(check('Format/String--------------------: ', key, 'format'))
    general.append(check('Format/Info----------------------: ', key, 'format_info'))
    general.append(check('Format_Profile-------------------: ', key, 'format_profile'))
    general.append(check('Format_Settings------------------: ', key, 'format_settings'))
    general.append(check('Format_Settings_CABAC/String-----: ', key, 'format_settings__cabac'))
    general.append(check('Format_Settings_RefFrames/String-: ', key, 'other_format_settings__reframes'))
    general.append(check('CodecID--------------------------: ', key, 'codec_id'))
    general.append(check('Duration/String------------------: ', key, 'other_duration'))
    general.append(check('BitRate/String-------------------: ', key, 'other_bit_rate'))
    general.append(check('Width/String---------------------: ', key, 'other_width'))
    general.append(check('Height/String--------------------: ', key, 'other_height'))
    general.append(check('DisplayAspectRatio/String--------: ', key, 'other_display_aspect_ratio'))
    general.append(check('FrameRate_Mode/String------------: ', key, 'other_frame_rate_mode'))
    general.append(check('FrameRate/String-----------------: ', key, 'other_frame_rate'))
    general.append(check('ColorSpace-----------------------: ', key, 'color_space'))
    general.append(check('ChromaSubsampling/String---------: ', key, 'chroma_subsampling'))
    general.append(check('BitDepth/String------------------: ', key, 'other_bit_depth'))
    general.append(check('ScanType/String------------------: ', key, 'other_scan_type'))
    general.append(check('Bits-(Pixel*Frame)---------------: ', key, 'bits__pixel_frame'))
    general.append(check('StreamSize/String----------------: ', key, 'other_stream_size'))
    general.append(check('Default/String-------------------: ', key, 'default'))
    general.append(check('Forced/String--------------------: ', key, 'forced '))

    general = '\n'.join(part for part in general if part)
    return general


# if __name__ == "__main__":
#     path = r"W:\HUDBT-2019-06-09\八两金.1989.720p.国粤双语.简繁中字￡CMCT鸠摩智\[八两金].Eight.Taels.of.Gold.1989.BluRay.720p.x264.FLAC.2Audios-CMCT.mkv"
#     video_info = get_video_info(path)
#     for item in video_info:
#         print(video_info[item])
