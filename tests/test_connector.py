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

from redfish_client.connector import Connector
from redfish_client.exceptions import AuthException, InaccessibleException


class TestInit:
    def test_header_copy(self):
        c1 = Connector("", "", "")
        c1._set_header("a", "b")
        c2 = Connector("", "", "")
        assert c1._client.headers != c2._client.headers

    def test_inaccessible_url(self):
        with pytest.raises(InaccessibleException):
            Connector("https://inaccessible", "user", "pass").get("/data")


class TestLogin:
    def test_basic_login(self, requests_mock):
        requests_mock.get(
            "https://demo.dev/test_auth", status_code=200,
            request_headers=dict(Authorization="Basic dXNlcjpwYXNz"),
        )
        conn = Connector("https://demo.dev", "user", "pass")
        conn.set_basic_auth_data("/test_auth")
        conn.login()

    def test_basic_login_invalid_credentials(self, requests_mock):
        requests_mock.get("https://demo.dev/test_auth", status_code=401)
        conn = Connector("https://demo.dev", "user", "notpass")
        conn.set_basic_auth_data("/test_auth")
        with pytest.raises(AuthException):
            conn.login()

    def test_session_login_id_in_location_header(self, requests_mock):
        def matcher(req):
            return (
                req.json()["UserName"] == "user" and
                req.json()["Password"] == "pass"
            )

        requests_mock.post(
            "https://demo.dev/sessions", additional_matcher=matcher,
            status_code=201,
            headers={"X-Auth-Token": "abc", "Location": "/sessions/1"},
        )
        conn = Connector("https://demo.dev", "user", "pass")
        conn.set_session_auth_data("/sessions")
        conn.login()

    def test_session_login_id_in_body(self, requests_mock):
        def matcher(req):
            return (
                req.json()["UserName"] == "user1" and
                req.json()["Password"] == "pass1"
            )

        requests_mock.post(
            "https://demo.dev/sessions", additional_matcher=matcher,
            status_code=201, headers={"X-Auth-Token": "abc"},
            json={"@odata.id": "/sessions/1"},
        )
        conn = Connector("https://demo.dev", "user1", "pass1")
        conn.set_session_auth_data("/sessions")
        conn.login()

    def test_session_login_invalid_credentials(self, requests_mock):
        requests_mock.post(
            "https://demo.dev/sessions", status_code=400, text="Invalid",
        )
        conn = Connector("https://demo.dev", "user1", "pass1")
        conn.set_session_auth_data("/sessions")
        with pytest.raises(AuthException):
            conn.login()


class TestSessionAuthData:
    def test_no_data(self):
        conn = Connector("", "", "")
        assert (None, None, None) == conn.session_auth_data

    def test_no_active_session(self):
        conn = Connector("", "", "")
        conn.set_session_auth_data("/sessions")
        assert ("/sessions", None, None) == conn.session_auth_data

    def test_active_session(self, requests_mock):
        requests_mock.post(
            "http://demo.site/sessions", status_code=201,
            headers={"x-auth-token": "xyz", "Location": "/sessions/1"},
        )
        conn = Connector("http://demo.site", "", "")
        conn.set_session_auth_data("/sessions")
        conn.login()
        assert ("/sessions", "/sessions/1", "xyz") == conn.session_auth_data

    def test_user_supplied_session_data(self):
        conn = Connector("", "", "")
        conn.set_session_auth_data("/sessions", "/sessions/2", "dfg")
        assert ("/sessions", "/sessions/2", "dfg") == conn.session_auth_data


class TestLogout:
    def test_basic_logout(self, requests_mock):
        conn = Connector("https://demo.dev", "user", "pass")
        conn.set_basic_auth_data("/test_auth")
        conn.logout()

    def test_session_logout(self, requests_mock):
        requests_mock.delete(
            "https://demo.dev/sessions/1", status_code=204,
            request_headers={"X-Auth-Token": "abc"},
        )
        conn = Connector("https://demo.dev", "user1", "pass1")
        conn.set_session_auth_data("/sessions", "/sessions/1", "abc")
        conn.logout()

    def test_session_logout_expired_session(self, requests_mock):
        requests_mock.delete("https://demo.dev/sessions/1", status_code=401)
        conn = Connector("https://demo.dev", "user", "pass")
        conn.set_session_auth_data("/sessions", "/sessions/1", "invalid")
        conn.logout()

    def test_session_logout_no_session(self, requests_mock):
        conn = Connector("https://demo.dev", "user", "pass")
        conn.set_session_auth_data("/sessions")
        conn.logout()


