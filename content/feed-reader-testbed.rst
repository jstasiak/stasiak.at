Testing feed readers with feed-reader-testbed
#############################################

:date: 2025-03-03
:slug: testing-feed-readers-with-feed-reader-testbed
:tags: atom, rss, feeds

I found myself contemplating the idea of implementing an Atom/RSS feed reader
because I have a pretty specific itch I'd like to scratch and you know how
`if you want something done right obviously you need to do it yourself
<https://en.wikipedia.org/wiki/Not_invented_here>`_.

Now, there is a little bit of nuance involved if a feed reader is to be
a good citizen - something I wasn't fully aware of until I read `Rachel Kroll's
post titled "A sysadmin's rant about feed readers and crawlers"
<https://rachelbythebay.com/w/2022/03/07/get/>`_.

Putting aside behaviors like polling every ten seconds – which I'm not planning
on doing – my focus is on getting the caching right. In the article Rachel says:

    Given this, you can keep track of the "Last-Modified" header when you get
    a copy of the feed. Then, you can turn around and use that same value in
    an "If-Modified-Since" header the next time you come to look for an update.
    If nothing's changed, the web server will notice it's the same as what it
    already has, and it'll send you a HTTP 304 code telling you to use your
    local (cached) copy. In other words, there is no reason for you to download
    another ~640 KB of data right now.

    Alternatively, many web servers (mine included) support this thing called
    "ETag", and it amounts to a blob that you just return in your requests. If
    it hasn't changed, you get a nice small 304. Otherwise, you'll get the same
    content as always. It's effectively another way to do the "IMS" behavior
    described above. 

All in all not particularly complex:

1. When the client makes an unconditional request or there is new content the
   server returns the `ETag
   <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ETag>`_ or the
   `Last-Modified <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Last-Modified>`_
   response header or both.
2. The client uses these response headers to the request the content *conditionally*
   with the `If-Modified-Since <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-Modified-Since>`_
   and `If-None-Match <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-None-Match>`_
   request headers.

To make sure no one is annoyed by my yet-to-materialize feed reader
I wrote a little tool to check feed readers' behavior vis-a-vis caching:
`feed-reader-testbed <https://github.com/jstasiak/feed-reader-testbed>`_.
It's currently Atom-only but adding RSS support won't be hard if needed.

The tool serves a static single-entry feed and logs information about
the relevant request headers and whether a conditional fetch succeeded.

An example output after subscribing to a feed with `Vienna <https://www.vienna-rss.com/>`_
and refreshing it once::

    > cargo run
    ...
    2025-03-03T23:35:29.185126Z  INFO feed_reader_testbed: Returning 200 OK with full content request_id=53b035e40bf7f91e user_agent=Vienna/8414 (Macintosh; Intel macOS 15_3_0) if_none_match=None if_modified_since=None
    2025-03-03T23:35:54.032359Z  INFO feed_reader_testbed: Returning 304 Not Modified (ETag and Last-Modified match) request_id=8eeb56fb8ea3c62a user_agent=Vienna/8414 (Macintosh; Intel macOS 15_3_0) if_none_match=Some("\"be363b466230b823db7c8f2f6626dc90\"") if_modified_since=Some("Sun, 03 Mar 2024 00:00:00 GMT")

Now that the `yak's hair has been trimmed down <https://en.wiktionary.org/wiki/yak_shaving>`_
I can get to implementing that feed reader that originally triggered this
whole thing.

