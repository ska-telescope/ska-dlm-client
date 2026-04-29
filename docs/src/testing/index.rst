Testing
========

*WIP*

Helm tests
----------

A Helm chart has been created for testing: ``tests/charts/test-ska-dlm-client``.

The test chart is used to configure an existing DLM instance running in the same cluster namespace.

Usage:

.. code-block:: shell

   helm install -f resources/dp-proj-user.yaml test-ska-dlm-client tests/charts/test-ska-dlm-client/
   helm test test-ska-dlm-client
   helm uninstall test-ska-dlm-client


Local Docker tests
-------------------

Run all tests on your local machine (unit and integration) alongside the DLM server images:

.. code-block:: shell

    make all-tests
