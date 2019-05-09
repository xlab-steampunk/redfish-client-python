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
from itertools import cycle
from unittest import mock

import pytest

from redfish_client.connector import Connector, Response
from redfish_client.exceptions import (BlacklistedValueException,
    MissingOidException, TimedOutException, ResourceNotFound)
from redfish_client.resource import Resource


class TestGetKey:
    def test_get_value_of_a_key(self):
        assert Resource(None, data={
            "ProcessorSummary": {"State": "Enabled"}
        }).ProcessorSummary.State == "Enabled"

    def test_wrong_id(self):
        connector = mock.Mock(spec=Connector)
        with pytest.raises(ResourceNotFound):
            Resource(connector, oid="id", data={})

    def test_get_invalid_key(self):
        with pytest.raises(KeyError):
            Resource(None, data={}).Invalid_key

    def test_dig(self):
        assert Resource(None, data={
            "ProcessorSummary": {"State": "Enabled"}
        }).dig("ProcessorSummary", "State") == "Enabled"


class TestExecuteAction:
    def setup_method(self,):
        self.connector = mock.Mock(spec=Connector)

    def test_execute_action_without_actions_key(self):
        with pytest.raises(KeyError):
            Resource(self.connector, data={
            }).execute_action("#ComputerSystem.Reset", "payload")

    def test_execute_action(self):
        Resource(self.connector, data={
            "Actions": {"#ComputerSystem.Reset": {"target": "/reset/"}}
        }).execute_action("#ComputerSystem.Reset", "payload")

        self.connector.post.assert_called_once_with("/reset/", payload="payload")

    def test_execute_action_multilevel(self):
        Resource(self.connector, data={
            "Actions": {"Oem": {"#ComputerSystem.CustomizedReset": {"target": "/reset/"}}}
        }).execute_action("#ComputerSystem.CustomizedReset", "payload")

        self.connector.post.assert_called_once_with("/reset/", payload="payload")

    def test_execute_invalid_action(self):
        with pytest.raises(KeyError):
            Resource(self.connector, data={
                "Actions": {"#ComputerSystem.Reset": {"target": "/reset/"}}
            }).execute_action("#ComputerSystem.InvalidAction", "payload")


@mock.patch("time.sleep")
class TestWaitFor:
    @staticmethod
    def build_connector(jsons):
        connector = mock.Mock(spec=Connector)
        connector.get.side_effect = (Response(200, {}, j, b"") for j in jsons)
        return connector

    def test_wait_for_no_oid(self, mock_sleep):
        with pytest.raises(MissingOidException):
            Resource(None, data={
                "PowerState": "On"
            }).wait_for(["PowerState"], "Off")

    def test_wait_for_refresh_missing_oid(self, mock_sleep):
        connector = self.build_connector([
            {"PowerState": "On"},
        ])
        with pytest.raises(MissingOidException):
            Resource(connector, data={
                "@odata.id": "id",
                "PowerState": "On"
            }).wait_for(["PowerState"], "Off")

    def test_wait_for_value(self, mock_sleep):
        connector = self.build_connector([
            {"@odata.id": "id", "PowerState": "On"},
            {"@odata.id": "id", "PowerState": "On"},
            {"@odata.id": "id", "PowerState": "Off"}
        ])
        assert Resource(connector, data={
            "@odata.id": "id",
            "PowerState": "On"
        }).wait_for(["PowerState"], "Off") is True

    def test_wait_for_invalid_value(self, mock_sleep):
        connector = self.build_connector([
            {"@odata.id": "id", "PowerState": "On"},
            {"@odata.id": "id", "PowerState": "On"},
            {"@odata.id": "id", "PowerState": "Fail"}
        ])
        with pytest.raises(BlacklistedValueException):
            Resource(connector, data={
                "@odata.id": "id",
                "PowerState": "On"
            }).wait_for(["PowerState"], "Off", blacklisted=("Fail", ))

    def test_wait_for_timeout(self, mock_sleep):
        connector = self.build_connector(cycle([
            {"@odata.id": "id", "PowerState": "On"},
        ]))
        with pytest.raises(TimedOutException):
            Resource(connector, data={
                "@odata.id": "id",
                "PowerState": "On"
            }).wait_for(["PowerState"], "Off", timeout=0.1)


class TestPost:
    def test_post_on_resource(self):
        connector = mock.Mock(spec=Connector)
        Resource(connector, data={
            "@odata.id": "/redfish/v1/EventService/Subscriptions/"
        }).post(payload={"Destination": "http://123.10.10.234"})
        connector.post.assert_called_once_with(
            "/redfish/v1/EventService/Subscriptions/", payload={"Destination":
            "http://123.10.10.234"})

    def test_post_on_resource_invalid(self):
        connector = mock.Mock(spec=Connector)
        with pytest.raises(MissingOidException):
            Resource(connector, data={}).post(payload={})


class TestDelete:
    def test_delete_a_resource(self):
        connector = mock.Mock(spec=Connector)
        Resource(connector, data={
            "@odata.id": "/redfish/v1/Managers/Steampunk/Accounts/4"
            }
        ).delete()
        connector.delete.assert_called_once_with(
            "/redfish/v1/Managers/Steampunk/Accounts/4")

    def test_delete_an_invalid_resource(self):
        connector = mock.Mock(spec=Connector)
        with pytest.raises(MissingOidException):
            Resource(connector, data={}).delete()


class TestPatch:
    def test_patch_a_resource(self):
        connector = mock.Mock(spec=Connector)
        Resource(connector, data={
            "@odata.id": "/redfish/v1/Systems/1"
        }).patch(payload={"Misc": "MyValue"})
        connector.patch.assert_called_once_with(
            "/redfish/v1/Systems/1", payload={"Misc": "MyValue"})

    def test_patch_an_invalid_resource(self):
        connector = mock.Mock(spec=Connector)
        with pytest.raises(MissingOidException):
            Resource(connector, data={}).patch(payload={"Misc": "MyValue"})
