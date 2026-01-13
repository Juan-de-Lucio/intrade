<a id="load_adb"></a>
# load_ADB

---

**Description**


`load_ADB` reads an Asian Development Bank (ADB) multi-regional input–output (MRIO) table from an Excel file, performs basic cleaning, infers the main MRIO dimensions (number of countries, sectors, and final-demand components), and converts ADB country codes to ISO3 / ISO3-like codes (including regional aggregates such as RoW, etc.).

It returns a convenient dictionary with the cleaned matrix and basic dimension metadata, ready to be passed to downstream MRIO / value-added decomposition functions.

---

**Usage**

`load_ADB(dire, year, typ="LAC")`

---

**Arguments**

`load_ADB(dire, year, typ="LAC")`

- `dire` : `str` or `pathlib.Path`
  Directory where the ADB Excel files are stored. It should normally include the trailing separator, e.g. `"path/to/ADB/"`.

- `year` : `int`
  Reference year of the ADB MRIO to load. Valid years depend on `typ` and on which ADB files are present in `dire`, for example:
  - `"LAC"`: 2007, 2011, 2017 (Latin American MRIO releases used here).
  - `"CUR-62"`: 2000, 2007, and annual series after 2007 according to file naming conventions.
  - `"CUR-72"`: any year for which an `ADB-MRIO-{year}*.xlsx` file exists in `dire`.

- `typ` : `{"LAC", "CUR-62", "CUR-72"}`, default `"LAC"`
  Variant of the ADB MRIO to load:
  - `"LAC"`: Latin American MRIO, with explicit Latin American region codes (e.g. RoLAC).
  - `"CUR-62"`: “Current” 62-region MRIO (standard ADB release).
  - `"CUR-72"`: “Current” 72-region MRIO (extended ADB release).

---

**Details**

The function executes the following steps:

1. **Select and read the Excel file**
   - For `typ="LAC"` and `typ="CUR-62"`, the file name is built explicitly from `year` (e.g. `"ADB-MRIO-LAC-2017_Mar2022-2.xlsx"`, `"ADB-MRIO62-2018_Dec2022.xlsx"`).
   - For `typ="CUR-72"`, the function searches `dire` using a glob pattern (`"ADB-MRIO-{year}*.xlsx"`) and reads the first match.
   - In all cases, it reads the sheet named `"ADB MRIO {year}"`, skipping the first four header rows and reading a fixed number of rows/columns (`nrows` and `usecols` depend on the variant).

2. **Build country–sector labels**
   - The first two rows of the data area (country and sector headers) are combined into single labels of the form `"COUNTRY_SECTOR"`.
   - The first two columns (row identifiers) are also combined into `"COUNTRY_SECTOR"` row labels.
   - Suffix `"_c"` in ADB labels is removed to obtain cleaner codes.

3. **Clean structure and rename output column**
   - The first two header rows and the first two identifier columns are dropped.
   - The last column is renamed to `"OUT"`, interpreted as total output for each country–sector.

4. **Infer MRIO dimensions**
   - A reference country (hard-coded as `"AUS"`) is used to infer:
     - `S`: number of sectors per country, by counting how many rows belong to a specific country.
     - `SplusFD`: number of columns (intermediate + final demand) associated with a specific country.
     - `FD = SplusFD - S`: number of final-demand components per country.
   - Given the total number of rows, the number of countries is computed as `C = n_rows / S`, and:
     - `CS = C × S`: number of country–sector pairs.
     - `CFD = C × FD`: number of country–final-demand columns.

5. **Convert ADB country codes to ISO3 / ISO-like codes**
   - A fixed mapping from ADB internal codes (e.g. `"SWI"`, `"PRC"`, `"SPA"`) to ISO3 codes (`"CHE"`, `"CHN"`, `"ESP"`) is applied.
   - Some codes correspond to regional aggregates (e.g. `"RoW"`, `"RoLAC"`), which are converted to stable labels (e.g. `"RoW"`, `"RoL"`) and treated as pseudo-ISO3 codes.
   - The mapping is applied to both column and row labels by replacing the leading code in each `"CODE_sector"` string.

