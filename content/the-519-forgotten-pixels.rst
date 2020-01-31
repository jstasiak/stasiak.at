The 519 forgotten pixels
########################

:date: 2020-01-31 03:00
:tags: openpol, polanie, trivia, digital preservation

You've probably never played Polanie (AKA Osadnici, VICTORY or Slavs), a niche Polish real-time
strategy game released in 1996.  But even if you have, I bet you haven't noticed this one tiny
little detail. I know I haven't – and I played the game *a lot* when I was a child.

Some backstory
==============

What is it? Well, let's dive in the source code first. Yes, there *is* code. Janusz Prokulewicz, the
man behind `the Polanie fan site polanie.prv.pl <http://polanie.prv.pl/>`_ managed to obtain `the
game's source code <http://polanie.prv.pl/files/pliki/kodpol.zip>`_ from Mirosław Dymek, the game's
designer and lead developer (and that, together with the way the game came to life, is a story for
another time).  I'm `mirroring the source code of the game and the map editor on GitHub
<https://github.com/jstasiak/polanie-src>`_, because `polanie.prv.pl` seems
to not be maintained anymore (the last update is from the 10th of April, 2005) and I'd hate for the
code to be lost. Actually, I'd hate for *any* content from the site to be lost and, frankly, I find
it surprising that the site is still up at all – so I went ahead and `mirrored the whole site on
GitHub <https://github.com/jstasiak/polanie.prv.pl-mirror>`_. The author painstakingly gathered a lot
of game-related resources and this is my way of helping preserve it.

Why was I even looking at the source code? Some time ago I set about reimplementing the game, for
few reasons:

* I really like the game and I'd like to bring it to life in a new shape
* I like Rust and I'd like to become reasonably proficient in it, this seemed like a good project to
  help me get there so I'm writing it in Rust
* I wanted to do some game development

Thus the `OpenPol project <https://github.com/jstasiak/openpol>`_ was born. When learning how the
game's resources are stored I learned about the thing that this post is about.

The code
========

Here's few details about the game so that the next parts are easier to understand. Polanie uses
`VGA mode 13h <https://en.wikipedia.org/wiki/Mode_13h>`_, which means the resolution is 320x200 with
1-byte pixels. The pixel values don't store color information directly, but instead indexes into
a color palette (1-byte indexes, so 256 colors available). Now that we know that, let's see how the
game's main menu is displayed:

.. code-block:: c
    :hl_lines: 4 5

    void ShowMainMenu(void) {
      DownPalette(1);
      LoadExtendedPalette(2);
      ShowPicture(2, 0);
      ShowPicture(17, 100);

      // ShowPicture(11,0);
      // ShowPicture(26,100);
      // LoadExtendedPalette(11);

      RisePalette(0);
    }

I highlighted the important lines here. The palette manipulation (``DownPalette(1)`` darkens the
current palette slowly, ``LoadExtendedPalette(2)`` loads palette with index 2 and ``RisePalette``
activates the palette, effectively) and the disabled code are irrelevant – what's interesting is
what ``ShowPicture`` is doing:

.. code-block:: c

    extern char *VirtualScreen;
    void ShowPicture(int nr, int b) {
      // ClearScreen13h();
      if (!b)
        memset(VirtualScreen, 0, 32000);
      else
        memset((void *)(VirtualScreen + 32000), 0, 32000);
      int t = LoadToScreen13h(nr, b);
    }

where ``VirtualScreen`` is set here

.. code-block:: c

    void SetScreen(int Screen) {
      if ((Screen) && (RealVirtualScreen != NULL))
        VirtualScreen = RealVirtualScreen;
      else
        VirtualScreen = (char *)0xA0000;
    }

to either point to ``0xA0000``, which is where the `display memory is mapped
<http://www.osdever.net/FreeVGA/vga/vgamem.htm>`_ or to ``RealVirtualScreen``, which is
a 64 000 bytes memory block allocated by the game. Since right before showing the main menu
``SetScreen(0)`` is called

.. code-block:: c

    SetScreen(0);
    if (show) {
      ClearScreen13h();
      ShowMainMenu();
    }

when we write to the block of memory pointed to by ``VirtualScreen`` now we're actually
displaying pixels. Those were truly simpler times in some manners, when you could do that.

OK, back to those two ``ShowPicture`` calls:

.. code-block:: c

    ShowPicture(2, 0);
    ShowPicture(17, 100);

    // (...)

    void ShowPicture(int nr, int b) {
      // ClearScreen13h();
      if (!b)
        memset(VirtualScreen, 0, 32000);
      else
        memset((void *)(VirtualScreen + 32000), 0, 32000);
      int t = LoadToScreen13h(nr, b);
    }

It looks like when ``b`` is zero we set the first half of the screen to color 0 (the screen
has 320 * 240 = 64 000 pixels, half of that is 32 000), and when it's non-zero we clear the
second half. Then we call ``LoadToScreen13h``:

.. code-block:: c

    int LoadToScreen13h(int offset, int line) {
      int i = 0, j = 1;
      int Offset = offset * 33000;
      short size;

      if (graphicfile == NULL)
        return 1;

      fseek(graphicfile, Offset, 0);
      fread(&size, 2, 1, graphicfile);
      fread(&size, 2, 1, graphicfile);
      fread(&size, 2, 1, graphicfile);
      if (line)
        j = 0;
      for (i = 0; i < 99 + j; i++) {
        size = fread((void *)(VirtualScreen + (line * 320) + (i * 320)), 1, 319,
                     graphicfile);
        if (size != 319)
          j = 2;
      }

      return j;
    }

