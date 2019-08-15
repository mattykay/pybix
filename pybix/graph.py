#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Graph
    Contains methods relating to graph image exporting
"""

import urllib3
import requests
import os
import sys
import logging
from datetime import datetime
from requests import Response
from pathlib import PurePath
from api import ZabbixAPI

logger = logging.getLogger(__name__)


class GraphImage(object):
    """Class that handles getting/saving Zabbix Graph Images directly
        Note: This is not a Zabbix API object
    """

    def __init__(self,
                 base_url: str = None,
                 username: str = None,
                 password: str = None,
                 ssl_verify: bool = True):
        """Initialise the GraphImage session (including login)

        Arguments:
            base_url {str} -- Base URL to Zabbix (default: ZABBIX_SERVER environment variable or
                                                    https://localhost/zabbix)
            username {str} -- Zabbix Username (default: ZABBIX_USER environment variable or 'Admin')
            password {str} -- Zabbix Password (default: ZABBIX_PASSWORD environment variable or 'zabbix')
            ssl_verify {bool} -- Whether to attempt SSL verification during call (default: True)
        """
        url = base_url or os.environ.get(
            'ZABBIX_SERVER') or 'http://localhost/zabbix'
        self.BASE_URL = url.replace(
            "/api_jsonrpc.php",
            "") if not url.endswith('/api_jsonrpc.php') else url

        payload = {
            'name': username or os.environ.get('ZABBIX_USER') or 'Admin',
            'password': password or os.environ.get('ZABBIX_PASSWORD')
            or 'zabbix',  # noqa: W503
            'enter': 'Sign in'
        }
        self.SESSION = requests.Session()
        self.SSL_VERIFY = ssl_verify

        # Perform Login (note: not via Zabbix API since it doesn't
        #   expose graph exports, only configuration)
        logger.debug(
            f"GraphImage: Attempting to login to Zabbix server at {self.BASE_URL}/index.php")
        if not self.SSL_VERIFY:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.SESSION.post(f"{self.BASE_URL}/index.php",
                          data=payload, verify=self.SSL_VERIFY)

    def _get_by_graphid(self,
                        graph_id: str,
                        from_date: str = "now-1d",
                        to_date: str = "now",
                        width: str = "1782",
                        height: str = "452",
                        output_path: str = None) -> str:
        """Gets the Zabbix Graph by Graph ID and save to file based on output_path

        Arguments:
            graph_id {str} -- Zabbix Graph object ID
            from_date {str} -- Time to graph from like "now-x", "2019-08-03 16:20:04" etc (default: now-1d)
            to_date {str} -- Time to graph until like "now", "2019-08-03 16:20:04" etc (default: now)
            width {str} -- Width of graph (default: 1782)
            height {str} -- Height of graph (default: 452)
            output_path {str} -- (default: os.getcwd())

        Returns:
            file_name {str} -- The name of the saved graph image
        """
        self._validate_times(from_date=from_date, to_date=to_date)
        self._validate_inputs(from_date=from_date,
                              to_date=to_date, width=width, height=height)

        with self.SESSION.get(
                f"{self.BASE_URL}/chart2.php?graphid={graph_id}&from={from_date}&to={to_date}"
                f"&profileIdx=web.graphs.filter&width={width}&height={height}",
                stream=True) as image:
            file_name = self._save(
                image, f"graph-{graph_id}-from-{from_date}-to-{to_date}", output_path)

        return file_name

    def _get_by_itemids(self,
                        item_ids: list,
                        from_date: str = "now-1d",
                        to_date: str = "now",
                        width: str = "1782",
                        height: str = "452",
                        batch: str = "1",
                        graph_type: str = "0",
                        output_path: str = None) -> str:
        """Gets the Zabbix Graph by Item ID(s) and save to file based on output_path

        Arguments:
            item_ids {list(str)} -- Zabbix Graph object ID
            from_date {str} -- Time to graph from like "now-x", "2019-08-03 16:20:04" etc (default: now-1d)
            to_date {str} -- Time to graph until like "now", "2019-08-03 16:20:04" etc (default: now)
            width {str} -- Width of graph (default: 1782)
            height {str} -- Height of graph (default: 452)
            batch {str} -- Whether to get all values (0) or averages (1) (default: 1)
            type {str} -- Whether to get normal overlay graph (0) or stacked graph (1) (default: 0)
            output_path {str} -- Path to save to (default: None)

        Returns:
            file_name {str} -- The name of the saved graph image
        """
        self._validate_times(from_date=from_date, to_date=to_date)
        self._validate_inputs(from_date=from_date,
                              to_date=to_date, width=width, height=height, batch=batch)

        encoded_itemids = "&".join(
            [f"itemids%5B{item_id}%5D={item_id}" for item_id in item_ids])
        formatted_itemids = "-".join(item_ids)

        with self.SESSION.get(
                f"{self.BASE_URL}/chart.php?from={from_date}&to={to_date}&{encoded_itemids}"
                f"&type={graph_type}&batch={batch}&profileIdx=web.graphs.filter&width={width}&height={height}"
                f"",
                stream=True) as image:
            file_name = self._save(
                image, f"items-{formatted_itemids}-from-{from_date}-to-{to_date}", output_path)

        return file_name

    def _save(self, image: Response, graph_details: str, output_path: str = None) -> str:
        """Saves Image to file in format 'graphimage-<graph_details>-<<yearmonthday>.png'

        Arguments:
            image {Response} -- Binary stream representing image to be saved
            graph_details {str} -- Either Zabbix Graph or Item ID
            output_path {str} -- Path to save to (default: os.getcwd())

        Returns:
            file_name {str} -- The name of the saved graph image
        """
        output_path = output_path or os.getcwd()
        file_name = PurePath(
            output_path, f"zabbix_{graph_details}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.png").__str__()
        try:
            with open(file_name, 'wb') as f:
                for chunk in image.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive new chunks
                        f.write(chunk)
        except FileNotFoundError as ex:
            logger.error(
                f"_save(): Unable to save to output_path:{output_path}")
            logger.error(
                f"    Exception:{ex}")
            return ""

        logger.debug(f"_save(): Saved GraphImage to {file_name}")
        return file_name

    def _validate_times(self, from_date: str, to_date: str):
        # TODO: validate times in correct format
        # Can be "now-x" or "2019-08-03 16:20:04" (note this must be encoded)
        pass

    def _validate_inputs(self, **kwargs):
        # TODO: validate inputs have acceptable values and type
        pass


class GraphImageAPI(GraphImage):
    """Helper class for easier Zabbix Graph Image calls"""

    def __init__(self,
                 base_url: str = None,
                 username: str = None,
                 password: str = None,
                 output_path: str = None,
                 ssl_verify: bool = True):
        """Initialise the GraphImage session (including login)

        Arguments:
            base_url {str} -- Base URL to Zabbix (default: ZABBIX_SERVER environment variable or
                                                    https://localhost/zabbix)
            username {str} -- Zabbix Username (default: ZABBIX_USER environment variable or 'Admin')
            password {str} -- Zabbix Password (default: ZABBIX_PASSWORD environment variable or 'zabbix')
            output_path {str} -- Path of directory to save to (default: os.getcwd())
            ssl_verify {bool} -- Whether to attempt SSL verification during call (default: True)
        """
        super().__init__(base_url, username, password, ssl_verify=ssl_verify)
        self.ZAPI = ZabbixAPI(base_url, ssl_verify=ssl_verify)
        self.ZAPI.login(username, password)
        self.OUTPUT_PATH = output_path

    def get_by_graphid(self, graph_id: str,
                       from_date: str = "now-1d",
                       to_date: str = "now",
                       width: str = "1782",
                       height: str = "452") -> str:
        return self._get_by_graphid(graph_id=graph_id, from_date=from_date, to_date=to_date,
                                    width=width, height=height, output_path=self.OUTPUT_PATH)

    def get_by_itemids(self, item_ids: list,
                       host_names: list = None,
                       from_date: str = "now-1d",
                       to_date: str = "now",
                       width: str = "1782",
                       height: str = "452",
                       batch: str = "1",
                       graph_type: str = "0"):
        return self._get_by_itemids(item_ids=item_ids, from_date=from_date, to_date=to_date, width=width,
                                    height=height, batch=batch, graph_type=graph_type, output_path=self.OUTPUT_PATH)

    def get_by_itemkeys(self, item_keys: list,
                        host_names: list = None,
                        from_date: str = "now-1d",
                        to_date: str = "now",
                        width: str = "1782",
                        height: str = "452",
                        graph_type: str = "0"):
        if not item_keys:
            raise ValueError("item_keys cannot be an empty string")

        if host_names:
            host_ids = [host['hostid']
                        for host in self.ZAPI.host.get(filter={'host': host_names})]
            items = [item for item in self.ZAPI.item.get(
                hostids=host_ids, filter={'key_': item_keys})]
        else:
            items = [item for item in self.ZAPI.item.get(
                search={'key_': item_keys})]

        if not items:
            logger.warn("get_by_graphname: No graphs returned")
            return [""]
        else:
            return self.get_by_itemids(item_ids=[item['itemid'] for item in items], from_date=from_date,
                                       to_date=to_date, width=width, height=height, graph_type=graph_type)

    def get_by_itemnames(self, item_names: list,
                         host_names: list = None,
                         from_date: str = "now-1d",
                         to_date: str = "now",
                         width: str = "1782",
                         height: str = "452",
                         batch: str = "1",
                         graph_type: str = "0"):
        if not item_names:
            raise ValueError("item_names cannot be an empty string")

        if host_names:
            host_ids = [host['hostid']
                        for host in self.ZAPI.host.get(filter={'host': host_names})]
            items = [item for item in self.ZAPI.item.get(
                hostids=host_ids, search={'name': item_names})]
        else:
            items = [item for item in self.ZAPI.item.get(
                search={'name': item_names})]

        if not items:
            logger.warn("get_by_graphname: No graphs returned")
            return [""]
        else:
            return self.get_by_itemids(item_ids=[item['itemid'] for item in items], from_date=from_date,
                                       to_date=to_date, width=width, height=height, graph_type=graph_type)

    def get_by_graphname(self, graph_name: str,
                         host_names: list = None,
                         from_date: str = "now-1d",
                         to_date: str = "now",
                         width: str = "1782",
                         height: str = "452") -> list:
        """Get graph images by graph name (e.g. 'CPU')

        Arguments:
            graph_name {str} == filter by graph name
            host_names {list} == filter by host names (default: None, so get for ALL hosts),
            from_date {str} -- Time to graph from like "now-x", "2019-08-03 16:20:04" etc (default: now-1d)
            to_date {str} -- Time to graph until like "now", "2019-08-03 16:20:04" etc (default: now)
            width {str} -- Width of graph (default: 1782)
            height {str} -- Height of graph (default: 452)
        """
        if not graph_name:
            raise ValueError("graph_name cannot be an empty string")

        if host_names:
            host_ids = [host['hostid']
                        for host in self.ZAPI.host.get(filter={'host': host_names})]
            graphs = [graph for graph in self.ZAPI.graph.get(hostids=host_ids)
                      if graph_name.lower() in graph['name'].lower()]
        else:
            graphs = [graph for graph in self.ZAPI.graph.get()
                      if graph_name.lower() in graph['name'].lower()]

        if not graphs:
            logger.warn("get_by_graphname: No graphs returned")
            return [""]
        else:
            return [self.get_by_graphid(graph_id=graph['graphid'], from_date=from_date,
                                        to_date=to_date, width=width, height=height)
                    for graph in graphs]
