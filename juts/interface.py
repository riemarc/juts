from .container import JobScheduler, Job, Configuration, load_configurations
from .widgets import SchedulerForm, VisualizerForm, UserInterfaceForm
import warnings


def block_signal(meth):
    def handle(*args, **kwargs):
        args[0]._block_signal = True
        res = meth(*args, **kwargs)
        args[0]._block_signal = False

        return res

    return handle


def on_unblocked_signal(meth):
    def handle(*args, **kwargs):
        if not args[0]._block_signal:
            return meth(*args, **kwargs)

    return handle


class SchedulerInterface(SchedulerForm):
    def __init__(self):
        super().__init__()

        self.load_configs_bt.on_click(self.on_load_configs)
        self.save_configs_bt.on_click(self.on_save_configs)
        self.save_results_bt.on_click(self.on_save_results)
        self.play_queue_bt.observe(self.on_play_queue, names="value")

        self.config_list.select.observe(self.on_config_change, names="index")
        self.queue_list.select.observe(self.on_queue_change, names="index")
        self.busy_list.select.observe(self.on_busy_change, names="index")
        self.result_list.select.observe(self.on_result_change, names="index")

        self.job_view.queue_bt.on_click(self.on_queue_bt)
        self.job_view.sync_bt.on_click(self.on_sync_bt)
        self.job_view.save_config_bt.on_click(self.on_save_config_bt)
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
        pass

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
    def on_config_change(self, change):
        self.view_new_job(0, change["new"])

    @on_unblocked_signal
    def on_queue_change(self, change):
        self.view_new_job(1, change["new"])

    @on_unblocked_signal
    def on_busy_change(self, change):
        self.view_new_job(2, change["new"])

    @on_unblocked_signal
    def on_result_change(self, change):
        self.view_new_job(3, change["new"])

    @on_unblocked_signal
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

    def on_sync_bt(self, change):
        pass

    @block_signal
    def on_queue_bt(self, change):
        assert self.job_view.source_list == "config"
        config = self.job_view.get_config()
        job = Job(config)
        self.job_scheduler.append_queue_job(job)

    def on_save_config_bt(self, change):
        pass

    def on_save_result_bt(self, change):
        pass

    def on_discard_bt(self, change):
        pass

    @block_signal
    def on_js_sync_queue(self, change):
        self.queue_list.sync_items(list(self.job_scheduler.queue_jobs))

    @block_signal
    def on_js_sync_busy(self, change):
        self.busy_list.sync_items(list(self.job_scheduler.busy_jobs))

    @block_signal
    def on_js_sync_done(self, change):
        self.result_list.sync_items(list(self.job_scheduler.done_jobs))

    @staticmethod
    def get_jobs_from_user_input(handle, config):
        jobs = list()
        for key, value in config.items():
            job_config = {key: value}
            jobs.append(Job(Configuration(job_config, handle)))

        return jobs

    def add_config(self, handle, config):
        jobs = self.get_jobs_from_user_input(handle, config)
        self.config_list.append_items(jobs)


class VisualizerInterface(VisualizerForm):
    def __init__(self, play_queue_bt):
        super().__init__(play_queue_bt)

        self.create_plot_bt.on_click(self.on_create_plot_bt)

    def add_visualizer(self, visualizer):
        self.widget_list.append_items([visualizer])

    def on_create_plot_bt(self, change):
        indices = self.job_list.select.index
        jobs = [self.job_list.item_list[i] for i in indices]
        pwidget = self.widget_list.item_list[self.widget_list.select.index]
        plot = pwidget(jobs)
        self.plot_list.append_items([plot])


class UserInterface(UserInterfaceForm):
    def __init__(self):
        scheduler = SchedulerInterface()
        visualizer = VisualizerInterface(scheduler.play_queue_bt)
        super().__init__(scheduler, visualizer)

        self.scheduler.job_view.add_to_visu_bt.on_click(self.on_add_to_visu)

    def add_config(self, handle, config=None, configfile=None):
        if config and configfile:
            raise NotImplementedError

        elif configfile:
            config = load_configurations(configfile)

        self.scheduler.add_config(handle, config)

    def add_visualizer(self, visualizer):
        self.visualizer.add_visualizer(visualizer)

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
