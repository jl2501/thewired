import thewired
import unittest

from thewired.namespace.nsid import Nsid, validate_nsid, is_valid_nsid_str
from thewired.namespace.nsid import sanitize_nsid, make_child_nsid, get_parent_nsid
from thewired.namespace.nsid import get_nsid_parts, find_common_prefix, strip_common_prefix
from thewired.namespace.nsid import list_nsid_segments, get_nsid_ancestry, nsid_basename
from thewired.exceptions import InvalidNsidError

class test_nsid(unittest.TestCase):

    def test_nsid_class(self):
        test_nsid = 'a.b.c.d'
        n = Nsid(test_nsid)
        self.assertEqual(n.nsid, test_nsid)

    def test_nsid_class_sanitization(self):
        test_nsid = 'x..y..z'
        with self.assertRaises(InvalidNsidError):
            Nsid(test_nsid)

    def test_is_valid_nsid_str1(self):
        nsid = 'a.b.c'
        self.assertTrue(is_valid_nsid_str(nsid, fully_qualified=False))

    def test_is_valid_nsid_str2(self):
        nsid = 'a.'
        self.assertFalse(is_valid_nsid_str(nsid))

    def test_is_valid_nsid_str3(self):
        nsid = '.a.b'
        self.assertTrue(is_valid_nsid_str(nsid))

    def test_is_valid_nsid_str4(self):
        nsid = '.a.'
        self.assertFalse(is_valid_nsid_str(nsid))

    def test_validate_nsid1(self):
        nsid = '.a.b.c.'
        with self.assertRaises(InvalidNsidError):
            validate_nsid(nsid)
        
    def test_make_child_nsid1(self):
        parent = 'a.b.c'
        child = 'd'
        self.assertEqual(make_child_nsid(parent, child), 'a.b.c.d')

    def test_make_child_nsid2(self):
        parent = '.'
        child = 'a'
        self.assertEqual(make_child_nsid(parent, child), '.a')

    def test_get_parent_nsid1(self):
        nsid = '.a.b.c.d'
        self.assertEqual('.a.b.c', get_parent_nsid(nsid))

    def test_get_parent_nsid2(self):
        nsid = '.a.b.c.d'
        self.assertEqual('.a.b.c', get_parent_nsid(nsid))

    def test_get_parent_nsid3(self):
        nsid = '.a.b.c.d'
        self.assertEqual('.a.b', get_parent_nsid(nsid, parent_num=2))

    def test_get_parent_nsid4(self):
        nsid = '.a'
        self.assertEqual('.', get_parent_nsid(nsid))

    def test_find_common_prefix1(self):
        nsid1 = 'a.b.c.d'
        nsid2 = 'a.b.x'
        self.assertEqual('a.b', find_common_prefix(nsid1,nsid2))

    def test_find_common_prefix2(self):
        nsid1 = '.a.b.c.d'
        nsid2 = '.a.b.x'
        self.assertEqual('.a.b', find_common_prefix(nsid1,nsid2))

    def test_strip_common_prefix1(self):
        nsid1 = 'a.b.c.d'
        nsid2 = 'a.b.c.x'
        self.assertEqual(('d', 'x'), strip_common_prefix(nsid1, nsid2))

    def test_strip_common_prefix2(self):
        nsid1 = '.a.b.c.d'
        nsid2 = '.a.b.c.x'
        self.assertEqual(('d', 'x'), strip_common_prefix(nsid1, nsid2))

    def test_strip_common_prefix3(self):
        nsid1 = '.a.b.c.d.e.f.g.h'
        nsid2 = '.a.b.c.x'
        self.assertEqual(('d.e.f.g.h', 'x'), strip_common_prefix(nsid1, nsid2))

    def test_list_nsid_segments(self):
        nsid1 = '.a.b.c'
        self.assertEqual(['.','a','b','c'], list_nsid_segments(nsid1))

    def test_list_nsid_segments2(self):
        nsid1 = '.'
        self.assertEqual(['.'], list_nsid_segments(nsid1))

    def test_list_nsid_segments3(self):
        nsid = '.a'
        self.assertEqual(['.', 'a'], list_nsid_segments(nsid))

    def test_get_nsid_parts(self):
        nsid1 = '.a.b.c'
        self.assertEqual(['','a','b','c'], get_nsid_parts(nsid1))

    def test_get_nsid_ancestry(self):
        nsid1 = '.a.b.c'
        nsid1_ancestry = ['.','.a','.a.b', '.a.b.c' ]
        self.assertEqual(get_nsid_ancestry(nsid1), nsid1_ancestry)

    def test_get_new_ancestry(self):
        new_nsid1 = '.a.b.c.d'
        deepest_ancestor_nsid = '.a'
        starting_point =  strip_common_prefix(
            deepest_ancestor_nsid,
            new_nsid1)[1]
        new_ancestry = get_nsid_ancestry(starting_point)
        self.assertEqual(new_ancestry, ['b', 'b.c', 'b.c.d'])

    def test_make_root_nsid(self):
        nsid = Nsid('.')
        self.assertEqual(str(nsid), '.')

    def test_get_basename(self):
        nsid = Nsid('.a.b.c.d.e.f')
        self.assertEqual(nsid_basename(nsid), 'f')

    def test_nsid_with_spaces(self):
        nsid = '.a b c.'
        with self.assertRaises(InvalidNsidError):
            validate_nsid(nsid)
    def test_relative_nsid(self):
        nsid='a.b.c'
        with self.assertRaises(InvalidNsidError):
            validate_nsid(nsid)

if __name__ == '__main__' :
    unittest.main()
