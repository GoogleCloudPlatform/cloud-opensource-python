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
    
      curl 'http://0.0.0.0:8888/?package=tensorflow&python-version=3' | python3 -m json.tool        
      {
          "result": "SUCCESS",
          "packages": [
              "tensorflow"
          ],
          "description": null,
          "requirements": "absl-py==0.2.2\nastor==0.6.2\nbleach==1.5.0\ngast==0.2.0\ngrpcio==1.12.1\nhtml5lib==0.9999999\nMarkdown==2.6.11\nnumpy==1.14.4\nprotobuf==3.5.2.post1\nsix==1.11.0\ntensorboard==1.8.0\ntensorflow==1.8.0\ntermcolor==1.1.0\nWerkzeug==0.14.1\n"
      }

Disclaimer
----------

This is not an official Google product.
