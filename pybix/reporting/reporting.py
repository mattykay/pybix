from pybix import ZabbixAPI, GraphImageAPI
import logging
import tempfile

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
            hosts: list = None,
            hostgroups: list = None,
            from_date: str = "now-1M",
            to_date: str = "now",):
        with tempfile.TemporaryDirectory() as TEMP_DIR:
            # Obtain Zabbix hosts metadata
            with ZabbixAPI(url=url) as ZAPI:
                ZAPI.login(user=user, password=password)
                GRAPHS = self._get_graphs(ZAPI, hosts, hostgroups)

            # Save all graphs per host to file, storing save path to metadata
            with GraphImageAPI(url=url,
                               user=user,
                               password=password) as GAPI:
                for index, graph in enumerate(GRAPHS):
                    GRAPHS[index]["file_path"] = GAPI.get_by_graphid(graph_id=graph["graphid"],
                                                                     from_date=from_date,
                                                                     to_date=to_date,
                                                                     output_path=TEMP_DIR)

            # Compile into report based on _OUTPUT_FORMAT
            # TODO

            # Output
            # TODO

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

        return zabbix_api.graph.get(**args)

    def _compile_html(self):
        raise NotImplementedError("Not implemented yet")


# DEBUG
if __name__ == "__main__":
    pass
