from itertools import groupby
from pybix import ZabbixAPI, GraphImageAPI
from jinja2 import Environment, PackageLoader, select_autoescape
import logging
import tempfile
import os
import sys


logger = logging.getLogger(__name__)


class Reporting:
    """ Contains methods to allow reporting """

    _SUPPORTED_OUTPUT_FORMATS = ["pdf", "html"]

    def __init__(self, **kwargs):
        # Set and perform validation of known inputs, prior to doing anything
        self._OUTPUT_FORMAT = self._validate_output_format(
            kwargs.get('output_format'))

    def save(self, compiled_html):
        if self._OUTPUT_FORMAT == "html":
            raise NotImplementedError("Not implemented yet")
        elif self._OUTPUT_FORMAT == "pdf":
            self._save_as_pdf()
        else:
            # Shouldn't be able to get this far since we validate on init
            raise TypeError("Unknown output format.")

    def _save_as_pdf(self):
        raise NotImplementedError("Not implemented yet")

    def _validate_output_format(self, output_format: str) -> str:
        output_format = output_format.lower()

        if not output_format or output_format not in self._SUPPORTED_OUTPUT_FORMATS:
            logger.warning("Unable to determine output format or not in supported types"
                           ", falling back to PDF")
            output_format = "pdf"

        return output_format


class GraphReporting(Reporting):
    """ Gets and outputs all Graphs for input  """

    def __init__(self, output_format: str = "pdf"):
        super().__init__(output_format=output_format)

    def run(self,
            url: str = None,
            user: str = None,
            password: str = None,
            ssl_verify: bool = True,
            hosts: list = None,
            hostgroups: list = None,
            from_date: str = "now-1M",
            to_date: str = "now",):
        with tempfile.TemporaryDirectory() as TEMP_DIR:
            # Obtain Zabbix hosts metadata
            with ZabbixAPI(url=url, ssl_verify=ssl_verify) as ZAPI:
                ZAPI.login(user=user, password=password)
                GRAPHS = self._get_graphs(ZAPI, hosts, hostgroups)

            # Save all graphs per host to file, storing save path to metadata
            GAPI = GraphImageAPI(url=url,
                                 user=user,
                                 password=password, ssl_verify=ssl_verify, output_path=TEMP_DIR)
            for index, graph in enumerate(GRAPHS):
                GRAPHS[index]["file_path"] = GAPI.get_by_graph_id(graph_id=graph["graphid"],
                                                                  from_date=from_date,
                                                                  to_date=to_date)

            # Compile into html based report and output to alternate format if appropriate
            self._output(self._compile(GRAPHS))

    def _get_graphs(self, zabbix_api: ZabbixAPI, hosts: list, hostgroups: list) -> list:
        """ Gets all hosts with graphs for input hosts AND hostgroups """
        logger.debug(f"inputs: hosts={hosts} - hostgroups={hostgroups}")

        args = dict()

        if not hosts and not hostgroups:
            logger.warn(
                "No hostgroups or hosts used so getting all, this may result in long processing times")
        if hosts:
            args["hostids"] = [host["hostid"] for host in zabbix_api.host.get(
                filter={"host": hosts}, output="hostid")]
        if hostgroups:
            args["groupids"] = [group["groupid"] for group in zabbix_api.hostgroup.get(
                filter={"hostgroup": hostgroups}, output="groupid")]

        logger.debug(f"args={args}")

        return zabbix_api.graph.get(**args, selectHosts=True)

    def _compile(self, graphs: list) -> str:
        # Group saved graphs per host
        sorted_graphs = {host: [graph for graph in grouped_graphs] for host, grouped_graphs in groupby(
            graphs, key=lambda x: x['hosts'][0]['host'])}

        # Using Jinja templating, compile html of report
        env = Environment(
            loader=PackageLoader('reporting', 'templates'),
            autoescape=select_autoescape(['html'])
        )
        template = env.get_template('graph_report_template.html')
        return template.render(page_title="test", sorted_graphs=sorted_graphs.items())

    def _output(self, compiled_html):
        raise NotImplementedError("Not yet added")


# DEBUG
if __name__ == "__main__":
    pass
