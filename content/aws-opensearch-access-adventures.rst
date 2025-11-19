================================
AWS OpenSearch access adventures
================================

:date: 2025-11-20
:tags: aws, opensearch, terraform

..

    This post was originally published on `Lune Engineering Blog
    <https://eng.lune.co/posts/2025/11/18/aws-opensearch-access-adventures/>`_
    on 2025-11-18.

    `Lune <https://lune.co>`_ graciously allowed me to republish it here.

I had to set up an `OpenSearch (née
Elasticsearch) <https://en.wikipedia.org/wiki/OpenSearch_(software)>`__
cluster on AWS recently and I was not entertained to find out there were
actually two distinct access failure modes.

Say as a `Terraform <https://developer.hashicorp.com/terraform>`__ user
you set this up with
`aws_opensearch_domain <https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/opensearch_domain>`__
and your configuration looks like this:

.. code:: terraform

   resource "aws_opensearch_domain" "jaeger" {
     # ...
     access_policies = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Action    = "es:*"
           Principal = "*"
           Effect    = "Allow"
           Resource  = "arn:aws:es:eu-west-1:*:domain/jaeger/*"
         }
       ]
     })
   }

You need to be really careful and make sure that the
`ARN <https://docs.aws.amazon.com/IAM/latest/UserGuide/reference-arns.html>`__
pattern is correct.

The infrastructure relevant to this story operates in ``eu-west-1`` and
initially we had a region mismatch by mistake: ``eu-central-1`` instead
of ``eu-west-1``. That resulted in all accesses to the cluster being
rejected with HTTP 403 Forbidden and body reading:

::

   {"Message":"User: anonymous is not authorized to perform: es:ESHttpGet because no resource-based policy allows the es:ESHttpGet action"}

Ok, good, that's an *authorization* problem (AWS knows who we are, we're
just not allowed to access what we want) change the ARN, fixed.

Then there's the problem of supplying the right credentials if
OpenSearch is configured to require them, for example using the internal
user database and a master user (it may not be the best practice, I
truly don't know):

.. code:: terraform

   advanced_security_options {
     enabled                        = true
     internal_user_database_enabled = true
     master_user_options {
       # Note: not our actual production credentials
       master_user_name     = "AzureDiamond"
       master_user_password = "hunter2"
     }
   }

If one fails to provide the credentials when trying to contact such
cluster one will observe HTTP 401 Unauthorized responses with the
following body, indicating an *authentication* problem in OpenSearch
once AWS already allowed us to contact it:

::

   Unauthorized

I'm sharing this because maybe it will help someone identifying which of
these problems are they actually facing:

- HTTP 403 -> broken access policy, AWS won't let us contact the cluster
  in the first place.
- HTTP 401 -> the access policy is fine and we contacted the cluster
  successfully but the credentials are wrong or missing and the cluster
  refused to cooperate.

But wait, there's more.

Say you set up a cluster with ``advanced_security_options`` and that
internal user database and authentication required and it worked fine
for a week but then your application started seeing these HTTP 401
responses again.

What gives?

From what I gathered the OpenSearch credentials are correctly set up by
Terraform when a cluster is created but then AWS may arbitrarily
recreate the cluster behind the scenes (because of upgrades or maybe the
underlying infrastructure changes etc.) in which case the internal
credentials DB is lost.

I haven't been able to find conclusive information about this but there
are some clues:

- https://stackoverflow.com/questions/79450830/aws-opensearch-service-master-user-gets-invalid-from-time-to-time
- https://forum.opensearch.org/t/aws-opensearch-instance-loses-role-mappings/24008

And then there's also the fact that when I created a new user manually
(``master2``) I was able to query the cluster users and only got that
new user in response:

::

   > curl -H "Authorization: Basic .......=" \
       https://vpc-....eu-west-1.es.amazonaws.com/_plugins/_security/api/rolesmapping/all_access | jq
   {
     "all_access": {
     "hosts": [],
     "users": [
       "master2"
     ],
     "reserved": false,
     "hidden": false,
     "backend_roles": [],
     "and_backend_roles": []
     }
   }

Even if Terraform was then able to recreate the credentials DB (which I
don't think it can if I remember correctly but don't quote me on that)
it would still require an intervention to get the infrastructure in the
right shape.

I offer no solutions to this "losing the credentials DB" problem as I'm
unaware of any, just know it's something that can randomly happen to you
if you use it.
