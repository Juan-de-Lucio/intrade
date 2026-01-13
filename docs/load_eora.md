<a id="load_eora"></a>
# load_EORA

---


**Description**

`load_EORA` reads an Eora26 multi-regional input–output (MRIO) table for a given year and price concept (basic prices or purchaser prices), combines the **intermediate transactions matrix** (`T`) with the **final demand matrix** (`FD`), and infers the basic MRIO dimensions: number of countries, sectors, and final-demand components.

Country codes in Eora26 are already in ISO3 format (plus some aggregate regions such as `ROW`). These are combined with sector labels to form keys like `"USA_Agriculture"`, which are used as row and column labels in the returned DataFrame.

---

**Usage**

`load_EORA(dire, year, typ="pp")`

---

**Arguments**

`load_EORA(dire, year, typ="pp")`

- `dire` : `str` or `pathlib.Path`
  Directory where the Eora26 zip files are stored. It should normally include the trailing separator, e.g. `"path/to/EORA/raw/"`.

- `year` : `int`
  Reference year of the Eora26 MRIO to load (typically between 1990 and 2016, depending on data availability).

- `typ` : `{"bp", "pp"}`, default `"pp"`
  Price concept of the Eora26 MRIO:
  - `"bp"`: basic prices.
  - `"pp"`: purchaser prices.

---

**Details**

The function performs the following steps:

1. **Open the Eora26 zip file and read the text files**
   It expects a zip archive named:
   ```text
   Eora26_{year}_{typ}.zip
with the following content:

- Eora26_{year}_{typ}_T.txt : intermediate transactions matrix (T)
- Eora26_{year}_{typ}_FD.txt : final demand matrix (FD)
- Eora26_{year}_{typ}_VA.txt : value added vector (VA, read but not used here)
- labels_T.txt : labels for rows/columns of T
- labels_FD.txt : labels for columns of FD

The function uses zipfile.ZipFile to open the archive and pandas.read_csv (with tab separator, no header) to read each text file into DataFrames: df_T, df_FD, df_VA, df_lT, df_lFD.

2. **Build country–sector labels**
Label files (labels_T.txt, labels_FD.txt) have a typical structure:

- Column 1: country code (ISO3 or aggregate like ROW)

- Column 3: sector or component name

The function constructs labels as "ISO3_sector":

  ```python
  df_T.columns = list(df_lT[1] + "_" + df_lT[3])
  df_T.index   = list(df_lT[1] + "_" + df_lT[3])

  df_FD.columns = list(df_lFD[1] + "_" + df_lFD[3])
  df_FD.index   = list(df_lT[1] + "_" + df_lT[3])
  ```
so that:

- Rows of both T and FD correspond to the same set of country–sector accounts.
- Columns of T are country–sector uses, and columns of FD are final-demand components.

3. **Combine intermediate transactions and final demand**
The main MRIO table df is obtained by merging the two matrices on their common index:

  ```python

  df = pd.merge(df_T, df_FD, left_index=True, right_index=True)
  ```
The resulting DataFrame has:

- Rows: country–sector labels (plus, potentially, an aggregate like ROW).
- Columns: all intermediate-use columns (from T), followed by all final-demand columns (from FD).
- Infer number of sectors (S) and final-demand components (FD)
Using a reference country (ref = "USA"), the function infers: S: number of sectors per country, as the number of rows belonging to the reference country:

```python
S = df.T.filter(like="USA").shape[1]
SplusFD: total number of columns corresponding to the reference country (sectors + final demand):
```

```python
SplusFD = int(df.filter(like="USA").shape[1])

```

FD: number of final-demand components per country.

Eora26 typically includes a ROW (rest-of-world) aggregate that does not always have the full sectoral detail. The function assumes: ``filas_adic = 1``additional row (the ROW aggregate).

Then:

- C = (number_of_rows - filas_adic) / S: number of countries/regions.
- CS = C × S: total country–sector rows.
- CFD = C × FD: total country–final-demand columns.

As a cross-check, it also computes: `C0 = df_lFD[0].nunique()`  and compares C0 with C. If they differ, the function warns that at least one country (e.g. ROW) does not have the full set of sectors and will be dropped.

Drop ROW (rest-of-world aggregate)
To obtain a consistent square block of country–sector accounts, the function removes:

Any row whose index starts with "ROW".

Any column whose label starts with "ROW".

  ```python
  df = df[~df.index.str.startswith("ROW")]
  df = df.loc[:, ~df.columns.str.startswith("ROW")]
  ```


Finally, the function builds a dictionary:

```python

dic = {
    "df": df,
    "C": int(C),
    "S": int(S),
    "FD": int(FD),
    "CS": int(CS),
    "CFD": int(CFD),
}
```
which contains both the combined MRIO table and the inferred dimensions.


---

**Returns**

dict with the following keys:

- "df" : pandas.DataFrame
  Combined Eora26 MRIO table with:

  - Rows: country–sector accounts for all countries except the dropped ROW aggregate (e.g. "USA_Agriculture", "ESP_Manufacturing").

  - Columns: all country–sector intermediate-use entries followed by all final-demand components.

- "C" : int
Number of countries/regions (before dropping ROW, used to infer dimensions).

- "S" : int
Number of sectors per country.

- "FD" : int
Number of final-demand components per country.

- "CS" : int
Total number of country–sector rows (C × S).

- "CFD" : int
Total number of country–final-demand columns (C × FD).


---

**Example**

```python

from intrade import load_EORA

# Directory where Eora26 zip files are stored
eora_dir = "/path/to/EORA/raw/"

# Example 1: Eora26 MRIO at purchaser prices (pp), year 2010
eora_pp_2010 = load_EORA(dire=eora_dir, year=2010, typ="pp")

df_pp  = eora_pp_2010["df"]
C_pp   = eora_pp_2010["C"]
S_pp   = eora_pp_2010["S"]
FD_pp  = eora_pp_2010["FD"]

# Example 2: Eora26 MRIO at basic prices (bp), year 2005
eora_bp_2005 = load_EORA(dire=eora_dir, year=2005, typ="bp")

df_bp  = eora_bp_2005["df"]
C_bp   = eora_bp_2005["C"]
S_bp   = eora_bp_2005["S"]

# The resulting df can then be transformed into a WIO structure
# or decomposed into value-added components using other intrade functions.

```

---

**Notes**

Implemented with the following with the following original files:

- 'Eora26_1990_bp.zip', ... to 'Eora26_2017_bp.zip',
- 'Eora26_1990_pp.zip', ... to 'Eora26_2017_pp.zip'


---