#  Copyright 2018 XLAB d.o.o.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import operator
import time
from functools import reduce

from redfish_client.exceptions import (
    BlacklistedValueException,
    TimedOutException,
    MissingOidException,
    ResourceNotFound
)


class Resource:
    @staticmethod
    def _parse_fragment_string(fragment):
        if fragment:
            # /my/0/part -> ["my", "0", "part"]
            return fragment.strip("/").split("/")
        return []

    @staticmethod
    def _get_fragment(data, fragment):
        # data, /my/0/part -> data["my"][0]["part"]
        for component in Resource._parse_fragment_string(fragment):
            if isinstance(data, list):
                data = data[int(component)]
            else:
                data = data[component]
        return data

    def __init__(self, connector, oid=None, data=None):
        self._connector = connector
        if oid:
            self._headers, self._content = self._init_from_oid(oid)
        else:
            self._content = data
            self._headers = {}

    def _init_from_oid(self, oid):
        if "#" in oid:
            url, fragment = oid.split("#", 1)
        else:
            url, fragment = oid, ""

        resp = self._connector.get(url)
        if resp.status != 200:
            raise ResourceNotFound(resp.raw)
        return resp.headers, self._get_fragment(resp.json, fragment)

    def _build(self, data):
        if isinstance(data, dict):
            return self._build_from_hash(data)
        if isinstance(data, list):
            return [self._build(i) for i in data]
        return data

    def _build_from_hash(self, data):
        if "@odata.id" in data:
            return Resource(self._connector, oid=data["@odata.id"])
        return Resource(self._connector, data=data)

    def refresh(self):
        try:
            oid = self._content["@odata.id"]
        except KeyError:
            raise MissingOidException("Cannot refresh resource without @odata.id")

        self._connector.reset(oid)
        self._headers, self._content = self._init_from_oid(oid)

    def __getattr__(self, name):
        return self[name]

    def __getitem__(self, name):
        return self._build(self._content[name])

    def __contains__(self, item):
        return item in self._content

    def dig(self, *keys):
        resource = self
        for k in keys:
            if k in resource:
                resource = resource[k]
            else:
                return None
        return resource

    def find_object(self, key):
        """ Recursively search for a key and return key's content """
        if key in self._content.keys():
            return self[key]

        for k in self._content.keys():
            if hasattr(self[k], "find_object"):
                result = self[k].find_object(key)
                if result:
                    return result

    def execute_action(self, action_name, payload):
        """
        Perform an action supported by the resource.

        Args:
          action_name: The field representing the action to perform.
          payload: The dictionary with the action parameters.
        """
        if "Actions" not in self._content:
            raise KeyError("Element does not have Actions attribute")
        action = self.Actions.find_object(action_name)
        if action:
            return self._connector.post(action.target, payload=payload)
        raise KeyError("Action with {} does not exist".format(action_name))

    def wait_for(
            self, stat, expected, blacklisted=None, poll_interval=3,
            timeout=15,
    ):
        """
        :param stat: list or tuple of keys
        :param expected: expected value
        :param blacklisted: list or tuple of blacklisted values
        :param poll_interval: number of requests per second
        :param timeout: timeout in seconds
        :return: actual value if match is found
        Raises:
            MissingDataIdException: If '@odata.id' is missing in the content
            TimedOutError: If timeout is exceeded.
            FailedError: If value matches one of the fail values
        """
        if "@odata.id" not in self._content:
            raise MissingOidException(
                "Element does not have '@odata.id' attribute, cannot wait "
                "for a stat inside inner object"
            )
        start_time = time.time()
        while time.time() <= start_time + timeout:
            self.refresh()
            actual_value = reduce(operator.getitem, stat, self._content)
            if actual_value == expected:
                return True
            if blacklisted and actual_value in blacklisted:
                raise BlacklistedValueException(
                    "Detected blacklisted value '{}'".format(actual_value)
                )
            time.sleep(poll_interval)
        raise TimedOutException(
            "Could not wait for stat {} in time".format(stat)
        )

    @property
    def raw(self):
        return self._content

    def post(self, payload=None):
        """
        Perform a POST at the resource with the given payload.

        Args:
          payload: The contents of the POST payload.
        """
        path = self._content.get("@odata.id")
        if not path:
            raise MissingOidException("The resource cannot be POSTed to.")
        return self._connector.post(path, payload=payload)

    def patch(self, payload):
        """
        Perform a PATCH at the resource with the given payload.

        Args:
          payload: The contents of the POST payload.
        """
        path = self._content.get("@odata.id")
        if not path:
            raise MissingOidException("The resource cannot be PATCHed.")
        return self._connector.patch(path, payload=payload)

    def delete(self):
        """
        Perform a DELETE at the resource.
        """
        path = self._content.get("@odata.id")
        if not path:
            raise MissingOidException("The resource cannot be DELETEd.")
        return self._connector.delete(path)
