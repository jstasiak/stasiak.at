What's next for Python dependency injection and Injector?
#########################################################

:date: 2020-02-03 17:30
:tags: python, dependency injection, injector, programming

Some stuff out of the way
=========================

Disclaimer: I'm a maintainer of `Injector <https://github.com/alecthomas/injector>`_, so I'm naturally
gonna be biased. Keep that in mind.

If you don't know what dependency injection or Injector are: dependency injection is (to a degree) a fancy
way of saying "don't use global state, provide dependencies to the code requiring them", and Injector is a
Python dependency injection framework (a library simplifying your code using dependency injection, making
it more manageable and reducing boilerplate). If you want to know more go watch this `approachable "Don't
Look For Things!" talk by Miško Hevery <https://www.youtube.com/watch?v=RlfLCWKxHJ0>`_ but this post is
not really meant to introduce you to those concepts.

The goal of this post is not to convince you about the benefits of using a dependency injection framework
or dependency injection in general – this is a wide topic on which a lot has been said already (really,
watch the talk linked above).

This post is meant for people using dependency injection in Python and, possibly, using Injector.  I'll
provide a brief summary of the current state of affairs and speculate about the future.

If you're using dependency injection but you're either not using any framework or using another framework
I urge you to try Injector. It's developed to be simple, flexible, lightweight, not get in your way, not
force you to inherit your business logic classes from anything, not take over normal Python mechanisms,
generate as little magic and surprising behavior as possible and interact gracefully with type hints
and static type checkers.

Check it out. There are some publications on the Internet that describe working with Injector and its
sister project, `Flask-Injector, which adds Injector support to Flask
<https://github.com/alecthomas/flask_injector>`_. In no particular arrangement:

* `Python Dependency Injection with flask-injector by Julie Perilla Garcia
  <https://levelup.gitconnected.com/python-dependency-injection-with-flask-injector-50773d451a32>`_
* `Building Microservices with Python, Part I by Sergio Sola
  <https://medium.com/@ssola/building-microservices-with-python-part-i-5240a8dcc2fb>`_
* `Elegant Flask API Development Part 1: Working with Flask-Injector by Christopher Samiullah
  <https://christophergs.github.io/python/2018/09/25/elegant-flask-apis-pt-1/>`_
* `Dependency Injection in Python: The Java Guy's Perspective by Preslav Rachev
  <https://preslav.me/2018/12/20/dependency-injection-in-python/>`_
* `Type annotations in dependency injection by Antoni Piotr Oleksicki
  <https://tech.webinterpret.com/type-annotations-in-dependecy-injection/>`_

Now... In order to speculate about the future we need to talk about the past first.

The past
========

When I first learned about Injector, in November 2012, the project (version 0.4.3) still supported
Python 2 and the way to declare dependencies was different than it is today (exampled adapted from
`the README from that time
<https://github.com/alecthomas/injector/tree/ee44d60a680a1cb8df1fe392ea1095746509aa93>`_):

.. code-block:: python

    class RequestHandler(object):
        @inject(db=sqlite3.Connection)
        def __init__(self, db):
            self._db = db

There are two annoyances connected to that, one obvious and one not. The first is the fact that you
had to declare parameters twice: list them first in the ``@inject()`` call and then actually declare
a method parameter. The second issue is more subtle – the ``@inject()`` decorator actually substituted
the decorated method with a wrapper method that actually depended on a special ``__injector__``
attribute of the class instance being set to an Injector instance *before* the now-wrapped ``__init__``
was called. `Things broke
<https://github.com/alecthomas/injector/commit/b7f6fc7c9e86e63230ad776b34cd4f7d2482fae9>`_
when you used ``__slots__`` without mentioning ``__injector__`` in there.
Also the wrapper returned by ``@inject()`` required keyword arguments to be used with injectable
parameters, so this would work (if you wanted to manually create an instance of ``RequestHandler``):

.. code-block:: python

    RequestHandler(db=some_dummy_connection)

And this wouldn't (with an obscure error):

.. code-block:: python

    RequestHandler(some_dummy_connection)

But, although imperfect, the old `@inject()` way worked well enough.

Then, on August 9, 2013 `Alec Thomas, the Injector's creator <https://github.com/alecthomas>`_, added
`support for using Python 3 parameter annotations for declaring dependencies 
<https://github.com/alecthomas/injector/commit/7c1aa98aeaab405c2d5a7f9c4ce5926766ec684b>`_ which was
released as part of Injector 0.7.5. You could do this now on Python 3, which was *big*:

.. code-block:: python

    class RequestHandler(object):
        def __init__(self, db: sqlite3.Connection):
            self._db = db

Things stopped changing for a while. There was an experiment with decorating whole classes
with @inject() and automatically generating constructors to reduce repetition, but `I removed it
on October 17, 2016
<https://github.com/alecthomas/injector/commit/25f2455d926a721ca6087f6ec2acfdc85d1e01aa>`_ (change
released in 0.11.0).

The more recent past
====================

