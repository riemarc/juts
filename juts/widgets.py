from .utils import (Configuration, Result, Job, load_configurations,
                    dump_configurations)
from collections import OrderedDict
from ast import literal_eval
import ipywidgets as iw


fx_layout = iw.Layout()


class ConfigurationView(iw.VBox):
    def __init__(self, config):
        self.text = iw.Text()
        self.queue_bt = iw.Button(
            value=False, description='Queue Job', icon="check")
        self.sync_bt = iw.Button(
            value=False, description='Sync Config', icon="sync")
        self.remove_bt = iw.Button(
            value=False, description='Remove Conifg', icon="remove")
        self.save_bt = iw.Button(
            value=False, description='Save Config', icon="save")
        self.header_box = iw.HBox(
            children=[self.text, self.queue_bt, self.sync_bt, self.remove_bt, self.save_bt])
        super(ConfigurationView, self).__init__(children=[self.header_box])

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
            result_items = [iw.HTML(value="not yet assigned")]
            self.set_title(0, "None")
        super(ResultView, self).__init__(children=result_items)
        for i, key in enumerate(result):
            self.set_title(i, key)
        self.selected_index = None


class JobView(iw.VBox):
    def __init__(self, job):
        self.text = iw.Text(value=job.config.name, disabled=True)
        self.show_bt = iw.Button(
            value=False, description='Show Result', icon="eye")
        self.save_bt = iw.Button(
            value=False, description='Save Result', icon="save")
        self.delete_bt = iw.Button(
            value=False, description='Discard Job', icon="remove")
        self.header_box = iw.HBox(
            children=[self.text, self.show_bt, self.save_bt, self.delete_bt])

        self.job = job
        progress_label = iw.Label("Progress")
        config_label = iw.Label("Configuration")
        self.config_view = ConfigurationView(self.job.config)
        self.config_view.children = (self.config_view.children[1],)
        result_label = iw.Label("Result")
        self.result_view = ResultView(self.job.result)
        super(JobView, self).__init__(
            children=[self.header_box, progress_label, self.job.progress,
                      result_label, self.result_view, config_label,
                      self.config_view])


class SelectWithLabel(iw.VBox):
    def __init__(self, label, list_items, **kwargs):
        self.label = iw.Label(label)
        select_layout = iw.Layout(width="auto", height="100px")
        self.select_view = iw.Select(options=list_items, layout=select_layout)
        super(SelectWithLabel, self).__init__(
            [self.label, self.select_view], **kwargs)


class ControlTabWiring:
    def __init__(self, sv_conf_bt, sv_res_bt, run_bt, pause_bt, config_sel,
                 queue_sel, busy_sel, res_sel, view_tab):
        pass


def get_std_gui_widget(config):
    assert len(config) > 0

    get_layout = lambda lbl: iw.Layout(width='auto', grid_area=lbl)

    save_configs_bt = iw.Button(
        value=False, description="Save Configs", icon="save",
        layout=get_layout("save_config_button"))
    save_results_bt = iw.Button(
        value=False, description="Save Results", icon="save",
        layout=get_layout("save_result_button"))
    run_queue_bt = iw.ToggleButton(
        value=False, description="Run", icon="play",
        layout=get_layout("run_button"))
    pause_queue_bt = iw.ToggleButton(
        value=False, description="Pause", icon="pause",
        layout=get_layout("pause_button"))

    config_list = SelectWithLabel("Configurations", config,
                                  layout=get_layout("config_list"))
    busy_list = SelectWithLabel("Busy", tuple(),
                                layout=get_layout("busy_list"))
    queue_list = SelectWithLabel("Queue", tuple(),
                                 layout=get_layout("queue_list"))
    result_list = SelectWithLabel("Results", tuple(),
                                  layout=get_layout("result_list"))

    config_1 = Configuration([{k: v} for k, v in config.items()][0])
    config_view = ConfigurationView(config_1)
    job_1 = Job(config_1)
    job_view = JobView(job_1)
    view_tab = iw.Tab([config_view, job_view], layout=get_layout("view_tab"))
    view_tab.set_title(0, "Config View")
    view_tab.set_title(1, "Job View")

    grid_items = [save_configs_bt, save_results_bt, run_queue_bt,
                  pause_queue_bt, config_list, busy_list, queue_list,
                  result_list, view_tab]
    grid_layout = iw.Layout(
            width='100%',
            grid_template_rows='auto auto auto auto',
            grid_template_columns='24% 24% 24% 24%',
            grid_gap='0% 1%',
            grid_template_areas='''
            "save_config_button save_result_button run_button pause_button "
            "config_list config_list queue_list queue_list "
            "result_list result_list busy_list busy_list "
            "view_tab view_tab view_tab view_tab "
            ''')
    control_tab = iw.GridBox(children=grid_items, layout=grid_layout)

    visu_tab = iw.VBox()

    main_layout = iw.Layout(display="flex", width="98%")
    main_tab = iw.Tab([control_tab, visu_tab], layout=main_layout)
    main_tab.set_title(0, "Scheduler")
    main_tab.set_title(1, "Visualizer")

    return main_tab
