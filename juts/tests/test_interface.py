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
        return_dict.update(dict(time_series=[i, i]))
        #return_dict.update(dict(not_a_time_series=[i]))
        #return_dict.update(dict(also_not_a_time_series=i))
        #return_dict.update(dict(not_a_time_series_too=i))
        process_queue.put(dict(progress=i))
        time.sleep(.01)

    return_dict.update(dict(result_1=[[0, 1], [1, 2], [2, 3]]))

config = {"config_1": config_flat}
job = jt.Job(jt.Configuration(config, function))

class TestInterface(TestCase):
    def test_widgets(self):
        ui = jt.UserInterface()
        ui.scheduler.job_view.queue_bt.value = True
        # ui.scheduler.config_view.queue_bt.value = True
        print(ui.scheduler.config_list.select)

        ui = jt.UserInterface()
        ui.add_config(function, config)
        ui.scheduler.on_queue_bt(dict(new=1))

        ui = jt.UserInterface()
        ui.add_config(handle=function, configfile="configurations.yml")
        ui.add_plot_widget(jt.TimeSeriesPlot)

    def test_time_series_plot(self):
        conf = jt.Configuration(config, function)
        job_1 = jt.Job(conf)
        job_1.start()
        job_1.join()
        job_2 = jt.Job(conf)

        plot = jt.TimeSeriesPlot([job_1, job_2])
        plot.start()
        plot.join()

