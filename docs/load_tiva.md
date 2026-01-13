<a id="load_tiva"></a>
# load_TIVA

---

**Description**

`load_TIVA` reads an OECD Inter-Country Input–Output (ICIO) / TiVA table from a compressed CSV file (inside a zip archive), performs basic checks and cleaning, reconstructs the `"OUT"` (total output) column if necessary, and infers the main ICIO dimensions (number of countries, sectors and final-demand components).

For **extended** ICIO releases, it also merges split entries for Mexico and China (`MX1 + MX2 → MEX`, `CN1 + CN2 → CHN`) both in rows and columns, so each country is represented by a single ISO3-like code.

---

**Usage**

`load_TIVA(dire, year, typ="extended")`

---

**Arguments**

`load_TIVA(dire, year, typ="extended")`

- `dire` : `str` or `pathlib.Path`
  Directory where the ICIO zip files are stored. It should normally include the trailing separator, e.g. `"path/to/ICIO/raw/"`.

- `year` : `int`
  Reference year of the ICIO/TiVA data to load. The function automatically selects the appropriate zip archive that contains this year, based on the OECD file naming convention (e.g. `ICIO-2016-2020-extended.zip`).

- `typ` : `{"small", "extended"}`, default `"extended"`
  Layout/type of the ICIO table:
  - `"small"`: “small” ICIO layout (fewer regions/sectors or more aggregated structure).
  - `"extended"`: “extended” ICIO layout (more regions/sectors, split entries for MEX/CHN, etc.).

---

**Details**

The function proceeds in several steps:

1. **Select the ICIO zip archive**
   ICIO releases are grouped into 5-year zip archives. Given `year` and `typ`, the function determines which file to use:
   - `ICIO-1995-2000-{typ}.zip`
   - `ICIO-2001-2005-{typ}.zip`
   - `ICIO-2006-2010-{typ}.zip`
   - `ICIO-2011-2015-{typ}.zip`
   - `ICIO-2016-2020-{typ}.zip`

2. **Read the CSV from inside the zip**
   The zip file is opened with `zipfile.ZipFile` and the appropriate CSV is read with `pandas.read_csv`:
   - For `typ="small"`: the file is named `{year}_SML.csv`.
   - For `typ="extended"`: the file is named `{year}.CSV`.
   The first column is used as index (`index_col=0`), and the index name is reset (`df.index.name = None`) to avoid issues in later operations.

3. **Check and reconstruct the `"OUT"` column**
   Some ICIO releases do not contain a valid `"OUT"` column. The function:
   - Compares the sum of all elements with the value of the last column’s first element.
   - If the test suggests that `"OUT"` is missing or incorrect, the function creates/overwrites `"OUT"` as the **row sum** across all columns: `df["OUT"] = df.sum()`

4. **Infer sectors (S) and final-demand components (FD)**
   Using a reference country (`ref = "USA"`), the function infers:
   - `S`: number of sectors per country, as:
     ```python
     S = int(df.T.filter(like="USA").shape[1])
     ```
   - `SplusFD`: total number of columns (sectors + final demand) corresponding to `"USA"`:
     ```python
     SplusFD = int(df.filter(like="USA").shape[1])
     ```
   - `FD = SplusFD - S`: number of final-demand columns per country.

5. **Collapse split entries for MEX and CHN (extended layout)**
   For `typ="extended"`, the ICIO table splits Mexico and China into `MX1`/`MX2` and `CN1`/`CN2`. The nested helper function: `def mex_chn(df, MEX, MX1, MX2)`: Takes a DataFrame (df) and three codes (e.g. "MEX", "MX1", "MX2"). Sums the blocks corresponding to MEX, MX1 and MX2 over the sectoral columns. Replaces the main country’s block (MEX) with that sum. Drops all columns containing MX1 and MX2.
This is applied:

First to columns (destinations): MEX, then CHN.

Then to the transposed DataFrame (rows/origins): again MEX and CHN.
Finally, the table is transposed back to its original orientation.

Compute number of countries and related dimensions
The ICIO layout typically contains a few “extra” rows beyond country–sector rows, for example:

- TLS (total intermediate use),
- VA (value added),
- OUT (total output).

The code assumes filas_adic = 3 such additional rows. Then:

- C = (number_of_rows - filas_adic) / S: number of countries.
- CS = C × S: total number of country–sector combinations.
- CFD = C × FD: total number of country–final-demand combinations.

---

**Returns**

The function returns a dictionary with:
- The full cleaned ICIO table (df), including extra rows such as TLS, VA, OUT.
- The inferred dimensions (C, S, FD, CS, CFD), which are required for subsequent MRIO/ICIO operations (e.g. decomposition into value-added components).


dict with the following keys:

- "df" : pandas.DataFrame
  ICIO matrix with:
  - Rows: country–sector rows plus additional rows such as TLS, VA, and OUT.
  - Columns: all country–sector intermediate-use blocks, final-demand columns, and (if present or reconstructed) an "OUT" column for total output.
- "C" : int
Number of countries in the ICIO.
- "S" : int
Number of sectors per country.
- "FD" : int
Number of final-demand components per country.
- "CS" : int
Total number of country–sector combinations (C × S).
- "CFD" : int
Total number of country–final-demand combinations (C × FD).

---

**Example**

```python

from intrade import load_TIVA

# Directory where ICIO zip files are stored
icio_dir = "/path/to/ICIO/raw/"

# Example 1: Extended ICIO layout, year 2015
tiva_ext_2015 = load_TIVA(dire=icio_dir, year=2015, typ="extended")

df_ext  = tiva_ext_2015["df"]
C_ext   = tiva_ext_2015["C"]
S_ext   = tiva_ext_2015["S"]
FD_ext  = tiva_ext_2015["FD"]

# Example 2: Small ICIO layout, year 2018
tiva_small_2018 = load_TIVA(dire=icio_dir, year=2018, typ="small")

df_sml  = tiva_small_2018["df"]
C_sml   = tiva_small_2018["C"]
S_sml   = tiva_small_2018["S"]

# The returned df can be passed to downstream routines,
# e.g. to build a WIO structure or perform value-added decompositions.

```


---

**Notes**

Two types of tables are provided: small and extended.
The small tables are distributed as ICIO-PERIOD-small.zip, and the extended tables as ICIO-PERIOD-extended.zip, where PERIOD refers to the five-year intervals 1995–2000, 2001–2005, 2006–2010, 2011–2015, and 2016–2020.

Within each small archive, annual files are provided as 1995_SML.csv through 2020_SML.csv.
Within each extended archive, the corresponding annual files are named 1995.csv through 2020.csv.


---