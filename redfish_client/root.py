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

from redfish_client.resource import Resource


class Root(Resource):
    def _has_session_support(self):
        return self._content.get("Links", {}).get("Sessions", False)

    def _session_login(self, username, password):
        session_path = self._content["Links"]["Sessions"]["@odata.id"]
        resp = self._connector.post(
            session_path, payload=dict(UserName=username, Password=password)
        )
        self._connector.set_header("X-Auth-Token",
                                   resp.headers["X-Auth-Token"])

    def _basic_login(self, username, password):
        self._connector.set_header("Authorization",
                                   basic_auth_header(username, password))

    def login(self, username, password):
        if self._has_session_support():
            self._session_login(username, password)
        else:
            self._basic_login(username, password)

    def find(self, oid):
        return Resource(self._connector, oid=oid)
