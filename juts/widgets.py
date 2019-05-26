from .utils import (Configuration, Result, Job, load_configurations,
                    dump_configurations)
from collections import OrderedDict
from ast import literal_eval
import ipywidgets as iw


fx_layout = iw.Layout(display="flex", flex="1 1 auto",
                      align_items="flex-start", align_content="flex-start",
                      justify_content="flex-start")


class ConfigurationView(iw.VBox):
    def __init__(self, config=None):
        self.text = iw.Text()
        self.queue_bt = iw.Button(
            value=False, description='Queue', icon="check")
        self.save_bt = iw.Button(
            value=False, description='Save', icon="save")
        self.save_all_bt = iw.Button(
            value=False, description='Save All', icon="save")
        self.delete_bt = iw.Button(
            value=False, description='Delete', icon="delete")
        self.header_box = iw.HBox(
            children=[self.text, self.queue_bt, self.save_bt, self.save_all_bt,
                      self.delete_bt])
        super(ConfigurationView, self).__init__(children=[self.header_box])

        if config is not None:
            self.new_config(config)

    def new_config(self, config):
        self.text.value = config.name
        self.config = config

        accordion_items = list()
        for param_set in config.values():

            param_set_items = list()
            for key, value in param_set.items():
                param_set_items.append(
                    iw.Text(value=str(value),
                            description=key,
                            disabled=config.is_locked()))

            accordion_items.append(iw.Box(children=param_set_items))

        accordion = iw.Accordion(children=accordion_items)
        accordion.selected_index = None
        for i, key in enumerate(config):
            accordion.set_title(i, key)

        self.children = (self.header_box, accordion)

    def get_config(self):
        if self.config.is_locked():
            self.new_config(self.config)
            return self.config

        name = self.text.value

        config = OrderedDict()
        accordion = self.children[1]
        for i, param_set in enumerate(accordion.children):

            key = accordion.get_title(i)
            value = OrderedDict()
            for param in param_set.children:

                try:
                    text_value = literal_eval(param.value)
                    use_last_valid = False

                    if not Configuration.is_valid_setting(text_value):
                        use_last_valid = True

                except (SyntaxError, TypeError, ValueError):

                    use_last_valid = True

                if use_last_valid:
                    text_value = self.config[key][param.description]
                    param.value = str(text_value)

                value.update({param.description: text_value})

            config.update({key: value})

        self.config = Configuration(OrderedDict({name: config}))

        return self.config


class ResultView(iw.Accordion):
    def __init__(self, result):
        assert isinstance(result, Result)

        result_items = [iw.HTML(value=str(val)) for val in result.values()]
        if len(result_items) == 0:
            result_items = [iw.HTML(value="None")]
            self.set_title(0, "None")
        super(ResultView, self).__init__(children=result_items)
        for i, key in enumerate(result):
            self.set_title(i, key)
        self.selected_index = None


class JobView(iw.VBox):
    def __init__(self, job):
        self.text = iw.Text(value=job.config.name, disabled=True)
        self.show_bt = iw.Button(
            value=False, description='Show', icon="show")
        self.save_bt = iw.Button(
            value=False, description='Save Result', icon="save")
        self.save_all_bt = iw.Button(
            value=False, description='Save Results', icon="save")
        self.delete_bt = iw.Button(
            value=False, description='Delete Job', icon="delete")
        self.header_box = iw.HBox(
            children=[self.text, self.show_bt, self.save_bt, self.save_all_bt,
                      self.delete_bt])

        self.job = job
        progress_label = iw.Label("Progress")
        config_label = iw.Label("Configuration")
        self.config_view = ConfigurationView(self.job.config)
        self.config_view.children = (self.config_view.children[1],)
        result_label = iw.Label("Result")
        self.result_view = ResultView(self.job.result)
        super(JobView, self).__init__(
            children=[self.header_box, progress_label, self.job.progress,
                      config_label, self.config_view, result_label,
                      self.result_view])


class SelectWithLabel(iw.VBox):
    def __init__(self, label, list_items=tuple()):
        self.label = iw.Label(label)
        self.select_view = iw.Select(options=list_items)
        super(SelectWithLabel, self).__init__(
            children=[self.label, self.select_view])
        self.set_layout()

    def set_layout(self):
        self.layout = fx_layout
        self.select_view.layout = iw.Layout(flex="0 1 auto")
        self.label.layout = iw.Layout(flex="0 1 auto")


def get_setup_panel(config):
    assert len(config) > 0

    config_list = SelectWithLabel("Configurations", config)
    queue_list = SelectWithLabel("Queue")
    busy_list = SelectWithLabel("Busy")
    queue_hbox = iw.VBox([queue_list, busy_list])
    queue_hbox.layout = fx_layout
    result_list = SelectWithLabel("Results")

    list_hbox = iw.HBox([config_list, queue_hbox, result_list])
    list_hbox.layout = fx_layout

    config_1 = Configuration([{k: v} for k, v in config.items()][0])
    config_view = ConfigurationView(config_1)
    job_1 = Job(config_1)
    job_view = JobView(job_1)
    view_tab = iw.Tab([config_view, job_view])

    control_panel = iw.VBox([list_hbox, view_tab])
    control_panel.layout = iw.Layout(display="flex", width="100%")
    print(config_list.layout, config_list.select_view.layout)
    print(result_list.layout, result_list.select_view.layout)

    return control_panel
