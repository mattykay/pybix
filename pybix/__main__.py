#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
    pybix.py <method> [--zabbix-server=ZABBIX_SERVER] [--zabbix-user=ZABBIX_USER]
            [--zabbix-password=ZABBIX_PASSWORD] [--ssl-verify] [(-v | --verbose)] [<args> ...]
    pybix.py (-h | --help)
    pybix.py --version

Arguments:
  method        either Zabbix API reference e.g. 'host.get' or 'graphimage'
  args          what arguments to pass to API call

Options:
  -h, --help
  --version
  -v, --verbose                      Whether to use verbose logging [default: False]
  --output-path=PATH                 Where to save graphs to default: cwd
  --zabbix-server=ZABBIX_SERVER      [default: https://localhost/zabbix]
  --zabbix-user=ZABBIX_USER          [default: Admin]
  --zabbix-password=ZABBIX_PASSWORD  [default: zabbix]
  --ssl-verify                       Whether to use SSL verification for API [default: True]
"""
from docopt import docopt
from os import path, environ
import re
import ast
import logging.config
import pybix

logger = logging.getLogger(__name__)


def main():
    arguments = docopt(__doc__, version=pybix.__version__)

    # Validate in expected structure
    if arguments['<method>'] and "." not in arguments['<method>']:
        logger.error(
            "Missing fullstop so appears invalid (expecting 'object.method', e.g. 'host.get' or 'graphimage.graphname')"
        )
        exit(1)
    elif "log" in arguments['<method>']:
        logger.error(
            "Unable to perform logout/login methods via CLI, these are handled by this module."
        )
        exit(1)

    # Setup logging
    logging.config.fileConfig(path.join(path.dirname(path.abspath(__file__)),
                                        'logging.ini'),
                              disable_existing_loggers=False)
    if arguments['--verbose']:
        logging.getLogger().setLevel(logging.DEBUG)
    logger.debug(arguments)

    # Format args into dictionary to pass later
    try:
        FORMATTED_ARGUMENTS = {
            key: value
            for key, value in
            [re.split(r'(^\w*)=(.*)', args)[1:3]
             for args in arguments['<args>']]
        }

        # Handle if value is dictionary
        for key, value in FORMATTED_ARGUMENTS.items():
            # for filter="{name:[matthew,matt]}"
            if '[' in value:
                value = value.replace('{', '{\'').replace(
                    '[', '[\'').replace(':', '\':').replace(']', '\']').replace(',', '\',\'')
            # for filter="{name:matthew}"
            elif '{' in value:
                value = value.replace('{', '{\'').replace(
                    ':', '\':\'').replace('}', '\'}')
            # for value=key
            else:
                continue
            FORMATTED_ARGUMENTS[key] = ast.literal_eval(value)

        logger.debug(FORMATTED_ARGUMENTS)
    except (ValueError, SyntaxError) as ex:
        logger.debug(ex)
        logger.error(
            "Unable to interpret arguments, should be like: key1=value1"
            " or key2=\"{value2:[subvalue1, subvalue2]}\" or key3=\"{value3:subvalue3}\""
        )
        exit(1)

    URL = arguments['--zabbix-server'] or environ.get(
        'ZABBIX_SERVER') or 'http://localhost/zabbix'
    USER = arguments['--zabbix-user'] or environ.get(
        'ZABBIX_USER') or 'Admin'
    PASSWORD = arguments['--zabbix-password'] or environ.get(
        'ZABBIX_PASSWORD') or 'zabbix'

    try:
        if "graphimage" in arguments['<method>']:
            ZAPI = pybix.GraphImageAPI(url=URL,
                                       user=USER,
                                       password=PASSWORD,
                                       ssl_verify=arguments['--ssl-verify'])
            print(ZAPI.get(arguments['<method>'].split(
                ".")[1], **FORMATTED_ARGUMENTS))
            ZAPI.ZAPI.logout()
        else:
            with pybix.ZabbixAPI(url=URL, ssl_verify=arguments['--ssl-verify']) as ZAPI:
                ZAPI.login(user=USER, password=PASSWORD)
                print(ZAPI.do_request(
                    arguments['<method>'], FORMATTED_ARGUMENTS)['result'])
    except TypeError as ex:
        logger.error(f"Unable to get '{arguments['<method>']}': {ex}")
        exit(1)

    exit(0)


if __name__ == '__main__':
    main()
