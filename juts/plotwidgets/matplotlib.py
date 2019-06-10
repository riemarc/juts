import matplotlib.pyplot as plt
from abc import abstractmethod, ABCMeta
from ..container import Plot

try:
    import ipympl
except ImportError:
    raise ImportError(
        "Install ipympl to use matplotlib figures as jupyter widgets.")

try:
    _ = ipympl.backend_nbagg.FigureCanvasNbAgg
except AttributeError:
    raise AttributeError(
        "Maybe '%matplotlib widget' magic is missing in the notebook!")

plt.ioff()
plt.clf()


class MplPlot(Plot, metaclass=ABCMeta):
    def __init__(self, jobs, update_cycle=0.1, timeout=2, jobs_valid=True):
        self.fig = plt.figure()
        widget = self.fig.canvas

        super().__init__(jobs, widget, update_cycle=update_cycle,
                         timeout=timeout, jobs_valid=jobs_valid)

    @abstractmethod
    def update_plot(self):
        pass
