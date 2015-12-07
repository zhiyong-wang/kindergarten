#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

'''
A WSGI application entry.
'''

import logging; logging.basicConfig(level=logging.INFO)
import os

from transwarp import db
from flask import Flask,render_template
from config import configs

# init db:
db.create_engine(**configs.db)

# init wsgi app:
import urls
app = urls.app

if __name__ == '__main__':
    app.run()