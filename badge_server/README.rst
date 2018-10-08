Badge Server
============

    Displaying the compatibility status for your package as a Github Badge.

Types of badges
---------------

1. Self Compatibility
2. Compatibility with Google OSS Python packages
3. Dependency version status

Usage
-----

- One badge

Add this line to your README file on Github:

.. code-block::

    .. |package_details_example| image:: http://35.226.8.89/one_badge_image?package=compatibility_lib
       :target: http://35.226.8.89/one_badge_target?package=compatibility_lib

And the badge for package details will show up like below:

|package_details_example|

.. |package_details_example| image:: http://35.226.8.89/one_badge_image?package=compatibility_lib
   :target: http://35.226.8.89/one_badge_target?package=compatibility_lib

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

.. csv-table::
   :header: "CHECK_TYPE", "RESULT"
   :widths: 20, 30

   "Self Compatibility", |self_compat|
   "Google Compatibility", |google_compat|
   "Dependency Version Status", |dep_version_status|

.. |self_compat| image:: http://35.226.8.89/self_compatibility_badge_image?package=compatibility_lib
   :target: http://35.226.8.89/self_compatibility_badge_target?package=compatibility_lib
.. |google_compat| image:: http://35.226.8.89/google_compatibility_badge_image?package=compatibility_lib
   :target: http://35.226.8.89/google_compatibility_badge_target?package=compatibility_lib
.. |dep_version_status| image:: http://35.226.8.89/self_dependency_badge_image?package=compatibility_lib
   :target: http://35.226.8.89/self_dependency_badge_target?package=compatibility_lib

For maintainers
---------------

Steps for building the docker image and deploying to GKE:

- Update the dependency version in `requirements.txt` if there are any.

- Build the docker image with updated tag.

.. code-block::

    docker build -t gcr.io/python-compatibility-tools/badge_server:ver10 .

- Push the image to GCR (Google Container Registry)

.. code-block::

    gcloud docker -- push gcr.io/python-compatibility-tools/badge_server:ver10

- Deploy!

.. code-block::

    kubectl apply -f deployment/app-with-secret.yaml

- Send a PR for updating the image tag after deployment.
