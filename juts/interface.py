from .widgets import SchedulerForm, VisualizerForm, UserInterfaceForm
from .container import as_config_list


def on_unblocked_signal(meth):
    def handle(*args, **kwargs):
        if not args[0]._block_signal:
            return meth(*args, **kwargs)

    return handle


def block_signal(meth):
    def handle(*args, **kwargs):
        args[0]._block_signal = True
        res = meth(*args, **kwargs)
        args[0]._block_signal = False

        return res

    return handle


class SchedulerInterface(SchedulerForm):
    def __init__(self, config=None):
        super().__init__(config)

        self._block_signal = False

        self.config_list.select.observe(self.on_config_change, names="index")

    # @block_signal
    def add_configs(self, configs):
        self.config_list.add_items(as_config_list(configs))

    # @on_unblocked_signal
    def on_config_change(self, change):
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

    def block_signal(self, meth, *args, **kwargs):
        self._block_signal = True
        meth(*args, **kwargs)
        self._block_signal = False


def get_user_interface(config=None):
    scheduler = SchedulerInterface(config)
    visualizer = VisualizerInterface()

    return UserInterface(scheduler, visualizer)
