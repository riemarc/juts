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
job = jt.Job(config, lambda: 0)


class TestWidgets(TestCase):
    def test_widgets(self):
        jt.SelectWithLabel("label", config)
        jt.ConfigurationView()
        jt.ConfigurationView(config)
        jt.JobView()
        jt.JobView(job)
        ui = jt.UserInterface()
        ui.add_configs(config)

