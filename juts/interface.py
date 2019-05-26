from .widgets import SchedulerForm, VisualizerForm, UserInterfaceForm


class SchedulerInterface(SchedulerForm):
    def __init__(self, config=None):
        super().__init__(config)

        self.config_list.select.observe(self.on_config_change, names="index")

    def on_config_change(self, change):
        if not self.ignore_events:
            new_config = self.config_list._list_items[change["new"]]
            self.config_view.new_config(new_config)

    def on_queue_change(self, change):
        pass

    def on_busy_change(self, change):
        pass

    def on_result_change(self, change):
        pass


class VisualizerInterface(VisualizerForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UserInterface(UserInterfaceForm):
    def __init__(self, scheduler, visualizer):
        super().__init__(scheduler, visualizer)


def get_user_interface(config=None):
    scheduler = SchedulerInterface(config)
    visualizer = VisualizerInterface()

    return UserInterface(scheduler, visualizer)
