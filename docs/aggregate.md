<a id="aggregate"></a>
# aggregate

---

**Description**

`aggregate` collapses an input–output table from the **country–sector** level to the **country** level, summing over **all sectors** and **all final-demand categories**. The resulting IO structure is a compact **country × country** table where:

- each country has **one aggregated “sector”** (suffix `"_1"`),
- each country has **one aggregated final-demand category** (suffix `"_2"`),
- intermediate flows become a **C × C** block (**Z**),
- final demand becomes a **C × C** block (**F**),
- and the returned table is the concatenation **[Z | F]** stored in `dic["df"]`.

Internally, the function assumes that row/column labels follow the InTrade convention:

- rows/columns are named like `"ISO3_sectorCode"` (e.g. `"ESP_01T09"`, `"USA_10T39"`),
- the country code is the substring **before the first underscore**.

The aggregation is implemented by extracting the intermediate block and final-demand block from `d["df"]`, grouping rows and columns by country, and then rebuilding a new IO dictionary with `S=1` and `FD=1`.

---

**Usage**

`aggregate(d)`

---

**Arguments**

`aggregate(d)`

- `d` : `dict`
  InTrade IO dictionary containing at least:

  - `d["df"]` : `pandas.DataFrame`
    Full IO table, with the **core** country–sector block located in the first `d["CS"]` rows and columns, and the **final demand** block located in the next `d["CFD"]` columns.

  - `d["C"]` : `int`
    Number of countries.

  - `d["CS"]` : `int`
    Total number of country–sector accounts (`C × S`) in the original table.

  - `d["CFD"]` : `int`
    Total number of country–final-demand accounts (`C × FD`) in the original table.

---

**Details**

1. **Extract intermediate block (Z)**

The intermediate-input matrix is extracted as the top-left country–sector block.
Countries are inferred from labels by taking the substring before "_".
Rows are summed by exporter country, and then columns are summed by importer country.
The resulting row/column labels are renamed to COUNTRY_1.

The final-demand block is extracted from the columns immediately following the intermediate block.
Final demand is aggregated by exporter (rows) and by destination country (columns).
Labels are renamed to COUNTRY_1 for rows and COUNTRY_2 for final-demand columns.

The output table and the returned dictionary updates the structural dimensions to reflect country-level aggregation:

S = 1 (one sector per country)

FD = 1 (one final-demand category per country)

CS = C

CFD = C


---

**Returns**

dict with:

"df" : pandas.DataFrame
Aggregated country-level IO table with shape (C, 2C), formed as [Z | F]:

Columns COUNTRY_1 … are intermediate inputs (Z, country × country)

Columns COUNTRY_2 … are final demand (F, country × country)

"C" : int
Number of countries (unchanged from input).

"S" : int
Number of sectors per country after aggregation (S = 1).

"FD" : int
Number of final-demand components per country after aggregation (FD = 1).

"CS" : int
Total country–sector combinations after aggregation (CS = C).

"CFD" : int
Total country–final-demand combinations after aggregation (CFD = C).

---

**Example**

```python
Copiar código
import pandas as pd
from intrade import aggregate

# Suppose `wio` is an InTrade IO dictionary already created (e.g. from load_* + obj_IO)
# wio["df"] has labels like "ESP_01T09", "USA_10T39", etc.

wio_cty = aggregate(wio)

df_cty = wio_cty["df"]
C      = wio_cty["C"]

print(df_cty.shape)  # (C, 2C)

# Intermediate block (Z) and final demand block (F)
Z_cty = df_cty.iloc[:, :C]
F_cty = df_cty.iloc[:, C:]

print(Z_cty.head())
print(F_cty.head())

```

---

**Notes**

The function assumes that country codes are encoded as the substring before the first underscore in row/column labels.

This aggregation is useful for producing compact country-level IO tables or for diagnostics and reporting when sectoral detail is not needed.

---

<hr style="border:1px solid blue; margin-top: 0; margin-bottom: 0;">


<div id=" " style="font-size:50px; text-align:center; padding:10px 0; margin:0;">

</div>