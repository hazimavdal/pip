import unittest
from avdal import annotations


def fails(f, *args, **kwargs):
    try:
        f(*args, **kwargs)
        return False
    except:
        return True


class TestTyping(unittest.TestCase):
    def test_enforce_static_annotations(self):

        @annotations.enforce_types
        def f1(a: str, b: int):
            pass

        self.assertFalse(fails(f1, "a", 1))
        self.assertTrue(fails(f1, "a", "1"))

        @annotations.enforce_types
        def f2(a: str, b: int, c: str = "", d=1):
            pass

        self.assertFalse(fails(f2, "a", 1, "", 1))
        self.assertFalse(fails(f2, "a", 1, "", ""))
        self.assertTrue(fails(f2, "a", 1, 1, ""))

        @annotations.enforce_types
        def f3(a=1, b=2, c: str = ""):
            pass

        self.assertFalse(fails(f3, a=2))
        self.assertFalse(fails(f3, 0, b=2))
        self.assertFalse(fails(f3, c="1", a=2))
        self.assertFalse(fails(f3, 1, 2))
        self.assertTrue(fails(f3, 1, 2, 1))
