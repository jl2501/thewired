import pytest

from thewired.namespace import NamespaceNodeBase, Nsid, Namespace


@pytest.fixture
def blank_namespace():
    return Namespace()

def test_base_node_nsid(blank_namespace):
    nsid_s = '.a.b.c'
    nsid = Nsid(nsid_s)
    ns = NamespaceNodeBase(nsid=nsid_s, namespace=blank_namespace)
    assert ns.nsid == nsid
