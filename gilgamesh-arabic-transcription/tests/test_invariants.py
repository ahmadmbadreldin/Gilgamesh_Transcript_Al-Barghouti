import unittest

from src.diacritization import assert_same_letters
from src.merge_segments import overlap_size


class InvariantTests(unittest.TestCase):
    def test_overlap(self):
        self.assertEqual(overlap_size(["قال", "جلجامش"], ["جلجامش", "مضى"]), 1)

    def test_diacritization_invariant(self):
        assert_same_letters("جلجامش", "جِلْجَامِش")


if __name__ == "__main__":
    unittest.main()

