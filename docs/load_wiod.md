<a id="load_wiod"></a>
# load_WIOD

---

**Description**

`load_WIOD` reads a **WIOD** inter-country input–output (WIOT) table for a given year and infers the main MRIO dimensions:

- number of countries/regions,
- number of sectors per country,
- number of final-demand components per country,
- and the derived country–sector and country–final-demand dimensions.

The function is currently implemented for the **WIOD 2016** release in Stata (`.dta`) format, using the **ROW-extended** tables (`*_ROW.dta`). It:

1. Reads the WIOT for the requested year.
2. Builds country–sector row labels of the form `"ISO3_sectorIndex"` from the WIOD `Country` and `RNr` fields.
3. Renames flow columns in a similar `"ISO3_sectorIndex"` style (e.g. `"USA_1"`, `"DEU_5"`).
4. Uses a reference country (`USA`) to infer:
   - sectors per country (`S`),
   - final-demand components per country (`FD`),
   - total countries (`C`),
   - and the composite dimensions (`CS`, `CFD`).

The result is a convenient dictionary containing both the IO table (`df`) and its basic structural dimensions.

---

**Usage**

`load_WIOD(dire, year, typ)`

---

**Arguments**

`load_WIOD(dire, year, typ)`


- `dire` : `str` or `pathlib.Path`
  Base directory where the WIOD files are stored. It **must** include the trailing separator, for example:
  ```text
  "/path/to/WIOD/"
The function internally expects to find the Stata file in:


`dire + "WIOD 2016\\WIOT{year}_October16_ROW.dta"`
year : int
Reference year of the WIOT to load. For the WIOD 2016 release this typically covers 2000–2014 (plus some earlier/later years depending on the specific dataset).

typ : {"WIOD 2016", "WIOD 2013", "Long-run"}
Type of WIOD dataset. Currently, only:

``typ = "WIOD 2016"``
is implemented in this function. Other values preserve the original behaviour (and will fail due to the absence of a defined df).

---

**Details**

1. **Load WIOD 2016 table from Stata**

For `typ == "WIOD 2016"` the function reads the WIOT from a Stata file:

`df = pd.read_stata(dire + "WIOD 2016\\WIOT" + str(year) + "_October16_ROW.dta")`

The original WIOD 2016 WIOT*_ROW.dta file typically contains the following columns (among others):

- IndustryCode
- IndustryDescription
- Country (3-letter WIOD country code, ISO3-like)
- RNr (row number, used to distinguish sectors/rows)
- Year
- vXXXYY columns for flows (e.g. vUSA01, vDEU12, …) and final demand.

2. **Build the row index**

The row index is constructed as: `df = df.set_index(df["Country"] + "_" + df["RNr"].astype(str))`
giving labels such as:

"USA_1", "USA_2", …, "DEU_1", "DEU_2", …

This index approximates country–sector accounts, with RNr representing the sector index within each country.

3. **Drop metadata / non-flow columns**

The following metadata columns are removed from the IO matrix: `df = df.drop(columns=["IndustryCode", "IndustryDescription", "Country", "RNr", "Year"])`

The remaining columns correspond to flows (intermediate and final demand), usually prefixed with "v".

3. **Clean column names and convert them to "ISO3_sectorIndex"**

WIOD 2016 uses column names like "vUSA01", "vDEU12", etc. The function:

Removes the leading 'v' (if present): `df = df.rename(columns=lambda x: x[1:] if isinstance(x, str) and x.startswith("v")else x)`

4. **Splits them into "ISO3_sectorIndex"** using:`df.columns = [col[:3] + "_" + col[3:] for col in df.columns]`
So:

- "vUSA01" → "USA01" → "USA_01",

- "vDEU14" → "DEU14" → "DEU_14", etc.

This ensures that both rows and columns follow a country–sector index pattern, facilitating subsequent processing into WIO structures.

5. **Infer number of sectors (S) and final-demand components (FD)**

A reference country (ref = "USA") is used to infer structural dimensions:

- Number of sectors S
- Count how many rows belong to USA when looking across origin-side sectors: `S = int(df.T.filter(like="USA").shape[1])`
- Total columns for USA (sectors + FD)
- Count how many columns correspond to USA: `SplusFD = int(df.filter(like="USA").shape[1])`
- FD = SplusFD - S . FD is the number of final-demand components per country.

6. **Account for additional rows (aggregates, totals, etc.)**

WIOD IO tables include some extra rows that are not part of the country–sector block (e.g. totals, adjustments). The function assumes: ``filas_adic = 8``
additional rows beyond the C × S core.

7. **Compute number of countries and composite dimensions**

With: ``n_rows = df.shape[0]`` the number of countries is:

```python
C   = (n_rows - filas_adic) / S
CS  = C * S     # total country–sector combinations
CFD = C * FD    # total country–final-demand combinations
```
Basic checks are printed to the console:
``print("Year:", year, "\nFile:", "WIOD\\WIOT" + str(year) + "_October16_ROW")``
``print("\n Num Countries", C, "\n Num sect", S, "\n Num components FD", FD)``


8. **The function returns a dictionary:**

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
which can be directly used to build a wio structure or to feed value-added decomposition routines.

---

**Returns**

dict with:

- "df" : pandas.DataFrame
  WIOD IO table with:

  - Rows: country–sector-like accounts, indexed as "ISO3_sectorIndex"
  (plus ~8 additional rows for aggregates/totals).

  - Columns: country–sector blocks and final-demand columns, all named as "ISO3_sectorIndex" (e.g. "USA_1", "DEU_5", etc.).

- "C" : int
Number of countries/regions in WIOD (including the rest-of-world entry, ROW).

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
from intrade import load_WIOD

# Base directory where WIOD 2016 files are stored
wiod_dir = "D:/MRIO/WIOD/"

# Example 1: Load WIOD 2016 table for year 2010
wiod_2010 = load_WIOD(dire=wiod_dir, year=2010, typ="WIOD 2016")

df_wiod = wiod_2010["df"]
C       = wiod_2010["C"]
S       = wiod_2010["S"]
FD      = wiod_2010["FD"]

print(df_wiod.shape)  # (rows, cols) including aggregates

# Example 2: Extract only country–sector rows (excluding extra rows)
CS = wiod_2010["CS"]
df_core = df_wiod.iloc[:CS, :]   # first C*S rows as core MRIO block

# Example 3: Subset USA as exporter (rows starting with "USA_")
usa_rows = [idx for idx in df_wiod.index if idx.startswith("USA_")]
df_usa   = df_wiod.loc[usa_rows, :]

# The resulting df_wiod can then be converted into a WIO dictionary:
#   wio = make_wio_from_df(df_core, C=C, S=S, FD=FD)
# and used for standard value-added export decompositions.

```


---


**Notes**

Implemented using the WIOD 2016 release. The program reads the files WIOT2000_October16_ROW.dta ... to WIOT2014_October16_ROW.dta from the WIOTS_in_STATA.zip archive.

---

<hr style="border:1px solid blue; margin-top: 0; margin-bottom: 0;">


<div id=" " style="font-size:50px; text-align:center; padding:10px 0; margin:0;">

</div>