import ipywidgets as iw


class Widget:
    def __init__(self, widget):
        self.widget = widget

    def get_widget(self):
        return self.widget

    def set_layout(self, layout):
        self.widget.layout = layout


class LabeledList(Widget):
    def __init__(self, label, list_items):
        label = iw.Label(label)
        self.config_select_view = iw.Select(list_items)

        widget = iw.VBox(children=[label, self.config_select_view])
        super(LabeledList, self).__init__(widget)


class ConfigurationView(Widget):
    def __init__(self):

        widget = iw.VBox(children=[])
        super(ConfigurationView, self).__init__(widget)

