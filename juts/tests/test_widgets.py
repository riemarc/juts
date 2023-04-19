from unittest import TestCase
import ipywidgets as iw
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
        process_queue.put(dict(progress=i))
        time.sleep(.01)

config = jt.Configuration({"config_1": config_flat}, function)
job = jt.Job(config)


class TestWidgets(TestCase):
    def test_widgets(self):
        jt.JobList("label", [job])
        jt.ConfigurationView()
        cv = jt.ConfigurationView(config)
        print(cv.get_config("test", function))
        jt.JobView()
        jv = jt.JobView(job)
        print(jv.get_job())
        jt.UserInterfaceForm(iw.Widget(), iw.Widget())

    def test_job_thread(self):
        job = jt.Job(config)
        job_view = jt.JobView(job, "busy")
        job.start()
        job.join()
        job_view.result_view.update_view(job.result)

