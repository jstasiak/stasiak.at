My usual strace options
#######################

:date: 2025-03-12
:slug: my-usual-strace-options
:tags: debugging, linux

`strace <https://en.wikipedia.org/wiki/Strace>`_ is a useful diagnostic tool that I reach
for from time to time when Things Go Wrong. Yes, there is `eBPF <https://en.wikipedia.org/wiki/EBPF>`__
and such but good ol' strace is still very much alive.

The thing with ``strace`` is it accepts a lot of command-line options and I never quite
remember all of them so this list is a much for me as it is for anyone else:

* ``-p pid`` – attach to a running process with the provided pid
* ``-f`` (short for ``--follow-forks``) – trace child processes/threads
* ``-s strsize`` (short for ``--string-limit=strsize``) – set the maximum size of printed
  strings to ``strsize``
* ``-tt`` (short for ``--absolute-timestamps=precision:us``) – prefix each line with
  a microsecond-precision system timestamp
* ``-T`` (short for ``--syscall-times``) – show duration of system calls in microseconds
  (the unit is configurable)
* ``-x`` (short for ``--strings-in-hex=non-ascii``) – print non-ASCII strings in hexadecimal
  format
* ``-yy`` (short for ``--decode-fds=all``) – show all kinds of useful information attached
  to file descriptors, from ``man strace``:

    protocol-specific information associated with socket file descriptors, block/character
    device number associated with device file descriptors, and PIDs associated with pidfd
    file descriptors

I don't think I forgot anything here. If I did I'll come back and update this list.

Putting that all together we get something like (not all the options have visible effect
in this sample)::

    > sudo strace -p 2561 -f -s 128 -tt -T -x -yy
    strace: Process 2561 attached with 4 threads
    [pid  2560] 00:51:31.316265 restart_syscall(<... resuming interrupted restart_syscall ...> <unfinished ...>
    [pid  2563] 00:51:31.316337 restart_syscall(<... resuming interrupted restart_syscall ...> <unfinished ...>
    [pid  2562] 00:51:31.316362 futex(0x564911906a20, FUTEX_WAIT_PRIVATE, 1, NULL <unfinished ...>
    [pid  2561] 00:51:31.316409 restart_syscall(<... resuming interrupted poll ...>) = 0 <1.378133>
    [pid  2561] 00:51:32.694712 inotify_add_watch(14<anon_inode:inotify>, "/etc/NetworkManager/VPN", IN_MODIFY|IN_ATTRIB|IN_CLOSE_WRITE|IN_MOVED_FROM|IN_MOVED_TO|IN_CREATE|IN_DELETE|IN_DELETE_SELF|IN_MOVE_SELF|IN_UNMOUNT|IN_ONLYDIR) = -1 ENOENT (No such file or directory) <0.000100>
    [pid  2561] 00:51:32.695095 poll([{fd=4<{eventfd-count=0, eventfd-id=7, eventfd-semaphore=0}>, events=POLLIN}, {fd=14<anon_inode:inotify>, events=POLLIN}], 2, 3999^Cstrace: Process 2563 detached
    strace: Process 2562 detached
    strace: Process 2560 detached
    strace: Process 2561 detached
    <detached ...>

There is a lot of other options for Special Occasions, like string formatting, syscall filtering
etc. – ``man strace`` to the rescue when that's needed.
