<a id="obj_grav_panel"></a>
# obj_Grav_panel

---

**Description**

Build a multi-year **panel** of bilateral trade flows for gravity estimation.

`obj_Grav_panel` iterates over a dictionary of MRIO dictionaries (one per year),
applies `obj_Grav` to each of them, and stacks the resulting exporter–sector–importer
cross-sections into a single long-format `pandas.DataFrame` with a `year` identifier.

This is a convenience wrapper that makes it straightforward to move from a set
of annual MRIO tables to a panel dataset that can be fed into panel gravity routines
(e.g. `grav_panel`) after merging additional gravity covariates.

---

**Usage**

`obj_Grav_panel(dicc)`

---

**Arguments**

- `dicc` : `dict`
  Dictionary of the form:
  `{year_1: dic_1, year_2: dic_2, ...}`
  where each `dic_t` is a harmonised MRIO dictionary suitable for `obj_Grav`
  (i.e. contains at least: `"df", "C", "S", "FD", "CS", "CFD"`).

  Notes:
  - Years can be `int` or `str` (they are stored as-is in the output column `year`).
  - If you want years in chronological order, pass `dicc` already sorted by year
    (or build it using an ordered insertion).

---

**Details**

For each `(year, dic_year)` pair in `dicc.items()`:

1. Compute bilateral trade flows for that year:
   - `df_t = obj_Grav(dic_year)`
   which returns a long DataFrame with columns:
   `exporter`, `sector`, `importer`, `interm`, `final`, `trade`.

2. Add a time identifier:
   - `df_t["year"] = year`

3. Append the year-specific DataFrame to a list.

Finally, all years are stacked with:
`panel_df = pd.concat(panel_data, ignore_index=True)`

The function prints the current `year` while looping and confirms completion with
`"Gravity Panel Object Done!"`.

---

**Returns**

- `panel_df` : `pandas.DataFrame`
  Long-format panel with one row per exporter–sector–importer–year observation:

  - `"exporter"` : `str` – ISO3 code of exporting country.
  - `"sector"`   : `str` – sector index.
  - `"importer"` : `str` – ISO3 code of importing country.
  - `"interm"`   : `float` – intermediate exports.
  - `"final"`    : `float` – final-goods exports.
  - `"trade"`    : `float` – total exports (`interm + final`).
  - `"year"`     : `int` or `str` – year identifier.

---

**Example**


```python
import pandas as pd
from intrade import load_TIVA, obj_Grav, obj_Grav_panel, grav_panel

# 1) Load several annual MRIO tables (example with OECD ICIO/TiVA)
icio_dir = "path/to/ICIO/raw/"

dicc = {
    2016: load_TIVA(dire=icio_dir, year=2016, typ="extended"),
    2017: load_TIVA(dire=icio_dir, year=2017, typ="extended"),
    2018: load_TIVA(dire=icio_dir, year=2018, typ="extended"),
}

# 2) Build panel of exporter–sector–importer trade flows
df_panel_trade = obj_Grav_panel(dicc)

print(df_panel_trade.head())
# exporter  sector  importer   interm    final    trade   year
# USA       1       DEU       ...       ...      ...     2016

# 3) (Optional) Merge gravity covariates before estimation
# df_cov should contain exporter, importer, year, and covariates like LN_DIST, CNTG, LANG, BRDR, ...
# df_panel = df_panel_trade.merge(df_cov, on=["exporter","importer","year"], how="left")

# 4) Estimate a panel PPML gravity model (after adding covariates)
# out = grav_panel(data=df_panel, fe=["ey","iy"], ref_country="USA", verbose=True)
# print(out["results"].summary())
```


```python
dicc = {2020: ddff20, 2021: ddff21}

panel = obj_grav_panel(dicc)

return panel_df
```

---

<hr style="border:1px solid blue; margin-top: 0; margin-bottom: 0;">


<div id="" style="font-size:50px; text-align:center; padding:10px 0; margin:0;">
</div>