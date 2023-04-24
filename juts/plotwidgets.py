import warnings

from .widgets import Plot, ReplayPanel
from collections import OrderedDict
from numbers import Number
import ipywidgets as iw
import bqplot as bq
import numpy as np


class TimeSeriesPlot(Plot):
    def __init__(self, jobs, plot_layout="tab"):
        self.n_points = iw.BoundedIntText(
            value=0,
            min=0,
            max=10 ** 8,
            step=1,
            description='Number of points (0 means all):',
            style={'description_width': 'initial'})
        self.n_points.observe(self.on_n_points, names="value")

        self.plot_layout = plot_layout
        if plot_layout == "tab":
            self.fig_wid = iw.Tab()
        elif plot_layout == "vbox":
            self.fig_wid = iw.VBox()
        else:
            raise NotImplementedError

        widget = iw.VBox([self.fig_wid, self.n_points])
        super().__init__(jobs, widget)

        self.indices = dict()
        self.figures = dict()
        self.jobs = jobs
        self.update_plot()

    def on_n_points(self, change):
        if all([not job.is_alive() for job in self.jobs]):
            self.update_plot()

    def update_plot(self, *args, **kwargs):
        if self.result_structure_changed():
            self.update_figures()

        for res_name, job_dict in self.indices.items():
            x = list()
            y = list()
            for index in job_dict.values():
                if "time" not in self.jobs[index].result:
                    continue

                x.append(list(
                    self.jobs[index].result["time"][-self.n_points.value:]))
                y.append(list(
                    self.jobs[index].result[res_name][-self.n_points.value:]))

            if any([len(xi) != len(yi) for xi, yi in zip(x, y)]):
                raise ValueError("X (time) and Y data have different shapes.")

            if not(len(x) > 0 and any([len(xi) > 1 for xi in x])):
                return

            xx = np.empty((len(x), max([len(xi) for xi in x])), float)
            xx[:] = np.nan
            yy = np.array(xx)
            for i, xi in enumerate(x):
                xx[i, :len(xi)] = xi
            for i, yi in enumerate(y):
                yy[i, :len(yi)] = yi

            self.figures[res_name].marks[0].x = xx
            self.figures[res_name].marks[0].y = yy

    def result_structure_changed(self):
        indices = OrderedDict()
        for i, job in enumerate(self.jobs):
            for res_name, res in job.result.items():
                if res_name == "time":
                    continue

                is_timeseries = self.is_timeseries(res)
                if res_name not in indices:
                    if is_timeseries:
                        indices[res_name] = OrderedDict()

                if is_timeseries:
                    indices[res_name][job.name] = i

        res = not indices == self.indices

        if res:
            self.indices = indices

        return res

    def update_figures(self):
        self.figures = OrderedDict()
        self.fig_wids = OrderedDict()
        for res_name, job_dict in self.indices.items():
            sc_x = bq.LinearScale()
            sc_y = bq.LinearScale()
            line = bq.Lines(
                scales={'x': sc_x, 'y': sc_y},
                labels=list(job_dict.keys()),
                display_legend=True)
            ax_x = bq.Axis(scale=sc_x, label='time')
            ax_y = bq.Axis(scale=sc_y, orientation='vertical', label=res_name)
            self.figures[res_name] = bq.Figure(
                marks=[line], axes=[ax_x, ax_y], legend_location="top-right")

            pan_zoom = self.get_pan_zoom(sc_x, sc_y, self.figures[res_name])

            fig_wid = iw.VBox([
                self.figures[res_name], pan_zoom], align_self='stretch')
            self.fig_wids[res_name] = fig_wid

        self.layout_figures()

    def get_pan_zoom(self, sc_x, sc_y, figure):
        pz = bq.PanZoom(scales={'x': [sc_x], 'y': [sc_y]})
        pzx = bq.PanZoom(scales={'x': [sc_x]})
        pzy = bq.PanZoom(scales={'y': [sc_y], })

        zoom_interacts = iw.ToggleButtons(
            options=OrderedDict([
                ('xy ', pz),
                ('x ', pzx),
                ('y ', pzy),
                (' ', None)]),
            icons=["arrows", "arrows-h", "arrows-v", "stop"],
            tooltips=["zoom/pan in x & y", "zoom/pan in x only",
                      "zoom/pan in y only", "cancel zoom/pan"]
        )
        zoom_interacts.value = None
        zoom_interacts.style.button_width = '60px'

        reset_zoom_bt = iw.Button(
            description='',
            disabled=False,
            tooltip='reset zoom',
            icon='arrows-alt'
        )

        def reset_zoom(new, fig=figure):
            fig.axes[0].scale.min = None
            fig.axes[1].scale.min = None
            fig.axes[0].scale.max = None
            fig.axes[1].scale.max = None

        reset_zoom_bt.on_click(reset_zoom)
        reset_zoom_bt.layout.width = '60px'

        iw.link((zoom_interacts, 'value'), (figure, 'interaction'))

        return iw.HBox([zoom_interacts, reset_zoom_bt])

    def layout_figures(self):
        if self.plot_layout == "tab":
            self.layout_figures_tab()
        else:
            self.layout_figures_vbox()

    def layout_figures_tab(self):
        self.fig_wid.children = list(self.fig_wids.values())
        for i, res_name in enumerate(self.fig_wids):
            self.fig_wid.set_title(i, res_name)

    def layout_figures_vbox(self):
        n_columns = 2
        n_figures = len(self.figures)
        n_rows = int(np.ceil(n_figures / n_columns))
        figures = list(self.fig_wids.values())

        vbox_children = list()
        for i in range(n_rows):
            hbox_children = list()
            for j in range(n_columns):
                if figures:
                    hbox_children.append(figures.pop(0))

            vbox_children.append(iw.HBox(hbox_children))

        self.fig_wid.children = vbox_children

    @staticmethod
    def is_timeseries(result):
        if not hasattr(result, "__iter__"):
            return False

        if len(result) == 0:
            return False

        if not isinstance(result[0], Number):
            return False

        return True


class TimeSeriesReplayPlot(TimeSeriesPlot):
    def __init__(self, jobs, plot_layout="tab"):
        super().__init__(jobs, plot_layout=plot_layout)

        self.replay_panel = ReplayPanel()
        self.replay_panel.time_slider.observe(
            self.on_replay_time_change, names="value")
        self.widget.children = [self.replay_panel] + list(self.widget.children)

    def on_replay_time_change(self, change):
        with self.widget.hold_sync():
            for res_name, figure in self.figures.items():
                figure.marks[1].x = [self.replay_panel.current_time()] * 2

    def on_no_jobs_alive(self):
        self.replay_panel.update_time_axis(self.jobs)
        for res_name, figure in self.figures.items():
            min_values = list()
            max_values = list()
            for y in figure.marks[0].y:
                min_values.append(np.min(y))
                max_values.append(np.max(y))

            line = bq.Lines(
                colors=["green"],
                scales={'x': figure.marks[0].scales["x"],
                        'y': figure.marks[0].scales["y"]},
                display_legend=False,
                x=[self.replay_panel.current_time()] * 2,
                y=[np.min(min_values), np.max(max_values)]
            )
            figure.marks = [figure.marks[0], line]
