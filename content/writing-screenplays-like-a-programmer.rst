Writing screenplays like a programmer or: How I reinvented the wheel again
##########################################################################

:date: 2020-03-05 22:00
:tags: screenwriting, fountain

I hate using `WYSIWYG <https://en.wikipedia.org/wiki/WYSIWYG>`_ text processors with a passion.

So, now that we have that out of the way: I'd become interested in filmmaking some time ago and
I wanted to write some screenplays. I wrote one in LibreOffice Writer but I failed to be able to
format it nicely and even my unsuccessful attempt took way too much of my time. Since I'm
a programmer I figured what I wanted was some lightweight markup language, so I could stick my
screenplays as text files in a Git repository for version control.

I looked around and I found the `screenplay LaTeX package <https://www.ctan.org/pkg/screenplay>`_.
When I saw the `output it produced <https://mirrors.nic.cz/tex-archive/macros/latex/contrib/screenplay/test.pdf>`_
I was happy, but when I saw the actual syntax I had to reconsider using it, as it reminded me of
why I dislike using LaTeX in some cases – it can be annoying to write by hand:

.. code-block:: latex

    \intslug{SPACE STATION}

    Dark corridor. Something lurks in the shadows.

    \extslug{MILITARY BASE -- DAY}

    COLONEL SMITH smokes a cigarette. There are items on his desk: a bottle of whisky, a gun and a doll. SMITH looks up as CAPTAIN PARKER approaches.

    CAPTAIN PARKER doesn't look too well.

    \begin{dialogue}{SMITH}So, it's begun.\end{dialogue}
    \begin{dialogue}{PARKER}Yes, it has.\end{dialogue}

Unfortunately the LaTeX and screenplay package combo fails at something important to me: it's
not lightweight enough for me, so I needed something better.

I *swear* I looked for better solutions, but somehow I didn't find any (a failure on my part, more on
this later), so I wrote my own: `a lightweight screenplay markup language to LaTeX translator named
scripter <https://github.com/jstasiak/scripter>`_. The language is extremely ad-hoc and its rules are
so simple I can copy them here verbatim:

* Whitespace at beginning and end of lines are ignored
* Lines with only whitespace in them are ignored
* The first line is the title
* The second line is the author(s)
* Empty lines are ignored
* Lines beginning with ``INT.`` or ``EXT.`` are treated as sluglines, what
  comes after ``INT.`` and ``EXT.`` is free-form
* Lines beginning with whitespace are assumed to contain dialogue. That requires
  them to contain at least one ``:`` character. The part before the first colon is
  is the character that's speaking, the second is what's being said. Parts in
  parentheses are treated as parentheticals. Colon characters other than the
  first are treated as plain text.
* Other lines are treated as description

This allowed me to write this to get exactly the same output as shown above::

    INT. SPACE STATION

    Dark corridor. Something lurks in the shadows.

    EXT. MILITARY BASE -- DAY

    COLONEL SMITH smokes a cigarette. There are items on his desk: a bottle of whisky, a gun and a doll. SMITH looks up as CAPTAIN PARKER approaches.

    CAPTAIN PARKER doesn't look too well.

        SMITH: So, it's begun.
        PARKER: Yes, it has.

All in all implementing it was fun and not too difficult, about 100 lines of dependency-free Rust.
Well, dependency-free if one wasn't counting LaTeX – this is one issue with the program, it requires
LaTeX to actually render the screenplays, so I can't expect any of my non-programmer friends to
actually use it when collaborating on screenplays. The other issue is it only renders PDF-s,
and I would quite like to be able to render nicely formatted screenplays on mobile devices as well,
so that I could apply changes in the field, so to speak, and give actors the updated output to read
on their phones or ebook readers. This means I also want HTML or EPUB output.

I went on the Internet and looked again, because someone *must* have had done this already. I'm not
sure now what phrase did I use when searching for a solution (it could've been "screenplay markdown"
for all I know), but I found what I looked for – `an excellent post aptly titled Screenplay Markdown
Or: How I Fought The Battle With Usability and Lost, But Received Actual Productivity as a Consolation
Prize by Stu Maschwitz <https://prolost.com/blog/2011/8/9/screenplay-markdown.html>`_ (dated August 9,
2011). The blog post resonated with me. I won't quote it here, go read it, it's good and to the point.
It contains a well-put description of what I too dislike about WYSIWYG editors and why I want a
lightweight markup language for my screenplays. (This is exactly what I totally missed on my first go
at the problem, which made me reinvent the wheel without knowing it even existed.)

The blog post lead me to the `Fountain screenplay markup <https://fountain.io/>`_, which `has some
interesting history behind it <https://fountain.io/developers>`_:

    Fountain comes from several sources. John August and Nima Yousefi developed Scrippets, which used
    simple markup to embed screenplay-formatted material in websites. Stu Maschwitz drafted a more
    extensive spec known as Screenplay Markdown or SPMD, designed for full-length screenplays.

    Stu and John discovered that they were simultaneously working on similar text-based screenplay
    formats, and merged them into what you see here. Other contributors to the spec include
    Martin Vilcans, Brett Terpstra, Jonathan Poritsky, and Clinton Torres.

Now we're talking! `Fountain is supported by a wide range of software <https://fountain.io/apps>`_,
including a `nice graphical Mac OS editor named Writer <https://github.com/HendrikNoeller/Writer>`_,
an `an editor for Android named DubScript <https://www.dubscript.com/>`_, `Vim syntax highlighting
<https://www.vim.org/scripts/script.php?script_id=3880>`_ and `a Python library/CLI application named
screenplain <https://github.com/vilcans/screenplain/>`_ (it's even provided as a `web service to the
people that need it <http://www.screenplain.com/>`_!).

Its `syntax <https://fountain.io/syntax>`_ is much more extensive than what I implemented, but simple
cases remain simple. The screenplay fragment from above looks like this when written using Fountain::

    INT. SPACE STATION

    Dark corridor. Something lurks in the shadows.

    EXT. MILITARY BASE -- DAY

    COLONEL SMITH smokes a cigarette. There are items on his desk: a bottle of whisky, a gun and a doll. SMITH looks up as CAPTAIN PARKER approaches.

    CAPTAIN PARKER doesn't look too well.

    SMITH
    So, it's begun.

    PARKER
    Yes, it has.

Notice how the syntax is almost the same? So cool!

I hit a jackpot with this. I'll be migrating all my screenplays and CI workflow to Fountain.

And *scripter*, which was one of my first Rust programs? It's time to put it to rest, there are
better tools available. I'll update its readme to redirect anyone reading it to the Fountain homepage.
