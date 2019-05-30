from .widgets import SchedulerForm, VisualizerForm, UserInterfaceForm
from .container import JobScheduler, Job, Configuration, load_configurations, Signal
import warnings


def get_jobs_from_user_input(handle, config):
    jobs = list()
    for key, value in config.items():
        job_config = {key: value}
        jobs.append(Job(Configuration(job_config, handle)))

    return jobs

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
    def __init__(self, handle=None, config=None):
        if isinstance(config, str):
            config = load_configurations(config)

        if handle is None:
            jobs = list()

        else:
            jobs = get_jobs_from_user_input(handle, config)

        super().__init__(jobs)

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
        self.job_view.show_bt.on_click(self.on_show_bt)
        self.job_view.discard_bt.on_click(self.on_discard_bt)

        self.job_scheduler = JobScheduler(handle)
        self.job_scheduler.start()
        self.job_scheduler.sync_queue.observe(self.on_js_sync_queue, names="value")
        self.job_scheduler.sync_busy.observe(self.on_js_sync_busy, names="value")
        self.job_scheduler.sync_done.observe(self.on_js_sync_done, names="value")

        self._block_signal = False

    def on_load_configs(self):
        pass

    def on_save_configs(self):
        pass

    def on_save_results(self):
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
        print("on_config_change")
        self.view_new_job(0, change["new"])

    @on_unblocked_signal
    def on_queue_change(self, change):
        print("on_queue_change")
        self.view_new_job(1, change["new"])

    @on_unblocked_signal
    def on_busy_change(self, change):
        print("on_busy_change")
        self.view_new_job(2, change["new"])

    @on_unblocked_signal
    def on_result_change(self, change):
        print("on_result_change")
        self.view_new_job(3, change["new"])

    @on_unblocked_signal
    def view_new_job(self, list_index, item_index):
        print("view_new_job")
        if item_index is not None:
            for i, lst in enumerate(self.job_lists):
                if i != list_index:
                    lst.select.index = None
            try:
                new_job = self.job_lists[list_index].job_list[item_index]
                self.job_view.update_view(new_job, self.job_list_labels[list_index])

            except IndexError:
                warnings.warn("can not show job: index out of range")

    def on_sync_bt(self, change):
        pass

    @block_signal
    def on_queue_bt(self, change):
        print("on_queue_bt")
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

    def on_show_bt(self, change):
        pass

    @block_signal
    def on_js_sync_queue(self, change):
        print("on_js_sync_queue")
        self.queue_list.sync_jobs(list(self.job_scheduler.queue_jobs))

    @block_signal
    def on_js_sync_busy(self, change):
        print("on_js_sync_busy")
        self.busy_list.sync_jobs(list(self.job_scheduler.busy_jobs))

    @block_signal
    def on_js_sync_done(self, change):
        print("on_js_sync_done")
        self.result_list.sync_jobs(list(self.job_scheduler.done_jobs))

    def add_config(self, handle, config):
        jobs = get_jobs_from_user_input(handle, config)
        self.config_list.append_jobs(jobs)


class VisualizerInterface(VisualizerForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UserInterface(UserInterfaceForm):
    def __init__(self, handle=None, config=None):
        scheduler = SchedulerInterface(handle, config)
        visualizer = VisualizerInterface()
        super().__init__(scheduler, visualizer)

    def add_config(self, handle, config):
        self.scheduler.add_config(handle, config)
