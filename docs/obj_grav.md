<a id="obj_grav"></a>
# obj_Grav

---

**Description**

Build bilateral trade flows by exporter–sector–importer for gravity models.

This function takes a harmonised MRIO dictionary (as returned by the loader
functions and possibly processed by `obj_IO`) and aggregates both intermediate
and final goods exports into a long-format DataFrame suitable for gravity
estimation.

For each exporter–sector–importer triplet `(i, k, n)`, it computes:

- exports of intermediate goods,
- exports of final goods,
- total exports (intermediate + final).

Country and sector labels are parsed from the column/index structure
(e.g. `"USA_1"`, `"DEU_3"`, `"FRA_2"`, …).

---

**Usage**

`obj_Grav(dic)`

---

**Arguments**

- `dic` : `dict`
  MRIO dictionary with at least:
  - `"df"`   : `pandas.DataFrame`
    Harmonised IO table with:
    - rows   = `CS` country–sector rows (`C × S`),
    - cols   = first `CS` columns for intermediate use (Z block),
               next `CFD` columns for final demand (Yfd block),
               optionally a last column with total output.
  - `"C"`    : `int` – number of countries (`C`).
  - `"S"`    : `int` – number of sectors per country (`S`).
  - `"FD"`   : `int` – number of final demand categories per country (`FD`).
  - `"CS"`   : `int` – total country–sector pairs (`C × S`).
  - `"CFD"`  : `int` – total country–final-demand pairs (`C × FD`).

---

**Details**

The function assumes the following harmonised layout of `dic["df"]`:

- Rows:
  `0 .. CS-1` correspond to country–sector combinations,
  labelled as strings `"ISO3_sector"` (e.g. `"USA_1"`, `"DEU_3"`).

- Columns:
  1. `0 .. CS-1` → intermediate input block `Z` (`CS × CS`),
  2. `CS .. CS+CFD-1` → detailed final demand block `Yfd` (`CS × CFD`),
  3. Optional last column → total output (`OUT`).

Steps:

1. **Intermediate goods exports (Z block)**
   - Extract `Z_block = df.iloc[:CS, :CS]`.
   - Stack to long format via `stack()`, giving a Series indexed by
     `(origin_row_label, destination_col_label)`.
   - Parse both labels `"ISO3_sector"` into:
     - exporter country `i` (first 3 characters),
     - exporter sector `k` (characters after `"ISO3_"`),
     - importer country `n` (first 3 characters of destination label),
     - destination sector `j` (ignored later).
   - Group by `["i", "k", "n"]` and sum over `j` to obtain intermediate exports
     from exporter–sector `(i,k)` to importer `n`.

2. **Final goods exports (Yfd block)**
   - Extract `Yfd_block = df.iloc[:CS, CS:CS+CFD]`.
   - Stack to long format, again resulting in a Series indexed by
     `(origin_label, fd_destination_label)`.
   - Parse labels into:
     - exporter `i` and sector `k` (from the row label),
     - importer `n` and final-demand category `f` (from the column label).
   - Group by `["i", "k", "n"]` and sum over `f` to obtain total final-goods
     exports from `(i,k)` to `n`.

3. **Combine intermediate and final exports**
   - Merge the intermediate and final exports DataFrames on index
     `("i", "k", "n")`.
   - Rename resulting columns:
     - `"interm"` : exports of intermediates,
     - `"final"`  : exports of final goods.
   - Compute `"trade" = interm + final`.

4. **Output format**
   - Reset the index and rename dimensions to:
     - `"exporter"` (i),
     - `"sector"` (k),
     - `"importer"` (n),
     - plus `"interm"`, `"final"`, `"trade"`.

---

**Returns**

- `df_t` : `pandas.DataFrame`
  Long-format DataFrame with one row per exporter–sector–importer triplet:

  - `"exporter"` : `str` – ISO3 code of exporting country `i`.
  - `"sector"`   : `str` – sector index `k` (as string).
  - `"importer"` : `str` – ISO3 code of importing country `n`.
  - `"interm"`   : `float` – exports of intermediate goods from `(i,k)` to `n`.
  - `"final"`    : `float` – exports of final goods from `(i,k)` to `n`.
  - `"trade"`    : `float` – total exports from `(i,k)` to `n`
                         (`interm + final`).


---

**Example**

```python
import pandas as pd
from intrade import load_TIVA, obj_IO, obj_Grav

# 1. Load and harmonise an MRIO (e.g. OECD ICIO/TiVA)
tiva_dic = load_TIVA(dire="path/to/ICIO/raw/", year=2018, typ="extended")

# 2. Optionally build the IO object (e.g. to get Z, Y, EXGR, ...)
io_dic = obj_IO(tiva_dic)

# 3. Build bilateral exporter–sector–importer trade flows
df_grav = obj_Grav(tiva_dic)  # or obj_Grav(io_dic) if you harmonise there

# Inspect the resulting gravity-ready dataset
print(df_grav.head())

# Typical columns
#   exporter  sector  importer  interm    final    trade
# 0      USA       1      DEU   ...       ...      ...
```

---

**Notes**

---