
# Relational NetCDF Atmospheric data

There should be a relational way to map netCDF4 dimension information to a SQL query. If
we have 1000 files, we could make a single query to generate dropdown menus and other
widgets without having to exhaustively search/cache all of that meta-data in the Cloud

```
{
   'variables': {
      'time_0': {
        'values': []
      },
      'relative_humidity': {
        'time_variable': 'time_0'
      }
   }
}
```

In SQL land we can keep track of unique time values and a mapping from variables

```

file
----
id name reference
     
variable
--------
id name file_id

variable_to_id
--------------
variable_id time_id

time
----
id i value
```

The idea being that a meta-data lookup on S3 takes 200ms per file, if we have 20 files per run and 4 runs per day
after a month we would need to query approx. 240 files to construct an index
