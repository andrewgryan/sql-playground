#!/usr/bin/env python
import sqlite3
import argparse
import netCDF4
import numpy as np
import os


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True)
    parser.add_argument("paths", nargs="+")
    return parser.parse_args(args=argv)


def main():
    args = parse_args()

    # Generate hierarchical data structure from paths
    data = {}
    for path in args.paths:
        file_name = os.path.basename(path)
        with netCDF4.Dataset(path) as dataset:
            data[file_name] = scrape(dataset)

    save(data, args.database)


def scrape(dataset):
    data = {}
    var = dataset.variables['forecast_reference_time']
    datetimes = netCDF4.num2date(var[:], units=var.units)
    reference = np.array(datetimes, dtype='datetime64[s]')
    data['reference'] = str(reference)
    data['variables'] = {}
    for v, obj in dataset.variables.items():
        if hasattr(obj, "um_stash_source"):
            data['variables'][v] = coord_variable(dataset, v, 'time')

    d = {}
    for v, obj in dataset.variables.items():
        if not v.startswith('time'):
            continue
        values = obj[:]
        if values.ndim == 0:
            # We don't know how to deal with this yet
            continue
        d[v] = np.array(
            netCDF4.num2date(values, units=obj.units),
            dtype='datetime64[s]')
    data['time_variables'] = d

    d = {}
    for v, obj in dataset.variables.items():
        if not v.startswith('pressure'):
            continue
        values = obj[:]
        if values.ndim == 0:
            # We don't know how to deal with this yet
            continue
        d[v] = values
    data['pressure_variables'] = d

    return data


def save(data, database):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()

    # Design TABLES
    cursor.execute("CREATE TABLE file (id INTEGER PRIMARY KEY, name TEXT, reference TEXT)")
    cursor.execute("CREATE TABLE variable (id INTEGER PRIMARY KEY, name TEXT, file_id INTEGER, FOREIGN KEY(file_id) REFERENCES file(id))")
    cursor.execute("""
CREATE TABLE time (
    id INTEGER PRIMARY KEY, i INTEGER, value TEXT, UNIQUE(i, value)
)
""")
    cursor.execute("""
CREATE TABLE pressure (
    id INTEGER PRIMARY KEY, i INTEGER, value REAL, UNIQUE(i, value)
)
""")
    cursor.execute("""
CREATE TABLE variable_to_time (
    variable_id INTEGER,
    time_id INTEGER,
    FOREIGN KEY(variable_id) REFERENCES variable(id),
    FOREIGN KEY(time_id) REFERENCES time(id)
)
""")
    cursor.execute("""
CREATE TABLE variable_to_pressure (
    variable_id INTEGER,
    pressure_id INTEGER,
    FOREIGN KEY(variable_id) REFERENCES variable(id),
    FOREIGN KEY(pressure_id) REFERENCES pressure(id)
)
""")

    for file_name, obj in data.items():
        reference = obj['reference']
        cursor.execute(
            "INSERT INTO file (name, reference) VALUES (?,?)",
            (file_name, reference))

        for variable in obj['variables']:
            print(variable, file_name)
            cursor.execute(
                "INSERT INTO variable (name, file_id) VALUES (?,(SELECT id FROM file WHERE name = ?))",
                (variable, file_name))

        for variable, times in obj['time_variables'].items():
            for i, time in enumerate(times):
                value = str(time)
                cursor.execute(
                    "INSERT OR IGNORE INTO time (i, value) VALUES (?,?)", (i, value))
                print(file_name, variable, i, value)
                cursor.execute("""
INSERT INTO variable_to_time (variable_id, time_id) VALUES (
    (SELECT v.id FROM variable AS v JOIN file AS f ON v.file_id = f.id WHERE f.name = ? AND v.name = ?),
    (SELECT id FROM time WHERE i = ? AND value = ?))
                """, (file_name, variable, i, value))

        for variable, values in obj['pressure_variables'].items():
            for i, value in enumerate(values):
                cursor.execute(
                    "INSERT OR IGNORE INTO pressure (i, value) VALUES (?,?)", (i, value))

    connection.commit()
    connection.close()

def load_times(dataset, variable):
    time_name = coord_variable(dataset, variable, 'time')
    var = dataset.variables[time_name]
    datetimes = netCDF4.num2date(var[:], units=var.units)
    return np.array(datetimes, dtype='datetime64[s]')


def coord_variable(dataset, name, coord):
    obj = dataset.variables[name]
    for d in obj.dimensions:
        if not d.startswith(coord):
            continue
        if d in dataset.variables:
            return d
    for c in obj.coordinates.split():
        if not c.startswith(coord):
            continue
        if c in dataset.variables:
            return c


if __name__ == '__main__':
    main()
