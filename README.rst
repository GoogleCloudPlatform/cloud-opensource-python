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

.. csv-table::
   :header: "CHECK_TYPE", "RESULT"
   :widths: 20, 30

   "Self Compatibility", |self_compatibility|

.. |self_compatibility| image:: http://35.226.8.89/self_compatibility_badge/image?package=compatibility_lib
   :target: http://35.226.8.89/self_compatibility_badge/target?package=compatibility_lib

Development Workflow (Linux)
---------------------------------

Set Up Python Environment

https://cloud.google.com/python/setup


Install py 3.6 (may not be included in previous step)

.. code-block:: bash

    sudo apt install python3.6


Clone the cloud-opensource-python project and cd to project

.. code-block:: bash

    git clone git@github.com:GoogleCloudPlatform/cloud-opensource-python.git
    cd cloud-opensource-python


Fork project and configure git remote settings

.. code-block:: bash

    git remote add upstream git@github.com:GoogleCloudPlatform/cloud-opensource-python.git
    git config --global user.email "email@example.com"


Install tox, create a virtualenv, and source

.. code-block:: bash

    pip install tox
    tox -e py36
    source .tox/py36/bin/activate

Build compatibility_lib library from source and install

.. code-block:: bash

    python compatibility_lib/setup.py bdist_wheel
    pip install compatibility_lib/dist/*

Install Nox for testing

.. code-block:: bash

    pip install nox-automation

Install gcloud SDK and initialize

.. code-block:: bash

    curl https://sdk.cloud.google.com | bash
    gcloud init

Install google-cloud-bigquery

.. code-block:: bash

    pip install google-cloud-bigquery

Create new service account key (**do this on the workstation**)

- in chrome browser, navigate to pantheon/

- menu > IAM & admin > Service accounts

- under bigquery-admin, actions > create new key 

Set GOOGLE_APPLICATION_CREDENTIALS

.. code-block:: bash
    
    export GOOGLE_APPLICATION_CREDENTIALS=”path/to/service/key.json”

Test credentials within python interpreter (no errors means it’s working)

.. code-block:: python
    
    from google.cloud import bigquery
    bigquery.client.Client()

Run tests:

.. code-block:: bash

    nox -s unit     # unit tests
    nox -s lint     # linter
    nox -s system   # system tests
    nox -l          # see available options
    nox             # run everything


License
-------

Apache 2.0 - See `LICENSE <LICENSE>`__ for more information.

Disclaimer
----------

This is not an official Google product.
