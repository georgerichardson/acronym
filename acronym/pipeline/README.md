# Pipeline

## 1. Fetch CORDIS data

Fetches CORDIS project and organization data, including individual project XML files (optional). Project and organization csvs are reformatted to conventional csv format, made pandas friendly and formatting errors are removed.

```bash
python acronym/pipeline/cordis/fetch_cordis.py
```

To skip downloading the individual XML files (which are larger than the csv files), pass the `--no-xml` flag.

The main outputs for the pipeline are `organization.csv` and `project.csv` for each framwork programme and are saved to `inputs/data/cordis/{framework programme}/`. Individual XML projects are saved to a `xml_projects/` subdirectory. For some framework programmes, there are additional project metadata files.

## 2. Extract acronyms (acronymity)

Finds the best match between each project's acronym and title. The algorithm attempts to find the letters from the title that match those of the acronym and are in the same order. Characters are searched up to the nth order, where n is the number of first characters to search of each term in the title. Once a match has been found, the Levenshtein distance between the original acronym and the matched title acronym is calculated. The number of title terms and the number of title terms used to in the attempt to reconstruct the acronym are also generated. This gives an overal picture of a project's 'acronymity'.

```bash
python acronym/pipeline/cordis/acronym_match.py
```

The acronymity results for CORDIS are saved to `outputs/data/cordis/{framework_programme}/acronymity.csv`. The fields in each file are:

- `acronym`: The original acronym.
- `{order}_match`: The closest match within the title.
- `{order}_dist`: The Levenshtein distance between the `acronym` and `{order}_match`.
- `{order}_n_terms_used`: The number of terms in the title used to construct `{order}_match`.
- `n_title_terms`: The number of title terms available to search for a match.
