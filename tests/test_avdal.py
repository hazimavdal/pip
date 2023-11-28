import json
import unittest
from avdal import annotations
from avdal import rbac
from avdal.env import DotEnv
from avdal.dict import AttrDict
from avdal.aql import Filter


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

    def test_auto_attrs(self):
        class A:
            @annotations.auto_attrs
            def __init__(self, a, b, c, d=4, e=5, f=6):
                pass

        a = A(1, 2, 3, 7, f=8)

        self.assertTrue(getattr(a, "a"), 1)
        self.assertTrue(getattr(a, "b"), 2)
        self.assertTrue(getattr(a, "c"), 3)
        self.assertTrue(getattr(a, "d"), 7)
        self.assertTrue(getattr(a, "e"), 5)
        self.assertTrue(getattr(a, "f"), 8)


class TestRbac(unittest.TestCase):
    def test_permset(self):
        r1 = rbac.PermSet("rn:a:b", "read")

        self.assertTrue(r1.check("rn:a:b", {"read"}))
        self.assertTrue(r1.check("rn:a:b", {"*"}))
        self.assertFalse(r1.check("rn:a:b", {"write"}))
        self.assertFalse(r1.check("rn:a:b:c", {"read"}))
        self.assertFalse(r1.check("rn:a:b:c", {"write"}))
        self.assertFalse(r1.check("rn:a", {"write"}))
        self.assertFalse(r1.check("rn:a:*", {"write"}))
        self.assertTrue(r1.check("rn:a:*", {"read"}))
        self.assertTrue(r1.check("rn:*", {"read"}))
        self.assertTrue(r1.check("*", {"read"}))
        self.assertFalse(r1.check("*", {"write"}))
        self.assertTrue(r1.check("*", {"*"}))

        r2 = rbac.PermSet("rn:a:b", "write")

        self.assertFalse(r2.check("rn:a:b", {"read"}))
        self.assertTrue(r2.check("rn:a:b", {"write"}))
        self.assertTrue(r2.check("rn:a:b", {"write", "read"}))
        self.assertTrue(r2.check("rn:a:b", {"update", "write", "read"}))
        self.assertFalse(r2.check("rn:a:b", {"update"}))
        self.assertFalse(r2.check("rn:a:b", set()))
        self.assertTrue(r2.check("rn:a:b", {"*"}))
        self.assertTrue(r2.check("rn:a:b", {"*", "read"}))
        self.assertTrue(r2.check("rn:a:b", {"*", "write"}))
        self.assertTrue(r2.check("rn:a:b", {"*", "update", "read"}))
        self.assertFalse(r2.check("rn:a:b:c", {"*", "update", "read"}))
        self.assertTrue(r2.check("rn:a:b:*", {"*", "update", "read"}))

        r3 = rbac.PermSet("rn:a:b", "read")
        self.assertTrue(r3.check("rn:a:*", {"read"}))
        self.assertTrue(r3.check("rn:a:b:*", {"read"}))
        self.assertFalse(r3.check("rn:a:b:c", {"read"}))
        self.assertFalse(r3.check("rn:a:c", {"read"}))
        self.assertFalse(r3.check("rn:a", {"read"}))


class TestEnv(unittest.TestCase):
    def test_load_env(self):
        env = DotEnv("tests/test_env", prefix="PREFIX")

        expects = AttrDict.from_file("tests/test_env.json")

        for var, v in expects.items():
            if v.get("masked"):
                assert (
                    env.get(var, nullable=True) is None
                ), f"{var}: unexpected environment variable"
                continue

            cast = eval(getattr(v, "cast", "str"))
            actual = env.get(var, mapper=cast)

            assert (
                cast(actual) == v.value
            ), f"{var}: expected [{v.value}], got [{actual}]"


class TestQF(unittest.TestCase):
    def test_match_object(self):
        obj1 = {"k0": [1, 2, 3], "k1": "1", "k2": 2, "k3": 2.3, "k4": "2023-12-31"}
        obj2 = {"key1": "abcdefg"}
        obj3 = {"da_date": "2023-11-26T11:28:17.791000-05:00", "not_date": "something_else"}

        tests = [
            (
                obj1,
                "k1 = '1' + k2 = 2 + k3 = 2.3 + k4 > d'2023-11-30' + k4 < d'2024-01-01' + k1 in ['1', '2'] + k3 > 1.0 + k5 is null + k4 is_not null",
                True,
            ),
            (obj1, "key1 not_in ['a']", True),
            (obj1, "key1 in ['a']", False),
            (obj1, "key1 in ['a'] + key1 not_in ['a']", False),
            (obj1, "key1 in ['a'] , key1 not_in ['a']", True),
            (obj1, "k1 = 1", False),
            (obj1, "k1='1'", True),
            (obj1, "symbol='aaaaaaa'", False),
            (obj1, "(k1 = 1),(k2 = 2+k3 < 100.0)", True),
            (obj1, "(k2 > -2)", True),
            (obj1, "(k3 > -2.0)", True),
            (obj2, "key1 ~ 'abcdefg'", True),
            (obj2, "key1 ~ 'AbCDefg'", True),
            (obj2, "key1 = 'abcdefg'", True),
            (obj2, "key1 ~ 'abcdefg '", False),
            (obj2, "key1 !~ 'abcdefg '", True),
            (obj3, "da_date > d'2023-11-25'", True),
            (obj3, "not_a_key > d'2023-11-25'", False),
            (obj3, "not_date > d'2023-11-25'", False),
        ]

        for obj, q, should_match in tests:
            filter = Filter(q)
            actual = filter.match(obj, debug=True)
            self.assertEqual(should_match, actual, msg=f"q={q}")
