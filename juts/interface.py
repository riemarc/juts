from .container import JobScheduler, Job, Configuration, load_configs_from_file, \
    block_signal, on_unblocked_signal, dump_configurations, get_filename
from .widgets import SchedulerForm, VisualizerForm, UserInterfaceForm
from IPython.display import FileLink
import warnings


class SchedulerInterface(SchedulerForm):
    def __init__(self):
        super().__init__()

        self.load_configs_bt.on_click(self.on_load_configs)
        self.save_configs_bt.on_click(self.on_save_configs)
        self.save_results_bt.on_click(self.on_save_results)
        self.play_queue_bt.observe(self.on_play_queue, names="value")

        self.config_list.select.observe(self.on_config_change, names="index")
        self.func_list.select.observe(self.on_func_change, names="index")

        self.queue_list.select.observe(self.on_queue_change, names="index")
        self.busy_list.select.observe(self.on_busy_change, names="index")
        self.result_list.select.observe(self.on_result_change, names="index")

        # only config view
        self.config_job_view.queue_bt.on_click(self.on_queue_bt)

        # config + job view
        self.config_job_view.pick_bt.on_click(self.on_cjv_pick_bt)
        self.config_job_view.save_config_bt.on_click(self.on_cjv_save_config_bt)
        self.job_view.pick_bt.on_click(self.on_jv_pick_bt)
        self.job_view.save_config_bt.on_click(self.on_jv_save_config_bt)

        # only job view
        self.job_view.save_result_bt.on_click(self.on_save_result_bt)
        self.job_view.discard_bt.on_click(self.on_discard_bt)

        self.job_scheduler = JobScheduler()
        self.job_scheduler.start()
        self.job_scheduler.sync_queue.observe(self.on_js_sync_queue, names="value")
        self.job_scheduler.sync_busy.observe(self.on_js_sync_busy, names="value")
        self.job_scheduler.sync_done.observe(self.on_js_sync_done, names="value")

        self._block_signal = False

    def on_load_configs(self, change):
        pass

    def on_save_configs(self, change):
        fn = get_filename("configs", "yml")
        dump_configurations(fn, self.config_list.item_list)
        fl = FileLink(fn)
        self.download_view.add_file_link(fl)

    def on_save_results(self, change):
        pass

    def on_play_queue(self, change):
        if change["new"]:
            self.play_queue_bt.description = "Pause"
            self.play_queue_bt.icon = "pause"
            self.job_scheduler.start_queue()

        else:
            self.play_queue_bt.description = "Run"
            self.play_queue_bt.icon = "play"
            self.job_scheduler.pause_queue()

    @on_unblocked_signal
    def on_func_change(self, change):
        self.setup_new_job()

    @on_unblocked_signal
    def on_config_change(self, change):
        self.setup_new_job()

    def setup_new_job(self):
        f_idx = self.func_list.select.index
        c_idx = self.config_list.select.index
        if c_idx is not None and f_idx is not None:
            new_job = Job(self.func_list.item_list[f_idx],
                          self.config_list.item_list[c_idx])
            self.config_job_view.update_view(new_job, "config")

    @on_unblocked_signal
    def on_queue_change(self, change):
        self.view_new_job(0, change["new"])

    @on_unblocked_signal
    def on_busy_change(self, change):
        self.view_new_job(1, change["new"])

    @on_unblocked_signal
    def on_result_change(self, change):
        self.view_new_job(2, change["new"])

    def view_new_job(self, list_index, item_index):
        if item_index is not None:
            for i, lst in enumerate(self.job_lists):
                if i != list_index:
                    lst.select.index = None
            try:
                new_job = self.job_lists[list_index].item_list[item_index]
                self.job_view.update_view(new_job, self.job_list_labels[list_index])

            except IndexError:
                warnings.warn("can not show job: index out of range")

    def on_cjv_pick_bt(self, change):
        self.add_config(self.config_job_view.get_config())

    def on_jv_pick_bt(self, change):
        self.add_config(self.config_job_view.get_config())

    @block_signal
    def on_queue_bt(self, change):
        assert self.config_job_view.source_list == "config"
        job = self.config_job_view.get_job()
        self.job_scheduler.append_queue_job(job)

    def on_cjv_save_config_bt(self, change):
        self.on_save_config_bt(self.config_job_view.get_config())

    def on_jv_save_config_bt(self, change):
        self.on_save_config_bt(self.job_view.get_config())

    def on_save_config_bt(self, config):
        fn = get_filename("", "yml", post=config.name.replace(" ", "_"))
        dump_configurations(fn, [config])
        fl = FileLink(fn)
        self.download_view.add_file_link(fl)

    def on_save_result_bt(self, change):
        pass

    def on_discard_bt(self, change):
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
        job_list_label = None
        for i, lst in enumerate(self.job_lists):
            if lst.select.index is not None:
                self.job_view.update_view(lst.item_list[lst.select.index],
                                          self.job_list_labels[i])
                return

        self.job_view.set_mode(job_list_label)



class VisualizerInterface(VisualizerForm):
    def __init__(self, play_queue_bt):
        super().__init__(play_queue_bt)

        self.create_plot_bt.on_click(self.on_create_plot_bt)
        self.plot_list.select.observe(self.on_plot_change, names="index")

    def add_plot_widget(self, widget):
        self.widget_list.append_items([widget])

    def on_plot_change(self, change):
        plots = [self.plot_list.item_list[i] for i in change["new"]]
        self.plot_view.sync_plots(plots)

    def on_create_plot_bt(self, change):
        indices = self.job_list.select.index
        jobs = [self.job_list.item_list[i] for i in indices]

        if self.widget_list.select.index is None:
            self.valid_icon.value = False
            self.valid_icon.readout = "select a widget"

            return

        if len(self.job_list.select.index) ==  0:
            self.valid_icon.value = False
            self.valid_icon.readout = "select a job"

            return

        pwidget = self.widget_list.item_list[self.widget_list.select.index]
        plot = pwidget(jobs)
        if plot.jobs_valid:
            plot.start()
            self.plot_list.append_items([plot])
            self.valid_icon.value = True

        else:
            self.valid_icon.value = False
            self.valid_icon.readout = "not compatible"



class UserInterface(UserInterfaceForm):
    def __init__(self):
        scheduler = SchedulerInterface()
        visualizer = VisualizerInterface(scheduler.play_queue_bt)
        super().__init__(scheduler, visualizer)

        self.scheduler.job_view.add_to_visu_bt.on_click(self.on_add_to_visu)

    def on_add_to_visu(self, change):
        job_list = None
        for lst in self.scheduler.job_lists:
            if lst.select.index is not None:
                job_list = lst

        if job_list is None:
            raise NotImplementedError

        index = job_list.select.index
        job = job_list.item_list[index]
        self.visualizer.job_list.append_items([job])
