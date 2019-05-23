import bokeh.plotting
import argparse
import control
import database as db


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database",
        required=True,
        help="SQL database to optimise menu system")
    parser.add_argument(
        "--config-file",
        required=True, metavar="YAML_FILE",
        help="YAML file to configure application")
    return parser.parse_args(args=argv)


def main():
    args = parse_args()
    database = db.Database.connect(args.database)
    controls = control.Controls(database)
    document = bokeh.plotting.curdoc()
    document.add_root(controls.layout)


if __name__.startswith('bk'):
    main()
