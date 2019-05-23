"""Control navigation of FOREST data"""
import bokeh.models
import bokeh.layouts
import util
from collections import namedtuple


State = namedtuple("State", ("pattern", "variable", "initial"))
State.__new__.__defaults__ = (None,) * len(State._fields)


def next_state(current, **kwargs):
    _kwargs = current._asdict()
    _kwargs.update(kwargs)
    return State(**_kwargs)


class Observable(object):
    def __init__(self):
        self.subscribers = []

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def notify(self, state):
        for callback in self.subscribers:
            callback(state)


class Controls(Observable):
    def __init__(self, database, patterns=None):
        if patterns is None:
            patterns = []
        self.patterns = patterns
        self.database = database
        self.initial_times = database.initial_times()
        self.state = State(
            initial=self.first(self.initial_times),
            variable=None)
        self.dropdowns = {
            "pattern": bokeh.models.Dropdown(
                label="Model/observation",
                menu=patterns),
            "variable": bokeh.models.Dropdown(
                label="Variable"),
            "initial_time": bokeh.models.Dropdown(
                label="Initial time"),
            "valid_time": bokeh.models.Dropdown(
                label="Valid time"),
            "pressure": bokeh.models.Dropdown(
                label="Pressure")
        }
        self.dropdowns["pattern"].on_click(self.on_pattern)
        for dropdown in self.dropdowns.values():
            util.autolabel(dropdown)
        self.layout = bokeh.layouts.column(
            self.dropdowns["pattern"],
            self.dropdowns["variable"],
            self.dropdowns["initial_time"],
            self.dropdowns["valid_time"],
            self.dropdowns["pressure"])

        super().__init__()

        # Connect state changes to render
        self.subscribe(self.render)

    def render(self, state):
        """Configure dropdown menus"""
        if state.pattern is None:
            return
        variables = self.database.variables(pattern=state.pattern)
        self.dropdowns["variable"].menu = self.menu(variables)

        initial_times = self.database.initial_times(
            pattern=state.pattern)
        self.dropdowns["initial_time"].menu = self.menu(initial_times)

    def on_pattern(self, pattern):
        """Select observation/model file pattern"""
        state = State(
            pattern=pattern,
            variable=self.state.variable,
            initial=self.state.initial)
        self.notify(state)
        self.state = state

    def on_variable(self, value):
        state = next_state(self.state, variable=value)
        self.notify(state)
        self.state = state

    @staticmethod
    def menu(values, formatter=str):
        return [(formatter(o), formatter(o)) for o in values]

    @staticmethod
    def hpa(p):
        return "{}hPa".format(int(p))

    @staticmethod
    def first(items):
        try:
            return items[0]
        except IndexError:
            return
