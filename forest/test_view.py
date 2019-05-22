import unittest
import unittest.mock
import bokeh.models
import bokeh.layouts
from collections import namedtuple


State = namedtuple("State", ("variable", "initial"))


class Observable(object):
    def __init__(self):
        self.subscribers = []

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def notify(self, state):
        for callback in self.subscribers:
            callback(state)


class Controls(Observable):
    def __init__(self, database):
        self.database = database
        self.initial_times = database.initial_times()
        self.state = State(
            initial=self.first(self.initial_times),
            variable=None)
        self.drop_downs = {}
        self.drop_downs["pressure"] = bokeh.models.Dropdown()
        self.drop_downs["initial_time"] = bokeh.models.Dropdown()
        self.layout = bokeh.layouts.row(
            self.drop_downs["pressure"],
            self.drop_downs["initial_time"])
        super().__init__()

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
        except KeyError:
            return


class TestControls(unittest.TestCase):
    def setUp(self):
        self.database = unittest.mock.Mock()
        self.database.pressures.return_value = [1000., 850.]
        self.initial_times = [
            "2019-01-01 00:00:00",
            "2019-01-01 12:00:00",
        ]
        self.database.initial_times.return_value = self.initial_times
        self.controls = Controls(self.database)

    def test_on_variable_sets_pressure_drop_down(self):
        self.controls.on_variable("air_temperature")
        result = self.controls.drop_downs["pressure"].menu
        expect = [("1000hPa", "1000hPa"), ("850hPa", "850hPa")]
        self.assertEqual(expect, result)

    def test_on_variable_sets_initial_times_drop_down(self):
        self.controls.on_variable("air_temperature")
        result = self.controls.drop_downs["initial_time"].menu
        expect = [
            ("2019-01-01 00:00:00", "2019-01-01 00:00:00"),
            ("2019-01-01 12:00:00", "2019-01-01 12:00:00"),
        ]
        self.assertEqual(expect, result)

    def test_observable(self):
        callback = unittest.mock.Mock()
        self.controls.subscribe(callback)
        self.controls.notify((1, 2, 3))
        callback.assert_called_once_with((1, 2, 3))

    def test_on_variable_emits_state(self):
        callback = unittest.mock.Mock()
        self.controls.subscribe(callback)
        self.controls.on_variable("air_temperature")
        expect = State(
            initial=self.controls.state.initial,
            variable="air_temperature")
        callback.assert_called_once_with(expect)

    def test_on_plus_sets_initial_time_to_next_value(self):
        self.controls.on_plus()
        result = self.controls.state.initial
        expect = self.controls.initial_times[1]
        self.assertEqual(expect, result)

    def test_on_plus_emits_state(self):
        callback = unittest.mock.Mock()
        self.controls.subscribe(callback)
        self.controls.on_plus()
        expect = State(variable=None, initial=self.initial_times[1])
        callback.assert_called_once_with(expect)
