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

FEED_DOMAIN = SITEURL
FEED_ALL_ATOM = 'feeds/all.atom.xml'
TAG_FEED_ATOM = 'feeds/{slug}.atom.xml'
# Disabled Atom feeds, don't need them
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

AUTHORS_SAVE_AS = ''
AUTHOR_SAVE_AS = ''
CATEGORIES_SAVE_AS = ''
CATEGORY_SAVE_AS = ''
ARCHIVES_SAVE_AS = ''

PLUGIN_PATHS = ['./pelican-plugins']
PLUGINS = ['sitemap']

SITEMAP = {
    'format': 'xml',
    'priorities': {
        'articles': 0.5,
        'indexes': 0.5,
        'pages': 0.5
    },
    'changefreqs': {
        'articles': 'monthly',
        'indexes': 'daily',
        'pages': 'monthly'
    }
}
