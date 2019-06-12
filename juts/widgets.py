from .container import Configuration, Job
from abc import abstractmethod, ABCMeta
from threading import Thread, Event
from collections import OrderedDict
from ast import literal_eval
import ipywidgets as iw
import numpy as np
import time


class ConfigurationView(iw.Accordion):
    def __init__(self, config=None):
        super().__init__(children=[])

        if config is not None:
            self.update_view(config, True)

    def update_view(self, config, editable):
        assert isinstance(config, Configuration)
        self.config = config

        accordion_items = list()
        for param_set in config.values():

            param_set_items = list()
            for key, value in param_set.items():
                param_set_items.append(
                    iw.Text(value=str(value),
                            description=key,
                            disabled=not editable))

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
        self.add_to_visu_bt = iw.Button(
            description='Add to Visu', icon="eye")
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
        editable = source_list == "config"
        self.config_view.update_view(self.job.config, editable)
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
            header = [self.text, self.add_to_visu_bt, self.discard_bt]
            accordion = [self.config_view]
            accordion_title = ["Configuration"]
            self.children = [self.label, self.header_box, self.accordion]

        elif source_list == "busy":
            self.text.disabled = True
            header = [self.text]
            accordion = [self.config_view, self.log_view]
            accordion_title = ["Configuration", "Log"]
            self.children = [self.label, self.header_box, self.job.progress,
                             self.accordion]

        elif source_list == "result":
            self.text.disabled = True
            header = [self.text, self.sync_bt, self.add_to_visu_bt,
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


class PlotView(iw.VBox):
    def __init__(self):
        self.label = iw.Label("Plot View")
        self.plots = dict()

        super().__init__([self.label, iw.HBox()])

    def sync_plots(self, plots):
        children = []
        for plot in plots:
            if plot in self.plots:
                children.append(self.plots[plot])

            else:
                widget = iw.Accordion([plot.widget])
                widget.set_title(0, PlotList.get_item_str(plot))
                self.plots[plot] = widget
                children.append(widget)

        self.children[1].children = tuple(children)


class ItemList(iw.VBox):
    def __init__(self, label, items, mode, **kwargs):
        self.label = iw.Label(label)

        if items is None:
            self.item_list = list()

        else:
            self.item_list = list(items)

        select = [self.get_item_str(it) for it in self.item_list]
        select_layout = iw.Layout(width="auto", height="100px")
        if mode == "select":
            self.select = iw.Select(options=select, layout=select_layout)

        elif mode == "select_multiple":
            self.select = iw.SelectMultiple(options=select, layout=select_layout)

        else:
            raise NotImplementedError

        super().__init__([self.label, self.select], **kwargs)

    @staticmethod
    def get_item_str(it):
        return it.name

    def append_items(self, items):
        self.item_list += items
        self.select.options = (
            tuple(list(self.select.options) +
                  [self.get_item_str(it) for it in items]))

        if isinstance(self.select, iw.Select):
            self.select.index = None
        else:
            self.select.index = tuple()

    def pop_item(self, index=None):
        if not index:
            index = self.select.index

        item = self.item_list[index]
        self.item_list = [
            it for i, it in enumerate(self.item_list) if i != index]
        self.select.options = tuple([
            it for i, it in enumerate(self.select.options) if i != index])

        if isinstance(self.select, iw.Select):
            self.select.index = None
        else:
            self.select.index = tuple()

        return item

    def sync_items(self, jobs):
        self.item_list = jobs
        self.select.options = tuple([it.config.name for it in jobs])

        if isinstance(self.select, iw.Select):
            self.select.index = None
        else:
            self.select.index = tuple()


class JobList(ItemList):
    def __init__(self, label, jobs, **kwargs):
        super().__init__(label, jobs, "select", **kwargs)

    @staticmethod
    def get_item_str(it):
        return it.config.name


class VisuJobList(ItemList):
    def __init__(self, label, jobs, **kwargs):
        super().__init__(label, jobs, "select_multiple", **kwargs)

    @staticmethod
    def get_item_str(it):
        return it.config.name


class PlotWidgetList(ItemList):
    def __init__(self, label, widgets, **kwargs):
        super().__init__(label, widgets, "select", **kwargs)

    @staticmethod
    def get_item_str(it):
        return it.__name__


class PlotList(ItemList):
    def __init__(self, label, plots, **kwargs):
        super().__init__(label, plots, "select_multiple", **kwargs)

    @staticmethod
    def get_item_str(it):
        args = ", ".join([job.config.name for job in it.jobs])

        return "{}({})".format(it.__class__.__name__, args)


class SchedulerForm(iw.GridBox):
    def __init__(self):
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
            "Configurations", tuple(), layout=head_it_layout("config_list"))
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


