# -*- coding: utf-8 -*-
# Author:tomorrow505


import subprocess
from PIL import Image, ImageDraw, ImageFont
from pymediainfo import MediaInfo
import json
import re
import os


class Video:
    def __init__(self, filename):
        # 影片名字
        self.filename = filename
        # 影片大小
        self.filesize = self.get_file_size()

        # 获取图片——第0秒的 及其大小，模式？
        example = self.get_frame_at(0)
        self.resolution = example.size
        # RBG
        self.mode = example.mode

        # 获取秒数
        self.duration = self.get_video_duration()

        self.thumbnails = []

        # 图片大小
        self.thumbsize = self.resolution
        self.thumbcount = 0

    def get_file_size(self):
        return round(os.stat(self.filename).st_size / 1048576.0 / 1024, 2)

    def get_video_duration(self):
        media_info = MediaInfo.parse(self.filename)
        data = media_info.to_json()
        data = json.loads(data)['tracks']
        frame_rate = 1
        frame_count = 0
        for key in data:
            if key['track_type'] == 'Video':
                frame_rate = key['frame_rate']
                frame_count = key['frame_count']
                break
        duration = int(frame_count) / (int(frame_rate.split('.')[0]))
        return duration

    def get_frame_at(self, seektime, n=99):
        timestring = get_time_string(seektime)
        file_name = os.path.basename(self.filename)
        tmp_path = './tmp'
        img_path = os.path.join(tmp_path, "{filename}-out-{d}.jpg".format(filename=file_name, d=n))
        # print(img_path)
        command = 'ffmpeg -ss {timestring} -y -i "{file}" "-f" "image2" "-frames:v"  "1" "-c:v" "png" ' \
                  '"-loglevel" "8" {img_path}'.format(timestring=timestring, file=self.filename, img_path=img_path)
        try:
            subprocess.call(command, shell=True)
            img = Image.open(img_path.format(n=n))
        except Exception as exc:
            print(exc)
        return img

    # 把所有间隔多少的截图都放到一个列表里
    def make_thumbnails(self, interval, number=0):
        if not number:
            total_thumbs = int(self.duration//interval)
        else:
            total_thumbs = number
        thumbs_list = []
        seektime = 0
        for n in range(0, total_thumbs):
            seektime += interval
            img = self.get_frame_at(seektime, n)
            if img:
                thumbs_list.append(img)
        self.thumbnails = thumbs_list
        self.thumbcount = len(thumbs_list)
        return thumbs_list

    # 收缩图片大小
    def shrink_thumbs(self, maxsize):
        if self.thumbcount == 0:
            return
        for i in range(0, self.thumbcount):
            self.thumbnails[i].thumbnail(maxsize)
        self.thumbsize = self.thumbnails[0].size
        return self.thumbnails


def get_time_string(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    timestring = str(hours) + ":" + str(minutes).rjust(2, '0') + ":" + str(seconds).rjust(2, '0')
    return timestring


class Sheet:
    def __init__(self, video):
        # fontfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Cyberbit.ttf")
        fontfile = './docs/Cyberbit.ttf'
        if os.path.exists('./docs/Palace-Script-MT-Semi-Bold.ttf'):
            name_file = './docs/Palace-Script-MT-Semi-Bold.ttf'
        else:
            name_file = './docs/P22Virginian.ttf'

        self.font = ImageFont.truetype(fontfile, 18)
        self.namefont = ImageFont.truetype(name_file, 48)
        self.headerColour = (255, 255, 224, 0)
        self.backgroundColour = (255, 255, 224, 0)
        self.textColour = (0, 0, 0, 0)
        self.headerSize = 135
        # self.gridColumn = 4
        # self.maxThumbSize = (300, 300)
        self.gridColumn = 3
        t = int(1200/self.gridColumn)
        self.maxThumbSize = (t, t)

        self.timestamp = True

        self.audio_string = ''
        self.video_string = ''
        self.info_string = ''

        info = open('./conf/picture_id.txt').read()
        info = info.split(';')
        self.special_id = info[0].replace('id=', '')
        if len(info) > 1:
            if info[1].find('position') >= 0:
                nums = re.findall('\d{1,4}', info[1])
                self.position = (int(nums[0]), int(nums[1]))
            else:
                self.position = (1040, 45)
        if len(info) > 2:
            if info[2].find('color') >= 0:
                numss = re.findall('\d{1,3}', info[2])
                self.headerColour = (int(numss[0]), int(numss[1]), int(numss[2]), 0)
        self.box_width = 4

        self.video = video

    def set_property(self, prop, value):
        if prop == 'font':
            self.font = ImageFont.truetype(value[0], value[1])
        elif prop == 'backgroundColour':
            self.backgroundColour = value
        elif prop == 'textColour':
            self.textColour = value
        elif prop == 'headerSize':
            self.headerSize = value
        elif prop == 'gridColumn':
            self.gridColumn = value
        elif prop == 'maxThumbSize':
            self.maxThumbSize = value
        elif prop == 'timestamp':
            self.timestamp = value
        else:
            raise Exception('Invalid Sheet property')

    def make_grid(self):
        column = self.gridColumn
        row = self.video.thumbcount//column
        if (self.video.thumbcount % column) > 0:
            row += 1
        width = self.video.thumbsize[0]
        height = self.video.thumbsize[1]
        grid = Image.new(self.video.mode, (width*column+self.box_width*(column+1), height*row+self.box_width*(row+1)),
                         self.backgroundColour)
        d = ImageDraw.Draw(grid)
        seektime = 0
        for j in range(0, row):
            for i in range(0, column):
                if j*column+i >= self.video.thumbcount:
                    break
                aps_x = (i+1)*self.box_width
                aps_y = (j+1)*self.box_width
                grid.paste(self.video.thumbnails[j*column+i], (width*i+aps_x, height*j+aps_y))
                if self.timestamp:
                    seektime += self.vid_interval
                    ts = get_time_string(seektime)
                    d.text(((width+self.box_width)*(i+1)-60, (height+self.box_width)*(j+1)-25), ts, font=self.font,
                           fill=self.backgroundColour)
        self.grid = grid
        dir_name = './tmp'
        base_name = os.path.basename(self.video.filename)
        img_name = os.path.join(dir_name, base_name)
        for i in range(0, 12):
            try:
                img_path = '{filename}-out-{d}.jpg'.format(filename=img_name, d=i)
                # print(img_path)
                os.remove(img_path)
            except Exception:
                pass
        try:
            os.remove('{filename}-out-99.jpg'.format(filename=img_name))
        except Exception:
            pass
        return grid

    def make_header(self):
        self.get_header_info()
        duration = self.video.duration
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        timestring = (str(hours)+":" + str(minutes).rjust(2, '0')+":" + str(seconds).rjust(2, '0'))

        header = Image.new(self.grid.mode, (self.grid.width, self.headerSize), self.headerColour)

        d = ImageDraw.Draw(header)
        d.text((10, 14), "File: "+os.path.basename(self.video.filename), font=self.font, fill=self.textColour)
        d.text((10, 38), "Size: " + str(self.video.filesize) + "GB, " + 'Duration: ' + timestring + self.info_string,
               font=self.font, fill=self.textColour)
        d.text((10, 62), self.audio_string, font=self.font, fill=self.textColour)
        d.text((10, 86), self.video_string, font=self.font, fill=self.textColour)
        d.text((10, 110), "Auto generated by FFMPEG combined with python code.", font=self.font, fill=self.textColour)
        d.text(self.position, self.special_id, font=self.namefont, fill=self.textColour)
        self.header = header
        return header

    def make_sheet_by_interval(self, interval, number=0):
        # self.vid_interval = interval

        self.video.make_thumbnails(interval, number)
        self.video.shrink_thumbs(self.maxThumbSize)
        self.make_grid()
        self.make_header()
        self.sheet = Image.new(self.grid.mode, (self.grid.width, self.grid.height + self.header.height))
        self.sheet.paste(self.header, (0, 0))
        self.sheet.paste(self.grid, (0, self.header.height))
        return self.sheet

    def make_sheet_by_number(self, num_of_thumbs):
        # for i in range(0, 12):
        #     try:
        #         os.remove('out-{d}.jpg'.format(d=i))
        #     except Exception:
        #         pass
        # try:
        #     os.remove('out-99.jpg')
        # except Exception:
        #     pass
        if num_of_thumbs == 8:
            self.gridColumn = 2
            t = int(1200 / self.gridColumn)
            self.maxThumbSize = (t, t)
        interval = (self.video.duration/(num_of_thumbs+1))
        self.vid_interval = interval
        return self.make_sheet_by_interval(interval, number=num_of_thumbs)

    def get_header_info(self):
        media_info = MediaInfo.parse(self.video.filename)
        data = media_info.to_json()
        data = json.loads(data)['tracks']
        audio_num = 0

        overall_bit_rate = ''
        video_format = ''
        video_color = ''
        video_chroma_subsampling = ''
        video_codec_id = ''
        video_format_profile = ''
        video_other_frame_rate = ''
        video_other_bit_rate = ''
        audio_other_format = ''
        audio_other_sampling_rate = ''
        audio_other_bit_rate = ''
        audio_other_fram_rate = ''

        for key in data:
            if key['track_type'] == 'General':
                if 'other_overall_bit_rate' in key.keys():
                    overall_bit_rate = key['other_overall_bit_rate'][0]
            elif key['track_type'] == 'Video':
                if 'format' in key.keys():
                    video_format = key['format'].lower()
                if 'color_space' in key.keys():
                    video_color = key['color_space'].lower()
                if 'chroma_subsampling' in key.keys():
                    video_chroma_subsampling = key['chroma_subsampling']
                if 'codec_id' in key.keys():
                    video_codec_id = key['codec_id'].lower()
                if 'format_profile' in key.keys():
                    video_format_profile = key['format_profile'].lower()
                if 'other_frame_rate' in key.keys():
                    video_other_frame_rate = key['other_frame_rate'][0]
                if 'other_bit_rate' in key.keys():
                    video_other_bit_rate = key['other_bit_rate'][0]
            elif key['track_type'] == 'Audio':
                audio_num = audio_num + 1
                if audio_num > 1:
                    continue
                if 'other_format' in key.keys():
                    audio_other_format = key['other_format'][0].lower()
                if 'other_sampling_rate' in key.keys():
                    audio_other_sampling_rate = key['other_sampling_rate'][0]
                if 'other_bit_rate' in key.keys():
                    audio_other_bit_rate = key['other_bit_rate'][0]
                if 'other_fram_rate' in key.keys():
                    audio_other_fram_rate = key['other_fram_rate'][0]

        self.info_string = ', avg.bitrate: ' + overall_bit_rate
        self.audio_string = 'Audio: %s, %s, %s, %s' % (audio_other_format, audio_other_sampling_rate,
                                                       audio_other_fram_rate, audio_other_bit_rate)
        self.video_string = 'Video: %s, %s, %s, %s: %s, %sx%s, %s, %s' % (video_format, video_format_profile,
                                                                          video_codec_id, video_color,
                                                                          video_chroma_subsampling,
                                                                          self.video.resolution[0],
                                                                          self.video.resolution[1],
                                                                          video_other_bit_rate, video_other_frame_rate)



