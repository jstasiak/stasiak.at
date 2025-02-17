Unable to mount root fs? Don't panic
####################################

:date: 2025-02-17
:slug: unable-to-mount-root-fs-dont-panic
:tags: linux

If you're like me you hate it when a server doesn't come back up after a reboot.

The last time this happened to me, a couple of days ago, I was luckily in the physical
vincinity of the machine in question so I was able to just walk to it, plug a monitor
and a keyboard and see what's what. (The machine is an HP device with iLO 4 available
but having tried to use iLO 4 remote console a few times in the past I do everything
I can to avoid it now).

What I saw was a wall of text ending with::

    end Kernel panic - not syncing: VFS: Unable to mount root fs on unknown-block(0,0)

Not something you want to see. A broken kerenel? – I wondered, as I just applied some
updates shortly before the reboot.

A cursory search revealed this `helpful Ask Ubuntu answer by user psusi
<https://askubuntu.com/questions/41930/kernel-panic-not-syncing-vfs-unable-to-mount-root-fs-on-unknown-block0-0/41939#41939>`_:

    You are missing the initramfs for that kernel. Choose another kernel from the
    GRUB menu under Advanced options for Ubuntu and run ``sudo update-initramfs -u -k version``
    to generate the initrd for ``version`` (replace ``version`` with the kernel version string
    such as ``4.15.0-36-generic``) then ``sudo update-grub``.

Now, ignoring the fact that I run Fedora with Dracut, not Ubuntu with initramfs-tools,
that seemed plausible for one reason which I'll reveal in a moment.

I rebooted the server again and this time I paid attention to what happened step by step.
Right before the kernel panic happened GRUB actually logged the following::

    error: ../../grub-core/fs/fshelp.c:257:file
    '/initramfs-6.12.13-200.fc41.x86_64.img' not found.

Another reboot, an older kernel in GRUB selected and all was working well again.

A quick ``ls -lah /boot`` confirmed the initramfs was – indeed – missing.

Fine.

Well, no, not fine, why was it missing?

Right before the reboot I applied a bunch of updates including a new kernel. The initramfs
generation for that new kernel was interrupted – a package meant to be included in the
image was missing and I had to install it).

I *did* run my usual ``dracut -f -v`` after I installed the missing dependency –
I didn't want to end up with a failing-to-boot server after all. That's clearly not it
then?

What I forgot about is that Dracut only (re)generates the initramfs for the currently
running kernel by default - truly a facepalm moment. And since ``-f`` always regenerates
the initramfs, even if it's there, I didn't have any signal there to tell me that
something was off (running ``dracut`` without ``-f`` would tell me the initramfs was
already there and there was nothing to do).

So when the kernel you're running is not the same kernel as the one with broken
(or missing!) initramfs you either need to provide the version explicitly::

    dracut --kver 6.12.13-200.fc41.x86_64

or use the ``--regenerate-all`` option::

    dracut --regenerate-all

Best to make this mistake when the server is in the other room or count on your
out-of-band management solution to work.
