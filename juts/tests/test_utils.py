from unittest import TestCase
from juts import (Configuration, load_configurations, dump_configurations,
                  Job)
from collections import OrderedDict
import os


config_flat = dict({
    "params_1": dict({
        "param_1": 1,
        "param_2": 2,
    }),
    "params_2": dict({
        "param_1": "1",
        "param_2": [1.1, 2.2j],
        "param_3": [[1j, 2], ["3", "t", [1, [2j, 2]]]],
    }),
})

config_1 = {"config_1": config_flat}
config_2 = {"config_2": config_flat}

config_multiple = OrderedDict()
config_multiple.update(config_1)
config_multiple.update(config_2)

config_deep = {"config_3": config_multiple}

config_invalid = OrderedDict({
    "config_1":
        OrderedDict({
            "params_1": OrderedDict({
                "param_1": 1,
                "param_2": 1,
            }),
            "params_2": OrderedDict({
                "param_1": "1",
                "param_2": dict(a=1),
            }),
        })})


class TestConfiguration(TestCase):
    def test_depth(self):
        with self.assertRaises(ValueError):
            Configuration(config_flat)

        with self.assertRaises(ValueError):
            Configuration(config_deep)

    def test_valid(self):
        c1 = Configuration(config_1)
        self.assertIsInstance(c1, OrderedDict)
        self.assertIsInstance(c1["params_1"], OrderedDict)
        self.assertEqual(c1.name, "config_1")

        with self.assertRaises(ValueError):
            Configuration(config_multiple)

    def test_load_dump(self):
        filename = "configs_temp_test.yml"
        dump_configurations(filename, config_multiple)
        self.assertEqual(config_multiple, load_configurations(filename))
        os.remove(filename)


class TestJob(TestCase):
    def test_job(self):
        config = Configuration(config_1)
        Job(config)

