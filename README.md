stasiak.at
##########

This is the source of `my website <https://stasiak.at>`_.

The content is licensed under the Attribution-NonCommercial-NoDerivatives 4.0 International
(CC BY-NC-ND 4.0) license (https://creativecommons.org/licenses/by-nc-nd/4.0/).

The repository may contain files under different licenses, it will be explicitly
documented in the appropriate places if so.

The site uses `Pelican Static Site Generator <https://blog.getpelican.com/>`_
written in `Python <https://www.python.org/>`_.
Syntax in code blocks is lighlighted using `Pygments <https://pygments.org/>`_.

Common tasks
============

Becuase I'm forgetful.

Prerequisites:

* Python (duh)
* `uv <https://docs.astral.sh/uv/>`_

How to run the blog locally
---------------------------

::

    uv sync && uv run invoke livereload