class TestGet:
    def test_get_no_auth(self, requests_mock):
        requests_mock.get(
            "https://demo.dev/data", status_code=200, json=dict(hello="fish"),
        )
        conn = Connector("https://demo.dev", "user", "pass")
        r = conn.get("/data")
        assert r.status == 200
        assert r.json == dict(hello="fish")

    def test_get_non_json_body(self, requests_mock):
        requests_mock.get("https://demo.dev/data", status_code=200)
        conn = Connector("https://demo.dev", "user", "pass")
        r = conn.get("/data")
        assert r.status == 200
        assert r.json is None

    def test_get_non_200(self, requests_mock):
        requests_mock.get(
            "https://demo.dev/data", status_code=404, json=dict(error="bad"),
        )
        conn = Connector("https://demo.dev", "user", "pass")
        r = conn.get("/data")
        assert r.status == 404
        assert r.json == dict(error="bad")

    def test_get_basic_relogin(self, requests_mock):
        # Define more specific mock aafter less specific ones, since they are
        # matched in bottom-up order.
        requests_mock.get("https://demo.dev/data", status_code=401)
        requests_mock.get(
            "https://demo.dev/test", status_code=200,
            request_headers=dict(Authorization="Basic dXNlcjpwYXNz"),
        )
        requests_mock.get(
            "https://demo.dev/data", status_code=200,
            request_headers=dict(Authorization="Basic dXNlcjpwYXNz"),
        )
        conn = Connector("https://demo.dev", "user", "pass")
        conn.set_basic_auth_data("/test")
        r = conn.get("/data")
        assert r.status == 200
        assert r.json is None

    def test_get_session_relogin(self, requests_mock):
        requests_mock.get("https://demo.dev/data", [
            dict(status_code=401), dict(status_code=200),
        ])
        requests_mock.post(
            "https://demo.dev/sessions", status_code=201,
            headers={"X-Auth-Token": "123", "Location": "/sessions/3"},
        )
        conn = Connector("https://demo.dev", "user", "pass")
        conn.set_session_auth_data("/sessions")
        r = conn.get("/data")
        assert r.status == 200
        assert r.json is None

    def test_get_use_existing_session(self, requests_mock):
        requests_mock.get(
            "https://demo.dev/data", status_code=200,
            request_headers={"X-Auth-Token": "123"},
        )
        conn = Connector("https://demo.dev", "user", "pass")
        conn.set_session_auth_data("/sessions", "/sessions/1", "123")
        r = conn.get("/data")
        assert r.status == 200
        assert r.json is None

    def test_get_caching_ok(self, requests_mock):
        requests_mock.get("https://demo.dev/data", [
            dict(status_code=200, json=dict(hello="fish")),
            dict(status_code=200, json=dict(solong="fish")),
        ])
        conn = Connector("https://demo.dev", None, None)
        assert conn.get("/data").json == dict(hello="fish")
        assert conn.get("/data").json == dict(solong="fish")

    def test_get_caching_non_ok(self, requests_mock):
        requests_mock.get("https://demo.dev/data", [
            dict(status_code=404, json=dict(error="bad")),
            dict(status_code=500, json=dict(really="bad")),
        ])
        conn = Connector("https://demo.dev", None, None)
        assert conn.get("/data").json == dict(error="bad")
        assert conn.get("/data").json == dict(really="bad")


class TestPost:
    def test_post_no_payload(self, requests_mock):
        requests_mock.post("https://demo.dev/post", status_code=200)
        conn = Connector("https://demo.dev", None, None)
        status, *_ = conn.post("/post")
        assert status == 200

    def test_post_no_payload(self, requests_mock):
        requests_mock.post(
            "https://demo.dev/post", status_code=200,
            additional_matcher=lambda r: r.json()["post"] == "payload",
        )
        conn = Connector("https://demo.dev", None, None)
        status, *_ = conn.post("/post", dict(post="payload"))
        assert status == 200


class TestPatch:
    def test_patch_no_payload(self, requests_mock):
        requests_mock.patch("https://demo.dev/patch", status_code=200)
        conn = Connector("https://demo.dev", None, None)
        status, *_ = conn.patch("/patch")
        assert status == 200

    def test_patch_no_payload(self, requests_mock):
        requests_mock.patch(
            "https://demo.dev/patch", status_code=200,
            additional_matcher=lambda r: r.json()["patch"] == "payload",
        )
        conn = Connector("https://demo.dev", None, None)
        status, *_ = conn.patch("/patch", dict(patch="payload"))
        assert status == 200


class TestDelete:
    def test_delete(self, requests_mock):
        requests_mock.delete("https://demo.dev/delete", status_code=204)
        conn = Connector("https://demo.dev", None, None)
        status, *_ = conn.delete("/delete")
        assert status == 204


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
        conn = Connector("https://demo.dev", "user", "pass")
        assert conn.get("/1").json == dict(hello="fish")
        assert conn.get("/2").json == dict(solong="fish")
        conn.reset()
        assert conn.get("/1").json == dict(hello="bear")
        assert conn.get("/2").json == dict(solong="bear")

    def test_reset_with_path(self, requests_mock):
        self.mock_paths(requests_mock)
        conn = Connector("https://demo.dev", "user", "pass")
        assert conn.get("/1").json == dict(hello="fish")
        assert conn.get("/2").json == dict(solong="fish")
        conn.reset("/2")
        assert conn.get("/1").json == dict(hello="bear")
        assert conn.get("/2").json == dict(solong="bear")
