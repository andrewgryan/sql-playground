import unittest
import datetime as dt
import sqlite3
import database as db


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.cursor = self.connection.cursor()
        self.database = db.Database(self.connection)
        self.path = "file.nc"
        self.variable = "temperature"

    def tearDown(self):
        self.connection.commit()
        self.connection.close()

    def test_database_opened_twice_on_same_connection(self):
        """Should create table if not exists"""
        db.Database(self.connection)
        db.Database(self.connection)

    def test_file_names_given_no_files_returns_empty_list(self):
        result = self.database.file_names()
        expect = []
        self.assertEqual(result, expect)

    def test_file_names_given_file(self):
        self.database.insert_file_name("file.nc")
        result = self.database.file_names()
        expect = ["file.nc"]
        self.assertEqual(result, expect)

    def test_insert_file_name_unique_constraint(self):
        self.database.insert_file_name("a.nc")
        self.database.insert_file_name("a.nc")
        result = self.database.file_names()
        expect = ["a.nc"]
        self.assertEqual(expect, result)

    def test_insert_variable(self):
        self.database.insert_variable(self.path, self.variable)
        self.cursor.execute("""
            SELECT file.name, variable.name FROM file
              JOIN variable ON file.id = variable.file_id
        """)
        result = self.cursor.fetchall()
        expect = [("file.nc", "temperature")]
        self.assertEqual(expect, result)

    def test_insert_variable_unique_constraint(self):
        self.database.insert_variable(self.path, self.variable)
        self.database.insert_variable(self.path, self.variable)
        self.cursor.execute("SELECT * FROM variable")
        result = self.cursor.fetchall()
        expect = [(1, self.variable, 1)]
        self.assertEqual(expect, result)

    def test_insert_time_unique_constraint(self):
        time = dt.datetime(2019, 1, 1)
        i = 0
        self.database.insert_time(self.path, self.variable, time, i)
        self.database.insert_time(self.path, self.variable, time, i)
        self.cursor.execute("SELECT id, i, value FROM time")
        result = self.cursor.fetchall()
        expect = [(1, i, str(time))]
        self.assertEqual(expect, result)

    def test_insert_pressure_unique_constraint(self):
        pressure = 1000.001
        i = 0
        self.database.insert_pressure(self.path, self.variable, pressure, i)
        self.database.insert_pressure(self.path, self.variable, pressure, i)
        self.cursor.execute("SELECT id, i, value FROM pressure")
        result = self.cursor.fetchall()
        expect = [(1, i, pressure)]
        self.assertEqual(expect, result)

    def test_insert_pressure(self):
        path = "some.nc"
        variable = "relative_humidity"
        i = 18
        pressure = 1000.00001
        self.database.insert_pressure(path, variable, pressure, i)
        result = self.database.find(variable, pressure)
        expect = [("some.nc", i)]
        self.assertEqual(expect, result)

    def test_insert_time_distinguishes_paths(self):
        self.database.insert_time("a.nc", self.variable, "2018-01-01T00:00:00", 6)
        self.database.insert_time("b.nc", self.variable, "2018-01-01T01:00:00", 7)
        result = self.database.find_time(self.variable, "2018-01-01T01:00:00")
        expect = [("b.nc", 7)]
        self.assertEqual(expect, result)

    def test_insert_pressure_distinguishes_paths(self):
        pressure = [1000.0001, 950.0001]
        index = [5, 14]
        path = ["a.nc", "b.nc"]
        self.database.insert_pressure(path[0], self.variable, pressure[0], index[0])
        self.database.insert_pressure(path[1], self.variable, pressure[1], index[1])
        result = self.database.find_pressure(self.variable, pressure[1])
        expect = [(path[1], index[1])]
        self.assertEqual(expect, result)

    def test_insert_times(self):
        path = "file.nc"
        variable = "mslp"
        times = [dt.datetime(2019, 1, 1, 12), dt.datetime(2019, 1, 1, 13)]
        self.database.insert_times(path, variable, times)
        result = self.database.fetch_times(path, variable)
        expect = ["2019-01-01 12:00:00", "2019-01-01 13:00:00"]
        self.assertEqual(expect, result)

    def test_find_all_available_dates(self):
        self.cursor.executemany("""
            INSERT INTO time (i, value) VALUES(:i, :value)
        """, [
            dict(i=0, value="2018-01-01T00:00:00"),
            dict(i=1, value="2018-01-01T01:00:00"),
        ])
        result = self.database.fetch_dates(pattern="a*.nc")
        expect = ["2018-01-01T00:00:00", "2018-01-01T01:00:00"]
        self.assertEqual(expect, result)

    def test_insert_reference_time(self):
        reference_time = dt.datetime(2019, 1, 1, 12)
        self.database.insert_file_name(self.path, reference_time=reference_time)

        self.cursor.execute("SELECT reference FROM file")
        result = self.cursor.fetchall()
        expect = [(str(reference_time),)]
        self.assertEqual(expect, result)

    def test_variable_to_pressure_junction_table_should_be_unique(self):
        pressure = 1000.001
        i = 5

        self.database.insert_pressure(self.path, self.variable, pressure, i)
        self.database.insert_pressure(self.path, self.variable, pressure, i)

        self.cursor.execute("SELECT variable_id,pressure_id FROM variable_to_pressure")
        result = self.cursor.fetchall()
        expect = [(1, 1)]
        self.assertEqual(expect, result)

    def test_variable_to_time_junction_table_should_be_unique(self):
        time = dt.datetime(2019, 1, 1)
        i = 5

        self.database.insert_time(self.path, self.variable, time, i)
        self.database.insert_time(self.path, self.variable, time, i)

        self.cursor.execute("SELECT variable_id,time_id FROM variable_to_time")
        result = self.cursor.fetchall()
        expect = [(1, 1)]
        self.assertEqual(expect, result)


    class DatabaseQueries(unittest.TestCase):
        def test_find_all_variables(self):
            connection = sqlite3.connect(':memory:')
            cursor = connection.cursor()
            cursor.execute("SELECT DISTINCT name FROM variable")
            result = cursor.fetchall()
            expect = []
            self.assertEqual(expect, result)
