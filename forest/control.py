"""Control navigation of FOREST data"""
import bokeh.models
import bokeh.layouts
from collections import namedtuple


State = namedtuple("State", ("pattern", "variable", "initial"))
State.__new__.__defaults__ = (None,) * len(State._fields)


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
            patterns = {}
        self.patterns = patterns
        self.database = database
        self.initial_times = database.initial_times()
        self.state = State(
            initial=self.first(self.initial_times),
            variable=None)
        self.drop_downs = {
            "pattern": bokeh.models.Dropdown(label="Datasets"),
            "pressure": bokeh.models.Dropdown(label="Pressure"),
            "initial_time": bokeh.models.Dropdown(label="Initial time")
        }
        self.layout = bokeh.layouts.column(
            self.drop_downs["pattern"],
            self.drop_downs["pressure"],
            self.drop_downs["initial_time"])
        super().__init__()

    def on_pattern(self, key):
        """Select observation/model file pattern"""
        pattern = self.patterns[key]
        state = State(
            pattern=pattern,
            variable=self.state.variable,
            initial=self.state.initial)
        self.notify(state)
        self.state = state

    def on_plus(self):
        i = self.initial_times.index(self.state.initial)
        initial = self.initial_times[i + 1]
        state = State(
            variable=self.state.variable,
            initial=initial)
        self.notify(state)
        self.state = state

    def on_variable(self, value):
        initial_times = self.database.initial_times(value)
        pressures = self.database.pressures(value)
        self.drop_downs["pressure"].menu = self.menu(pressures, self.hpa)
        self.drop_downs["initial_time"].menu = self.menu(initial_times)

        state = State(variable=value, initial=self.state.initial)
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
