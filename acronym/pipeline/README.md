# Pipeline

## 1. Fetch CORDIS data

Fetches CORDIS project and organization data, including individual project XML files (optional). Project and organization csvs are reformatted to conventional csv format, made pandas friendly and formatting errors are removed.

```bash
python acronym/pipeline/cordis/fetch_cordis.py
```

To skip downloading the individual XML files (which are larger than the csv files), pass the `--no-xml` flag.

The outputs are saved to `inputs/data/cordis/{framework programme}/`.
