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

import base64
import collections
import json

import requests

from redfish_client.exceptions import AuthException, InaccessibleException


Response = collections.namedtuple("Response", "status headers json raw")


class Connector:
    # Default headers, as required by Redfish spec
    # https://redfish.dmtf.org/schemas/DSP0266_1.5.0.html#request-headers
    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "OData-Version": "4.0"
    }

    def __init__(self, base_url, username, password, verify=True):
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password

        self._session_path = None
        self._session_id = None

        self._basic_path = None

        self._client = requests.Session()
        self._client.verify = verify
        self._client.headers = Connector.DEFAULT_HEADERS.copy()

    def _url(self, path):
        return self._base_url + path

    def _request(self, method, path, payload=None):
        args = dict(json=payload) if payload else {}
        try:
            resp = self._client.request(method, self._url(path), **args)
        except requests.exceptions.ConnectionError:
            raise InaccessibleException(
                "Endpoint at {} is not accessible".format(self._base_url))

        if resp.status_code == 401:
            self.login()
            resp = self._client.request(method, self._url(path), **args)

        try:
            json_data = resp.json()
        except json.JSONDecodeError:
            json_data = None
        headers = dict(resp.headers.lower_items())

        return Response(resp.status_code, headers, json_data, resp.content)

    def _set_header(self, key, value):
        self._client.headers[key] = value

    def _unset_header(self, key):
        if key in self._client.headers:
            del self._client.headers[key]

    def set_session_auth_data(self, path, session_id=None, token=None):
        self._basic_logout()
        self._basic_path = None

        self._session_path = path
        self._session_id = session_id
        if token:
            self._set_header("x-auth-token", token)

    @property
    def session_auth_data(self):
        return (
            self._session_path,
            self._session_id,
            self._client.headers.get("x-auth-token"),
        )

    def set_basic_auth_data(self, path):
        self._session_logout()
        self._session_path = None

        self._basic_path = path

    @property
    def _has_session_support(self):
        return bool(self._session_path)

    def _session_login(self):
        resp = self._client.post(self._url(self._session_path), json=dict(
            UserName=self._username, Password=self._password,
        ))
        if resp.status_code != 201:
            raise AuthException("Cannot create session: {}".format(resp.text))

        self._set_header("x-auth-token", resp.headers["x-auth-token"])
        # We combine with `or` here because the default value of the dict.get
        # method is eagerly evaluated, which is not what we want.
        self._session_id = (
            resp.headers.get("location") or resp.json()["@odata.id"]
        )

    def _session_logout(self):
        if self._session_id:
            self._client.delete(self._url(self._session_id))
            self._session_id = None
        self._unset_header("x-auth-token")

    def _basic_login(self):
        secret = "Basic {}".format(base64.b64encode(
            "{}:{}".format(self._username, self._password).encode("ascii"),
        ).decode("ascii"))
        resp = self._client.get(
            self._url(self._basic_path), headers=dict(authorization=secret),
        )
        if resp.status_code != 200:
            raise AuthException("Invalid credentials")
        self._set_header("authorization", secret)

    def _basic_logout(self):
        self._unset_header("authorization")

    def login(self):
        assert self._session_path or self._basic_path, "Use set_*_auth_data"

        if self._has_session_support:
            self._basic_logout()
            self._session_login()
        else:
            self._session_logout()
            self._basic_login()

    def logout(self):
        self._session_logout()
        self._basic_logout()

    def get(self, path):
        return self._request("GET", path)

    def post(self, path, payload=None):
        return self._request("POST", path, payload=payload)

    def patch(self, path, payload=None):
        return self._request("PATCH", path, payload=payload)

    def delete(self, path):
        return self._request("DELETE", path)

    def reset(self, _path=None):
        pass
