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

#### Zabbix API CLI

##### Zabbix API CLI Usage

```bash
Usage:
    pybix.py <method> [--zabbix-server=ZABBIX_SERVER] [--zabbix-user=ZABBIX_USER]
            [--zabbix-password=ZABBIX_PASSWORD] [--ssl-verify] [(-v | --verbose)] [<args> ...]
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
  --zabbix-server=ZABBIX_SERVER      [default: https://localhost/zabbix]
  --zabbix-user=ZABBIX_USER          [default: Admin]
  --zabbix-password=ZABBIX_PASSWORD  [default: zabbix]
  --ssl-verify                       Whether to use SSL verification for API [default: True]
```

##### Zabbix API CLI Example

```bash
python -m pybix host.get filter="{host:server1}" # Get host server1
python -m pybix host.get filter="{host:[server1,server2]}" # Get host server1 and server2
python -m pybix user.get # Get all Users
```

### Graph Image Export

Zabbix does not let you export graphs via API (only the configuration for them). Instead of using `ZabbixAPI` class, use included `GraphImage`.

#### GraphImage Python Example

```python
from pybix import GraphImageAPI
graph = GraphImageAPI(url="http://localhost/zabbix",
                      user="Admin",
                      password="zabbix")
graph.get_by_graph_id("4038") # will save to png file in current working directory
graph.get_by_graphname("CPU") # will save any "CPU" graph png images to file in current working directory
```

#### GraphImage CLI

##### GraphImage CLI Usage

Refer to [ZabbixAPI usage](#####zabbix-api-cli-usage).

`search_types` include `graph_id, graph_name, item_names, item_keys, item_ids`

##### GraphImage CLI Examples

```bash
python -m pybix graphimage.graph_name graph_name=CPU host_names=server1
python -m pybix graphimage.graph_name graph_name=CPU host_names=[server1,server2]
python -m pybix graphimage.item_names item_names=CPU host_names=server1
python -m pybix graphimage.item_keys item_keys=availability.agent.available host_names=server1

# Not as useful, but is what above methods call after calculating id
python -m pybix graphimage.graph_id graph_id=4038 host_names=server1
python -m pybix graphimage.item_ids item_ids=138780,138781 host_names=server1
```

## Known Issues

### SSL Verification

* If server using a self signed cert or serving on HTTPS, will need to use `ssl_verify` overide

### User configuration

* Zabbix user used during API calls must have viewing rights to queried Zabbix object
  * i.e. appropriate hostgroup read rights to user/usergroup OR super admin
  * If it does not, it will simply return empty results without warning

### Graph Items Usage

* User used to login must have frontend access (i.e. in Zabbix user group, set frontend access to true)
* No error messages or warnings if graph is invalid (i.e. wrong values used to call it)

## Contributing

Feel free to raise any feature requests/problems/improvements as issue or pull request via [GitHub](https://github.com/mattykay/pybix).
