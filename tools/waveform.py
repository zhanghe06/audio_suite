#!/usr/bin/env python
# encoding: utf-8

"""
@author: zhanghe
@software: PyCharm
@file: waveform.py
@time: 2020-02-25 16:31
@desc: 声音波形
"""


import os
import sys

input_dir = 'apps/static/uploads/wav'
output_dir = 'apps/static/uploads/waveform'


def generate_waveform(audio_name):
    waveform_name, ext = os.path.splitext(audio_name)

    cmd = 'audiowaveform -i %(input_dir)s/%(audio_name)s -o %(output_dir)s/%(waveform_name)s -b 8' % \
        {
            'input_dir': input_dir,
            'output_dir': output_dir,
            'audio_name': audio_name,
            'waveform_name': '%s.dat' % waveform_name,
        }
    os.system(cmd)


def main(args):
    try:
        if len(args) < 1:
            sys.stderr.write(
                'Usage: tools/waveform.py <wav file name>\n')
            sys.exit(1)
        generate_waveform(args[0])
    except Exception as e:
        print(e.message)


if __name__ == '__main__':
    # python tools/waveform.py test.wav
    main(sys.argv[1:])
