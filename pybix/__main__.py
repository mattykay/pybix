#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
    pybix.py <method> [--zabbix-server=ZABBIX_SERVER] [--zabbix-user=ZABBIX_USER]
            [--zabbix-password=ZABBIX_PASSWORD] [--ignore-ssl-verify] [(-v | --verbose)] [<args> ...]
    pybix.py (-h | --help)
    pybix.py --version

Arguments:
  method        either Zabbix API reference as '<object>.<action>' or GraphImage API as 'graphimage.<search_type>' (e.g. 'host.get' or 'graphimage.graph_id')
  args          what arguments to pass to API call

Options:
  -h, --help
  --version
  -v, --verbose                      Whether to use verbose logging [default: False]
  --output-path=PATH                 Where to save graphs to default: cwd
  --zabbix-server=ZABBIX_SERVER      Server URL - default: ZABBIX_SERVER env or https://localhost/zabbix
  --zabbix-user=ZABBIX_USER          Username - default: ZABBIX_USER env or Admin
  --zabbix-password=ZABBIX_PASSWORD  Password - default: ZABBIX_PASSWORD env or zabbix
  --ignore-ssl-verify                Whether to ignore SSL verification for API [default: False]
"""
from docopt import docopt
from os import path, environ
import re
import ast
import logging.config
import pybix

logger = logging.getLogger(__name__)


def valid_method(method):
    """Validates whether input method conforms to what we expect (i.e. '<object>.<action>' like 'host.get' or 'graphimage.graph_id')

        Arguments:
            method {str} -- The API method to perform (e.g. 'host.get' or 'graphimage.graph_id')
    """
    error = ""

    if method and "." not in method:
        error = "Missing fullstop so appears invalid (expecting 'object.method', e.g. 'host.get' or 'graphimage.graph_name')"
    elif method and method.count('.') > 1:
        error = "Method contains multiple fullstops (expecting 'object.method', e.g. 'host.get' or 'graphimage.graph_name')"
    elif "log" in method:
        error = "Unable to perform logout/login methods via CLI, these are handled by this module."

    return True if not error else False


def format_arguments(arguments, method):
    """Formats the CLI arguments into appropriate form based on method

        Arguments:
            arguments {list[str]} -- The input arguments/paramaters to pass to API method
            method {str} -- The API method to perform (e.g. 'host.get' or 'graphimage.graph_id')
    """
    try:
        FORMATTED_ARGUMENTS = {
            key: value
            for key, value in
            [re.split(r'(^\w*)=(.*)', args)[1:3] for args in arguments]
        }

        # Handle if value is dictionary or list
        for key, value in FORMATTED_ARGUMENTS.items():
            # for filter="{name:[matthew,matt]}"
            if '[' in value and '{' in value:
                value = value.replace('{', '{\'').replace('[', '[\'').replace(
                    ':', '\':').replace(']', '\']').replace(',', '\',\'')
            # for host_names=[server1,server2]
            elif '[' in value:
                value = value.replace('[', '[\'').replace(',',
                                                          '\',\'').replace(
                                                              ']', '\']')
            # for filter="{name:matthew}"
            elif '{' in value:
                value = value.replace('{', '{\'').replace(':',
                                                          '\':\'').replace(
                                                              '}', '\'}')
            # for item search_types (e.g. item_ids=123) that expects list (e.g. item_ids=[123])
            elif "graphimage" in method and method.split(".")[1].endswith(
                    's') and key == method.split(".")[1] and '[' not in value:
                FORMATTED_ARGUMENTS[method.split(".")[1]] = [
                    v for v in value.split(',')
                ]
                continue
            # for value=key
            else:
                continue

            FORMATTED_ARGUMENTS[key] = ast.literal_eval(value)

        logger.debug(FORMATTED_ARGUMENTS)
        return FORMATTED_ARGUMENTS
    except (ValueError, SyntaxError) as ex:
        logger.debug(ex)
        logger.error(
            "Unable to interpret arguments, should be like: key1=value1 or key1='some value1'"
            " or key2=\"{value2:[subvalue1, subvalue2]}\" or key3=\"{value3:subvalue3}\""
        )
        return None


def main():
    arguments = docopt(__doc__, version=pybix.__version__)

    # Validate in expected structure
    if not valid_method(arguments['<method>']):
        exit(1)

    # Setup logging
    logging.config.fileConfig(path.join(path.dirname(path.abspath(__file__)),
                                        'logging.ini'),
                              disable_existing_loggers=False)
    if arguments['--verbose']:
        logging.getLogger().setLevel(logging.DEBUG)

    # Format args into dictionary to pass later, exiting if error
    logger.debug("Initial arguments: %s", arguments)
    FORMATTED_ARGUMENTS = format_arguments(arguments['<args>'],
                                           arguments['<method>'])

    # Set args & handle defaults
    URL = arguments['--zabbix-server'] or environ.get(
        'ZABBIX_SERVER') or 'http://localhost/zabbix'
    USER = arguments['--zabbix-user'] or environ.get('ZABBIX_USER') or 'Admin'
    PASSWORD = arguments['--zabbix-password'] or environ.get(
        'ZABBIX_PASSWORD') or 'zabbix'
    SSL_VERIFY = not arguments['--ignore-ssl-verify'] or False

    # Process depending on whether graphimage or other
    try:
        if "graphimage" in arguments['<method>']:
            if not FORMATTED_ARGUMENTS:
                exit(1)

            ZAPI = pybix.GraphImageAPI(url=URL,
                                       user=USER,
                                       password=PASSWORD,
                                       ssl_verify=SSL_VERIFY)
            print(
                ZAPI.get(arguments['<method>'].split(".")[1],
                         **FORMATTED_ARGUMENTS))
            ZAPI.ZAPI.logout()
        elif "reporting" in arguments['<method>']:
            OUTPUT_DIRECTORY = FORMATTED_ARGUMENTS.pop(
                "output_directory", '') or ''
            ZAPI = pybix.reporting.GraphReporting(
                output_directory=OUTPUT_DIRECTORY)
            print(ZAPI.run(url=URL,
                           user=USER,
                           password=PASSWORD,
                           ssl_verify=SSL_VERIFY,
                           **FORMATTED_ARGUMENTS))
        else:
            with pybix.ZabbixAPI(url=URL, ssl_verify=SSL_VERIFY) as ZAPI:
                ZAPI.login(user=USER, password=PASSWORD)
                print(
                    ZAPI.do_request(arguments['<method>'],
                                    FORMATTED_ARGUMENTS)['result'])
    except (TypeError, RuntimeError) as ex:
        logger.error("Unable to get '%s': %s", arguments['<method>'], ex)
        exit(1)

    exit(0)


if __name__ == '__main__':
    main()
