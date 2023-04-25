from multiprocessing import Process, Queue, Manager, cpu_count
from yamlordereddictloader import Dumper, Loader
from datetime import datetime as dt
from collections import OrderedDict
from collections.abc import Mapping
from threading import Thread
from pprint import pformat
from numbers import Number
from codecs import decode
from queue import Empty
import ipywidgets as iw
import logging
import time
import yaml
import io


class Configuration:
    def __init__(self, name, settings):
        self.name = name
        Configuration.validate_settings(settings)
        self.settings = settings

    def __repr__(self, *args, **kwargs):
        prt = ("Name: {}\n"
               "Settings:\n{}").format(
            self.name,
            pformat(list(self.settings.items())))

        return prt

    def __getitem__(self, item):
        return self.settings[item]

    @staticmethod
    def validate_settings(settings):
        for _name, parameters in settings.items():
            if not isinstance(parameters, Mapping):
                raise TypeError(
                    "Only depth-2 configurations supported.")
            for __name, parameter in parameters.items():
                if not Configuration.is_valid_parameter(parameter):
                    raise ValueError(
                        "A valid parameter is a number, string or list, \\"
                        "but not {}: {}".format(__name, parameter))

    @staticmethod
    def is_valid_parameter(parameter):
        if isinstance(parameter, (str, Number)):
            return True

        if not isinstance(parameter, list):
            return False

        return all([Configuration.is_valid_parameter(par) for par in parameter])


def load_configs_from_file(filename):
    with open(filename, "r") as f:
        configs = yaml.load(f, Loader=Loader)

    return load_configs_from_dict(configs)

def load_configs_from_file_upload(file_upload):
    configs = list()
    for file in file_upload.value:
        stream = io.StringIO(decode(file.content))
        config = yaml.load(stream, Loader=Loader)
        configs += load_configs_from_dict(config)

    return configs


def load_configs_from_dict(configs):
    return [Configuration(name, setting) for name, setting in configs.items()]


def get_filename(fix, ending, post=""):
    if post:
        return dt.now().strftime(
            f"%Y-%d-%m-{fix}-%H-%M-%S--{post}.{ending}")
    else:
        return dt.now().strftime(
            f"%Y-%d-%m-{fix}-%H-%M-%S.{ending}")


Dumper.ignore_aliases = lambda *args : True


def dump_configurations(filename, configs):
    _configs = dict()
    for config in configs:
        _configs.update({config.name: config.settings})

    with open(filename, "w") as f:
        yaml.dump(_configs, f, Dumper=Dumper, default_flow_style=False)


class Result(OrderedDict):
    def __init__(self, result=None):
        if result is None:
            result = dict()
        assert isinstance(result, Mapping)

        super().__init__(result)


log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')


class Job(Thread):
    job_count = 0

    def __init__(self, func, config, name=None):
        self.job_index = Job.job_count
        Job.job_count += 1
        # since self.is_alive() returns False before self.start()
        self.job_is_alive = True
        super().__init__()

        assert callable(func)
        self._func = func

        assert isinstance(config, Configuration)
        self._config = config

        if name is None:
            self.name = " + ".join([func.__name__, config.name])
        else:
            self.name = name

        self._result = Result()

        progress_layout = iw.Layout(width="auto")
        self.progress = iw.FloatProgress(value=0,
                                         min=0,
                                         max=100,
                                         bar_style='info',
                                         orientation='horizontal',
                                         layout=progress_layout)

        self.job_finished = Signal()
        self.live_result_update = Signal()

        self.logger = logging.getLogger(str(hash(self)))
        self.logger.setLevel(logging.INFO)
        self.log_handler = OutputWidgetHandler()
        self.log_handler.setLevel(logging.INFO)
        self.log_handler.setFormatter(log_formatter)
        self.logger.addHandler(self.log_handler)

        self._live_result = Result()

    def get_func(self):
        return self._func

    func = property(get_func)

    def get_config(self):
        return self._config

    config = property(get_config)

    def get_result(self):
        if self.job_is_alive:
            return self._live_result

        else:
            return self._result

    result = property(get_result)

    def process_queue_get(self, process_queue):
        try:
            status = process_queue.get(timeout=.5)

        except Empty:
            status = dict()
            self.logger.warning("multiprocesssing queue timout")

        if "progress" in status:
            self.progress.value = status.pop("progress")

        if status:
            self.update_live_results(status)
            self.live_result_update()

    def update_live_results(self, status):
        for key, value in status.items():
            if key not in self._live_result:
                self._live_result[key] = list()

            self._live_result[key].append(value)

    def run(self):
        process_queue = Queue()
        manager = Manager()
        return_dict = manager.dict()
        self.logger.info("initialize process")
        process = Process(target=self.func,
                          args=(self.config,),
                          kwargs=dict(return_dict=return_dict,
                                      process_queue=process_queue))
        self.logger.info("start process")
        process.start()

        while process.is_alive():
            self.process_queue_get(process_queue)
        self.logger.info("process finished")

        while not process_queue.empty():
            self.process_queue_get(process_queue)
        self.logger.info("queue empty")

        self.logger.info("fetch results")
        if len(return_dict) > 0:
            self._result = Result(OrderedDict(return_dict))

        else:
            self._result = Result(OrderedDict(self._live_result))

        self.logger.info("join process")
        process.join()

        self.progress.bar_style = "success"
        self.progress.value = 100
        self.job_finished(self.job_index)

        self.job_is_alive = False


