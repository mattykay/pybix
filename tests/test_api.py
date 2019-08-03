import pytest
import json
import httpretty
from pybix import ZabbixAPI


class TestAPI(object):
    def test_init(self):
        ZAPI = ZabbixAPI("http://test.com")
        assert ZAPI.ID == 0
        assert ZAPI.AUTH == ""
        assert not ZAPI.is_authenticated

    @httpretty.activate
    def test_login(self):
        response = {
            "jsonrpc": "2.0",
            "result": "0424bd59b807674191e7d77572075f33",
            "id": 0
        }
        httpretty.register_uri(
            httpretty.POST,
            "http://test.com/api_jsonrpc.php",
            body=json.dumps(response),
        )

        ZAPI = ZabbixAPI("http://test.com")
        ZAPI.login("Admin", "zabbix")

        self.__perform_login_tests(ZAPI, httpretty.last_request())

    @httpretty.activate
    def test_login_with_context(self):
        response = {
            "jsonrpc": "2.0",
            "result": "0424bd59b807674191e7d77572075f33",
            "id": 0
        }
        httpretty.register_uri(
            httpretty.POST,
            "http://test.com/api_jsonrpc.php",
            body=json.dumps(response),
        )

        with ZabbixAPI("http://test.com") as ZAPI:
            ZAPI.login("Admin", "zabbix")
            self.__perform_login_tests(ZAPI, httpretty.last_request())

    def __perform_login_tests(self, zabbix_api, last_request):
        expected = {
            'jsonrpc': '2.0',
            'method': 'user.login',
            'params': {
                'user': 'Admin',
                'password': 'zabbix'
            },
            'id': 0,
        }

        assert last_request.headers['content-type'] == "application/json-rpc"
        assert last_request.headers['user-agent'] == "python/pybix"
        assert json.loads(last_request.body.decode('utf-8')) == expected
        assert zabbix_api.AUTH == "0424bd59b807674191e7d77572075f33"
        # TODO Validate is authenticated?

    @httpretty.activate
    def test_logout(self):
        response = {"jsonrpc": "2.0", "result": True, "id": 1}
        expected = {
            "jsonrpc": "2.0",
            "method": "user.logout",
            "params": {},
            "id": 1,
            "auth": "16a46baf181ef9602e1687f3110abf8a"
        }

        httpretty.register_uri(
            httpretty.POST,
            "http://test.com/api_jsonrpc.php",
            body=json.dumps(response),
        )
        ZAPI = ZabbixAPI("http://test.com")

        # Override arbitrary ID and AUTH to match Zabbix example
        ZAPI.AUTH = "16a46baf181ef9602e1687f3110abf8a"
        ZAPI.ID = 1

        ZAPI.logout()

        assert json.loads(
            httpretty.last_request().body.decode('utf-8')) == expected
        assert ZAPI.AUTH == ""
        assert not ZAPI.is_authenticated

    @httpretty.activate
    def test_do_request(self):
        response = {
            "jsonrpc":
            "2.0",
            "result": [{
                "itemid": "23296",
                "clock": "1351090996",
                "value": "0.0850",
                "ns": "563157632"
            }],
            "id":
            1
        }

        httpretty.register_uri(
            httpretty.POST,
            "http://test.com/api_jsonrpc.php",
            body=json.dumps(response),
        )
        ZAPI = ZabbixAPI("http://test.com")

        # Override arbitrary ID and AUTH to match Zabbix example
        ZAPI.AUTH = "038e1d7b1735c6a5436ee9eae095879e"
        ZAPI.ID = 1

        item = ZAPI.history.get(itemids="23296",
                                output="extend",
                                history=0,
                                sortfield="clock",
                                sortorder="DESC",
                                limit=10)
        assert item == [{
            'clock': '1351090996',
            'itemid': '23296',
            'ns': '563157632',
            'value': '0.0850'
        }]

    @httpretty.activate
    def test_api_version(self):
        response = {"jsonrpc": "2.0", "result": "4.0.0", "id": 1}
        httpretty.register_uri(
            httpretty.POST,
            "http://test.com/api_jsonrpc.php",
            body=json.dumps(response),
        )
        ZAPI = ZabbixAPI("http://test.com")
        assert ZAPI.api_version == "4.0.0"
