from datetime import datetime
from itertools import groupby
from pybix import ZabbixAPI, GraphImageAPI
from jinja2 import Environment, PackageLoader, select_autoescape
import logging
import tempfile
import weasyprint


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
            to_date: str = "now",
            stylesheet_paths: list = [],
            skip_collated_graphs: bool = True):
        with tempfile.TemporaryDirectory() as TEMP_DIR:
            # Obtain Zabbix hosts metadata
            with ZabbixAPI(url=url, ssl_verify=ssl_verify) as ZAPI:
                ZAPI.login(user=user, password=password)
                GRAPHS = self._get_graphs(ZAPI, hosts, hostgroups)

            # Skip any graphs with more than one host (i.e. plotting multiple servers on one graph)
            if skip_collated_graphs:
                GRAPHS = [graph for graph in GRAPHS if len(
                    graph['hosts']) == 1]

            # Save all graphs per host to file, storing save path to metadata
            GAPI = GraphImageAPI(url=url, user=user, password=password,
                                 ssl_verify=ssl_verify, output_path=TEMP_DIR)
            for index, graph in enumerate(GRAPHS):
                # Tested Portrait ratio 500x150, landscape ratio 800 x 200
                GRAPHS[index]["file_path"] = "file://" + GAPI.get_by_graph_id(graph_id=graph["graphid"],
                                                                              from_date=from_date,
                                                                              to_date=to_date,
                                                                              width="560",
                                                                              height="150")
                logger.debug("Added %s", GRAPHS[index]['file_path'])
            # Compile into html based report and output to alternate format if appropriate
            self._output(self._compile(GRAPHS, from_date=from_date,
                                       to_date=to_date),
                         stylesheet_paths=stylesheet_paths)

    def _get_graphs(self, zabbix_api: ZabbixAPI, hosts: list, hostgroups: list) -> list:
        """ Gets all hosts with graphs for input hosts AND hostgroups """
        logger.debug("inputs: hosts=%s - hostgroups=%s", hosts, hostgroups)

        args = dict()

        if not hosts and not hostgroups:
            logger.warn(
                "No hostgroups or hosts used so getting all, this may result in long processing times")
        if hosts:
            args["hostids"] = [host["hostid"] for host in zabbix_api.host.get(
                filter={"host": hosts}, output="hostid")]
        if hostgroups:
            args["groupids"] = [group["groupid"] for group in zabbix_api.hostgroup.get(
                filter={"name": hostgroups}, output="groupid")]

        logger.debug("args=%s", args)

        return zabbix_api.graph.get(**args, selectHosts=True)

    def _compile(self, graphs: list, from_date: str, to_date: str) -> str:
        """ Uses Jinja templating """
        # Group saved graphs per host
        sorted_graphs = {host: [graph for graph in grouped_graphs] for host, grouped_graphs in groupby(
            graphs, key=lambda x: x['hosts'][0]['host'])}
        env = Environment(
            loader=PackageLoader('reporting', 'templates'),
            autoescape=select_autoescape(['html'])
        )
        template = env.get_template('base.html')
        return template.render(page_title="Zabbix Report", sorted_graphs=sorted_graphs.items(), from_date=from_date,
                               to_date=to_date, generated_time=datetime.now().strftime('%Y-%m-%d %H:%m'))

    def _output(self, compiled_html, stylesheet_paths):
        """ Uses weasyprint to render html to pdf"""
        stylesheets = [weasyprint.CSS(stylesheet_path)
                       for stylesheet_path in stylesheet_paths]
        document = weasyprint.HTML(string=compiled_html).render(
            stylesheets=stylesheets)
        document.write_pdf(
            target=f"zabbix-report-{datetime.now().strftime('%Y-%m-%d_%H-%m')}.pdf")

    def _generate_outline_str(self, bookmarks, indent=0):
        # TODO - move to Jinja template and use references like https://github.com/Kozea/WeasyPrint/tree/gh-pages/samples/report
        outline_str = ""
        for i, (label, (page, _, _), children, _) in enumerate(bookmarks, 1):
            outline_str += (
                f'<div style="position:absolute; left:{indent * 5}px;">{i}. {label.lstrip("0123456789. ")}</div><br />')
            outline_str += self._generate_outline_str(children, indent + 2)
        return outline_str