The Python 3-only way to declare dependencies introduced in 2013 got slightly improved –
``@inject`` was made to `optionally be a direct decorator (no parameters needed) in combination
with Python 3 annotations
<https://github.com/alecthomas/injector/commit/a1a9164539cfaf880612993d79298d73a8abd09f>`_. This
added an explicit marker in the code that informed a programmer, that a particular constructor
expected injectable dependencies. Later, when for Python 2 and declaring dependencies using
`@inject(name=type)` was removed (I'm not linking to specific commits here – there's a lot of them
and they're not that interesting), we could simplify things a lot: ``@inject`` no longer returns
wrappers (it annotates the decorated function /or class/ in place with lightweight markers), doesn't
mess with calling conventions (if you want to create an instance of a class with injectable
constructor parameters you can do it any way Python itself supports) and doesn't require Injector
instance to be (temporarily) saved as an attribute in the instance of the class being constructed
(``__slots__`` users rejoice). This gave us:

.. code-block:: python

    class RequestHandler:
        @inject
        def __init__(self, db: sqlite3.Connection):
            self._db = db

One small problem remained though (well, possibly more than that, but one that we know about):
specifying noninjectable arguments for `assisted injection
<https://injector.readthedocs.io/en/latest/terminology.html#assisted-injection>`_. While not
strictly necessary it's great for documentation purposes to explicitly declare which
arguments are *not* supposed to be provided by Injector. The official way to do it was, until
recently, to use the `noninjectable() decorator
<https://injector.readthedocs.io/en/latest/api.html#injector.noninjectable>`_, like this:

.. code-block:: python

    class UserUpdater:
        @inject
        @noninjectable('user')
        def __init__(self, db: DBConnection, user: User) -> None:
            self.db = db
            self.user = user

Similarly to the old ``@inject(parameter=type)`` mechanism this has the downside of having
to repeat oneself, but it's the best we could do until late 2019.

Enter "Flexible function and variable annotations " AKA PEP 593
===============================================================

There's been `some talk about mixing type and non-type information in type hints in a way that
doesn't break type safety <https://github.com/python/typing/issues/482>`_ in typing-related circles,
but it wasn't until `Till Varoquaux <https://github.com/till-varoquaux>`_ created a `concrete proposal
on December 13, 2018 <https://github.com/python/typing/issues/600>`_ that something finally started
happening.

The `proposal has been sent to python-ideas in January, 2019
<https://mail.python.org/pipermail/python-ideas/2019-January/054908.html>`_ and `a PEP has been 
forged in April and May <https://github.com/python/peps/pull/1014>`_. After `some discussion on
the typing-sig mailing list
<https://mail.python.org/archives/list/typing-sig@python.org/thread/CZ7N3M3PGKHUY63RWWSPTICVOAVYI73D/>`_
the PEP `has been accepted by Guido van Rossum in November <https://github.com/python/peps/pull/1225>`_.
You can find `the authoritative, rendered version here <https://www.python.org/dev/peps/pep-0593/>`_.

In the meantime `support for Annotated (the main part of PEP 593) has been added to typing_extensions
<https://github.com/python/typing/pull/632>`_ (version 3.7.4) and to `mypy
<https://github.com/python/mypy/issues/7021>`_ (version 0.750). Those made it possible to experiment
with the implementation from very early on (before the PEP acceptance) until today (the upcoming Python
version, 3.9, is supposed to include the PEP, but it's not yet merged, and one needs to use
``typing_extensions`` anyway on Python version pre-3.9).

The present
===========

I jumped on this opportunity rather quickly with `experimental API using Annotated in Injector
<https://github.com/alecthomas/injector/commit/d50e581734d6673ab0a2d9de7ccf09c0ad623a91>`_. The core is
rather simple:

.. code-block:: python

    InjectT = TypeVar('InjectT')
    Inject = Annotated[InjectT, _inject_marker]
    # (...)
    NoInject = Annotated[InjectT, _noinject_marker]

Now, instead of

.. code-block:: python

    class UserUpdater:
        @inject
        @noninjectable('user')
        def __init__(self, db: DBConnection, user: User) -> None:
            # ...

we can write

.. code-block:: python

    class UserUpdater:
        @inject
        def __init__(self, db: DBConnection, user: NoInject[User]) -> None:
            # ...

or even

.. code-block:: python

    class UserUpdater:
        def __init__(self, db: Inject[DBConnection], user: User) -> None:
            # ...

The interactions between
`@inject <https://injector.readthedocs.io/en/latest/api.html#injector.inject>`_,
`@noninjectable() <https://injector.readthedocs.io/en/latest/api.html#injector.noninjectable>`_,
`Inject <https://injector.readthedocs.io/en/latest/api.html#injector.Inject>`_ and
`NoInject <https://injector.readthedocs.io/en/latest/api.html#injector.NoInject>`_ are
`established as part of the get_bindings() function documentation
<https://injector.readthedocs.io/en/latest/api.html#injector.get_bindings>`_.

So, in the end, this is the current state – we have ``@inject`` that doesn't require repeating
parameter names, we have ``NoInject`` to mark noninjectable parameters, also without reiterating
information unnecessarily and we have ``Inject`` to complement them.

The future
==========

I don't actually expect much to change at this point.

I foresee ``noninjectable`` will be deprecated and fully replaced by ``NoInject`` once Injector
drops support for Python 3.5 and 3.6 (the current implementation requires Python 3.7 or newer
to work and it's not trivial to backport), but that's about it.

The current API is as simple as it's reasonably possible but not simpler. Interactions with
static type checkers are more or less as graceful as they can be without providing them with
Injector-specific plugins (probably not worth the effort). All in all the project is not
changing much not because it's stagnating, but because there aren't many reasons for a change.
It's stable and it's working.

One could wonder if something like `JSR-330 Dependency Injection standard for Java
<https://javax-inject.github.io/javax-inject/>`_ could happen for Python so that some of the
dependency injection markers could be standardized, but I doubt it. For one, as far as I know
dependency injection is much popular in Java than in Python. Secondly, seeing how most of the
other Python dependency injection frameworks have significantly different approaches to doing
things I don't believe we could find much common ground here and trying to standardize things
would not be particularly beneficial. I may be wrong, of course.

If a game-changing PEP (like PEP 593) is accepted in the future, Injector will react, but
for now this is it.
