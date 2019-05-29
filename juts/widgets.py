from .container import (Configuration, Result, Job, load_configurations,
                        dump_configurations, as_config_list)
from collections import OrderedDict
from ast import literal_eval
import ipywidgets as iw


class ConfigurationView(iw.VBox):
    def __init__(self, config=None):
        self.text = iw.Text()
        self.queue_bt = iw.Button(
            description='Queue Job', icon="check")
        self.sync_bt = iw.Button(
            description='Sync Config', icon="sync")
        self.remove_bt = iw.Button(
            description='Remove Conifg', icon="remove")
        self.save_bt = iw.Button(
            description='Save Config', icon="save")
        self.header_box = iw.HBox(
            children=[self.text, self.queue_bt, self.sync_bt, self.remove_bt, self.save_bt])
        super().__init__(children=[self.header_box])

        if config is not None:
            self.update_view(config)

    def update_view(self, config):
        if not isinstance(config, Configuration):
            config = Configuration(config)

        self.text.value = config.name
        self.config = config

        accordion_items = list()
        for param_set in config.values():

            param_set_items = list()
            for key, value in param_set.items():
                param_set_items.append(
                    iw.Text(value=str(value),
                            description=key))

            accordion_items.append(iw.Box(children=param_set_items))

        accordion = iw.Accordion(children=accordion_items)
        accordion.selected_index = None
        for i, key in enumerate(config):
            accordion.set_title(i, key)

        self.children = (self.header_box, accordion)

    def get_config(self):
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
    def __init__(self, result=None):
        super().__init__(children=[])
        self.selected_index = None

        if result is None:
            result = dict()

        self.update_view(result)

    def update_view(self, result):
        result_items = list()
        for i, (key, val) in enumerate(result.items()):
            result_items.append(iw.HTML(value=str(val)))
            self.set_title(i, key)

        self.children = tuple(result_items)


class JobView(iw.VBox):
    def __init__(self, job=None):
        self.text = iw.Text(value="", disabled=True)
        self.show_bt = iw.Button(
            description='Show Result', icon="eye", disabled=True)
        self.save_bt = iw.Button(
            description='Save Result', icon="save", disabled=True)
        self.discard_bt = iw.Button(
            description='Discard Job', icon="remove", disabled=True)
        self.header_box = iw.HBox(
            children=[self.text, self.show_bt, self.save_bt, self.discard_bt])

        super().__init__(children=[self.header_box])

        if job is not None:
            self.update_view(job)

    def update_view(self, job):
        self.job = job

        self.text.value = job.config.name

        config_view = ConfigurationView(self.job.config)
        config_view.children = (config_view.children[1],)

        self.result_view = ResultView(self.job.result)

        logger = self.job.log_handler.out

        accordion = iw.Accordion([config_view, self.result_view, logger])
        for i, title in enumerate(["Configuration", "Result", "Log"]):
            accordion.set_title(i, title)
        accordion.selected_index = None

        self.children = (self.header_box, self.job.progress, accordion)

        self.update_button_states()

    def update_result_view(self, result):
        self.result_view.update_view(result)
        self.update_button_states()

    def update_button_states(self):
        no_result = not bool(self.job.result)
        self.show_bt.disabled = no_result
        self.save_bt.disabled = no_result
        self.discard_bt.disabled = self.job.is_alive()



class SelectWithLabel(iw.VBox):
    def __init__(self, label, list_items, **kwargs):
        self.label = iw.Label(label)

        if list_items is None:
            self._list_items = list()

        else:
            self._list_items = as_config_list(list_items)

        select = [it.name for it in self._list_items]
        select_layout = iw.Layout(width="auto", height="100px")
        self.select = iw.Select(options=select, layout=select_layout)
        super().__init__([self.label, self.select], **kwargs)

    def add_items(self, items):
        self._list_items += items
        self.select.options = tuple(list(self.select.options) + [it.name for it in items])

    def pop_item(self):
        index = self.select.selected_index
        item = self._list_items[index]
        self._list_items = [
            it for i, it in enumerate(self._list_items) if i != index]
        self.select.options = tuple([
            it for i, it in enumerate(self.self.select.options) if i != index])

        return item


class SchedulerForm(iw.GridBox):
    def __init__(self, config=None):
        head_it_layout = lambda lbl: iw.Layout(width='auto', grid_area=lbl)

        self.load_configs_bt = iw.Button(
            description="Load Configs", icon="open",
            layout=head_it_layout("load_config_button"))
        self.save_configs_bt = iw.Button(
            description="Save Configs", icon="save",
            layout=head_it_layout("save_config_button"))
        self.save_results_bt = iw.Button(
            description="Save Results", icon="save",
            layout=head_it_layout("save_result_button"))
        self.play_queue_bt = iw.ToggleButton(
            description="Run", icon="play",
            layout=head_it_layout("run_button"))

        self.config_list = SelectWithLabel(
            "Configurations", config, layout=head_it_layout("config_list"))
        self.busy_list = SelectWithLabel(
            "Busy", tuple(), layout=head_it_layout("busy_list"))
        self.queue_list = SelectWithLabel(
            "Queue", tuple(), layout=head_it_layout("queue_list"))
        self.result_list = SelectWithLabel(
            "Results", tuple(), layout=head_it_layout("result_list"))

        self.config_view = ConfigurationView()
        self.job_view = JobView()

        self.view_tab = iw.Tab([self.config_view, self.job_view],
                               layout=head_it_layout("view_tab"))
        self.view_tab.set_title(0, "Config View")
        self.view_tab.set_title(1, "Job View")

        grid_items = [self.load_configs_bt, self.save_configs_bt,
                      self.save_results_bt, self.play_queue_bt,
                      self.config_list, self.busy_list, self.queue_list,
                      self.result_list, self.view_tab]
        grid_layout = iw.Layout(
                width='100%',
                grid_template_rows='auto auto auto auto',
                grid_template_columns='24% 24% 24% 24%',
                grid_gap='0% 1%',
                grid_template_areas='''
                "load_config_button save_config_button save_result_button run_button "
                "config_list config_list queue_list queue_list "
                "result_list result_list busy_list busy_list "
                "view_tab view_tab view_tab view_tab "
                ''')

        super().__init__(grid_items, layout=grid_layout)

    def add_configs(self, configs):
        self.config_list.add_items(as_config_list(configs))


class VisualizerForm(iw.VBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UserInterfaceForm(iw.Tab):
    def __init__(self, scheduler, visualizer):
        layout = iw.Layout(display="flex", width="98%")
        self.scheduler = scheduler
        self.visualizer = visualizer
        tabs = [scheduler, visualizer]

        super().__init__(tabs, layout=layout)

        self.set_title(0, "Scheduler")
        self.set_title(1, "Visualizer")

    def add_configs(self, configs):
        self.scheduler.add_configs(configs)
