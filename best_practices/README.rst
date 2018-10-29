Python Package Compatibility Guidelines
=======================================

This document uses terminology (MUST, SHOULD, etc) from `RFC 2119`_.

.. _RFC 2119: https://www.ietf.org/rfc/rfc2119.txt

----------
Background
----------

Incompatibilities between packages published on the `Python Package Index (PyPI)`_
have been a long standing issue. Diamond dependencies are a common problem where
a package or application has dependencies that are, themselves, dependant on
incompatible versions of shared packages.
has been a long standing issue. Diamond dependency (aka dependency hell) is a
common problem that a package’s dependencies depend on different and
incompatible versions of the shared packages.

.. _Python Package Index (PyPI): https://pypi.org/

Incompatibilities between packages can occur when:

- A package makes breaking API changes and doesn't follow `Semantic Versioning`_
- A package has a pinned dependency version which conflicts with other dependencies.
- A package depends on outdated dependencies.
- A package is dependent on deprecated dependencies.

.. _Semantic Versioning: https://semver.org/

This guide is a list of best practices that Python package authors can follow
to help reduce future incompatibilities. Google-sponsored projects are expected
to follow these guidelines but other projects may benefit from them as well.

-----
Tools
-----

    To detect and prevent version incompatibilities between Google Open Source Python
    packages, we provide a set of tooling to ensure we are compatible with
    ourselves. And the tooling can also run checks for any Google owned package that wants to
    know whether it is self-compatible or compatible with a list of other packages.
    Below lists our tooling:

Dependency Compatibility Dashboard
----------------------------------

The `dashboard`_ shows the compatibility status of a list of Google sponsored Open Source
Python packages.

.. _dashboard: https://googlecloudplatform.github.io/cloud-opensource-python/

Badge Server
------------

The badge server runs checks and generates an svg format badge image to show the
status of a given package. Supported usage includes:

- Self compatibility (the package has internally consistent dependencies)
- Google-wise compatibility
- Dependency version status
- One badge for all kinds of checks above

For more details please refer to `here`_.

.. _here: https://github.com/GoogleCloudPlatform/cloud-opensource-python/tree/master/badge_server

----------------------
Python Packaging Rules
----------------------

Package Versioning
------------------

We should use semantic versioning for all Google OSS Python distribution
packages. Semantic versioning requires that given a version number
`MAJOR.MINOR.PATCH`, increment the:

    * MAJOR version when you make incompatible API changes.
    * MINOR version when you add functionality in a backwards-compatible manner.
    * PATCH version when you make backwards-compatible bug fixes.

Requirements:

- `GA(Generally Available)`_ libraries must conform to semantic versioning.
- Non-GA libraries should use major version 0, and be promoted to 1.0 when reaching GA.
- Non-GA libraries could be excluded from semver stability guarantees.
- Dropping support for a Python major version(e.g. Python 2) should result in a major version increment

.. _GA(Generally Available): https://cloud.google.com/terms/launch-stages

Dependencies
------------

**1. Specify dependency version using closed ranges**

- Minor or patch versions shouldn’t be used as an upper bound for 1st party dependencies unless the dependency is not GA.
- Specific versions can be excluded if they are known to be incompatible. e.g. google-cloud-pubsub >= 0.1.1 !=2.0.0 !=2.0.1
- Specific versions may be specified if a package exists as a wrapper around another.

**2. Avoid depending on unstable release version dependencies**

- It’s not recommended to depend on non-GA packages.
- Avoid depending on pre-release, post-release and development release versions.
- GA packages must not depend on non-GA packages.

**3. Version range upper bound should be updated when there is a newer version available as soon as possible.**

- We allow a 30 day grace period for package owners to migrate to support new major version bump of the dependencies.

**4. Minimize dependencies**

- Packages should use Python built-in modules if possible. e.g. logging, unittest

**5. Never vendor dependencies**

Vendoring means having a copy of a specific version of the dependencies and ship it together with the library code.

Release and Support
-------------------

- Major version bumps should be rare
- Minimize the cost for users to go from one major version to another.
- Support every semver-major HEAD of every package that is 1.0+ for at least one year.
- Dropping support for any older version should be semver-major.

---------------
GA Requirements
---------------

The GA requirements are validated using the `github badge`_ service, so the badge
should be green before any GA launch.

- Packages must be self compatible
If package A has dependencies B and C, and they require different versions
of dependency D, package A is not self compatible. Packages that are not internally
compatible will have conflicts with all the rest of the packages in the world.

- Packages must be google-wise compatible
It’s required for any new package owned by Google to be compatible with all the other Google Python packages. So that using any combination of Google Python packages will not cause any conflicts during installation or failures during runtime.

- Packages must support latest version of its dependencies

.. _github badge: https://github.com/GoogleCloudPlatform/cloud-opensource-python/blob/master/badge_server/README.rst
