Stub-only Python package naming
###############################

:date: 2025-12-29
:slug: stub-only-python-package-naming
:tags: python

What are stubs in Python? From `Distributing type information
<https://typing.python.org/en/latest/spec/distributing.html>`_:

    Stub files, also called type stubs, provide type information for untyped Python
    packages and modules.

I found myself considering publishing a couple of stub-only Python packages to PyPI
for some Python code that doesn't currently provide any type information on its own.

The thing is I wasn't sure what to name them because I saw some packages following
the ``types-foo`` format (for example:
`types-requests <https://pypi.org/project/types-requests/>`_) while some others were named
like ``foo-stubs`` (for example: `pandas-stubs <https://pypi.org/project/pandas-stubs/>`_).

Actually, let me walk this back a little bit. When I said *packages* I really meant
*distributions* (or *PyPI projects*). What's the difference? In the examples above:

* ``types-requests`` and ``pandas-stubs`` are *distribution* names. You see them on
  PyPI and use them in ``pip install`` calls.
* These distributions install *packages* named ``requests-stubs`` and ``pandas-stubs``,
  respectively, meaning the directories somewhere in the filesystem have these names.

Thankfully the documentation has a relevant `Stub-only Packages section
<https://typing.python.org/en/latest/spec/distributing.html#stub-only-packages>`_ which
resolved my confusion:


    The name of the stub package MUST follow the scheme foopkg-stubs for type stubs for
    the package named foopkg.

    Note the name of the distribution (i.e. the project name on PyPI) containing the package
    MAY be different than the mandated \*-stubs package name. The name of the distribution SHOULD
    NOT be types-\*, since this is conventionally used for stub-only packages provided by typeshed.

Which is pretty convenient because what I need to do in this case is two different
distributions that will provide different (conflicting ones, a subject for another day) types for
the same package. With this new knowledge in mind I imagine it will look something like this:

* A distribution named ``foo-stubs-bar``
* Another distribution named ``foo-stubs-baz``
* Both provide a ``foo-stubs`` package
