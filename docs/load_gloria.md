<a id="load_gloria"></a>
# load_GLORIA

---

**Description**

`load_GLORIA` reads a **GLORIA** multi-regional input–output (MRIO) table for a given year from a compressed zip archive, extracts:

- the **intermediate transactions matrix** (`T-Results`),
- the **final demand matrix** (`Y-Results`),

and combines them into a single `pandas.DataFrame` with a consistent **country–sector** and **country–final-demand** structure.

The implementation assumes the standard GLORIA layout:

- `C = 164` countries/regions,
- `S = 120` sectors per country,
- `FD = 6` final-demand components per country.

Row/column labels are constructed as:

- `"i_j"` for country–sector (i = 1..C, j = 1..S),
- `"i_j"` for country–FD (i = 1..C, j = S+1..S+FD).

---

**Usage**

`load_GLORIA(dire, year)`

---

**Arguments**

`load_GLORIA(dire, year)`

- `dire` : `str` or `pathlib.Path`
  Directory where the GLORIA zip file is stored. It should include the trailing separator, e.g.:
  ```text
  "/path/to/Gloria/"
year : int
Reference year of the GLORIA MRIO to load (typically between 1990 and 2028, depending on the data release).

---

**Details**

The function proceeds in the following steps:

1. **Set fixed dimensions for GLORIA**
The GLORIA system is very large. In this implementation the dimensions are hard-coded:

- C  = 164   # number of countries/regions
- S  = 120   # sectors per country
- FD = 6     # final-demand components per country
- CS = 19680 # C * S
- CFD = 984  # C * FD

2. **Build labels for country–sector and country–FD accounts**

- Country–sector labels: `names = [f"{i}_{j}" for i in range(1, C + 1) for j in range(1, S + 1)]`
- Country–FD labels: `names_fd = [f"{i}_{j}" for i in range(1, C + 1) for j in range(S + 1, S + FD + 1)]`

3. **Select GLORIA zip file and define filename patterns**

The function expects a zip file: `GLORIA_MRIOs_59_{year}.zip`
containing CSV files for:

- intermediate transactions (T-Results),

- final demand (Y-Results).

File name patterns (regular expressions) are:

- `pattern  = r".*Mother_AllCountries_002_T-Results_" + str(year) + r"_059_Markup001\(full\)\.csv"`
- `patternY = r".*Mother_AllCountries_002_Y-Results_" + str(year) + r"_059_Markup001\(full\)\.csv"`

Inside the zip, the function searches for filenames that match these patterns.

4. **Row/column selection for GLORIA blocks**
GLORIA MRIOs have repeated blocks for different purposes. This implementation selects only the relevant blocks using index rules:

- Rows: keep only row indices where (i // S) % 2 == 0.

- Columns: for T-Results, keep only column indices where (i // S) % 2 != 0.

Concretely:

`rows = [i for i in range(0, C * S * 2) if (i // S) % 2 == 0]`
`cols = [i for i in range(0, C * S * 2) if (i // S) % 2 != 0]`
This exploits the internal GLORIA structure where blocks are stored in alternating fashion.

5. **Open the zip and load the T and Y matrices**
Using zipfile.ZipFile, the function:

- lists all files (namelist()),

- filters them with re.match(pattern, f) and re.match(patternY, f).

Then it reads:

- T matrix (intermediate transactions):


```python
df1 = pd.read_csv(archivo_txt, skiprows=rows, usecols=cols, delimiter=",",  encoding="utf-8",   header=None,)
```

- Y matrix (final demand):

```python
df2 = pd.read_csv(archivo_txt, skiprows=rows, delimiter=",", encoding="utf-8",  header=None,)
```
Both are read as numeric matrices without headers.

6. **Assign labels and combine [T | Y]**

For the intermediate block df1 (T):

```python

df1.index   = names      # country–sector rows
df1.columns = names      # country–sector columns
```
- For the final-demand block df2 (Y):

```python

df2.index   = names      # same country–sector rows
df2.columns = names_fd   # country–FD columns
```
- The final combined MRIO is:

```python

df = pd.concat([df1, df2], axis=1)
```
giving a matrix of dimension:

- rows: CS country–sector accounts (164 × 120 = 19,680),

- columns: CS + CFD (19,680 + 984) with all intermediate uses first, followed by final demand.

7. **Pack results in a dictionary**
The function returns:

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
This structure is ready to be transformed into a WIO object or used directly for further decompositions.

---

**Returns**

dict with the following keys:

- "df" : pandas.DataFrame
Combined GLORIA MRIO table [T | Y] with:

  Rows: country–sector indices "i_j" for i = 1..C, j = 1..S.

  Columns:
  - first CS columns: intermediate transactions between country–sectors "i_j",
  - next CFD columns: final demand components "i_j" for j = S+1..S+FD.

- "C" : int
Number of countries/regions (fixed at 164 in this implementation).

- "S" : int
Number of sectors per country (fixed at 120).

- "FD" : int
Number of final-demand components per country (fixed at 6).

- "CS" : int
Total number of country–sector combinations (C × S = 19,680).

- "CFD" : int
Total number of country–final-demand combinations (C × FD = 984).

---

**Example**

```python

from intrade import load_GLORIA

# Directory where GLORIA zip files are stored
gloria_dir = "/path/to/Gloria/"

# Example: Load GLORIA MRIO for year 2015
gloria_2015 = load_GLORIA(dire=gloria_dir, year=2015)

df_gloria = gloria_2015["df"]
C        = gloria_2015["C"]   # 164
S        = gloria_2015["S"]   # 120
FD       = gloria_2015["FD"]  # 6

# Inspect dimensions
print(df_gloria.shape)  # (CS, CS + CFD) = (19680, 19680 + 984)

# Example: subset a specific country (e.g. i = 10)
country_i = 10
rows_country_i = [idx for idx in df_gloria.index if idx.startswith(f"{country_i}_")]
df_country_i = df_gloria.loc[rows_country_i, :]

# The resulting df_gloria can then be passed to transformation routines
# that build a full WIO structure or perform value-added decompositions.

```

---

**Notes**


Implemented using the following original data files:

– GLORIA_MRIOs_59_1990.zip to GLORIA_MRIOs_59_2028.zip

Within each ZIP archive, the following files are used:

– 20240111_120secMother_AllCountries_002_T-Results_1990_059_Markup001(full).csv
... to
20240111_120secMother_AllCountries_002_T-Results_2028_059_Markup001(full).csv

and

-20240111_120secMother_AllCountries_002_Y-Results_1990_059_Markup001(full).csv
... to
20240111_120secMother_AllCountries_002_Y-Results_2028_059_Markup001(full).csv


---