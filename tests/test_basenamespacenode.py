import unittest

from thewired.namespace import NamespaceNodeBase, Nsid

class TestNamespaceNodeBase(unittest.TestCase):
    def test_nsid(self):
        nsid_s = '.a.b.c'
        nsid = Nsid(nsid_s)
        ns = NamespaceNodeBase(nsid=nsid_s)
        self.assertEqual(ns.nsid, nsid)
