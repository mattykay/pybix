import requests
import os
import sys


class GraphImage(object):
    """ Class that handles getting/saving Zabbix Graph Images directly """

    def __init__(self,
                 base_url: str = None,
                 username: str = None,
                 password: str = None):
        url = base_url or os.environ.get(
            'ZABBIX_SERVER') or 'https://localhost/zabbix'
        self.BASE_URL = url.replace(
            "/api_jsonrpc.php",
            "") if not url.endswith('/api_jsonrpc.php') else url

        # Perform Login (note: not via Zabbix API since it doesn't
        #   expose graph exports, only configuration)
        payload = {
            'name': username or os.environ.get('ZABBIX_USER') or 'Admin',
            'password': password or os.environ.get('ZABBIX_PASSWORD')
            or 'zabbix',  # noqa: W503
            'enter': 'Sign in'
        }
        self.SESSION = requests.Session()
        self.SESSION.post(f"{self.BASE_URL}/index.php", data=payload)

    def get_by_graph_id(self,
                        graph_id: str,
                        from_date: str = "now-1d",
                        to_date: str = "now",
                        width: str = "1782",
                        height: str = "452",
                        save: bool = False,
                        output_path: str = None):
        self._validate_times(from_date, to_date)

        with self.SESSION.get(
                f"{self.BASE_URL}/chart2.php?graphid={graph_id}&from={from_date}&to={to_date}"
                f"&profileIdx=web.graphs.filter&width={width}&height={height}",
                stream=True) as image:
            if save:
                # Save to file
                output_path = output_path or os.getcwd()
                with open(f"{output_path}/graph-{graph_id}.png", 'wb') as f:
                    for chunk in image.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
            else:
                # Output to console (which can be redirected to file)
                for chunk in image.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        sys.stdout.buffer.write(chunk)

    def get_by_itemids(self,
                       item_ids: list(str),
                       from_date: str = "now-1d",
                       to_date: str = "now",
                       width: str = "1782",
                       height: str = "452",
                       save: bool = False,
                       output_path: str = None):
        # TODO: add ad-hoc graphing support (i.e. graphs per item, NOT actual graph objects)
        #   this is done via "chart.php" not chart2
        raise NotImplementedError("Not yet added")

    def _validate_times(self, from_date: str, to_date: str):
        # TODO: validate times in correct format
        # Can be "now-x" or "2019-08-03 16:20:04" (note this must be encoded)
        pass
