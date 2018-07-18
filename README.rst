Dependency Management Toolkit for Google Cloud Python Projects
==============================================================

    Version conflicts between dependencies has been a big issue for GCP Python
    users. The issue typically happens when a user depends on two libraries A
    and B, both of which depend on incompatible versions of library C. This
    can lead to non-deterministic behavior, since only one version of C
    actually gets loaded into the library.

    This repository is providing a toolkit for GCP Python open source projects
    to bootstrap their development infrastructure, enforcing centralized
    dependency management, CI, and release process, thus ensuring compatibility
    across all of our GCP Python open source libraries for our end-users.

|circleci| |pypi|

.. |circleci| image:: https://circleci.com/gh/GoogleCloudPlatform/cloud-opensource-python.svg?style=shield
   :target: https://circleci.com/gh/GoogleCloudPlatform/cloud-opensource-python/tree/master
.. |pypi| image:: https://img.shields.io/pypi/v/compatibility_lib.svg
   :target: https://pypi.org/project/compatibility_lib/

-  `Compatibility Status Dashboard`_

.. _Compatibility Status Dashboard: https://googlecloudplatform.github.io/cloud-opensource-python/

License
-------

Apache 2.0 - See `LICENSE <LICENSE>`__ for more information.

Disclaimer
----------

This is not an official Google product.
