from IPython.display import display
import ipywidgets as iw


class SelectWithLabel(iw.VBox):
    def __init__(self, label, list_items):
        self.label = iw.Label(label)
        self.config_select_view = iw.Select(options=list_items)
        super(SelectWithLabel, self).__init__(children=[self.label, self.config_select_view])


class AccordionWithHeader(iw.Accordion):
    def __init__(self, header, labeled):
        widget = iw.VBox(children=[])
        super(AccordionWithHeader, self).__init__(widget)

