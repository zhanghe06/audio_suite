#!/usr/bin/env python
# encoding: utf-8

"""
@author: zhanghe
@software: PyCharm
@file: __init__.py.py
@time: 2019-09-02 15:19
"""


from flask import Flask
app = Flask(__name__)


from apps import views
