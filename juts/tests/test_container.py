from unittest import TestCase
import juts as jt
import time
from juts import (Configuration, load_configs_from_file, dump_configurations, Job)
from collections import OrderedDict
import os


settings = dict({
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

config = Configuration("set1", settings)

def function(config, process_queue=None, return_dict=None):
    for i in range(10):
        return_dict.update({i:i})
        process_queue.put(dict(progress=i))
        time.sleep(.5)


class TestConfiguration(TestCase):
    def test_load_dump(self):
        filename = "configs_temp_test.yml"
        dump_configurations(filename, [config])
        self.assertEqual(settings, load_configs_from_file(filename)[0].settings)
        os.remove(filename)


class TestJob(TestCase):
    def test_job(self):
        job = Job(config)
        job.start()
        job.join()

