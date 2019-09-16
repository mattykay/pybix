import pybix
import logging

logger = logging.getLogger(__name__)


class Reporting:
    """ Contains methods to allow reporting """

    _SUPPORTED_OUTPUT_FORMATS = ["pdf", "html"]

    def __init__(self, **kwargs):
        # Set and perform validation of known inputs, prior to doing anything
        self._OUTPUT_FORMAT = self._set_output_format(
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

    def _set_output_format(self, output_format: str) -> str:
        output_format = output_format.lower()

        if not output_format or output_format not in self._SUPPORTED_OUTPUT_FORMATS:
            logger.warning("Unable to determine output format or not in supported types"
                           ", falling back to PDF")
            output_format = "pdf"

        return output_format


class GraphReporting(Reporting):
    def __init__(self, output_format: str = "pdf"):
        super().__init__(output_format)

    def run(self, hosts: list, hostgroups: list, output_format: str = "pdf"):
        if not hosts and not hostgroups:
            raise ValueError("Require hosts or hostgroups")

        # Create temporary working directory
        # TODO

        # Get Zabbix metadata, then save all graphs per host
        if hosts and hostgroups:
            raise NotImplementedError("Not implemented yet")
        elif hosts:
            raise NotImplementedError("Not implemented yet")
        elif hostgroups:
            raise NotImplementedError("Not implemented yet")

        # Compile graphs into output_format, saving to cwd
        # TODO

        # Clean-up working directory
        # TODO

    def _compile_html(self):
        raise NotImplementedError("Not implemented yet")
