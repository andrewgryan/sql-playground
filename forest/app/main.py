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
    variable_menu = Menu(database.variables())
    pressure_menu = Menu(database.pressures(),
                         formatter=lambda x: "{:.1f} hPa".format(x))
    root = bokeh.layouts.column(
        bokeh.layouts.row(variable_menu.dropdown),
        bokeh.layouts.row(ui.minus, ui.div, ui.plus),
        bokeh.layouts.row(pressure_menu.dropdown)
    )
    document = bokeh.plotting.curdoc()
    document.add_root(root)


class Menu(object):
    def __init__(self, options, formatter=str):
        self.options = options
        self.dropdown = bokeh.models.Dropdown(
            menu=[(formatter(o), formatter(o)) for o in options])
        self.dropdown.on_click(self.on_label)
        self.dropdown.on_click(self.on_click)

    def on_label(self, value):
        for l, v in self.dropdown.menu:
            if v == value:
                self.dropdown.label = l

    def on_click(self, value):
        print(value)


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
