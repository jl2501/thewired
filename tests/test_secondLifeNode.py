import pytest

from thewired.namespace import SecondLifeNode

@pytest.fixture
def mock_attribute_map():
    def mock_provider_callable():
        print("mocked provider called!")
        return "just a value to return"

    return {
        "attribute_1" : "a value for attribute_1",
        "attribute_2" : "a.mock.provider.namespace.nsid",
        "attribute_3" : mock_provider_callable
    }



def test_SecondLife_instantation(mock_attribute_map):
    MapNode = SecondLifeNode(nsid=".test.nsid.string", secondlife=mock_attribute_map)
    assert str(MapNode.nsid) == '.test.nsid.string'
    assert MapNode._secondlife.keys() == mock_attribute_map.keys()

def test_SecondLife_map1(mock_attribute_map):
    MapNode = SecondLifeNode(nsid=".test.nsid.string", secondlife=mock_attribute_map)
    assert MapNode.attribute_1 == mock_attribute_map.get('attribute_1')
    assert MapNode.attribute_3 == mock_attribute_map.get('attribute_3').__call__()
