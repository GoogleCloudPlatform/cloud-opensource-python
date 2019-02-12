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

|circleci| |pypi| |package_details| |github_head|

.. |circleci| image:: https://circleci.com/gh/GoogleCloudPlatform/cloud-opensource-python/tree/master.svg?style=svg&circle-token=edd37af38ff6d303b11cd0620890537168144137
   :target: https://circleci.com/gh/GoogleCloudPlatform/cloud-opensource-python/tree/master
.. |pypi| image:: https://img.shields.io/pypi/v/compatibility-lib.svg
   :target: https://pypi.org/project/compatibility-lib/
.. |package_details| image:: https://python-compatibility-tools.appspot.com/one_badge_image?package=compatibility-lib
   :target: https://python-compatibility-tools.appspot.com/one_badge_target?package=compatibility-lib
.. |github_head| image:: https://python-compatibility-tools.appspot.com/one_badge_image?package=git%2Bgit://github.com/GoogleCloudPlatform/cloud-opensource-python.git%23subdirectory=compatibility_lib&force_run_check=1
   :target: https://python-compatibility-tools.appspot.com/one_badge_target?package=git%2Bgit://github.com/GoogleCloudPlatform/cloud-opensource-python.git%23subdirectory=compatibility_lib

-----------------
Compatibility Lib
-----------------

`Compatibility Lib`_ is a library to get compatibility status and dependency information of Python packages.
It contains three tools: compatibility checker, outdated dependency highlighter and deprecated dependency finder.
And it also provides utilities to query data from the BigQuery tables (external user will need to set up tables
with the same schema that this library is using).

.. _Compatibility Lib: https://pypi.org/project/compatibility-lib/

Installation:

.. code-block:: bash

    pip install compatibility-lib


Compatibility Checker
---------------------

Compatibility checker gets the compatibility data by sending requests to the Compatibility Server endpoint,
or by querying the BigQuery table (if the given package is listed in our configs, which are pre-computed).

Usage like below,

.. code-block:: python

    import itertools
    from compatibility_lib import compatibility_checker

    packages = ['package1', 'package2', 'package3']
    package_pairs = itertools.combinations(packages, 2)
    checker = compatibility_checker.CompatibilityChecker()

    # Get self compatibility data
    checker.get_self_compatibility(python_version='3', packages=packages)

    # Get pairwise compatibility data
    checker.get_pairwise_compatibility(
        python_version='3', pkg_sets=package_pairs)

Outdated Dependency Highlighter
-------------------------------

Outdated Dependency Highlighter finds out the outdated dependencies of a Python package, and determines
the priority of updating the dependency version based on a set of criteria below:

- Mark “High Priority” if dependencies have widely adopted major release. (e.g 1.0.0 -> 2.0.0)
- Mark “High Priority” if a new version has been available for more than 6 months.
- Mark “High Priority” if dependencies are 3 or more sub-versions behind the newest one. (e.g 1.0.0 -> 1.3.0)
- Mark “Low Priority” for other dependency updates.

Usage:

.. code-block:: python

    from compatibility_lib import dependency_highlighter

    packages = ['package1', 'package2', 'package3']
    highlighter = dependency_highlighter.DependencyHighlighter()
    highlighter.check_packages(packages)

Deprecated Dependency Finder
----------------------------

Deprecated Dependency Finder can find out the deprecated dependencies that a Python package
depends on.

Usage:

.. code-block:: python

    from compatibility_lib import deprecated_dep_finder

    packages = ['package1', 'package2', 'package3']
    finder = deprecated_dep_finder.DeprecatedDepFinder()
    for res in finder.get_deprecated_deps(packages):
        print(res)

------------
Badge Server
------------

Displaying the compatibility status for your package as a Github Badge.

Types of badges
---------------

1. Self Compatibility
2. Compatibility with Google OSS Python packages
3. Dependency version status

Usage
-----

See the usage `here`_.

.. _here: https://github.com/GoogleCloudPlatform/cloud-opensource-python/blob/master/badge_server/README.rst

------------
Contributing
------------

Set up environment
------------------

- Set Up Python Environment

https://cloud.google.com/python/setup


- Install py 3.6 (may not be included in previous step)

.. code-block:: bash

    sudo apt install python3.6


- Clone the cloud-opensource-python project and cd to project

.. code-block:: bash

    git clone git@github.com:GoogleCloudPlatform/cloud-opensource-python.git
    cd cloud-opensource-python


- Fork project and configure git remote settings

.. code-block:: bash

    git remote add upstream git@github.com:GoogleCloudPlatform/cloud-opensource-python.git
    git config --global user.email "email@example.com"


- Create a virtualenv, and source

.. code-block:: bash

    tox -e py36
    source .tox/py36/bin/activate

- Install gcloud SDK and initialize

.. code-block:: bash

    curl https://sdk.cloud.google.com | bash
    gcloud init

Set up credentials
------------------

- Create new service account key

1.  In your browser, navigate to Cloud Console

2. menu > IAM & admin > Service accounts

3. under bigquery-admin, actions > create new key

- Set GOOGLE_APPLICATION_CREDENTIALS

.. code-block:: bash
    
    export GOOGLE_APPLICATION_CREDENTIALS=”path/to/service/key.json”

Contributing to compatibility_lib
---------------------------------

- Build compatibility_lib library from source and install

.. code-block:: bash

    python compatibility_lib/setup.py bdist_wheel
    pip install compatibility_lib/dist/*

-------
Testing
-------

We use nox test suite for running tests.

- Install Nox for testing

.. code-block:: bash

    pip install nox-automation

- Run the tests

.. code-block:: bash

    nox -s unit     # unit tests
    nox -s lint     # linter
    nox -s system   # system tests
    nox -l          # see available options
    nox             # run everything

-------
License
-------

Apache 2.0 - See `LICENSE <LICENSE>`__ for more information.

----------
Disclaimer
----------

This is not an official Google product.
