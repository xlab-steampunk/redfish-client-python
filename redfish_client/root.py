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

from redfish_client.resource import Resource


class Root(Resource):
    def login(self):
        sessions = self._content.get("Links", {}).get("Sessions", {})
        authenticated_path = next(
            i["@odata.id"] for i in self._content.values() if "@odata.id" in i
        )
        if "@odata.id" in sessions:
            self._connector.set_session_auth_data(sessions["@odata.id"])
        else:
            self._connector.set_basic_auth_data(authenticated_path)
        self._connector.login()

    def logout(self):
        self._connector.logout()

    def find(self, oid):
        return Resource(self._connector, oid=oid)
