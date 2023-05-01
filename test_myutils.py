import unittest
import myutils

class TestMergeDictionary(unittest.TestCase):

    def test_basic(self):
        # Test case 1: simple merge
        base = {'a': 1, 'b': 2}
        new = {'b': 3, 'c': 4}
        expected = {'a': 1, 'b': 3, 'c': 4}
        myutils.merge_dictionary(new, base)
        self.assertDictEqual(base, expected)

    def test_nested(self):
        # Test case 2: nested dictionary merge
        base = {'a': {'b': 1, 'c': 2}, 'd': 3}
        new = {'a': {'b': 4, 'e': 5}, 'f': 6}
        expected = {'a': {'b': 4, 'c': 2, 'e': 5}, 'd': 3, 'f': 6}
        myutils.merge_dictionary(new, base)
        self.assertDictEqual(base, expected)

    def test_emptybase(self):
        # Test case 3: empty base dictionary
        base = {}
        new = {'a': 1, 'b': {'c': 2}}
        expected = {'a': 1, 'b': {'c': 2}}
        myutils.merge_dictionary(new, base)
        self.assertDictEqual(base, expected)

    def test_emptynew(self):
        # Test case 4: empty new dictionary
        base = {'a': 1, 'b': {'c': 2}}
        new = {}
        expected = {'a': 1, 'b': {'c': 2}}
        myutils.merge_dictionary(new, base)
        self.assertDictEqual(base, expected)

    def test_nooverlap(self):
        # Test case 5: no overlapping keys
        base = {'a': 1}
        new = {'b': 2}
        expected = {'a': 1, 'b': 2}
        myutils.merge_dictionary(new, base)
        self.assertDictEqual(base, expected)

if __name__ == '__main__':
    unittest.main()