import re

from bs4 import BeautifulSoup
from pelican import contents, signals


def insert_toc(content):
    if isinstance(content, contents.Static):
        return

    document = BeautifulSoup(content._content, 'html.parser')
    entries: list[str] = []

    for header in document.findAll(re.compile(r'^h[1-6]')):
        [link] = header.children
        href = link['href']
        level = int(header.name.lstrip('h'))
        # This will do for now. Once we have headers of different levels we'll need
        # to make some changes so that the levels look different in the TOC.
        assert level == 2
        label = link.get_text()
        entries.append(f'<a href="{href}">{label}</a>')

    if entries:
        rendered_toc = '\n'.join(entries)
        content.toc = rendered_toc

def register() -> None:
    signals.content_object_init.connect(insert_toc)
