Cloud Build for Dashboard
=========================

Generating the dashboard static files
-------------------------------------

This step is defined in the Dockerfile, which is basically the same as running it locally.
It is using the dashboard_builder.py script and the jinja templates to generate the HTML files,
and keep the files in the static/ folder.

As this step is done in a docker container, the generated files will not located in host by themselves.
We will need to mount the volume to the docker container and copy the files from docker to host.
This will be done by this command:

    ::

        docker run --name dashboard_builder -h dashboard_container -v /workspace/static:/export dashboard_builder /bin/bash -c "cp /compatibility_dashboard/dashboard/*.html /export/"

Deploy to App Engine
--------------------

This deploys the generated static files to app engine using:

    ::

        gcloud app deploy [PROJECT_NAME]

Note that the credential used in this step is different than in step #1, as the data for generating the files
is stored in a different project. But because the two steps are not running in the same environment (step #1 runs
in its docker container), the two credentials won't interfere with each other.


Build and deploy periodically
-----------------------------

In order to have a way to automatically build and deploy the dashboard to App Engine, we use the Cloud Build here.
The cloudbuild.yaml is the config file defining the steps described above. And running the command below will start the
build defined in the yaml file:

    ::

        gcloud builds submit --config=cloudbuild.yaml .

There is a cron job configured which can grab the credentials from a secret key store,
and then runs the gcloud command for starting the build periodically.
