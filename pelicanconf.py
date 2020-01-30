#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

import datetime
import subprocess

AUTHOR = 'Jakub Stasiak'
SITENAME = 'Jakub Stasiak'
SITEURL = 'https://stasiak.at'

PATH = 'content'

TIMEZONE = 'Europe/Warsaw'

DEFAULT_LANG = 'en'

THEME = 'stasiak.at-theme'
COMMIT_ID = subprocess.check_output(['git', 'rev-parse', '--short=7', 'HEAD'], text=True).strip()
TIMESTAMP = datetime.datetime.now().replace(microsecond=0).astimezone().isoformat(' ')

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

DEFAULT_PAGINATION = False

STATIC_PATHS = ['static']

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

MARKDOWN = {
    'extensions': ['markdown.extensions.smarty'],
}
