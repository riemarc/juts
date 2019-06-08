from multiprocessing import Process, Queue, Manager, cpu_count
from yamlordereddictloader import Dumper, Loader
from collections import OrderedDict, Mapping
from abc import abstractmethod
from threading import Thread, Event
from pprint import pformat
from numbers import Number
from queue import Empty
import ipywidgets as iw
import logging
import time
import yaml


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
    job_count = 0

    def __init__(self, config, result=None):
        Job.job_count += 1
        self.job_index = Job.job_count
        # since self.is_alive() returns True before self.start()
        self.job_is_alive = True
        super().__init__()

        assert isinstance(config, Configuration)
        self._config = config

        self._result = Result()

        progress_layout = iw.Layout(width="auto")
        self.progress = iw.FloatProgress(value=0,
                                         min=0,
                                         max=100,
                                         bar_style='info',
                                         orientation='horizontal',
                                         layout=progress_layout)

        self.job_finished = Signal()
        self.result_update = Signal()

        self.logger = logging.getLogger(str(hash(self)))
        self.logger.setLevel(logging.INFO)
        self.log_handler = OutputWidgetHandler()
        self.log_handler.setLevel(logging.INFO)
        self.log_handler.setFormatter(log_formatter)
        self.logger.addHandler(self.log_handler)

        self._live_result = Result()

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
            self.result_update()

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
        if len(return_dict) > 0:
            self._result = Result(OrderedDict(return_dict))

        else:
            self._result = Result(OrderedDict(self._live_result))

        self.logger.info("join process")
        process.join()

        self.progress.bar_style = "success"
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
        if len(self.busy_jobs) < cpu_count():
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


class Plot(Thread):
    def __init__(self, jobs, widget):
        super().__init__()

        self.jobs = jobs
        self.widget = widget
        self.last_update = time.time()
        self.update_cycle = 0.1
        self.fallback_cycle = 5
        self.update_event = Event()

        for job in jobs:
            job.result_update.observe(self.on_result_update, names="value")

    def on_result_update(self, change):
        self.update_event.set()

    @abstractmethod
    def update_plot(self):
        pass

    def run(self):
        while any(job.job_is_alive for job in self.jobs):
            self.update_plot()
            if self.update_event.wait(self.fallback_cycle):
                self.update_event.clear()

                cycle_margin = self.update_cycle - time.time() + self.last_update
                self.last_update = time.time()
                if cycle_margin > 0:
                    time.sleep(cycle_margin)

                with self.widget.hold_sync():
                    self.update_plot()

        self.update_plot()


