Python Dependency Groups
########################

:date: 2025-02-24
:slug: python-dependency-groups
:tags: python

While modernizing the `ifaddr <https://github.com/ifaddr/ifaddr>`_ CI setup (it's funny
how many things you forget when you stop touching a piece of software for a year)
I dicovered a relatively new feature of the Python packaging ecosystem called
Dependency Groups.

`PEP 735 – Dependency Groups in pyproject.toml <https://peps.python.org/pep-0735/>`_
introduced this mechanism while the living version of the specification can be found in
`Python Packaging User Guide <https://packaging.python.org/en/latest/specifications/dependency-groups/>`_,
which I'll allow myself to quote:

    This specification defines Dependency Groups, a mechanism for storing package
    requirements in pyproject.toml files such that they are not included in project
    metadata when it is built.

    Dependency Groups are suitable for internal development use-cases like linting and
    testing, as well as for projects which are not built for distribution, like
    collections of related scripts.

This sounds useful for use cases like managing the dependencies necessary to build
the documentation of a project (I'd not want to distribute the necessary versions in the
package metadata to the end-users).

Documentation dependencies specifically I had problems with in the past, most of the
time I had separate ``requirements.in`` or ``requirements.txt`` files just for the
documentation and if you ever used these you're probably aware of their defficiencies.

Turns out `uv <https://docs.astral.sh/uv/>`_, of which I've become a happy and frequent user recently,
`supports dependency groups <https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-groups>`_
so I couldn't be happier.

This is how `ifaddr's dependency groups
<https://github.com/ifaddr/ifaddr/blob/8193d730edbf4e0bc57b660d54c9bf502cce1a7f/pyproject.toml#L37>`_
look like right now:

.. code-block:: toml

    [dependency-groups]
    dev = [
        "mypy ; implementation_name == 'cpython'",
        "netifaces ; sys_platform != 'win32'",
        "pytest",
        "pytest-cov",
        "ruff>=0.9.6",
    ]
    docs = [
        "furo>=2024.8.6",
        "sphinx>=7.4.7",
    ]
    devdocs = [
        "sphinx-autobuild",
        {include-group = "docs"},
    ]

You'll notice dependency groups can include each other – pretty neat and DRY-y.

Now, the mechanism is rather fresh (`PEP 735 has only been acceptd on 2024-10-10
<https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/39233/312>`_)
so the tooling support is pretty spotty.

`A patch implementing dependency groups support in pip <https://github.com/pypa/pip/pull/13065>`_
has only been merged two days ago as (2025-02-22, I'm writing this on the 24th).

While `there is not first-class support on ReadTheDocs currently
<https://github.com/readthedocs/readthedocs.org/issues/11766>`_
it's quite easy to come up with a working solution. Take the configuration sample from
`the RTD documentation <https://docs.readthedocs.com/platform/latest/build-customization.html#install-dependencies-with-uv>`_,
adjust a little and you get `this <https://github.com/ifaddr/ifaddr/blob/8193d730edbf4e0bc57b660d54c9bf502cce1a7f/.readthedocs.yaml>`_:

.. code-block:: yaml

    version: 2

    build:
    os: ubuntu-24.04
    tools:
        python: "3.13"
    jobs:
        create_environment:
            - asdf plugin add uv
            - asdf install uv latest
            - asdf global uv latest
            - uv venv
        install:
            - uv sync --group docs
        build:
            html:
                - uv run sphinx-build -T -b html docs $READTHEDOCS_OUTPUT/html

All in all it was a cherry on top of my modernization work.

Check this feature out, it may make your developer experience at least a bit
better – I know it made mine.
