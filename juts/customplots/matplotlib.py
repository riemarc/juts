from abc import abstractmethod, ABCMeta
from ..widgets import Plot, ReplayPanel
import matplotlib.pyplot as plt
import ipywidgets as iw

try:
    import ipympl
except ImportError:
    raise ImportError(
        "Install ipympl to use matplotlib figures as jupyter widgets.")

try:
    ipympl.backend_nbagg.FigureCanvasWebAggCore
except AttributeError:
    raise AttributeError(
        "Maybe '%matplotlib widget' magic is missing in the notebook!")

plt.ioff()
plt.clf()


class MplPlot(Plot, metaclass=ABCMeta):
    def __init__(self, jobs, figsize=(4, 4), update_cycle=0.1, timeout=2,
                 jobs_valid=True):
        self.fig = plt.figure(figsize=figsize)
        widget = self.fig.canvas

        super().__init__(jobs, widget, update_cycle=update_cycle,
                         timeout=timeout, jobs_valid=jobs_valid)

    @abstractmethod
    def update_plot(self, *args, **kwargs):
        pass


class MplReplayPlot(MplPlot, metaclass=ABCMeta):
    def __init__(self, jobs, figsize=(4, 4), update_cycle=0.1, timeout=2,
                 jobs_valid=True):
        super().__init__(jobs, figsize=figsize, update_cycle=update_cycle,
                         timeout=timeout, jobs_valid=jobs_valid)

        self.replay_panel = ReplayPanel()
        self.replay_panel.time_slider.observe(
            self.on_replay_time_change, names="value")
        self.widget = iw.VBox([self.replay_panel, self.widget])

    @abstractmethod
    def update_plot(self, *args, **kwargs):
        pass

    def on_replay_time_change(self, change):
        with self.widget.hold_sync():
            self.update_plot(self.replay_panel.current_time())

    def on_no_jobs_alive(self):
        self.replay_panel.update_time_axis(self.jobs)
