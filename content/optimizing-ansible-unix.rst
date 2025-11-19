###########################################################################
 Optimizing rendering of Ansible templates with Vault secrets the Unix way
###########################################################################

:date:
   2021-11-26 18:00

:tags:
   ansible, devops, lune, unix, python, optimization

..

  This post was originally published on `Lune Engineering Blog
  <https://eng.lune.co/posts/2021/11/26/optimizing-ansible-templates-the-unix-way/>`_.

  `Lune <https://lune.co>`_, where I help fighting the climate crisis, kindly allowed
  me to republish it here.


***************
 On being fast
***************

Speed matters.

Not in the *sufficient condition* sort of way (being fast won't automatically make something good) but in a
*necessary condition* sense (being fast is often if not always a prerequisite for being good). Granted,
there's a subtle distinction between being *fast* and being *fast enough* but the general point stands.

As an example: there's a big qualitative difference between a test suite that runs in 50 miliseconds, 5
seconds or 50 seconds (not even mentioning 500 seconds and longer).

The first two kinds can be ran almost anytime you change something, providing near instantaneous feedback.
The longer the time to run the test suite though, the more this quality is lost and the risk of forced
coffee breaks or going on Reddit out of boredom increases.

The faster the feedback the faster one can get back to doing their job. Time is precious. Attention similarly
so.

In a minute you'll see why I'm talking about this.

************
 On Ansible
************

`Ansible <https://www.ansible.com/>`_ is an automation software that lets you install software, manage
configuration, configure networking and, in general, provision machines.

Ansible has been used at Lune extensively since the beginning, to manage a fleet of Virtual Machines on
which Lune's applications used to run and to deploy the applications to the VMs. There's a big deal of
complexity involved in using Ansible, contrary to its official site ironically calling it "Simple IT
Automation" – that's a subject for a separate article though.

For multiple reasons, not the least of which was aforementioned user-facing complexity, recently a migration
to Kubernetes has been performed and Ansible's role has been greatly limited. More specifically, its
responsibilities were as follows: render a bunch of templates using variables stored in `Ansible Vault
<https://docs.ansible.com/ansible/latest/user_guide/vault.html>`_ and store the results in files. We'd then
make `Kubernetes' kubectl apply
<https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#apply>`_ ingest them.

The Ansible playbook looked like this:

.. code-block:: yaml

    ---
    - hosts: localhost
      connection: local
      vars_files:
        - "vars/{{ lookup('env', 'ENV') }}.yml"
        - "vars/{{ lookup('env', 'ENV') }}-secrets.yml"
      tasks:
        - name: Find templates
          find:
            paths: ../kubernetes
            patterns: '*.yml'
          register: kubernetes_templates
        - name: Process a template
          template:
            src: "../kubernetes/{{ item | basename }}"
            dest: "../kubernetes/processed/{{ item | basename }}"
          with_items: "{{ kubernetes_templates.files | map(attribute='path') | list }}"

And we ran the whole thing like so::

    ./${ENV}-ansible-playbook process-kubernetes-templates.yml
    kubectl apply -f kubernetes/processed/

No roles. No remote VMs. No host groups. No inventories. Not much global state. Just the Good Parts
– variables, Ansible Vault and Jinja2 template rendering. Seems simple enough? It does, deceptively so.

*************
 The slowness
*************

The problem became apparent almost immediately – the process was really, *really* slow. How slow? With 27
templates the `ansible-playbook` invocation took around 14 seconds. Since Ansible prints the tasks as they're
executed I could see in real time how slow that was – a log line was produced every half a second, more or
less, so it wasn't just Ansible being slow to start up/decode the Vault, every template rendering had massive
time overhead.

`Performance problems are common in Ansible <https://github.com/ansible/ansible/search?q=slow&type=issues>`_
and I have encountered many of them in my career, but never something that slow while not even contacting any
remote servers – just reading variables from files, rendering templates, storing results in other files.

What made things worse is that debugging this turned out to be so involved (Ansible's codebase is vast and
there are many abstractions and moving pieces, additionally the work is offloaded to subprocesses which
hindered profiling using the tools that I attempted to use).

I'm sure I'd get to the bottom of this given enough time (and I still may) but:

* I'm not sure if the cause of the slowness would be easy enough to fix anyway
* I already had a different solution in mind which had a range of advantages over Ansible (more on that below)

*************************
 Enter specialized tools
*************************

It's commonly accepted that one of the pillars of Unix philosophy is `Do One Thing and Do It Well
<https://en.wikipedia.org/wiki/Unix_philosophy#Do_One_Thing_and_Do_It_Well>`_.

(There are reasonable arguments for and against it and there are definitely some good examples of complex
pieces of software that that work well *because* of integrating many concepts (Blender, Ardour and Unity come
to mind)).

With the above in mind I decided to try switching from Ansible (a large multi-tool solution) to a bunch of
smaller applications. The applications would:

* Decode Ansible Vault
* Merge multiple YAML files together
* Render Jinja2 templates using YAML dictionary with some variables


This is it, really. This is all what Ansible was doing in the Kubernetes case at Lune.

The first task was simple enough, there's the `ansivault CLI tool written in Rust
<https://crates.io/crates/ansivault>`_ (using the `ansible-vault Rust library
<https://crates.io/crates/ansible-vault>`_) that allows us to decode Ansible Vault files (the results are
printed to `standard output <https://en.wikipedia.org/wiki/Standard_streams#Standard_output_(stdout)>`_)::

    ANSIVAULT_KEY_FILE=ansible_vault_password ansivault -a view ansible/vars/${ENV}-secrets.yml

