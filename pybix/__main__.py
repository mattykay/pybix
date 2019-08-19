#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
    pybix.py <method> [--zabbix-server=ZABBIX_SERVER] [--zabbix-user=ZABBIX_USER] 
            [--zabbix-password=ZABBIX_PASSWORD] [<args> ...]
    pybix.py (-c CONFIG | --config CONFIG) [--zabbix-server=ZABBIX_SERVER] [--zabbix-user=ZABBIX_USER]
            [--zabbix-password=ZABBIX_PASSWORD]
    pybix.py (-h | --help)
    pybix.py --version

Arguments:
  method        either Zabbix API reference e.g. 'host.get' or 'graphimage'
  args          what arguments to pass to API call

Options:
  -h, --help
  --version
  --output-path=PATH                 Where to save graphs to default: cwd
  -c=CONFIG, --config=CONFIG         Use config file values instead of CLI arguments
  --zabbix-server=ZABBIX_SERVER      [default: https://localhost/zabbix]
  --zabbix-user=ZABBIX_USER          [default: Admin]
  --zabbix-password=ZABBIX_PASSWORD  [default: zabbix]
"""
from docopt import docopt
from os import path
import logging.config
import pybix

logger = logging.getLogger(__name__)

def config():
    pass

def main():
    arguments = docopt(__doc__, version=pybix.__version__)

    # Validate in expected structure
    if arguments['<method>'] and "." not in arguments['<method>']:
        raise ValueError(
            "Missing fullstop so appears invalid (expecting 'object.method', e.g. 'host.get' or 'graphimage.graphname')"
        )

    # Setup logging
    logging.config.fileConfig(path.join(path.dirname(path.abspath(__file__)),
                                        'logging.ini'),
                              disable_existing_loggers=False)
    logger.debug(arguments)

    # Format args into dictionary to pass later
    try:
        FORMATTED_ARGUMENTS = {
            key: value
            for key, value in
            [args.split("=") for args in arguments['<args>']]
        }
        logger.debug(FORMATTED_ARGUMENTS)
    except ValueError as ex:
        logger.debug(ex)
        logger.error(
            "Unable to format arguments, should be in format: key1=value1 key2=value2"
        )
        exit(1)

    if arguments['<method>'] == "graphimage":
        raise NotImplementedError("Not yet supported")
    else:
        raise NotImplementedError("Not yet supported")


if __name__ == '__main__':
    main()