6. **Natural sorting and numeric conversion**
   - Columns are rearranged so that:
     - The first `CS` columns correspond to all country–sector intermediate-use blocks.
     - These are followed by all final-demand columns.
     - The final `"OUT"` column is kept as the last column.
   - Within each block, columns are ordered using “natural” sorting, so sector indices follow `1, 2, 3, 10, 11, …` instead of lexicographic order.
   - The same logic is applied to the row dimension, if needed.
   - All entries are converted to numeric using `pandas.to_numeric(..., errors="coerce")`, turning any non-numeric “junk” into `NaN`.

7. **Packaging results**
   - A dictionary is built with the cleaned matrix and the inferred dimensions (`C`, `S`, `FD`, `CS`, `CFD`), which can be directly used by other functions in the library (e.g. MRIO decomposition or value-added export calculations).

---

**Returns**

`dict` with the following keys:

- `"df"` : `pandas.DataFrame`
  Cleaned ADB MRIO table with:
  - Index: country–sector labels (e.g. `"DEU_1"`, `"ESP_15"`), after converting ADB codes to ISO3 / ISO-like codes.
  - Columns ordered as:
    1. All `CS` country–sector intermediate-use columns.
    2. All `CFD` final-demand columns.
    3. One total output column `"OUT"`.

- `"C"` : `int`
  Number of countries/regions in the MRIO table.

- `"S"` : `int`
  Number of sectors per country.

- `"FD"` : `int`
  Number of final-demand components per country.

- `"CS"` : `int`
  Total number of country–sector pairs (`C × S`).

- `"CFD"` : `int`
  Total number of country–final-demand pairs (`C × FD`).

---

**Example**

```python
from intrade import load_ADB

# Directory where the ADB MRIO Excel files are stored
adb_dir = "/path/to/ADB/files/"

# Example 1: Latin-American MRIO (LAC), year 2017
adb_lac_2017 = load_ADB(dire=adb_dir, year=2017, typ="LAC")

df_lac = adb_lac_2017["df"]
C_lac  = adb_lac_2017["C"]
S_lac  = adb_lac_2017["S"]
FD_lac = adb_lac_2017["FD"]

# Example 2: 62-region "current" MRIO (CUR-62), year 2018
adb_cur62_2018 = load_ADB(dire=adb_dir, year=2018, typ="CUR-62")

df_62  = adb_cur62_2018["df"]
C_62   = adb_cur62_2018["C"]
S_62   = adb_cur62_2018["S"]

# The returned df can be passed to downstream routines,
# e.g. to construct a WIO dictionary or perform VA decomposition.
```

---

**Notes**

Implemented with the following with the following original files:

Current 62:

-  'ADB-MRIO-2000_Mar2022-3.xlsx',
-  'ADB-MRIO-2007.xlsx',
-  'ADB-MRIO-2008_Mar2022.xlsx', ... to 'ADB-MRIO-2016_Mar2022.xlsx',
-  'ADB-MRIO62-2017_Dec2022.xlsx', ... to 'ADB-MRIO62-2019_Dec2022.xlsx',
-  'ADB-MRIO62-2020_June2023.xlsx', ... to 'ADB-MRIO62-2022_June2023.xlsx',

Current 72:

-  'ADB-MRIO-2017_Dec2022-2.xlsx',
-  'ADB-MRIO-2018_Dec2022.xlsx',
-  'ADB-MRIO-2019_Dec2022.xlsx',
-  'ADB-MRIO-2020_June2023.xlsx',
-  'ADB-MRIO-2021_June2023.xlsx',
-  'ADB-MRIO-2022_June2023.xlsx',

LAC:

-  'ADB-MRIO-LAC-2007_Mar2022-1.xlsx',
-  'ADB-MRIO-LAC-2011_Mar2022.xlsx',
-  'ADB-MRIO-LAC-2017_Mar2022-2.xlsx',


---