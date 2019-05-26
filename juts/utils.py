from yamlordereddictloader import Dumper, Loader
from collections import OrderedDict, Mapping
from numbers import Number
from pprint import pprint, pformat
import ipywidgets as iw
import yaml


class Configuration(OrderedDict):
    def __init__(self, config):
        ord_dict = Configuration.as_ordered_dict(config)
        ord_config = [value for value in ord_dict.values()][0]
        super(Configuration, self).__init__(ord_config)

        self.name = [key for key in ord_dict.keys()][0]
        self._locked = False

    def __repr__(self, *args, **kwargs):
        prt = ("Name: {}\n"
               "Configuration:\t{}").format(
            self.name, pformat(list(self.items())).replace("\n", "\n\t\t"))

        return prt

    def lock_configuration(self):
        self._locked = True

    def is_locked(self):
        return self._locked

    @staticmethod
    def as_ordered_dict(config):
        if isinstance(config, str):
            config = load_configurations(config)

        elif not isinstance(config, Mapping):
            raise TypeError(
                "Use collection.OrderedDict for configuration specification\n"
                "or provide filename to yaml file.")

        if len(config) == 0:
            raise ValueError(
                "Empty configuration dictionary/file provided.")

        if len(config) > 1:
            raise ValueError(
                "Configuration loading from dictionary/file needs a \n"
                "dictionary/file with only one configuration. Use \n"
                "load_configurations() for multiple configurations.")

        config_name = [key for key in config.keys()][0]
        inter_config = OrderedDict([value for value in config.values()][0])

        settings = dict()
        configuration = OrderedDict()
        for key, value in inter_config.items():
            if not isinstance(value, Mapping):
                raise TypeError(
                    "At the moment only depth-2 configurations allowed.")

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

        super(Result, self).__init__(result)


class Job:
    def __init__(self, config, result=None):
        assert isinstance(config, Configuration)
        self.config = config

        if result is None:
            result = Result()
        assert isinstance(result, Result)
        self.result = result

        progress_layout = iw.Layout(width="auto")
        self.progress = iw.FloatProgress(value=0,
                                         min=0,
                                         max=100,
                                         bar_style='info',
                                         orientation='horizontal',
                                         layout=progress_layout)
