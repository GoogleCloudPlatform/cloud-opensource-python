Badge Server
============

.. image:: http://35.226.8.89/one_badge_image?package=tensorflow

Displaying the compatibility status for your package as a Github Badge.

Types of badges
---------------

1. Self Compatibility
2. Compatibility with Google OSS Python packages
3. Dependency version status

Usage
-----

What to Check
~~~~~~~~~~~~~

- Latest released version on PyPI


.. code-block::

    package=[name_on_pypi]

- Github head version

.. code-block::

    package=git%2Bgit://github.com/[your_repo_name].git%23subdirectory=[subdirectory_containing_setup_py_file]

How to Check
~~~~~~~~~~~~

- One badge

Add this line to your README file on Github:

.. code-block::

    .. |package_details_example| image:: http://35.226.8.89/one_badge_image?package=compatibility_lib
       :target: http://35.226.8.89/one_badge_target?package=compatibility_lib

And the badge for package details will show up like below:

.. image:: https://user-images.githubusercontent.com/12888824/46687056-c1255f00-cbae-11e8-9066-91d62cb120e0.png

- Multiple badges

Adding the link of the badge image and badge target to your README file on
Github:

.. code-block::

   .. csv-table::
      :header: "CHECK_TYPE", "RESULT"
      :widths: 20, 30

      "Self Compatibility", |self_compatibility|
      "Google Compatibility", |google_compatibility|
      "Dependency Version Status", |dependency_version_status|

   .. |self_compatibility| image:: http://35.226.8.89/self_compatibility_badge_image?package=compatibility_lib
      :target: http://35.226.8.89/self_compatibility_badge_target?package=compatibility_lib
   .. |google_compatibility| image:: http://35.226.8.89/google_compatibility_badge_image?package=compatibility_lib
      :target: http://35.226.8.89/google_compatibility_badge_target?package=compatibility_lib
   .. |dependency_version_status| image:: http://35.226.8.89/self_dependency_badge_image?package=compatibility_lib
      :target: http://35.226.8.89/self_dependency_badge_target?package=compatibility_lib

And the badges will show up like below:

.. image:: https://user-images.githubusercontent.com/12888824/46686958-8a4f4900-cbae-11e8-80dc-017bfd9ea437.png

For maintainers
---------------

Steps for building the docker image and deploying to GKE:

- Update the dependency version in `requirements.txt` if there are any.

- Deploy!

.. code-block::

    gcloud app deploy
