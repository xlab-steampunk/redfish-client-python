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

from redfish_client.connector import Connector
from redfish_client.caching_connector import CachingConnector
from redfish_client.root import Root


def connect(base_url, username, password, verify=True, cache=True,
            lazy_load=True, timeout=Connector.DEFAULT_TIMEOUT):
    klass = CachingConnector if cache else Connector
    connector = klass(base_url, username, password, verify=verify, timeout=timeout)
    root = Root(connector, oid="/redfish/v1", lazy=lazy_load)
    root.login()
    return root
