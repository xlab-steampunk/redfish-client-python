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


class Resource(object):
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
        self._cache = {}
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
        if resp.status_code != 200:
            raise Exception(resp.content)
        return dict(resp.headers), self._get_fragment(resp.json(), fragment)

    def _build(self, data):
        if isinstance(data, dict):
            return self._build_from_hash(data)
        elif isinstance(data, list):
            return [self._build(i) for i in data]
        else:
            return data

    def _build_from_hash(self, data):
        if "@odata.id" in data:
            return Resource(self._connector, oid=data["@odata.id"])
        else:
            return Resource(self._connector, data=data)

    def _get(self, name):
        if name not in self._cache:
            self._cache[name] = self._build(self._content[name])
        return self._cache[name]

    def __getattr__(self, name):
        return self._get(name)

    def __getitem__(self, name):
        return self._get(name)

    def __contains__(self, item):
        return item in self._content

    def dig(self, *keys):
        resource = self
        for k in keys:
            if k in resource:
                resource = resurce._get(k)
            else:
                return None
        return resource

    @property
    def raw(self):
        return self._content
