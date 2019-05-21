#!/usr/bin/env python3
import argparse
import database as db
import iris
import netCDF4


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database", required=True,
        help="database file to write/extend")
    parser.add_argument(
        "paths", nargs="+", metavar="FILE",
        help="unified model netcdf files")
    return parser.parse_args(args=argv)


def main(argv=None):
    args = parse_args(argv=argv)
    with db.Database.connect(args.database) as database:
        for path in args.paths:
            print("reading: {}".format(path))
            with netCDF4.Dataset(path) as dataset:
                try:
                    obj = dataset.variables["forecast_reference_time"]
                    reference_time = netCDF4.num2date(obj[:], units=obj.units)
                except KeyError:
                    reference_time = None

            database.insert_file_name(path, reference_time=reference_time)

            cubes = iris.load(path)
            for cube in cubes:
                variable = cube.var_name
                database.insert_variable(path, variable)
                try:
                    times = [cell.point for cell in cube.coord('time').cells()]
                    database.insert_times(path, variable, times)
                except iris.exceptions.CoordinateNotFoundError:
                    pass
                try:
                    pressures = [cell.point for cell in cube.coord('pressure').cells()]
                    database.insert_pressures(path, variable, pressures)
                except iris.exceptions.CoordinateNotFoundError:
                    pass


if __name__ == '__main__':
    main()
