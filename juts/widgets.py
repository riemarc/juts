from .container import (Configuration, Result, Job, load_configurations,
                        dump_configurations)
from collections import OrderedDict
from ast import literal_eval
import ipywidgets as iw


class ConfigurationView(iw.Accordion):
    def __init__(self, config=None):
        super().__init__(children=[])

        if config is not None:
            self.update_view(config)

    def update_view(self, config):
        assert isinstance(config, Configuration)
        self.config = config

        accordion_items = list()
        for param_set in config.values():

            param_set_items = list()
            for key, value in param_set.items():
                param_set_items.append(
                    iw.Text(value=str(value),
                            description=key))

            accordion_items.append(iw.Box(children=param_set_items))

        self.children = tuple(accordion_items)
        self.selected_index = None
        for i, key in enumerate(config):
            self.set_title(i, key)


    def get_config(self, name, function):
        config = OrderedDict()
        for i, param_set in enumerate(self.children):

            key = self.get_title(i)
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

        self.config = Configuration(OrderedDict({name: config}), function)

        return self.config


class ResultView(iw.Accordion):
    def __init__(self, result=None):
        super().__init__(children=[])
        self.selected_index = None

        if result is None:
            result = dict()

        self.update_view(result)

    def update_view(self, result):
        if result is None:
            return

        result_items = list()
        for i, (key, val) in enumerate(result.items()):
            result_items.append(iw.HTML(value=str(val)))
            self.set_title(i, key)

        self.children = tuple(result_items)


class JobView(iw.VBox):
    def __init__(self, job=None, source_list="config"):
        self.label = iw.Label("Job View")
        self.text = iw.Text(value="", disabled=True)
        self.queue_bt = iw.Button(
            description='Queue Job', icon="check")
        self.sync_bt = iw.Button(
            description='Sync Config', icon="sync")
        self.show_bt = iw.Button(
            description='Show Result', icon="eye")
        self.save_config_bt = iw.Button(
            description='Save Config', icon="save")
        self.save_result_bt = iw.Button(
            description='Save Result', icon="save")
        self.discard_bt = iw.Button(
            description='Discard Job', icon="remove")
        self.header_box = iw.HBox(children=[])

        self.text.value = str()
        self.config_view = ConfigurationView()
        self.result_view = ResultView()
        self.log_view = iw.Output()
        self.accordion = iw.Accordion()

        self.source_list = source_list

        super().__init__(children=[])

        if job is not None:
            assert isinstance(job, Job)
            self.update_view(job, self.source_list)

    def update_view(self, job, source_list):
        self.job = job
        self.source_list = source_list
        self.text.value = job.config.name
        self.config_view.update_view(self.job.config)
        self.result_view.update_view(self.job.result)
        self.log_view = self.job.log_handler.out

        self.set_mode(source_list)

    def set_mode(self, source_list):
        self.source_list = source_list
        if source_list == "config":
            self.text.disabled = False
            header = [self.text, self.queue_bt, self.sync_bt,
                      self.save_config_bt, self.discard_bt]
            accordion = [self.config_view]
            accordion_title = ["Configuration"]
            self.children = [self.label, self.header_box, self.accordion]

        elif source_list == "queue":
            self.text.disabled = True
            header = [self.text, self.discard_bt]
            accordion = [self.config_view]
            accordion_title = ["Configuration"]
            self.children = [self.label, self.header_box, self.accordion]

        elif source_list == "busy":
            self.text.disabled = True
            header = [self.text, self.show_bt]
            accordion = [self.config_view, self.log_view]
            accordion_title = ["Configuration", "Log"]
            self.children = [self.label, self.header_box, self.job.progress,
                             self.accordion]

        elif source_list == "result":
            self.text.disabled = True
            header = [self.text, self.sync_bt, self.show_bt,
                      self.save_result_bt, self.save_config_bt, self.discard_bt]
            accordion = [self.config_view, self.result_view, self.log_view]
            accordion_title = ["Configuration", "Result", "Log"]
            self.children = [self.label, self.header_box, self.job.progress,
                             self.accordion]

        else:
            raise NotImplementedError

        self.header_box.children = tuple(header)

        self.accordion.children = tuple(accordion)
        for i, title in enumerate(accordion_title):
            self.accordion.set_title(i, title)

    def get_config(self):
        return self.config_view.get_config(
            self.text.value, self.job.config.handle)



class JobList(iw.VBox):
    def __init__(self, label, jobs, **kwargs):
        self.label = iw.Label(label)

        if jobs is None:
            self.job_list = list()

        else:
            self.job_list = jobs

        select = [it.config.name for it in self.job_list]
        select_layout = iw.Layout(width="auto", height="100px")
        self.select = iw.Select(options=select, layout=select_layout)
        super().__init__([self.label, self.select], **kwargs)

    def add_items(self, items):
        self.job_list += items
        self.select.options = (tuple(list(self.select.options) +
                                     [it.config.name for it in items]))

    def pop_item(self):
        index = self.select.index
        item = self.job_list[index]
        self.job_list = [
            it for i, it in enumerate(self.job_list) if i != index]
        self.select.options = tuple([
            it for i, it in enumerate(self.select.options) if i != index])

        return item

    def sync_items(self, items):
        self.job_list = items
        self.select.options = tuple([it.name for it in items])


class SchedulerForm(iw.GridBox):
    def __init__(self, jobs):
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

        self.config_list = JobList(
            "Configurations", jobs, layout=head_it_layout("config_list"))
        self.busy_list = JobList(
            "Busy", tuple(), layout=head_it_layout("busy_list"))
        self.queue_list = JobList(
            "Queue", tuple(), layout=head_it_layout("queue_list"))
        self.result_list = JobList(
            "Results", tuple(), layout=head_it_layout("result_list"))
        self.job_list_labels = ["config", "queue", "busy", "result"]
        self.job_lists = [self.config_list, self.queue_list,
                          self.busy_list, self.result_list]

        self.job_view = JobView()
        self.job_view.layout = head_it_layout("job_view")
        spacer = iw.Label(str(""), layout=head_it_layout("spacer"))

        grid_items = [self.load_configs_bt, self.save_configs_bt,
                      self.save_results_bt, self.play_queue_bt,
                      self.config_list, self.busy_list, self.queue_list,
                      self.result_list, self.job_view, spacer]
        grid_layout = iw.Layout(
                width='100%',
                grid_template_rows='auto auto auto auto',
                grid_template_columns='24% 24% 24% 24%',
                grid_gap='0% 1%',
                grid_template_areas='''
                "load_config_button save_config_button save_result_button run_button "
                "config_list config_list queue_list queue_list "
                "result_list result_list busy_list busy_list "
                "spacer spacer spacer spacer "
                "job_view job_view job_view job_view "
                ''')

        super().__init__(grid_items, layout=grid_layout)


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
