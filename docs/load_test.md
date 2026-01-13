<a id="load_test"></a>
# load_Test

---

**Description**

`load_Test` builds **small synthetic input–output (IO) datasets** that are useful for:

- testing value-added decomposition routines (e.g. Decompr-style, Exvatools-style, WWZ-style),
- writing examples and unit tests for MRIO algorithms.

It returns a toy multi-country, multi-sector IO table plus the main structural dimensions (number of countries, sectors, and final-demand components).

Two test layouts are currently implemented:

- `"decompr"`: 3 countries (ARG, TUR, DEU) × 3 sectors each, 1 final-demand category. From Quast & Kummritz (2015)
- `"exvatools"`: 10 countries (ESP, FRA, MEX, USA, CHN, ROW, MX1, MX2, CN1, CN2) × 3 sectors each, 2 final-demand category. From Feás (2013)
- `"WWZ"`    : 3 countries (rrr, sss, ttt) × 2 sectors each, 1 final-demand category. From Wang et al. (2013)

The numeric values are arbitrary and only intended for **illustration and testing**.

---

**Usage**

`load_Test(typ)`

---

**Arguments**

`load_Test(typ)`

- `typ` : `{"decompr", "WWZ"}`
  Selects which toy dataset to generate:

  - `"decompr"`
    Three countries (**ARG**, **TUR**, **DEU**), each with **3 sectors**, and **1 final-demand** category per country.
    This layout is compatible with **Decompr-style** decompositions.

- `"exvatools"`
    Ten "countries" (**ESP**, **FRA**, **MEX**, **USA**, **CHN**, **ROW**, **MX1**, **MX2**, **CN1**, **CN2**), each with **3 sectors**, and **2 final-demand** category per country.
    This layout is compatible with **Exvatools-style** decompositions.

  - `"WWZ"`
    Three countries (**rrr**, **sss**, **ttt**), each with **2 sectors**, and **1 final-demand** category per country.


If a different string is passed, the current implementation will not create a dataset and will raise an error in subsequent steps (no internal validation is performed yet).

---

**Details**

1. **General structure**

   For both `typ="decompr"`, `typ="exvatools"` and `typ="WWZ"`, the function returns:

   - `df` : a **square IO matrix** with:
     - **rows** indexed by `country_sector`, e.g. `"ARG_1"`, `"TUR_3"`, `"DEU_2"`,
       or `"rrr_1"`, `"sss_2"`, `"ttt_1"`.
     - **columns** ordered as:
       1. All **country–sector intermediate-use** columns (one per exporter sector),
       2. All **country-specific final-demand** columns,
       3. One final column `"Output"` with total output by country–sector.

   - Structural dimensions:
     - `C`   – number of countries,
     - `S`   – number of sectors per country,
     - `FD`  – number of final-demand categories per country,
     - `CS`  – total country–sector pairs (`C × S`),
     - `CFD` – total country–final-demand pairs (`C × FD`).

2. **Case `typ="decompr"`**

   - Countries: `["ARG", "TUR", "DEU"]`
   - Sectors (per country): `"1"`, `"2"`, `"3"`
   - Final demand: 1 category per country (`ARG_4`, `TUR_4`, `DEU_4`)
   - Output: `"Output"` column

   The DataFrame is constructed from a hard-coded dictionary:

   - Row index:
     ```text
     ["ARG_1", "ARG_2", "ARG_3",
      "TUR_1", "TUR_2", "TUR_3",
      "DEU_1", "DEU_2", "DEU_3"]
     ```
   - Columns reordered as:
     ```text
     ["ARG_1","ARG_2","ARG_3",
      "TUR_1","TUR_2","TUR_3",
      "DEU_1","DEU_2","DEU_3",
      "ARG_4","TUR_4","DEU_4",
      "Output"]
     ```

   Dimensions for this toy dataset:

   - `C = 3`, `S = 3`, `FD = 1`
   - `CS = 3 × 3 = 9`
   - `CFD = 3 × 1 = 3`

   Printed message:  ```text load_Test, decompr: Done! Case typ="WWZ"

- Countries: ["rrr", "sss", "ttt"]
- Sectors (per country): "1", "2"
- Final demand: 1 category per country (rrr_4, sss_4, ttt_4)
- Output: "Output" column

- Row index:            ["rrr_1", "rrr_2",  "sss_1", "sss_2",  "ttt_1", "ttt_2"]
- Columns reordered as: ["rrr_1", "rrr_2",  "sss_1", "sss_2",  "ttt_1", "ttt_2",  "rrr_4","sss_4","ttt_4",  "Output"]

Dimensions for this toy dataset:

- C = 3, S = 2, FD = 1
- CS = 3 × 2 = 6
- CFD = 3 × 1 = 3


Intended use. These toy datasets are designed for:

- unit tests of decomposition routines (BM, WWZ components, etc.),
- examples in documentation or teaching materials,
- quick checks of consistency (row/column sums, balance conditions, etc.).

They are not calibrated to any real economy and should never be used for empirical analysis.

---

**Returns**

dict with:

- "df" : pandas.DataFrame
  IO matrix with:

  - Rows = country–sector accounts ("ARG_1", "TUR_2", "DEU_3", … or "rrr_2", etc.),

  - Columns = all intermediate-use country–sector blocks, followed by country-specific final demand, and a final "Output" column.

- "C" : int
Number of countries in the synthetic dataset.

- "S" : int
Number of sectors per country.

- "FD" : int
Number of final-demand categories per country.

- "CS" : int
Total number of country–sector combinations (C × S).

- "CFD" : int
Total number of country–final-demand combinations (C × FD).

---

**Example**

```python
from intrade import load_Test

# -----------------------------------
# 1) Decompr-style toy dataset
# -----------------------------------
toy_decompr = load_Test("decompr")

df_dec = toy_decompr["df"]
C_dec  = toy_decompr["C"]
S_dec  = toy_decompr["S"]
FD_dec = toy_decompr["FD"]

print(df_dec)
print("Countries:", C_dec, "Sectors:", S_dec, "FD:", FD_dec)

# Example: extract intermediate-use matrix A-like block
CS_dec = toy_decompr["CS"]
A_block = df_dec.iloc[:CS_dec, :CS_dec]  # 9x9 intermediate block (ARG/TUR/DEU × 3 sectors)

# -----------------------------------
# 2) WWZ-style toy dataset
# -----------------------------------
toy_wwz = load_Test("WWZ")

df_wwz = toy_wwz["df"]
C_w    = toy_wwz["C"]
S_w    = toy_wwz["S"]
FD_w   = toy_wwz["FD"]

print(df_wwz)
print("Countries:", C_w, "Sectors:", S_w, "FD:", FD_w)

# Intermediate-use block (6x6) for WWZ example
CS_w   = toy_wwz["CS"]
A_wwz  = df_wwz.iloc[:CS_w, :CS_w]

# These toy matrices can now be passed to your decomposition functions, e.g.:
#   wio = make_wio_from_df(df_dec, C=C_dec, S=S_dec, FD=FD_dec)
#   result = BM(wio)

```

---


**Notes**

---