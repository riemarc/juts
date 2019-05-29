from .widgets import SchedulerForm, VisualizerForm, UserInterfaceForm
from .container import JobScheduler


class SchedulerInterface(SchedulerForm):
    def __init__(self, handle=None, config=None):
        super().__init__(config)

        self.load_configs_bt.on_click(self.on_load_configs)
        self.save_configs_bt.on_click(self.on_save_configs)
        self.save_results_bt.on_click(self.on_save_results)
        self.play_queue_bt.observe(self.on_play_queue, names="value")

        self.config_list.select.observe(self.on_config_change, names="index")
        self.queue_list.select.observe(self.on_queue_change, names="index")
        self.busy_list.select.observe(self.on_busy_change, names="index")
        self.result_list.select.observe(self.on_busy_change, names="index")

        self.config_view.sync_bt.observe(self.on_cv_sync, names="value")
        self.config_view.queue_bt.on_click(self.on_cv_queue)
        self.config_view.remove_bt.observe(self.on_cv_remove, names="value")
        self.config_view.save_bt.observe(self.on_cv_save, names="value")

        self.job_view.show_bt.observe(self.on_jv_show, names="value")
        self.job_view.save_bt.observe(self.on_jv_save, names="value")
        self.job_view.discard_bt.observe(self.on_jv_discard, names="value")

        self.job_scheduler = JobScheduler(handle)

    def on_load_configs(self):
        pass

    def on_save_configs(self):
        pass

    def on_save_results(self):
        pass

    def on_play_queue(self, change):
        pass

    def on_config_change(self, change):
        new_config = self.config_list._list_items[change["new"]]
        self.config_view.update_view(new_config)

    def on_queue_change(self, change):
        self.view_tab.selected_index = 1
        self.view_new_job(self.queue_list, change["new"])

    def on_busy_change(self, change):
        self.view_tab.selected_index = 1
        self.view_new_job(self.busy_list, change["new"])

    def on_result_change(self, change):
        self.view_tab.selected_index = 1
        self.view_new_job(self.result_list, change["new"])

    def view_new_job(self, vlist, index):
        new_job = vlist._list_items[index]
        self.job_view.update_view(new_job)

    def on_cv_sync(self, change):
        pass

    def on_cv_queue(self):
        config = self.config_list.pop_item()
        print(config)
        # self.job_scheduler.append_queue_job(config)

    def on_cv_remove(self, change):
        pass

    def on_cv_save(self, change):
        pass

    def on_jv_show(self, change):
        pass

    def on_jv_save(self, change):
        pass

    def on_jv_discard(self, change):
        pass


class VisualizerInterface(VisualizerForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UserInterface(UserInterfaceForm):
    def __init__(self, handle=None, config=None):
        scheduler = SchedulerInterface(handle, config)
        visualizer = VisualizerInterface()
        super().__init__(scheduler, visualizer)
