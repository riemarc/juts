from unittest import TestCase
import juts as jt
import time


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

def function(s, process_queue=None, return_dict=None):
    for i in range(101):
        return_dict.update({str(i):i})
        process_queue.put([i])
        time.sleep(.01)

config = {"config_1": config_flat}
job = jt.Job(jt.Configuration(config, function))

class TestInterface(TestCase):
    def test_widgets(self):
        ui = jt.UserInterface(function, config)
        ui.scheduler.job_view.queue_bt.value = True
        # ui.scheduler.config_view.queue_bt.value = True
        print(ui.scheduler.config_list.select)

        ui = jt.UserInterface()
        ui.add_config(function, config)
        ui.scheduler.on_queue_bt(dict(new=1))
