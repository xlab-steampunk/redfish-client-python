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

import pytest

from redfish_client.caching_connector import CachingConnector


class TestGet:
    def test_get_caching_ok(self, requests_mock):
        requests_mock.get("https://demo.dev/data", [
            dict(status_code=200, json=dict(hello="fish")),
            dict(status_code=200, json=dict(solong="fish")),
        ])
        conn = CachingConnector("https://demo.dev", None, None)
        assert conn.get("/data").json == dict(hello="fish")
        assert conn.get("/data").json == dict(hello="fish")

    def test_get_caching_non_ok(self, requests_mock):
        requests_mock.get("https://demo.dev/data", [
            dict(status_code=404, json=dict(error="bad")),
            dict(status_code=500, json=dict(really="bad")),
        ])
        conn = CachingConnector("https://demo.dev", None, None)
        assert conn.get("/data").json == dict(error="bad")
        assert conn.get("/data").json == dict(really="bad")


class TestReset:
    @staticmethod
    def mock_paths(mock):
        mock.get("https://demo.dev/1", [
            dict(status_code=200, json=dict(hello="fish")),
            dict(status_code=200, json=dict(hello="bear")),
        ])
        mock.get("https://demo.dev/2", [
            dict(status_code=200, json=dict(solong="fish")),
            dict(status_code=200, json=dict(solong="bear")),
        ])

    def test_reset_all(self, requests_mock):
        self.mock_paths(requests_mock)
        conn = CachingConnector("https://demo.dev", "user", "pass")
        assert conn.get("/1").json == dict(hello="fish")
        assert conn.get("/2").json == dict(solong="fish")
        conn.reset()
        assert conn.get("/1").json == dict(hello="bear")
        assert conn.get("/2").json == dict(solong="bear")

    def test_reset_with_path(self, requests_mock):
        self.mock_paths(requests_mock)
        conn = CachingConnector("https://demo.dev", "user", "pass")
        assert conn.get("/1").json == dict(hello="fish")
        assert conn.get("/2").json == dict(solong="fish")
        conn.reset("/2")
        assert conn.get("/1").json == dict(hello="fish")
        assert conn.get("/2").json == dict(solong="bear")

    def test_reset_with_non_cached_path(self, requests_mock):
        self.mock_paths(requests_mock)
        conn = CachingConnector("https://demo.dev", "user", "pass")
        assert conn.get("/1").json == dict(hello="fish")
        assert conn.get("/2").json == dict(solong="fish")
        conn.reset("/3")
        assert conn.get("/1").json == dict(hello="fish")
        assert conn.get("/2").json == dict(solong="fish")
