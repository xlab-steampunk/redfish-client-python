#  Copyright 2019 XLAB d.o.o.
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

from redfish_client.connector import Connector


class CachingConnector(Connector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = {}

    def get(self, path):
        if path in self._cache:
            return self._cache[path]

        response = super().get(path)
        if response.status == 200:  # Do not cache failed requests
            self._cache[path] = response
        return response

    def reset(self, path=None):
        if path:
            self._cache.pop(path, None)
        else:
            self._cache = {}
