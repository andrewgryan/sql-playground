import unittest
import bokeh
import util


class TestDropdown(unittest.TestCase):
    def test_on_click_sets_label(self):
        dropdown = bokeh.models.Dropdown(menu=[("A", "a")])
        callback = util.autolabel(dropdown)
        callback("a")
        self.assertEqual(dropdown.label, "A")

    def test_autowarn(self):
        dropdown = bokeh.models.Dropdown(
            label="A",
            menu=[("A", "a")])
        callback = util.autowarn(dropdown)
        attr, old, new = "menu", None, [("B", "b")]
        callback(attr, old, new)
        self.assertEqual(dropdown.button_type, "danger")

    def test_find_label_given_menu_and_value(self):
        menu = [("A", "a"), ("B", "b"), ("C", "c")]
        value = "b"
        result = util.find_label(menu, value)
        expect = "B"
        self.assertEqual(expect, result)

    def test_pluck_label_given_menu(self):
        menu = [("A", "a"), ("B", "b"), ("C", "c")]
        result = util.pluck_label(menu)
        expect = ["A", "B", "C"]
        self.assertEqual(expect, result)
