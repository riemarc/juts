from .container import JobScheduler, Job, Configuration, \
    load_configs_from_file, block_signal, on_unblocked_signal, \
    dump_configurations, get_filename, \
    load_configs_from_file_upload, Signal
from .widgets import SchedulerForm, VisualizerForm, UserInterfaceForm
from IPython.display import FileLink
import ipywidgets as iw
import warnings


class SchedulerInterface(SchedulerForm):
    def __init__(self):
        super().__init__()

        self.load_configs_bt.observe(self.on_load_configs, names="value")
        self.save_configs_bt.on_click(self.on_save_configs)
        self.save_configs_bt.disabled = True
        self.save_results_bt.on_click(self.on_save_results)
        self.save_results_bt.disabled = True
        self.discard_func_bt.on_click(self.on_discard_func)
        self.discard_func_bt.disabled = True
        self.discard_config_bt.on_click(self.on_discard_config)
        self.discard_config_bt.disabled = True

        self.n_kernels.observe(self.on_n_kernels, names="value")
        self.play_queue_bt.observe(self.on_play_queue, names="value")
        self.discard_job_bt.on_click(self.on_discard_job_bt)
        self.dl2 = iw.dlink((self.job_view.pick_bt, "disabled"),
                            (self.discard_job_bt, "disabled"))

        self.config_list.select.observe(self.on_config_change, names="index")
        self.config_list.select.observe(self.on_config_change_options, names="options")
        self.func_list.select.observe(self.on_func_change, names="index")

        self.queue_list.select.observe(self.on_queue_change, names="index")
        self.busy_list.select.observe(self.on_busy_change, names="index")
        self.result_list.select.observe(self.on_result_change, names="index")
        self.result_list.select.observe(self.on_result_change_options, names="options")

        # only config view
        self.config_job_view.queue_bt.on_click(self.on_queue_bt)
        self.job_queued = Signal()
        self.queued_job = None

        # config + job view
        self.config_job_view.pick_bt.on_click(self.on_cjv_pick_bt)
        self.config_job_view.save_config_bt.on_click(self.on_cjv_save_config_bt)
        self.job_view.pick_bt.on_click(self.on_jv_pick_bt)
        self.job_view.save_config_bt.on_click(self.on_jv_save_config_bt)

        # only job view
        self.job_view.save_result_bt.on_click(self.on_save_result_bt)

        self.job_scheduler = JobScheduler()
        self.job_scheduler.start()
        self.job_scheduler.sync_queue.observe(self.on_js_sync_queue, names="value")
        self.job_scheduler.sync_busy.observe(self.on_js_sync_busy, names="value")
        self.job_scheduler.sync_done.observe(self.on_js_sync_done, names="value")
        self.job_scheduler_lists = [self.job_scheduler.queue_jobs,
                                    self.job_scheduler.busy_jobs,
                                    self.job_scheduler.done_jobs]
        if not self.job_scheduler.max_kernels > 0:
            raise ValueError("No kernels available.")

        self.n_kernels.max = self.job_scheduler.max_kernels
        self.n_kernels.min = 1
        self.n_kernels.value = self.job_scheduler.max_kernels

        self._block_signal = False

    def on_load_configs(self, change):
        configs = load_configs_from_file_upload(self.load_configs_bt)
        self.add_configs(configs)

    def on_save_configs(self, change):
        if len(self.config_list.item_list) == 0:
            return

        fn = get_filename("configs", "yml")
        self.dump_configs(fn, self.config_list.item_list)

    def dump_configs(self, fn, configs):
        dump_configurations(fn, configs)
        fl = FileLink(fn)
        self.download_view.add_file_link(fl)

    def on_save_results(self, change):
        pass

    def on_discard_func(self, change):
        self.func_list.pop_item()
        self.setup_new_job()

    def on_discard_config(self, change):
        self.config_list.pop_item()
        self.setup_new_job()

    def on_n_kernels(self, change):
        self.job_scheduler.available_kernels = self.n_kernels.value

    def on_play_queue(self, change):
        if change["new"]:
            self.play_queue_bt.description = "Pause"
            self.play_queue_bt.icon = "pause"
            self.job_scheduler.start_queue()

        else:
            self.play_queue_bt.description = "Run"
            self.play_queue_bt.icon = "play"
            self.job_scheduler.pause_queue()

    def on_discard_job_bt(self, change):
        for i, lst in enumerate(self.job_lists):
            if lst.select.index is not None:
                self.job_scheduler_lists[i].pop(lst.select.index)
                sync_handl = [self.on_js_sync_queue,
                              self.on_js_sync_busy,
                              self.on_js_sync_done][i]
                sync_handl(None)

    @on_unblocked_signal
    def on_func_change(self, change):
        self.setup_new_job()
        self.discard_func_bt.disabled = change["new"] is None

    @on_unblocked_signal
    def on_config_change(self, change):
        self.setup_new_job()
        self.discard_config_bt.disabled = change["new"] is None

    def on_config_change_options(self, change):
        self.save_configs_bt.disabled = len(change["new"]) == 0

    def setup_new_job(self):
        f_idx = self.func_list.select.index
        c_idx = self.config_list.select.index
        if c_idx is not None and f_idx is not None:
            new_job = Job(self.func_list.item_list[f_idx],
                          self.config_list.item_list[c_idx])
            self.config_job_view.update_view(new_job, "config")
        else:
            self.config_job_view.set_mode("config", empty=True)

    @on_unblocked_signal
    def on_queue_change(self, change):
        self.view_new_job(0, change["new"])

    @on_unblocked_signal
    def on_busy_change(self, change):
        self.view_new_job(1, change["new"])

    @on_unblocked_signal
    def on_result_change(self, change):
        self.view_new_job(2, change["new"])

    def on_result_change_options(self, change):
        self.save_results_bt.disabled = len(change["new"]) == 0

    def view_new_job(self, list_index, item_index):
        if item_index is None:
            return

        for i, lst in enumerate(self.job_lists):
            if i != list_index:
                lst.select.index = None

        try:
            new_job = self.job_lists[list_index].item_list[item_index]
            self.job_view.update_view(new_job, self.job_list_labels[list_index])
        except IndexError:
            warnings.warn("Can not show job: index out of range!")

    def on_cjv_pick_bt(self, change):
        self.add_config(self.config_job_view.get_config())

    def on_jv_pick_bt(self, change):
        self.add_config(self.job_view.get_config())

    def get_visible_job_names(self):
        return list(self.queue_list.select.options) + \
            list(self.busy_list.select.options) + \
            list(self.result_list.select.options)

    @block_signal
    def on_queue_bt(self, change):
        assert self.config_job_view.source_list == "config"
        job = self.config_job_view.get_job()
        visible_jobs = self.get_visible_job_names()
        if job.name in visible_jobs:
            i = 1
            while f"{job.name}_{i}" in visible_jobs:
                i += 1
            job.name = f"{job.name}_{i}"
        self.job_scheduler.append_queue_job(job)
        self.queued_job = job
        self.job_queued()

    def on_cjv_save_config_bt(self, change):
        self.on_save_config_bt(self.config_job_view.get_config())

    def on_jv_save_config_bt(self, change):
        self.on_save_config_bt(self.job_view.get_config())

    def on_save_config_bt(self, config):
        fn = get_filename("", "yml", post=config.name.replace(" ", "_"))
        self.dump_configs(fn, [config])

    def on_save_result_bt(self, change):
        if not self.job_view.results_empty:
            pass

    @block_signal
    def on_js_sync_queue(self, change):
        self.queue_list.sync_items(list(self.job_scheduler.queue_jobs))
        self.update_job_view()

    @block_signal
    def on_js_sync_busy(self, change):
        self.busy_list.sync_items(list(self.job_scheduler.busy_jobs))
        self.update_job_view()

    @block_signal
    def on_js_sync_done(self, change):
        self.result_list.sync_items(list(self.job_scheduler.done_jobs))
        self.update_job_view()

    def update_job_view(self):
        for i, lst in enumerate(self.job_lists):
            if lst.select.index is not None:
                self.job_view.update_view(lst.item_list[lst.select.index],
                                          self.job_list_labels[i])
                return

        self.job_view.set_mode("queue", empty=True)

