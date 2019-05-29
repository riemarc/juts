from unittest import TestCase
import juts as jt


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

config = {"config_1": config_flat}
job = jt.Job(jt.Configuration(config), lambda: 0)

def handle(config, process_queue=None, result_dict=None):
    pass

class TestInterface(TestCase):
    def test_widgets(self):
        ui = jt.UserInterface(handle, config)
        ui.scheduler.config_view.queue_bt.value = True
        # ui.scheduler.config_view.queue_bt.value = True
        print(ui.scheduler.config_list.select)
