#!/usr/bin/env python
# encoding: utf-8

"""
@author: zhanghe
@software: PyCharm
@file: pcm.py
@time: 2020-02-25 13:22
@desc: 格式转换
"""

import os
import sys

wav_dir = 'apps/static/uploads/wav'
pcm_dir = 'apps/static/uploads/pcm'


def convert_wav(audio_name):
    # -v 指定日志级别("quiet"、"panic"、"fatal"、"error"、"warning"、"info"、"verbose"、"debug"、"trace")
    # -y 覆盖
    cmd = 'ffmpeg -y -v quiet -i %(wav_dir)s/%(audio_name)s -ar 8000 -ac 1 -acodec pcm_s16le %(pcm_dir)s/%(audio_name)s' % \
        {
            'wav_dir': wav_dir,
            'pcm_dir': pcm_dir,
            'audio_name': audio_name,
        }
    os.system(cmd)


def main(args):
    try:
        if len(args) < 1:
            print('Usage: tools/pcm.py <wav file name>')
            return
        wav_name = args[0]
        wav_path = '%s/%s' % (wav_dir, wav_name)
        if not os.path.isfile(wav_path):
            raise Exception('wav file [%s] is not exists!' % wav_path)
        convert_wav(args[0])
    except Exception as e:
        print(e.message)


if __name__ == '__main__':
    # convert_wav('test.wav')
    # python tools/pcm.py test.wav
    main(sys.argv[1:])
