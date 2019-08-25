import pytest
from pybix.__main__ import format_arguments, valid_method


class TestMain(object):
    def test_valid_method(self):
        assert valid_method('graphimage.graph_id')
        assert valid_method('host.get')
        # Missing fullstop
        assert not valid_method('host')
        assert not valid_method('graphimage')
        # Multiple fullstops
        assert not valid_method('graphimage.graph_id.get')
        # Unsupported API calls
        assert not valid_method('user.login')
        assert not valid_method('user.logout')

    def test_format_arguments(self):
        # Single args
        assert format_arguments(['graphid=1'], 'graphimage.graph_id') == {
            'graphid': '1'
        }
        # Multi args
        assert format_arguments(['hostid=1', 'host=server'], 'host.get') == {
            'hostid': '1',
            'host': 'server'
        }
        # Spaces in argument and list
        assert format_arguments(
            ['item_names=agent availability', 'host_names=[server1,server2]'],
            'graphimage.item_names') == {
                'item_names': ['agent availability'],
                'host_names': ['server1', 'server2']
            }
        # Dictionary
        # TODO
