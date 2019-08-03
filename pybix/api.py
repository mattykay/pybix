import os
import requests
import json
import logging

logger = logging.getLogger(__name__)


class ZabbixAPIException(Exception):
    """ Zabbix API Exception
         -32700 - invalid JSON. An error occurred on the server while parsing the JSON text (typo, wrong quotes, etc.)
         -32600 - received JSON is not a valid JSON-RPC Request
         -32601 - requested remote-procedure does not exist
         -32602 - invalid method parameters
         -32603 - Internal JSON-RPC error
         -32400 - System error
         -32300 - Transport error
         -32500 - Application error
    """
    pass


class ZabbixAPI(object):
    def __init__(self, url: str = None, timeout: int = None):
        """Initialise the ZabbixAPI (but not login)

        Arguments:
            url {str} -- Base URL to Zabbix (default: ZABBIX_SERVER environment variable or https://localhost/zabbix)
            timeout {int} -- Timeout for API request in seconds
                             (default: ZABBIX_SESSION_TIMEOUT environment variable or None - don't timeout)
        """
        url = url or os.environ.get(
            'ZABBIX_SERVER') or 'https://localhost/zabbix'
        self.URL = f"{url}/api_jsonrpc.php" if not url.endswith(
            '/api_jsonrpc.php') else url

        # Zabbix auth specific
        self.AUTH = ''
        self.ID = 0

        # Requests specific
        self.TIMEOUT = timeout or os.environ.get(
            'ZABBIX_SESSION_TIMEOUT') or None
        self.SESSION = requests.Session()
        self.SESSION.headers.update({
            'Content-Type': 'application/json-rpc',
            'User-Agent': 'python/pybix',
            'Cache-Control': 'no-cache'
        })

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.logout()

    def __getattr__(self, name: str):
        return ZabbixObject(name, self)

    def login(self, user: str = None, password: str = None) -> None:
        if self.AUTH:
            # TODO validate still active, in which case use current auth
            pass
        else:
            user = user or os.environ.get('ZABBIX_USER') or 'Admin'
            password = password or os.environ.get(
                'ZABBIX_PASSWORD') or 'zabbix'

            logging.debug(f"ZabbixAPI.login(user={user})")
            self.AUTH = self.user.login(user=user, password=password)

    def logout(self):
        if self.AUTH:
            logger.debug("ZabbixAPI.logout()")

            # TODO check return for result
            if self.user.logout():
                self.AUTH = ''

    def do_request(self, method: str, params: dict = None) -> str:
        request = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params or {},
            'id': self.ID,
        }

        # Only add auth if method requires it
        if self.AUTH and (method not in ('apiinfo.version', 'user.login',
                                         'user.checkAuthentication')):
            request['auth'] = self.AUTH

        logger.debug(
            f"Sending: {json.dumps(request, indent=4, separators=(',', ': '))}",
        )

        response = self.SESSION.post(self.URL,
                                     data=json.dumps(request),
                                     timeout=self.TIMEOUT)
        response.raise_for_status()

        try:
            response_json = json.loads(response.text)
        except ValueError:
            raise ZabbixAPIException(f"Unable to parse json: {response.text}")

        self.ID += 1

        logger.debug(
            f"Sending: {json.dumps(response_json, indent=4, separators=(',', ': '))}",
        )

        if 'error' in response_json:
            raise ZabbixAPIException(
                f"Error {response_json['error']['code']}: {response_json['error']['message']},"
                f" {response_json['error']['data']}",
                response_json['error']['code'])

        return response_json

    def check_authentication(self):
        """ Convenience method for calling user.checkAuthentication of the current session """
        return self.user.checkAuthentication(sessionid=self.AUTH)

    @property
    def api_version(self) -> str:
        return self.apiinfo.version()

    @property
    def is_authenticated(self) -> bool:
        if not self.AUTH:
            logger.debug("is_authenticated(): No AUTH token")
            return False

        try:
            self.user.checkAuthentication(sessionid=self.AUTH)
        except ZabbixAPIException as ex:
            logger.debug(f"is_authenticated(): ZabbixAPIException {ex}")
            return False
        return True


class ZabbixObject(object):
    def __init__(self, name: str, parent: ZabbixAPI):
        self.NAME = name
        self.PARENT = parent

    def __getattr__(self, name):
        """ Dynamically create a method (ie: get) """

        def fn(*args, **kwargs):
            if args and kwargs:
                raise TypeError("Found both args and kwargs")

            return self.PARENT.do_request('{0}.{1}'.format(self.NAME, name),
                                          args or kwargs)['result']

        return fn
