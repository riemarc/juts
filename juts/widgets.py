from IPython.display import display
import ipywidgets as iw


class JutsWidget:
    def __init__(self, widget):
        self.widget = widget

    def get_widget(self):
        return self.widget

    def set_layout(self, layout):
        self.widget.layout = layout

    def _repr_pretty_(self, *args):
        display(self.widget)


class LabeledList(JutsWidget):
    def __init__(self, label, list_items):
        self.label = iw.Label(label)
        self.config_select_view = iw.Select(options=list_items)

        widget = iw.VBox(children=[self.label, self.config_select_view])
        super(LabeledList, self).__init__(widget)


class ConfigurationView(JutsWidget):
    def __init__(self):

        widget = iw.VBox(children=[])
        super(ConfigurationView, self).__init__(widget)