For the latter two tasks I created two custom tools using Python and some libraries:

* ``yaml-merge``

  .. code-block:: python

    #!/usr/bin/env python3
    """Merge multiple YAML files together and dump the result to stdout.

    The input files need to deserialize to dictionaries.

    The merging only happens one level deep (so we don't merge sub-dictionaries,
    if a key appears in a file it'll overwrite the whole content of that key if
    it was present in an earlier file).
    """

    import sys

    import yaml


    def main() -> None:
        result = {}
        for input_file in sys.argv[1:]:
            with open(input_file) as f:
                file_contents = yaml.safe_load(f)
                assert isinstance(file_contents, dict)
                result.update(file_contents)
        print(yaml.dump(result))


    if __name__ == '__main__':
        main()

* ``jinja2-render``

  .. code-block:: python

    #!/usr/bin/env python3
    """Render Jinja2 template(s) using variables loaded from a YAML file."""
    import os.path
    import sys
    from typing import Any, Dict

    import jinja2
    import yaml


    def main() -> None:
        try:
            (variable_file, *input_files, output_directory) = sys.argv[1:]
            if len(input_files) == 0:
                raise ValueError()
        except ValueError:
            print("Usage: jinja2-renderer VARIABLES_FILE TEMPLATE_FILES... OUTPUT_DIRECTORY", file=sys.stderr)
            exit(1)

        with open(variable_file) as f:
            variables = yaml.safe_load(f)
            assert isinstance(variables, dict)

        environment = jinja2.Environment(
            undefined=jinja2.StrictUndefined,
            keep_trailing_newline=True,
            # trim_blocks are disabled by default in Jinja2 itself, but Ansible templating enables it.
            # Let's keep it for now for Ansible compatibility.
            #
            # https://ansiblemaster.wordpress.com/2016/07/29/jinja2-lstrip_blocks-to-manage-indentation/
            trim_blocks=True,
        )

        for input_file in input_files:
            print(input_file)
            with open(input_file) as f:
                template = f.read()
            rendered = render_template(environment, variables, template)
            with open(os.path.join(output_directory, os.path.basename(input_file)), 'w') as f:
                f.write(rendered)
                # Let's make sure we always have newline at the end of file (it's customary in Unix-land).
                if rendered[-1] != '\n':
                    f.write('\n')


    def render_template(environment, variables: Dict[str, Any], text: str) -> str:
        template = environment.from_string(text)
        return template.render(variables)


    if __name__ == '__main__':
        main()

The applications are combined as follows:

.. code-block:: shell

    SECRETS=$(ANSIVAULT_KEY_FILE=ansible_vault_password ansivault -a view ansible/vars/${ENV}-secrets.yml)
    MERGED_VARIABLES=$(yaml-merge ansible/vars/${ENV}.yml <(echo "${SECRETS}"))
    jinja2-render <(echo "${MERGED_VARIABLES}") kubernetes/*.yml kubernetes/processed

(The ``$(...)`` construct captures the standard output of a command as text. The ``<(...)`` construct is
`process substitution <https://en.wikipedia.org/wiki/Process_substitution>`_ which allows capturing the
standard output of a command and making it appear as a file).

The solution is glorious in its simplicity. Each of the building blocks is super simple to debug. There are
explicit intermediate stages that one can go and intercept the data to see if it's ok. Each of the commands
can easily be run in isolation if needed. If something is slow it's easy to see what exactly is the problem.

Does the solution address the main issue (Ansible slowness)? I'll let the numbers speak:

* Ansible: 13.5 seconds
* ``ansivault`` + ``yaml-merge`` + ``jinja2-render``: 0.3 seconds

Additionally, this reduced the size of a Docker image used by the `Continuous Integration
<https://en.wikipedia.org/wiki/Continuous_integration>`_ pipeline by nearly 400 megabytes (yes, Ansible really
has a lot of dependencies). This wasn't the original goal but it's most welcome.

*************************
 Does it matter so much?
*************************

Yes, I will argue that it does. Both from the perspective of a local development experience (when I apply
Kubernetes changes I prefer to have feedback in under a second rather than in 15 seconds) and from the point
of view of the CI pipeline.

With 116 relevant CI job runs last month this results in up to 46.4 fewer gigabytes transferred (there's a
Docker image layer caching employed but it frequently doesn't have the relevant layers) and around 38 minutes
of CPU time saved (116 jobs times 20 seconds saved per
job, 20 seconds is the Ansible-related speedup plus few seconds saved on downloading smaller Docker images).

With more CI job runs in the future the difference will be proportionally higher.

Are the CI savings impressive? Not particularly, not in isolation. But all those inefficiencies add up.
Similarly, all the optimizations and improvements do add up when you have many of them and consistently apply
the performance-aware mindset.

Take this optimization, mix it with `switching from x86 to ARM with lower carbon footprint and no performance
degradation <https://lune.co/post/goodbye-intel-hello-lower-carbon-future>`_, sprinkle a few other improvements
and the results become significant.

**************
 A conclusion
**************

I've been a fan of all things Unix for a long time now. Time and time again I found myself entertained by
what's possible by combining multiple small programs together. This case only solidified that.

The result is a drastically faster, smaller, more maintainable and easy to understand solution. Putting it
together and seeing it work was a joyous experience.

Don't be afraid to write custom code if that's what is necessary to serve your needs well. If something's
slow – make it fast. Embrace the Unix way for fun and profit!