class VisualizerInterface(VisualizerForm):
    def __init__(self, play_queue_bt):
        super().__init__(play_queue_bt)

        self.job_list.select.observe(self.on_job_change, names="index")
        self.widget_list.select.observe(self.on_widget_change, names="index")
        self.plot_list.select.observe(self.on_plot_change, names="index")

        self.discard_job_bt.on_click(self.on_discard_job_bt)
        self.create_plot_bt.on_click(self.on_create_plot_bt)
        self.discard_plot_bt.on_click(self.on_discard_plot_bt)

    def add_plot_widget(self, widget):
        self.widget_list.append_items([widget])

    def update_create_plot_bt(self):
        self.create_plot_bt.disabled = (
                len(self.job_list.select.index) == 0
                or
                self.widget_list.select.index is None
        )

    def on_job_change(self, change):
        self.discard_job_bt.disabled = len(change["new"]) == 0
        self.update_create_plot_bt()

    def on_widget_change(self, change):
        self.update_create_plot_bt()

    def on_plot_change(self, change):
        self.discard_plot_bt.disabled = len(change["new"]) == 0
        plots = [self.plot_list.item_list[i] for i in change["new"]]
        self.plot_view.sync_plots(plots)

    def on_discard_job_bt(self, change):
        for idx in self.job_list.select.index:
            self.job_list.pop_item(idx)

    def on_discard_plot_bt(self, change):
        for idx in self.plot_list.select.index:
            self.plot_list.pop_item(idx)

    def on_create_plot_bt(self, change):
        indices = self.job_list.select.index
        jobs = [self.job_list.item_list[i] for i in indices]
        pwidget = self.widget_list.item_list[self.widget_list.select.index]
        plot = pwidget(jobs)
        if plot.jobs_valid:
            plot.start()
            self.plot_list.append_items([plot])
        else:
            self.job_list.raise_icon(False, "jobs not compatible")


class UserInterface(UserInterfaceForm):
    def __init__(self):
        scheduler = SchedulerInterface()
        visualizer = VisualizerInterface(scheduler.play_queue_bt)
        super().__init__(scheduler, visualizer)

        self.scheduler.job_view.add_to_visu_bt.on_click(self.on_add_to_visu)
        self.scheduler.job_queued.observe(self.on_job_queued, names="value")
        self.auto_add_to_visu = False

    def on_add_to_visu(self, change):
        job_list = None
        for lst in self.scheduler.job_lists:
            if lst.select.index is not None:
                job_list = lst

        if job_list is None:
            return
        if job_list.select.index is None:
            return

        self.add_to_visu(job_list.item_list[job_list.select.index])

    def add_to_visu(self, job):
        if job.name in self.visualizer.job_list.select.options:
            self.scheduler.job_view.raise_icon(False, "job already added to visualizer")
        else:
            self.visualizer.job_list.append_items([job])

    def on_job_queued(self, change):
        if self.auto_add_to_visu:
            self.add_to_visu(self.scheduler.queued_job)

    def set_auto_add_to_visu(self, auto_add=True):
        self.auto_add_to_visu = auto_add