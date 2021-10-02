import unittest
import avdal
from avdal.typing import enforce_type_annotations


def fails(f, *args, **kwargs):
    try:
        f(*args, **kwargs)
        return False
    except:
        return True


class TestTyping(unittest.TestCase):
    def test_enforce_static_annotations(self):

        @enforce_type_annotations()
        def f1(a: str, b: int):
            pass

        self.assertFalse(fails(f1, "a", 1))
        self.assertTrue(fails(f1, "a", "1"))

        @enforce_type_annotations()
        def f2(a: str, b: int, c: str = "", d=1):
            pass

        self.assertFalse(fails(f2, "a", 1, "", 1))
        self.assertFalse(fails(f2, "a", 1, "", ""))
        self.assertTrue(fails(f2, "a", 1, 1, ""))
