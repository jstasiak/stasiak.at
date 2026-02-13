===================================
Accessing Scaleway logs with LogCLI
===================================

:date: 2026-02-13
:tags: lune, grafana, loki, logcli, scaleway, cloud

..

    This post was originally published on `Lune Engineering Blog
    <https://eng.lune.co/posts/2026/02/13/accessing-scaleway-logs-with-logcli/>`_.

    `Lune <https://lune.co>`_ kindly allowed me to republish it here.

`Scaleway <https://www.scaleway.com/>`__'s standard way of viewing logs
seems to be via Scaleway-hosted `Grafana <https://grafana.com/>`__. For
example when you go to a container's overview and switch to the Logs tab
you'll see a big "Open Grafana logs dashboard" button.

Now, as much as I like Grafana (I really do), it's not the greatest log
viewing tool under the sun. The limitations become apparent when you
attempt to aggregate logs coming from multiple applications, apply
non-trivial filtering or fetch more than five thousand log events (I'm
not even sure if this is Grafana's limitation or Scaleway's doing).

If you're like me you probably want a CLI tool to access the logs with
all the fancy filtering and the ability to fetch as many logs as you'd
like for later analysis. It's 2026 but CLI tools and text processing are
not going away.

Fortunately it turns out it's all `Loki <https://grafana.com/docs/loki/>`__
under the hood and the logs can be accessed with
`LogCLI <https://grafana.com/docs/loki/latest/query/logcli/>`__.

You'll need two environment variables (these are region-specific and you
need their region to match your applications' region, I don't know if
there's an off-the-shelf multi-region solution):

- ``LOKI_ADDR`` - find it in Scaleway's Cockpit -> Data sources in the
  "Scaleway data sources" at the bottom of the page. It's the "API URL"
  value in the "Scaleway Logs" row.
- ``LOKI_BEARER_TOKEN`` - you'll need to create one in Cockpit ->
  Tokens. It needs the "Query logs" permission and ideally nothing else,
  less risk.

And then (the actual query and the output are specific to our
applications):

.. code:: bash

    > export LOKI_ADDR=...
    > export LOKI_BEARER_TOKEN=...
    > logcli query --limit 1 -o raw \
        '{resource_name=~".*-main-service"} | json | line_format "{{.message}}"' 2> /dev/null \
        | jq
    {
      "endpoint": "auth",
      "level": "info",
      "message": "running auth handler",
      "service": "main",
      "span_id": "s0k5e2h6p28g1",
      "time": "2026-02-13T12:19:17.020Z",
      "trace_id": "nhj7uihovdhp3cl2c03u31cv18"
    }
