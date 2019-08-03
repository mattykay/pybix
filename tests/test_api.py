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
        httpretty.register_uri(
            httpretty.POST,
            "http://test.com/api_jsonrpc.php",
            body=json.dumps({
                "jsonrpc": "2.0",
                "result": "0424bd59b807674191e7d77572075f33",
                "id": 0
            }),
        )

        ZAPI = ZabbixAPI("http://test.com")
        ZAPI.login("Admin", "zabbix")

        self.__perform_login_tests(ZAPI, httpretty.last_request())

    @httpretty.activate
    def test_login_with_context(self):
        httpretty.register_uri(
            httpretty.POST,
            "http://test.com/api_jsonrpc.php",
            body=json.dumps({
                "jsonrpc": "2.0",
                "result": "0424bd59b807674191e7d77572075f33",
                "id": 0
            }),
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
