import unittest
import unittest.mock
import datetime as dt
import control
import database as db


class TestControls(unittest.TestCase):
    def setUp(self):
        self.database = db.Database.connect(":memory:")
        self.controls = control.Controls(self.database)

    def tearDown(self):
        self.database.close()

    def test_on_click_emits_state(self):
        key = "k"
        value = "*.nc"
        controls = control.Controls(self.database, patterns=[(key, value)])
        callback = unittest.mock.Mock()
        controls.subscribe(callback)
        controls.on_click('pattern')(value)
        callback.assert_called_once_with(control.State(pattern=value))

    def test_on_variable_emits_state(self):
        value = "token"
        callback = unittest.mock.Mock()
        self.controls.subscribe(callback)
        self.controls.on_click("variable")(value)
        callback.assert_called_once_with(control.State(variable=value))

    @unittest.skip("refactoring test suite")
    def test_render_sets_pressure_drop_down(self):
        self.controls.render(control.State(variable="air_temperature"))
        result = self.controls.dropdowns["pressure"].menu
        expect = [("1000hPa", "1000hPa"), ("850hPa", "850hPa")]
        self.assertEqual(expect, result)

    @unittest.skip("refactoring test suite")
    def test_on_variable_sets_initial_times_drop_down(self):
        self.controls.on_variable("air_temperature")
        result = self.controls.dropdowns["initial_time"].menu
        expect = [
            ("2019-01-01 00:00:00", "2019-01-01 00:00:00"),
            ("2019-01-01 12:00:00", "2019-01-01 12:00:00"),
        ]
        self.assertEqual(expect, result)

    def test_next_state_given_kwargs(self):
        current = control.State(pattern="p")
        result = control.next_state(current, variable="v")
        expect = control.State(pattern="p", variable="v")
        self.assertEqual(expect, result)

    def test_observable(self):
        state = control.State()
        callback = unittest.mock.Mock()
        self.controls.subscribe(callback)
        self.controls.notify(state)
        callback.assert_called_once_with(state)

    def test_render_state_configures_variable_menu(self):
        self.database.insert_variable("a.nc", "air_temperature")
        self.database.insert_variable("b.nc", "mslp")
        controls = control.Controls(self.database)
        state = control.State(pattern="b.nc")
        controls.render(state)
        result = controls.dropdowns["variable"].menu
        expect = [("mslp", "mslp")]
        self.assertEqual(expect, result)

    def test_render_state_configures_initial_time_menu(self):
        for path, time in [
                ("a_0.nc", dt.datetime(2019, 1, 1)),
                ("a_3.nc", dt.datetime(2019, 1, 1, 12))]:
            self.database.insert_file_name(path, time)
        state = control.State(pattern="a_?.nc")
        self.controls.render(state)
        menu = self.controls.dropdowns["initial_time"].menu
        result = [label for label, _ in menu]
        expect = ["2019-01-01 00:00:00", "2019-01-01 12:00:00"]
        self.assertEqual(expect, result)

    def test_render_given_initial_time_populates_valid_time_menu(self):
        initial = dt.datetime(2019, 1, 1)
        valid = dt.datetime(2019, 1, 1, 3)
        self.database.insert_file_name("file.nc", initial)
        self.database.insert_time("file.nc", "variable", valid, 0)
        state = control.State(initial_time="2019-01-01 00:00:00")
        self.controls.render(state)
        result = [l for l, _ in self.controls.dropdowns["valid_time"].menu]
        expect = ["2019-01-01 03:00:00"]
        self.assertEqual(expect, result)
