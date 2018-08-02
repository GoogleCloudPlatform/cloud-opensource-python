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

.. |circleci| image:: https://circleci.com/gh/GoogleCloudPlatform/cloud-opensource-python/tree/master.svg?style=svg&circle-token=edd37af38ff6d303b11cd0620890537168144137
    :target: https://circleci.com/gh/GoogleCloudPlatform/cloud-opensource-python/tree/master
.. |pypi| image:: https://img.shields.io/pypi/v/compatibility_lib.svg
   :target: https://pypi.org/project/compatibility_lib/

-  `Compatibility Status Dashboard`_

.. _Compatibility Status Dashboard: https://googlecloudplatform.github.io/cloud-opensource-python/

-  Compatibility check results

CHECK_TYPE    |RESULT
Self Compatibility  |  |self_compatibility|

.. |self_compatibility| image:: http://35.226.8.89/self_compatibility_badge/image?package=compatibility_lib
   :target: http://35.226.8.89/self_compatibility_badge/target?package=compatibility_lib

License
-------

Apache 2.0 - See `LICENSE <LICENSE>`__ for more information.

Disclaimer
----------

This is not an official Google product.