class VisualizerForm(iw.GridBox):
    def __init__(self, play_queue_bt):
        head_it_layout = lambda lbl: iw.Layout(width='auto', grid_area=lbl)

        self.discard_job_bt = iw.Button(
            description="Discard Job(s)", icon="remove",
            layout=head_it_layout("discard_job_button"))
        self.job_list = VisuJobList(
            "Jobs", tuple(), layout=head_it_layout("job_list"))

        self.create_plot_bt = iw.Button(
            description="Create Plot", icon="play",
            layout=head_it_layout("create_button"))
        self.widget_list = PlotWidgetList(
            "Plot Widgets", tuple(), layout=head_it_layout("widget_list"))
        self.valid_icon = iw.Valid(value=True)
        widget_list_header = iw.HBox([self.widget_list.label, self.valid_icon])
        self.widget_list.children = tuple(
            [widget_list_header, self.widget_list.select])

        self.discard_plot_bt = iw.Button(
            description="Discard Plot(s)", icon="remove",
            layout=head_it_layout("discard_plot_button"))
        self.plot_list = PlotList(
            "Plots", tuple(), layout=head_it_layout("plot_list"))

        self.list_labels = ["job", "widget", "plot"]
        self.lists = [self.job_list, self.widget_list, self.job_list]

        self.plot_view = PlotView()
        self.plot_view.layout = head_it_layout("plot_view")

        spacer = iw.Label(str(""), layout=head_it_layout("spacer"))

        grid_items = [play_queue_bt, self.discard_job_bt, self.create_plot_bt,
                      self.discard_plot_bt, self.job_list, self.widget_list,
                      self.plot_list, self.plot_view, spacer]
        grid_layout = iw.Layout(
            width='100%',
            grid_template_rows='auto auto auto',
            grid_template_columns='15.7% 15.7% 15.7% 15.7% 15.7% 15.7%',
            grid_gap='0% 1%',
            grid_template_areas='''
                "run_button discard_job_button create_button create_button discard_plot_button discard_plot_button "
                "job_list job_list widget_list widget_list plot_list plot_list "
                "spacer spacer spacer spacer spacer spacer "
                "plot_view plot_view plot_view plot_view plot_view plot_view "
                ''')

        super().__init__(grid_items, layout=grid_layout)


class UserInterfaceForm(iw.Tab):
    def __init__(self, scheduler, visualizer):
        layout = iw.Layout(display="flex", width="98%")
        self.scheduler = scheduler
        self.visualizer = visualizer
        tabs = [scheduler, visualizer]

        super().__init__(tabs, layout=layout)

        self.set_title(0, "Scheduler")
        self.set_title(1, "Visualizer")


class Plot(Thread, metaclass=ABCMeta):
    def __init__(self, jobs, widget, update_cycle=0.1, timeout=2, jobs_valid=True):
        super().__init__()

        self.jobs = jobs
        self.widget = widget
        self.last_update = time.time()
        self.update_cycle = update_cycle
        self.timeout = timeout
        self.jobs_valid = jobs_valid
        self.update_event = Event()

        for job in jobs:
            job.live_result_update.observe(self.on_live_result_update, names="value")

    def on_live_result_update(self, change):
        self.update_event.set()

    def on_no_jobs_alive(self):
        pass

    @abstractmethod
    def update_plot(self, *args, **kwargs):
        pass

    def run(self):
        while any([job.job_is_alive for job in self.jobs]):
            if self.update_event.wait(self.timeout):
                self.update_event.clear()

                cycle_margin = self.update_cycle - time.time() + self.last_update
                self.last_update = time.time()
                if cycle_margin > 0:
                    time.sleep(cycle_margin)

                with self.widget.hold_sync():
                    self.update_plot()

        self.update_plot()
        self.on_no_jobs_alive()


class ReplayPanel(iw.HBox):
    def __init__(self):
        super().__init__()

        self.range_slider = iw.IntRangeSlider(
            value=[0, 1],
            step=1,
            min=0,
            max=1,
            continuous_update=False,
            orientation='horizontal',
            layout=iw.Layout(width="80%"))
        self.replay_widet = iw.Play(
            interval=100,
            value=0,
            min=0,
            max=1,
            step=1,
            layout=iw.Layout(width="auto"))
        self.interval = iw.BoundedIntText(
            value=100,
            min=1,
            max=10 ** 8,
            step=100,
            description='Interval (ms):',
            style={'description_width': 'initial'},
            layout=iw.Layout(width="initial"))
        self.time_slider = iw.IntSlider(
            min=0,
            max=1,
            layout=iw.Layout(width="80%"))
        self.interval_label = iw.Label("x 1s")

        def on_range_change(change):
            min_, max_ = change["new"]
            self.replay_widet.min = min_
            self.replay_widet.max = max_

        iw.link((self.replay_widet, 'value'), (self.time_slider, 'value'))
        iw.link((self.interval, 'value'), (self.replay_widet, 'interval'))
        self.range_slider.observe(on_range_change, names="value")
        self.children = [
            iw.VBox([iw.HBox([self.time_slider, self.interval_label]),
                     iw.HBox([self.range_slider, self.interval_label])],
                    layout=iw.Layout(width="50%")),
            iw.VBox([self.replay_widet, self.interval],
                    layout=iw.Layout(width="50%")),
        ]

        self.time_min = 0
        self.time_max = 1
        self.time_step = 1
        self.time_index = iw.ValueWidget(value=0)
        iw.link((self.replay_widet, 'value'), (self.time_index, 'value'))

        self.enable_panel(False)

    def enable_panel(self, enable=True):
        self.replay_widet.disabled = not enable
        self.interval.disabled = not enable
        self.range_slider.disabled = not enable
        self.time_slider.disabled = not enable

    def update_time_axis(self, jobs):
        min_times = list()
        max_times = list()
        mean_times = list()
        for job in jobs:
            if "time" in job.result:
                time = job.result["time"]
                min_times.append(time[0])
                max_times.append(time[-1])
                mean_times.append(np.mean(np.diff(time)))

        if not min_times or not max_times:
            return

        self.time_min = min(min_times)
        self.time_max = max(max_times)
        self.time_step = np.mean(mean_times)

        if self.time_min == self.time_max or self.time_step <= 0:
            return

        T = self.time_max - self.time_min
        N = np.ceil(T / self.time_step)
        self.time_slider.max = N
        self.range_slider.max = N
        self.replay_widet.max = N
        self.range_slider.value = (0, N)
        self.interval_label.value = "x {:.3f} s".format(self.time_step)
        self.replay_widet.interval = int(self.time_step * 1000)

        self.enable_panel()

    def current_time(self):
        return self.time_min + self.time_slider.value * self.time_step
