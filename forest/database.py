import sqlite3
import iris
import netCDF4


class Database(object):
    """Stores index and paths of forecast diagnostics"""
    def __init__(self, connection):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS file (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    reference TEXT,
                    UNIQUE(name))
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS variable (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    time_axis INTEGER,
                    pressure_axis INTEGER,
                    file_id INTEGER,
                    FOREIGN KEY(file_id) REFERENCES file(id),
                    UNIQUE(name, file_id))
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pressure (
                    id INTEGER PRIMARY KEY,
                    i INTEGER,
                    value REAL,
                    UNIQUE(i, value)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS variable_to_pressure (
                    variable_id INTEGER,
                    pressure_id INTEGER,
                    PRIMARY KEY(variable_id, pressure_id))
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS time (
                    id INTEGER PRIMARY KEY,
                    i INTEGER,
                    value TEXT,
                    UNIQUE(i, value))
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS variable_to_time (
                    variable_id INTEGER,
                    time_id INTEGER,
                    PRIMARY KEY(variable_id, time_id))
        """)

    @classmethod
    def connect(cls, path):
        """Create database instance from location on disk or :memory:"""
        return cls(sqlite3.connect(path))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.connection.commit()
        self.connection.close()

    def insert_netcdf(self, path):
        """Coordinate and meta-data information taken from NetCDF file"""
        with netCDF4.Dataset(path) as dataset:
            try:
                obj = dataset.variables["forecast_reference_time"]
                reference_time = netCDF4.num2date(obj[:], units=obj.units)
            except KeyError:
                reference_time = None

        self.insert_file_name(path, reference_time=reference_time)

        cubes = iris.load(path)
        for cube in cubes:
            variable = cube.var_name
            time_axis = self._axis(cube, 'time')
            pressure_axis = self._axis(cube, 'pressure')
            self.insert_variable(
                path,
                variable,
                time_axis=time_axis,
                pressure_axis=pressure_axis)
            try:
                times = [cell.point for cell in cube.coord('time').cells()]
                self.insert_times(path, variable, times)
            except iris.exceptions.CoordinateNotFoundError:
                pass
            try:
                pressures = [cell.point for cell in cube.coord('pressure').cells()]
                self.insert_pressures(path, variable, pressures)
            except iris.exceptions.CoordinateNotFoundError:
                pass

    @staticmethod
    def _axis(cube, coord):
        try:
            dims = cube.coord_dims(coord)
            if len(dims) == 0:
                return None
            else:
                return dims[0]
        except iris.exceptions.CoordinateNotFoundError:
            return None

    def initial_times(self, pattern=None):
        """Distinct initialisation times"""
        if pattern is None:
            query = """
                SELECT DISTINCT reference
                  FROM file
                 ORDER BY reference;
            """
        else:
            query = """
                SELECT DISTINCT reference
                  FROM file
                 WHERE name GLOB :pattern
                 ORDER BY reference;
            """
        self.cursor.execute(query, dict(pattern=pattern))
        rows = self.cursor.fetchall()
        return [r for r, in rows]

    def files(self, pattern=None):
        """File names"""
        if pattern is None:
            query = """
                SELECT name
                  FROM file
                 ORDER BY name;
            """
        else:
            query = """
                SELECT name
                  FROM file
                 WHERE name GLOB :pattern
                 ORDER BY name;
            """
        self.cursor.execute(query, dict(pattern=pattern))
        rows = self.cursor.fetchall()
        return [r for r, in rows]

    def variables(self):
        query = """
            SELECT DISTINCT name
              FROM variable
             ORDER BY name;
        """
        self.cursor.execute(query, dict())
        rows = self.cursor.fetchall()
        return [r for r, in rows]

    def path_points(self, variable, initial, valid, pressure):
        """Criteria needed to load diagnostics"""
        pts = None
        self.cursor.execute("""
            SELECT file.name, time.i, pressure.i, v.time_axis, v.pressure_axis
              FROM file
              JOIN variable AS v
                ON file.id = v.file_id
              JOIN variable_to_time AS vt
                ON vt.variable_id = v.id
              JOIN time
                ON vt.time_id = time.id
              JOIN variable_to_pressure AS vp
                ON vp.variable_id = v.id
              JOIN pressure
                ON vp.pressure_id = pressure.id
             WHERE file.reference = :initial
               AND v.name = :variable
               AND time.value = :valid
             ORDER BY ABS(pressure.value - :pressure)
        """, dict(
            initial=initial,
            valid=valid,
            variable=variable,
            pressure=pressure))
        rows = self.cursor.fetchall()
        path, ti, pi, ta, pa = rows[0]
        # Consider unit testing the logic below separately
        if ta == pa:
            pts = (ti,)
        else:
            pts = (ti, pi)
        return path, pts

    def insert_file_name(self, path, reference_time=None):
        self.cursor.execute("""
            INSERT OR IGNORE INTO file (name, reference)
            VALUES (:path, :reference)
        """, dict(path=path, reference=reference_time))

    def insert_variable(
            self,
            path,
            variable,
            time_axis=None,
            pressure_axis=None):
        self.insert_file_name(path)
        self.cursor.execute("""
            INSERT OR IGNORE
                        INTO variable (name, time_axis, pressure_axis, file_id)
                      VALUES (
                             :variable,
                             :time_axis,
                             :pressure_axis,
                             (SELECT id FROM file WHERE name=:path))
        """, dict(
            path=path,
            variable=variable,
            time_axis=time_axis,
            pressure_axis=pressure_axis))

    def insert_pressures(self, path, variable, values):
        """Helper method to insert a coordinate related to a variable"""
        for i, value in enumerate(values):
            self.insert_pressure(path, variable, value, i)

    def insert_pressure(self, path, variable, pressure, i):
        self.insert_variable(path, variable)
        self.cursor.execute("""
            INSERT OR IGNORE INTO pressure (i, value) VALUES (:i,:pressure)
        """, dict(i=i, pressure=pressure))
        self.cursor.execute("""
            INSERT OR IGNORE INTO variable_to_pressure (variable_id, pressure_id)
            VALUES(
                (SELECT variable.id FROM variable
                   JOIN file ON variable.file_id = file.id
                  WHERE file.name = :path AND variable.name=:variable),
                (SELECT id FROM pressure WHERE value=:pressure AND i=:i))
        """, dict(path=path, variable=variable, pressure=pressure, i=i))

    def valid_times(self, variable=None, pattern=None):
        """Valid times associated with search criteria"""
        if (variable is not None) and (pattern is not None):
            query = """
                SELECT value
                  FROM time
                  JOIN variable_to_time AS vt
                    ON vt.time_id = time.id
                  JOIN variable AS v
                    ON vt.variable_id = v.id
                  JOIN file
                    ON v.file_id = file.id
                 WHERE file.name GLOB :pattern
                   AND v.name = :variable
            """
        elif variable is not None:
            query = """
                SELECT value
                  FROM time
                  JOIN variable_to_time AS vt
                    ON vt.time_id = time.id
                  JOIN variable AS v
                    ON vt.variable_id = v.id
                 WHERE v.name = :variable
            """
        elif pattern is not None:
            query = """
                SELECT value
                  FROM time
                  JOIN variable_to_time AS vt
                    ON vt.time_id = time.id
                  JOIN variable AS v
                    ON vt.variable_id = v.id
                  JOIN file
                    ON v.file_id = file.id
                 WHERE file.name GLOB :pattern
            """
        else:
            query = """
                SELECT value
                  FROM time
            """
        self.cursor.execute(query, dict(
            variable=variable,
            pattern=pattern))
        rows = self.cursor.fetchall()
        return [time for time, in rows]


    def fetch_times(self, path, variable):
        """Helper method to find times related to a variable"""
        self.cursor.execute("""
            SELECT value FROM time
        """)
        return [time for time, in self.cursor.fetchall()]

    def insert_times(self, path, variable, times):
        """Helper method to insert a time coordinate related to a variable"""
        for i, time in enumerate(times):
            self.insert_time(path, variable, time, i)

    def insert_time(self, path, variable, time, i):
        self.insert_variable(path, variable)
        self.cursor.execute("""
            INSERT OR IGNORE INTO time (i, value) VALUES (:i,:value)
        """, dict(i=i, value=time))
        self.cursor.execute("""
            INSERT OR IGNORE INTO variable_to_time (variable_id, time_id)
            VALUES(
                (SELECT variable.id FROM variable
                   JOIN file ON variable.file_id = file.id
                  WHERE file.name=:path AND variable.name=:variable),
                (SELECT id FROM time WHERE value=:value AND i=:i))
        """, dict(path=path, variable=variable, value=time, i=i))

    def find_time(self, variable, time):
        self.cursor.execute("""
            SELECT file.name, time.i FROM file
              JOIN variable ON file.id = variable.file_id
              JOIN variable_to_time AS junction ON variable.id = junction.variable_id
              JOIN time ON time.id = junction.time_id
             WHERE variable.name = :variable AND time.value = :time
        """, dict(variable=variable, time=time))
        return self.cursor.fetchall()

    def find_pressure(self, variable, pressure):
        return self.find(variable, pressure)

    def find(self, variable, pressure):
        self.cursor.execute("""
            SELECT file.name, pressure.i FROM file
              JOIN variable ON file.id = variable.file_id
              JOIN variable_to_pressure AS junction ON variable.id = junction.variable_id
              JOIN pressure ON pressure.id = junction.pressure_id
            WHERE variable.name = :variable AND pressure.value = :pressure
        """, dict(variable=variable, pressure=pressure))
        return self.cursor.fetchall()

    def file_names(self):
        self.cursor.execute("SELECT name FROM file")
        return [row[0] for row in self.cursor.fetchall()]

    def fetch_dates(self, pattern=None):
        self.cursor.execute("""
            SELECT DISTINCT value FROM time
        """)
        rows = self.cursor.fetchall()
        return [row[0] for row in rows]
