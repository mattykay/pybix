# pybix

**NOTE: This module is still in development and may not be fully stable. Use at own risk.**

## Description

Python based Zabbix API utility containing helper functions and CLI capabilities.

Takes inspiration from existing Python-Zabbix API modules like [lukecyca/pyzabbix](https://github.com/lukecyca/pyzabbix) and [adubkov/py-zabbix](https://github.com/adubkov/py-zabbix).

While this module can be used in a similar way, the aim is to add a few out of the box helper functions and CLI handling for a more "batteries included" module. For example GraphImage as described in usage which enables saving Zabbix graphs which is not possible via the API at this time.

## Install

### Pip

```
pip install pybix
```

### Docker

TODO - not yet available.

## Requirements

* Python 3.6 or greater
* Zabbix 2.0 or greater
  * Only tested on >4.0

## Usage

### Zabbix API

Refer to [Zabbix Offical API object](https://www.zabbix.com/documentation/4.2/manual/api/reference) references for objects that can be queried and their parameters.

API structure all uses format like `ZAPI.<object>.<action>(<parameters>)` e.g. `ZAPI.host.get(output='extend')`.

#### Import as Python module

##### Directly

```python
from pybix import ZabbixAPI
ZAPI = ZabbixAPI(url="http://localhost/zabbix")
ZAPI.login(user="Admin", password="zabbix")

# Print all monitored hosts
for host in ZAPI.host.get(output="extend",monitored_hosts=1):
    print(host['host'])

ZAPI.logout() # Explicitly logout to clear Zabbix session
```

##### With context manager to handle logout

Note: Login still must be done manually (as in the future we may allow passing existing session, hence might not need to login everytime).

```python
from pybix import ZabbixAPI

with ZabbixAPI() as ZAPI: # using defaults for server
    ZAPI.login() # using defaults for user, password

    # Print all monitored hosts
    for host in ZAPI.host.get(output="extend",monitored_hosts=1):
        print(host['host'])
```

#### CLI

```python
# TODO
```

### Graph Image Export

Zabbix does not let you export graphs via API (only the configuration for them). Instead of using `ZabbixAPI` class, use included `GraphImage`.

```python
from pybix import GraphImageAPI
graph = GraphImageAPI(url="http://localhost/zabbix",
                      user="Admin",
                      password="zabbix")
graph.get_by_graphid("4038") # will save to png file in current working directory
graph.get_by_graphname("CPU") # will save any "CPU" graph png images to file in current working directory
```

## Known Issues

### SSL Verification

* If server using a self signed cert or serving on HTTPS

### User configuration

* Zabbix user used during API calls must have viewing rights to queried Zabbix object
  * i.e. appropriate hostgroup read rights to user/usergroup OR super admin
  * If it does not, it will simply return empty results without warning

### Graph Items Usage

* User used to login must have frontend access (i.e. in Zabbix user group, set frontend access to true)

## Contributing

Feel free to raise any feature requests/problems/improvements as issue or pull request via [GitHub](https://github.com/mattykay/pybix).
