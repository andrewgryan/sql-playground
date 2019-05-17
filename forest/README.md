
# Relational NetCDF Atmospheric data

There should be a relational way to map netCDF4 dimension information to a SQL query. If
we have 1000 files, we could make a single query to generate dropdown menus and other
widgets without having to exhaustively search/cache all of that meta-data in the Cloud

```python
# Python hierarchical structure
{
   'time_variables': {
       'time_0': [
            '2019-05-13T18:00:00',
            ...
        ]
   },
   'pressure_variables': {
       'pressure_1': [
            1000.000001,
            950.00001,
            ...
        ]
   },
   'variables': {
      'relative_humidity': {
        'time_axis': 0,
        'time_variable': 'time_0',
        'pressure_axis': 0,
        'pressure_variable': 'pressure_1'
      }
   }
}
```

In SQL land we can keep track of unique time values and a mapping from variables, this can be achieved
since every (file, variable) has a unique id and every (i, time) pair has a unique id.

```

file
----
id name reference
     
variable
--------
id name time_axis pressure_axis file_id

variable_to_id
--------------
variable_id time_id

time
----
id i value
```

The idea being that a meta-data lookup on S3 takes 200ms per file, if we have 20 files per run and 4 runs per day
after a month we would need to query approx. 2400 files to construct an index or about 50 minutes to catalogue. But on a local machine it may only take a few microseconds to insert a few rows as a new file is available and sync the database with S3
