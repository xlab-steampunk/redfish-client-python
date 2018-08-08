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

from __future__ import absolute_import, unicode_literals

import requests


class Connector(object):
    # Default headers, as required by Redfish spec
    # https://redfish.dmtf.org/schemas/DSP0266_1.5.0.html#request-headers
    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "OData-Version": "4.0"
    }

    def __init__(self, base_url, verify=True):
        self._base_url = base_url.rstrip("/")
        self._headers = {}
        self._client = requests.Session()
        self._client.verify = verify
        self._client.headers = Connector.DEFAULT_HEADERS

    def _url(self, path):
        return self._base_url + path

    def _request(self, method, path, payload=None):
        args = dict(json=payload) if payload else {}
        return self._client.request(method, self._url(path), **args)

    def set_header(self, key, value):
        self._client.headers[key] = value

    def get(self, path):
        return self._request("GET", path)

    def post(self, path, payload=None):
        return self._request("POST", path, payload=payload)

    def patch(self, path, payload=None):
        return self._request("PATCH", path, payload=payload)

    def delete(self, path):
        return self._request("DELETE", path)
