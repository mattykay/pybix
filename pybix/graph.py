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
            f"GraphImage(): Attempting to login to Zabbix server at {self.BASE_URL}/index.php")
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
        self._validate_times(from_date, to_date)

        with self.SESSION.get(
                f"{self.BASE_URL}/chart2.php?graphid={graph_id}&from={from_date}&to={to_date}"
                f"&profileIdx=web.graphs.filter&width={width}&height={height}",
                stream=True) as image:
            file_name = self._save(
                image, f"graph-{graph_id}-from-{from_date}-to-{to_date}", output_path)

        return file_name

    def _get_by_itemids(self,
                        item_ids: list,
                        type: str = 1,
                        from_date: str = "now-1d",
                        to_date: str = "now",
                        width: str = "1782",
                        height: str = "452",
                        output_path: str = None) -> str:
        """Gets the Zabbix Graph by Item ID(s) and save to file based on output_path

        Arguments:
            item_ids {list(str)} -- Zabbix Graph object ID
            type {str} -- Stacked graph (1) or normal overlay graph (0) (default 1)
            from_date {str} -- Time to graph from like "now-x", "2019-08-03 16:20:04" etc (default: now-1d)
            to_date {str} -- Time to graph until like "now", "2019-08-03 16:20:04" etc (default: now)
            width {str} -- Width of graph (default: 1782)
            height {str} -- Height of graph (default: 452)
            output_path {str} -- Path to save to (default: None)

        Returns:
            file_name {str} -- The name of the saved graph image
        """
        # TODO: add ad-hoc graphing support (i.e. graphs per item, NOT actual graph objects)
        #   this is done via "chart.php" not chart2 which requires url encoding for multiple ids
        raise NotImplementedError("Not yet added")

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
            output_path, f"graphimage-{graph_details}-{datetime.now().strftime('%Y%m%d')}.png").__str__()
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
