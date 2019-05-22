import bokeh.plotting
import argparse
import database as db


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database",
        required=True,
        help="SQL database to optimise menu system")
    return parser.parse_args()


def main():
    args = parse_args()
    database = db.Database.connect(args.database)
    initial_times = database.initial_times()
    initial_times = [t for t in initial_times if t is not None]

    ui = UI(initial_times, date=initial_times[0])

    pressure_menu = Menu(database.pressures(),
                         formatter=lambda x: "{:.1f} hPa".format(x))
    variable_menu = Menu(database.variables())
    variable_menu.on_click(on_variable(database, pressure_menu))
    root = bokeh.layouts.column(
        bokeh.layouts.row(variable_menu.dropdown),
        bokeh.layouts.row(ui.minus, ui.div, ui.plus),
        bokeh.layouts.row(pressure_menu.dropdown)
    )
    document = bokeh.plotting.curdoc()
    document.add_root(root)


def on_variable(database, pressure_menu):
    def callback(value):
        pressures = database.pressures(variable=value)
        pressure_menu.options = pressures
    return callback


class Menu(object):
    def __init__(self, options, formatter=str):
        self.dropdown = bokeh.models.Dropdown()
        self.dropdown.on_click(self.on_label)
        self.formatter = formatter
        self.options = options

    @property
    def options(self):
        return getattr(self, "_options", [])

    @options.setter
    def options(self, values):
        self._options = values
        self.dropdown.menu = [
            (self.formatter(o), self.formatter(o)) for o in self._options]

    def on_label(self, value):
        for l, v in self.dropdown.menu:
            if v == value:
                self.dropdown.label = l

    def on_click(self, callback):
        self.dropdown.on_click(callback)


class UI(object):
    def __init__(self, dates, date=None):
        self.dates = dates

        self.div = bokeh.models.Div()
        self.plus = bokeh.models.Button(
            label="+")
        self.plus.on_click(self.on_plus)
        self.minus = bokeh.models.Button(
            label="-")
        self.minus.on_click(self.on_minus)

        self.date = date

    @property
    def date(self):
        return getattr(self, "_date", None)

    @date.setter
    def date(self, value):
        self._date = value
        self.render()

    def on_plus(self):
        i = self.dates.index(self.date)
        self.date = self.dates[i + 1]
        self.render()

    def on_minus(self):
        i = self.dates.index(self.date)
        self.date = self.dates[i - 1]

    def on_frequency(self):
        pass

    def render(self):
        self.div.text = str(self.date)


if __name__.startswith('bk'):
    main()
