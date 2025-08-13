================================
Prewarming restored RDS instance
================================

:date: 2025-08-13
:tags: aws, postgres, rds

..

    This post was originally published on `Lune Engineering Blog
    <https://eng.lune.co/posts/2025/08/11/prewarming-restored-rds-instance/>`_.

    `Lune <https://lune.co>`_ graciously allowed me to republish it here.


Say you just restored an RDS instance from a snapshot, the instance is
up, your applications use the new DB and you're ready to call it a day.

Not so fast. Isn't it interesting that your DB multi-hundred-GiB DB was
restored from snapshot in something like ten minutes? It should be.

The `"Restoring to a DB instance" AWS user
guide <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_RestoreFromSnapshot.html>`__
sheds some light on this:

    You can use the restored DB instance as soon as its status is
    available. The DB instance continues to load data in the background.
    This is known as lazy loading.

    If you access data that hasn't been loaded yet, the DB instance
    immediately downloads the requested data from Amazon S3, and then
    continues loading the rest of the data in the background.

So this is nice as your DB is available quickly for the price of some
queries being randomly slower than others depending on the data they
touch. It gets worse: if a query is slow because it has to download some
data from S3 it won't be as slow when you run it again to reproduce the
problem (primarily because of the data being). already there but there
are other reasons like various caches being warm).

The same guide recommends:

    To help mitigate the effects of lazy loading on tables to which you
    require quick access, you can perform operations that involve
    full-table scans, such as ``SELECT *``. This allows Amazon RDS to
    download all of the backed-up table data from S3.

Armed with this knowledge and prepared to prefetch the relevant data we
went through a production Postgres instance restoration procedure
recently. As the prefetching queries (limited to the most important
tables) ran we observed some production queries to take abnormally long
time to finish (high tens of seconds instread of single seconds).

We expected that but also figured the slowness would go away once the
prefetching finished. What was surprising is that the slowness
persisted.

At first I thought the way I prefetched the data using psql missed
something (missed a table or missed the fact that the psql process was
killed or something). I wrote some more structured Python code that we
ultimately open-sourced as
`prewarmgres <https://github.com/lune-climate/prewarmgres>`__ that we
then used to prefetch *everything* (insert the Gary Oldman GIF here).

Alas, the problem was still there.

Then I thought "all right, my prefetching just queried all data but it
didn't really use the indices to do that so maybe the indices are also
lazily-loaded somehow or otherwise became stale in some way"? I didn't
have any other idea and there is a distinct lack of information about
this on the Internet so I figured why not.

I applied a bunch of targeted ``REINDEX TABLE CONCURRENTLY X;``
reindexing queries and the issue went away immediately. (Note:
``CONCURRENTLY`` allows concurrent writes to the table to continue but
it's Postgres-specific and it comes with some downsides, consult `the
REINDEX documentation <https://www.postgresql.org/docs/current/sql-reindex.html>`__
for details.)

I know what you may be thinking, "but the user guide says the DB
continues loading the rest of the data in the background so that's what
happened and your reindexing is a red herring". I doubt that because the
amount of time that passed since the DB restoration was much too long
for any background loading to continue by the time the problem was
ultimately resolved, although doubts is all I have here and I won't say
the suggestion is definitely incorrect.

Was it actually related to restoring from a snapshot and all that
lazy-loading or was it more of a Postgres-specific issue, an index
inefficiency of some sort? Was the inefficiency triggered by the
recovery procedure or was it a conincidence? I don't know, this process
looks like a large black box to me. If there is a way to figure this out
using the AWS logs or perhaps the RDS Performance Insights please let me
know, I'd like to know about it.
