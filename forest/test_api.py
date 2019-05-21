import unittest
import os
import netCDF4
import datetime as dt
import database as db


def to_datetime(texts, pattern="%Y-%m-%d %H:%M"):
    """Recursively convert lists of strings to list of datetimes"""
    if isinstance(texts, str):
        return dt.datetime.strptime(texts, pattern)
    else:
        return [to_datetime(text, pattern) for text in texts]


class TestToDatetime(unittest.TestCase):
    def test_to_datetime_given_list_of_lists(self):
        texts = [
            ["2019-01-01 12:00", "2019-01-01 13:00"],
            ["2019-01-01 14:00"]
        ]
        result = to_datetime(texts)
        expect = [
            [dt.datetime(2019, 1, 1, 12), dt.datetime(2019, 1, 1, 13)],
            [dt.datetime(2019, 1, 1, 14)]
        ]
        self.assertEqual(expect, result)


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.units = "hours since 1970-01-01 00:00:00"
        self.paths = [
            "test-api-0.nc",
            "test-api-1.nc",
            "test-api-2.nc"]

    def tearDown(self):
        for path in self.paths:
            if os.path.exists(path):
                os.remove(path)

    def test_path_points_related_to_dim0_format(self):
        variable = "air_temperature"
        pressure = 950.
        reference_times = to_datetime([
            "2019-01-01 12:00",
            "2019-01-01 12:00",
            "2019-01-01 12:00"])
        valid_times = to_datetime([
            ["2019-01-01 12:00", "2019-01-01 13:00"],
            ["2019-01-01 14:00"],
            ["2019-01-01 15:00", "2019-01-01 16:00"]
        ])
        pressures = [
            [pressure, pressure],
            [pressure],
            [pressure, pressure]
        ]
        for i, path in enumerate(self.paths):
            with netCDF4.Dataset(path, "w") as dataset:
                dataset.createDimension(
                    "dim0", len(valid_times[i]))
                obj = dataset.createVariable(
                    "time", "d", ("dim0",))
                obj.units = self.units
                obj[:] = netCDF4.date2num(valid_times[i], self.units)
                obj = dataset.createVariable(
                    "pressure", "d", ("dim0",))
                obj[:] = pressures[i]
                obj = dataset.createVariable(
                    "forecast_reference_time", "d", ())
                obj.units = self.units
                obj[:] = netCDF4.date2num(reference_times[i], self.units)
                obj = dataset.createVariable(
                    variable, "f", ("dim0",))
                obj.um_stash_source = "m01s16i203"
                obj.coordinates = "pressure time"

        database = db.Database.connect(':memory:')
        for path in self.paths:
            database.insert_netcdf(path)

        # System under test
        initial = to_datetime("2019-01-01 12:00")
        valid = to_datetime("2019-01-01 16:00")
        r_path, r_pts = database.path_points(variable, initial, valid, pressure)

        # Assertions
        e_path = self.paths[2]
        self.assertEqual(e_path, r_path)
        e_pts = (1,)
        self.assertEqual(e_pts, r_pts)