def as_job_list(config_list):
    job_list = list()

    for config in config_list:
        job_list.append(Job(config))

    return job_list


class JobScheduler(Thread):
    def __init__(self):
        super().__init__()
        self.sync_queue = Signal()
        self.sync_busy = Signal()
        self.sync_done = Signal()

        self.queue_jobs = list()
        self.busy_jobs = list()
        self.done_jobs = list()

        self.is_running = False

        self.max_kernels = cpu_count()
        self.available_kernels = self.max_kernels

    def append_queue_job(self, job):
        self.queue_jobs.append(job)
        self.sync_queue()

    def pop_queue_job(self, index):
        job = self.queue_jobs.pop(index)
        self.sync_queue()

        return job

    def pop_busy_job(self, index):
        job = self.busy_jobs.pop(index)
        self.sync_busy()

        return job

    def start_queue(self):
        self.is_running = True

    def pause_queue(self):
        self.is_running = False

    def run(self):
        while True:
            if self.is_running and len(self.queue_jobs) > 0:
                self.process_queue()

            time.sleep(.2)

    def process_queue(self):
        # if len(os.sched_getaffinity(0)) > 0:
        if len(self.busy_jobs) < self.available_kernels:
            job = self.queue_jobs.pop(0)
            self.sync_queue()

            job.start()

            self.busy_jobs.append(job)
            job.job_finished.observe(self.on_job_finished, names="value")
            self.sync_busy()

    def on_job_finished(self, change):
        job_index = Signal.as_index(change)
        index = None
        for i, job in enumerate(self.busy_jobs):
            if job.job_index == job_index:
                index = i

        if index < 0 or index >= len(self.busy_jobs):
            raise ValueError("Job is lost in busy queue.")

        else:
            self.done_jobs.append(self.busy_jobs.pop(index))
            self.sync_busy()
            self.sync_done()


class OutputWidgetHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.out = iw.Output()

    def emit(self, record):
        formatted_record = self.format(record)
        new_output = {
            'name': 'stdout',
            'output_type': 'stream',
            'text': formatted_record+'\n'
        }
        self.out.outputs = (new_output, ) + self.out.outputs


class Signal(iw.ValueWidget):
    def __init__(self):
        super().__init__(value=0)

    def __call__(self, index=None):
        if index is None:
            self.value += 1

        else:
            self.value -= index + 1

    @staticmethod
    def as_index(change):
        value = change["new"] - change["old"]
        if value < 0:
            return abs(value) - 1


def block_signal(meth):
    def handle(*args, **kwargs):
        args[0]._block_signal = True
        res = meth(*args, **kwargs)
        args[0]._block_signal = False

        return res

    return handle


def on_unblocked_signal(meth):
    def handle(*args, **kwargs):
        if not args[0]._block_signal:
            return meth(*args, **kwargs)

    return handle


