import unittest
import unittest.mock
import control
import database as db


class TestControls(unittest.TestCase):
    def setUp(self):
        self.database = unittest.mock.Mock()
        self.database.pressures.return_value = [1000., 850.]
        self.initial_times = [
            "2019-01-01 00:00:00",
            "2019-01-01 12:00:00",
        ]
        self.database.initial_times.return_value = self.initial_times
        self.controls = control.Controls(self.database)

    def test_on_pattern_emits_state(self):
        key = "k"
        value = "*.nc"
        database = db.Database.connect(":memory:")
        controls = control.Controls(database, patterns=[(key, value)])
        callback = unittest.mock.Mock()
        controls.subscribe(callback)
        controls.on_pattern(value)
        callback.assert_called_once_with(control.State(pattern="*.nc"))

    def test_on_variable_sets_pressure_drop_down(self):
        self.controls.on_variable("air_temperature")
        result = self.controls.dropdowns["pressure"].menu
        expect = [("1000hPa", "1000hPa"), ("850hPa", "850hPa")]
        self.assertEqual(expect, result)

    def test_on_variable_sets_initial_times_drop_down(self):
        self.controls.on_variable("air_temperature")
        result = self.controls.dropdowns["initial_time"].menu
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
        expect = control.State(
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
        expect = control.State(variable=None, initial=self.initial_times[1])
        callback.assert_called_once_with(expect)