``graphicfile`` is a file descriptor opened when game initialized its resources:

.. code-block:: c

    void OpenGraphicFile() {
      char ss[50];
      sprintf(ss, "graf.dat");
      graphicfile = fopen(ss, "rb");
    }

And ``graf.dat`` is a file with majority of the game's graphic assets (`grafika` is
`graphics` in Polish, hence the file name). In ``LoadToScreen13h`` we calculate an
offset in the file:

.. code-block:: c

      int Offset = offset * 33000;

This suggests the file consists of 33 000 byte blocks and this is indeed the case.
The whole file (I'm taking about the CD edition of the game) is 990 000 bytes, so
30 segments in total.

We move the current position inside the open file to ``Offset`` and then we move
6 bytes more, discarding an unused header within the selected segment:

.. code-block:: c

      fseek(graphicfile, Offset, 0);
      fread(&size, 2, 1, graphicfile);
      fread(&size, 2, 1, graphicfile);
      fread(&size, 2, 1, graphicfile);

And then we perform the actual data transfer:

.. code-block:: c

      int i = 0, j = 1;

      // (...)

      if (line)
        j = 0;
      for (i = 0; i < 99 + j; i++) {
        size = fread((void *)(VirtualScreen + (line * 320) + (i * 320)), 1, 319,
                     graphicfile);
        if (size != 319)
          j = 2;
      }

Now, since ``ShowPicture`` passes its parameters directly to ``LoadToScreen13h`` we
have those two call chains:

1. ``ShowPicture(2, 0)`` calls ``LoadToScreen13h(2, 0)``

   In this case ``line`` is set to ``0``, so the ``if (line)`` condition is not
   satisfied and ``j`` remains ``1``. The loop condition becomes ``i < 99 + 1``,
   or ``i < 100``, so we have a round 100 iterations.

   In every iteration we read 319 bytes to ``VirtualScreen`` indexed by ``line * 320
   + i * 320``. Since ``line`` is 0, we effectively write to
   ``VirtualScreen + i * 320``. ``320`` is the line size in mode 13h, so we're
   writing to the first half of the screen line by line. 100 iterations means 100
   lines displayed – half of the lines available.

2. ``ShowPicture(17, 100)`` calls ``LoadToScreen13h(17, 100)``

   ``line`` is set to 100, so ``if (line)`` triggers and ``j`` is set to 0. This
   changes the number of iterations to 99, because the loop condition becomes
   ``i < 99 + 0``. The image lines are written to ``VirtualScreen + 100 * 320 +
   i * 320``, so we're effectively writing to the second half of the screen
   line by line, 99 lines in total.

The ``if (size != 319)`` condition is never satisfied, because the code never
moves the file position to a place, where it's fewer than 319 bytes from the end
of file. Therefore ``j`` is never set to 2, it's for all intents and purposes
a red herring.

Can you see it?
===============

It took me a while to understand what I was looking at. "Hang on, this can't
be right" I told myself several times, until I actually implemented importing
the data from ``graf.dat`` and it worked.

If it worked what's the issue then?

See how in ``LoadToScreen13h`` when reading into the first half of the display
memory (100 lines, 320 pixels each – it's important!) we're indeed iterating
100 times (for 100 lines) but for every 320-byte destination line we only
read 319 bytes from the source?

See how we miss last one byte per line when reading into the second half of
the display *and* we only iterate 99 times, therefore we only fill 99 lines
and don't touch the last one? And it's not just the code doing it – the images
in ``graf.dat`` really have 319-pixel lines (otherwise the code reading 319
bytes at a time and moving the file cursor forward 319 bytes at a time would
not work) and the "second halves" only have 99 lines.

"No way", says you, "that would mean the game doesn't display anything on its
right and bottom borders". Well, see for yourself (you need to zoom in a whole
lot):

.. image:: /static/polanie-menu.jpg
    :alt: Polanie main menu
    :target: /static/polanie-menu.jpg
    :align: center

Just the corners, zoomed-in for your convenience:

.. image:: /static/polanie-menu-zoom.jpg
    :alt: Polanie main menu corners, zoomed-in
    :align: center

Clear as day. Black lines on the right and at the bottom. And it's not just the
main menu, of course. Almost all graphic assets, including backgrounds, menus etc.
that are almost-screen-sized-but-not-quote, are stored in ``graf.dat`` and you
can see the missing lines in almost all stages of the game (but intro videos are
loaded from separate files, for example, and they have the right resolution).

Now what?
=========

Well, I'm sorry, if it was underwhelming – there's nothing more to it, really.

Now, this is not the most useful piece of knowledge to have. Still, it was a lot of fun to
find it, debug it and confirm it (and, if you're reading it – I hope it was fun to read).
I document almost everything I discover about the game, the `graf.dat documentation lives
here <https://docs.rs/openpol/0.3.0/openpol/grafdat/index.html>`_. I stay hopeful that it
may be of use to someone.

I can't help but wonder: why were the images in ``graf.dat`` 1 pixel short here and there? Was
it an export issue that forced the programmers to code it that way? Was it a bug in the import
code that forced the team to export the assets in a format that would never fill the screen?
Was the bug noticed or did it slip through the cracks? Has anyone else spotted it?

I don't know the answer to any of those questions. We may never learn the truth. I know one
thing though: next time I play Polanie I'll be looking for those two black lines and even
if I can't see them I'll know they're there: the 519 forgotten pixels.
