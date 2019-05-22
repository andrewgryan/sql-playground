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
    print(database.initial_times())


if __name__.startswith('bk'):
    main()
