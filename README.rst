Redfish API client
==================

This repository contains minimalistic python client for Redfish API.


Quickstart
----------

The simplest and safest way of playing with this client is to install it into
dedicated virtual environment::

    $ virtualenv venv && . venv/bin/activate
    (venv) $ pip install redfish-client

Now we can start the interactive python interpreter and interact with the
api::

    (venv) $ python
    >>> import redfish_client
    >>> import json
    >>> root = redfish_client.connect(
    ...   "redfish.address", "username", "password"
    ... )
    >>> print(json.dumps(root.raw, indent=2, sort_keys=True))
    {
      "@odata.context": "/redfish/v1/$metadata#ServiceRoot.ServiceRoot",
      "@odata.etag": "W/\"bb7f4494b922dde991a940cc8251e8fc\"",
      "@odata.id": "/redfish/v1",
      "@odata.type": "#ServiceRoot.v1_2_0.ServiceRoot",
      "AccountService": {
        "@odata.id": "/redfish/v1/AccountService/"
      },
      # More content here
      "UpdateService": {
        "@odata.id": "/redfish/v1/UpdateService/"
      }
    }
    >>> system = root.Systems.Members[0]
    >>> print(json.dumps(system.raw, indent=2, sort_keys=True))
    {
      "@odata.context": "/redfish/v1/$metadata#ComputerSystem.ComputerSystem",
      "@odata.etag": "W/\"788f9827a97be1a4c8cbe9c085ef4d8b\"",
      "@odata.id": "/redfish/v1/Systems/1/",
      "@odata.type": "#ComputerSystem.v1_4_0.ComputerSystem",
      # More content here
      "SystemType": "Physical",
      "UUID": "REMOVED_FROM_MOCK"
    }
    >>> print(system.SystemType)
    Physical
