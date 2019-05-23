import unittest
import bokeh
import util


class TestDropdown(unittest.TestCase):
    def test_on_click_sets_label(self):
        dropdown = bokeh.models.Dropdown(menu=[("A", "a")])
        callback = util.autolabel(dropdown)
        callback("a")
        self.assertEqual(dropdown.label, "A")
