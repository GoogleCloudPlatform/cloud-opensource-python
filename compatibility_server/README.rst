Compatibility Server
====================

    A web application that returns compatibility information about Python packages.

Running the server
------------------

1. Install Docker_

.. _Docker: https://www.docker.com/community-edition

2. Download the code:

    ::
    
        git clone git@github.com:GoogleCloudPlatform/cloud-opensource-python.git

3. Build and run the Docker image

    ::

        cd cloud-opensource-python/compatbility_server
        ./run-in-docker.sh

Testing it out
--------------

    ::
    
      curl 'http://0.0.0.0:8888/?package=six&package=Django&python-version=3' | python3 -m json.tool
      {
        "result": "SUCCESS",
        "packages": [
          "six",
          "Django"
        ],
        "description": null,
        "requirements": "absl-py==0.2.2\napparmor==2.11.1\nasn1crypto==0.24.0\nastor==0.6.2\natomicwrites==1.1.5\nattrs==18.1.0\nbleach==1.5.0\nblinker==1.3\nBrlapi==0.6.6\ncachetools==2.1.0\ncertifi==2018.4.16\nchardet==3.0.4\ncheckbox-ng==0.23\ncheckbox-support==0.22\ncolorlog==2.10.0\ncryptography==2.1.4\ncupshelpers==1.0\ndecorator==4.3.0\ndefer==1.0.6\nDjango==2.0.6\nfeedparser==5.2.1\ngast==0.2.0\nglinux-rebootd==0.1\ngoobuntu-config-tools==0.1\ngoogle-api-core==1.2.0\ngoogle-auth==1.5.0\ngoogleapis-common-protos==1.5.3\ngpg==1.10.0\ngrpcio==1.12.1\nguacamole==0.9.2\nhtml5lib==0.9999999\nhttplib2==0.9.2\nidna==2.6\nimportlab==0.1.1\nIPy==0.83\nJinja2==2.9.6\nkeyring==10.5.1\nkeyrings.alt==2.2\nLibAppArmor==2.11.1\nlouis==3.3.0\nlxml==4.0.0\nMako==1.0.7\nMarkdown==2.6.11\nMarkupSafe==1.0\nmore-itertools==4.2.0\nnetworkx==2.1\nnox-automation==0.19.0\nnumpy==1.14.5\noauthlib==2.0.4\nobno==29\nolefile==0.44\nonboard==1.4.1\nopencensus==0.1.5\npadme==1.1.1\npexpect==4.2.1\nPillow==4.3.0\nplainbox==0.25\npluggy==0.6.0\nprotobuf==3.5.2.post1\npsutil==5.4.2\npy==1.5.3\npyasn1==0.4.3\npyasn1-modules==0.2.1\npycairo==1.15.4\npycrypto==2.6.1\npycups==1.9.73\npycurl==7.43.0\npygobject==3.26.1\npyinotify==0.9.6\nPyJWT==1.5.3\npyOpenSSL==17.5.0\npyparsing==2.1.10\npysmbc==1.0.15.6\npytest==3.6.1\npython-apt==1.4.0b3\npython-debian==0.1.31\npython-xapp==1.0.0\npython-xlib==0.20\npytype==2018.5.22.1\npytz==2018.4\npyxdg==0.25\nPyYAML==3.12\nreportlab==3.3.0\nrequests==2.18.4\nretrying==1.3.3\nrsa==3.4.2\nSecretStorage==2.3.1\nsetproctitle==1.1.10\nsix==1.11.0\ntensorboard==1.8.0\ntensorflow==1.8.0\ntermcolor==1.1.0\nufw==0.35\nunattended-upgrades==0.1\nurllib3==1.22\nvirtualenv==16.0.0\nWerkzeug==0.14.1\nXlsxWriter==0.9.6\nyoutube-dl==2017.11.6\n"
        }

Commands for deployment
-----------------------

1. Set the current context to compatibility-server

    ::

      gcloud container clusters get-credentials compatibility-checker-cluster --zone us-central1-b --project python-compatibility-tools

2. Build, test, push, and deploy a new image

TAG_NAME is in the format `v[NUMBER_OF_REVISION]`. Incrementing the number by 1 will be the new tag name.
IMAGE_NAME is the gcr.io/python-compatibility-tools/compatibility-server:[TAG_NAME].

    ::

      docker build -t gcr.io/python-compatibility-tools/compatibility-server:[TAG_NAME] .
      sudo docker run -v /var/run/docker.sock:/var/run/docker.sock -p 8888:8888 [IMAGE_NAME]
      gcloud docker -- push gcr.io/python-compatibility-tools/compatibility-server:[TAG_NAME]
      kubectl set image deployment/compatibility-server compatibility-server=gcr.io/python-compatibility-tools/compatibility-server:[TAG_NAME]

Alternatively, we can use the deploy.yaml to push a new deployment.

    ::

      kubectl apply -f deployment/deploy.yamlkubectl get deployment compatibility-server -o yaml > deployment/deploy.yaml

If asked to sync up the current deploy.yaml with the latest one,

    ::

      kubectl get deployment compatibility-server -o yaml > deployment/deploy.yaml

3. After the deployment, be sure to send a new PR to update the TAG_NAME in the deploy.yaml.

Commands for Maintenance
------------------------

1. Resizing the cluster (adding more instances)

Currently we have 24 instances in our cluster, this number is from our load
test and requirement for completing each round of checks within 15 minutes.
Potentially we will have 75 packages, and checking for both py2 and py3 pairwisely with one order
will need 75 + 75 * 74 * 2 * 2 / 2 = 11175 checks, and the average time spent for each check is 60 seconds,
which means we will need to run 745 checks at the same time.

    ::

      gcloud container clusters resize compatibility-server --size [SIZE]

2. Change the number of replicas

The current number of replicas is 120, which means each instance has 5 replicas.
We have 10 workers per replica, so that in total we have 120 * 10 = 1200 workers, which is
much more than the number 745 as we need.

The number of workers a single vm can tolerant is around 60, and we use 50 workers here.
Be sure to run the load test before making any changes to the number of replicas.

    ::

      kubectl scale deployment/compatibility-server --replicas [NUMBER_OF_REPLICAS]

Disclaimer
----------

This is not an official Google product.
