#!/usr/bin/env python
# encoding: utf-8

"""
@author: zhanghe
@software: PyCharm
@file: views.py
@time: 2019-09-02 15:27
"""

import os
from flask import request, render_template

from apps import app
from tools.vad import run as run_vad


@app.route('/')
def index():
    """
    后台首页
    """
    # return "Hello, World!"
    return render_template('index.html')


@app.route('/webrtc/')
def webrtc():
    """
    webrtc
    """
    # return "Hello, World!"
    return render_template('webrtc.html')


@app.route('/vad/')
def vad():
    """
    VAD
    """
    try:
        name = request.args.get('name', 'test.wav')
        shot_name, ext = os.path.splitext(name)
        segments = run_vad(name)
        return render_template(
            'vad.html',
            wav_name='%s.wav' % shot_name,
            # waveform_name='%s.dat' % shot_name,
            segments=segments,
        )
    except Exception as e:
        return e.message


@app.route('/ns/')
def ns():
    """
    NS
    """
    try:
        name = request.args.get('name', 'nose.wav')
        shot_name, ext = os.path.splitext(name)
        return render_template(
            'ns.html',
            wav_name='%s.wav' % shot_name,
        )
    except Exception as e:
        return e.message


@app.route('/af/')
def af():
    """
    AVFilter
    """
    try:
        name = request.args.get('name', 'nose.wav')
        shot_name, ext = os.path.splitext(name)
        return render_template(
            'af.html',
            wav_name='%s.wav' % shot_name,
        )
    except Exception as e:
        return e.message
