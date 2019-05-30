from collections import OrderedDict, Mapping, deque
from yamlordereddictloader import Dumper, Loader
from multiprocessing import Pool, Process, Queue, Manager, cpu_count
from queue import Empty
from threading import Thread
from numbers import Number
from pprint import pformat
import ipywidgets as iw
import logging
import time
import yaml
import os


class Configuration(OrderedDict):
    def __init__(self, config, handle=None):

        if isinstance(config, Configuration):
            assert handle is None

            self.name = config.name
            self.handle = config.handle
            super().__init__(config)

        else:
            assert callable(handle)

            ord_dict = Configuration.as_ordered_dict(config)
            ord_config = [value for value in ord_dict.values()][0]
            self.name = [key for key in ord_dict.keys()][0]
            self.handle = handle

            super().__init__(ord_config)

    def __repr__(self, *args, **kwargs):
        prt = ("Name: {}\n"
               "Function: {}\n"
               "Configuration:\n{}").format(
            self.name,
            self.handle,
            pformat(list(self.items())))

        return prt

    @staticmethod
    def as_ordered_dict(config):
        if not isinstance(config, Mapping):
            raise TypeError(
                "Use collection.OrderedDict for configuration specification\n"
                "or provide filename to yaml file.")

        if len(config) == 0:
            raise ValueError(
                "Empty configuration dictionary/file provided.")

        if len(config) > 1:
            raise ValueError(
                "Loading configuration from dictionary/file needs a \n"
                "dictionary/file with only one configuration. Use \n"
                "load_configurations() for multiple configurations.")

        config_name = [key for key in config.keys()][0]
        inter_config = OrderedDict([value for value in config.values()][0])

        settings = dict()
        configuration = OrderedDict()
        for key, value in inter_config.items():
            if not isinstance(value, Mapping):
                raise TypeError(
                    "Only depth-2 configurations allowed.")

            configuration.update({key: OrderedDict(value)})
            settings.update(value)

        for key, value in settings.items():
            if not Configuration.is_valid_setting(value):
                raise ValueError(
                    "A valid setting is a number, string or list, but not\n"
                    "{}: {}".format(key, value))

        return OrderedDict({config_name: configuration})

    @staticmethod
    def is_valid_setting(setting):
        if isinstance(setting, (str, Number)):
            return True

        if not isinstance(setting, list):
            return False

        return all([Configuration.is_valid_setting(st) for st in setting])


def load_configurations(filename):
    with open(filename, "r") as f:
        configs = yaml.load(f, Loader=Loader)

    valid_configs = OrderedDict()
    for key, value in configs.items():
        valid_configs.update(Configuration.as_ordered_dict({key: value}))

    return valid_configs


Dumper.ignore_aliases = lambda *args : True


def dump_configurations(filename, config):
    if isinstance(config, Configuration):
        config = OrderedDict({config.name: config})

    with open(filename, "w") as f:
        yaml.dump(config, f, Dumper=Dumper, default_flow_style=False)


class Result(OrderedDict):
    def __init__(self, result=None):
        if result is None:
            result = dict()
        assert isinstance(result, Mapping)

        super().__init__(result)


log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

class Job(Thread):
    def __init__(self, config, result=None):
        super().__init__()

        assert isinstance(config, Configuration)
        self._config = config

        self._result = None
        if result is not None:
            assert isinstance(result, Result)
            self.result = result

        progress_layout = iw.Layout(width="auto")
        self.progress = iw.FloatProgress(value=0,
                                         min=0,
                                         max=100,
                                         bar_style='info',
                                         orientation='horizontal',
                                         layout=progress_layout)

        self.job_started = Signal()
        self.job_finished = Signal()

        self.logger = logging.getLogger(str(hash(self)))
        self.logger.setLevel(logging.INFO)
        self.log_handler = OutputWidgetHandler()
        self.log_handler.setLevel(logging.INFO)
        self.log_handler.setFormatter(log_formatter)
        self.logger.addHandler(self.log_handler)

    def get_config(self):
        return self._config

    config = property(get_config)

    def set_result(self, result):
        if self._result is None:
            assert isinstance(result, Result)
            self._result = result

        else:
            raise ValueError("Once set, result is immutable.")

    def get_result(self):
        return self._result

    result = property(get_result, set_result)

    def process_queue_get(self, process_queue):
        try:
            status = process_queue.get(timeout=.5)

        except Empty:
            status = None
            self.logger.warning("multiprocesssing queue timout")

        if status is not None:
            self.progress.value = status[0]

    def run(self):
        process_queue = Queue()
        manager = Manager()
        return_dict = manager.dict()
        self.logger.info("initialize process")
        process = Process(target=self.config.handle,
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
        self.result = Result(dict(return_dict))

        self.logger.info("join process")
        process.join()

        self.progress.bar_style = "success"


def as_job_list(config_list):
    job_list = list()

    for config in config_list:
        job_list.append(Job(config))

    return job_list


class JobScheduler(Thread):
    def __init__(self, handle):
        super().__init__()
        self.handle = handle
        self.sync_queue = Signal()
        self.sync_busy = Signal()

        self.queue = deque()
        self.busy = deque()
        self.is_running = False
        self.pool = Pool()

    def append_queue_job(self, job):
        self.queue.append(job)
        self.sync_queue()

    def pop_queue_job(self, index):
        job = self.queue.pop(index)
        self.sync_queue()

        return job

    def pop_busy_job(self, index):
        job = self.queue.pop(index)
        job.join(timeout=1)
        self.sync_busy()

        return job

    def start_queue(self):
        self.is_running = True

    def stop_queue(self):
        self.is_running = False

    def run(self):
        while True:
            if self.is_running:
                self.process_queue()

            time.sleep(.5)

    def process_queue(self):
        if self.is_running and len(os.sched_getaffinity(0)) > 0:
            job = self.queue.popleft()
            self.sync_queue()

            job.start()

            self.busy.append(job)
            self.sync_busy()

    def process_busy(self):
        finished_jobs = list()
        for i, job in enumerate(self.busy):
            if job.result is not None:
                finished_jobs.append(i)

        for i in finished_jobs:
            self.sync_busy(i)


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
