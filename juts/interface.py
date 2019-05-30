from .widgets import SchedulerForm, VisualizerForm, UserInterfaceForm
from .container import JobScheduler, Job, Configuration, load_configurations


def get_jobs_from_user_input(handle, config):
    jobs = list()
    for key, value in config.items():
        job_config = {key: value}
        jobs.append(Job(Configuration(job_config, handle)))

    return jobs


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
        self.result_list.select.observe(self.on_busy_change, names="index")

        self.job_view.queue_bt.on_click(self.on_queue_bt)
        self.job_view.sync_bt.observe(self.on_sync_bt, names="value")
        self.job_view.save_config_bt.observe(self.on_save_config_bt, names="value")
        self.job_view.save_result_bt.observe(self.on_save_result_bt, names="value")
        self.job_view.show_bt.observe(self.on_show_bt, names="value")
        self.job_view.discard_bt.observe(self.on_discard_bt, names="value")

        self.job_scheduler = JobScheduler(handle)
        self.job_scheduler.sync_queue.observe(self.on_js_sync_queue, names="value")
        self.job_scheduler.sync_busy.observe(self.on_js_sync_busy, names="value")

    def on_load_configs(self):
        pass

    def on_save_configs(self):
        pass

    def on_save_results(self):
        pass

    def on_play_queue(self, change):
        pass

    def on_config_change(self, change):
        self.view_new_job(0, change["new"])

    def on_queue_change(self, change):
        self.view_new_job(1, change["new"])

    def on_busy_change(self, change):
        self.view_new_job(2, change["new"])

    def on_result_change(self, change):
        self.view_new_job(3, change["new"])

    def view_new_job(self, list_index, item_index):
        if item_index is not None:
            new_job = self.job_lists[list_index].job_list[item_index]
            self.job_view.update_view(new_job, self.job_list_labels[list_index])

    def on_sync_bt(self, change):
        pass

    def on_queue_bt(self, change):
        job = self.config_list.pop_item()
        self.job_scheduler.append_queue_job(job)

    def on_save_config_bt(self, change):
        pass

    def on_save_result_bt(self, change):
        pass

    def on_discard_bt(self, change):
        pass

    def on_show_bt(self, change):
        pass

    def on_js_sync_queue(self, change):
        self.queue_list.sync_items(list(self.job_scheduler.queue))

    def on_js_sync_busy(self, change):
        pass

    def add_config(self, handle, config):
        jobs = get_jobs_from_user_input(handle, config)
        self.config_list.add_items(jobs)


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
