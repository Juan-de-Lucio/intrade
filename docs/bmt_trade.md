<a id="bmt_trade"></a>
# BMT_trade

---

**Description**

`BMT_trade` implements the **BMT2025 tripartite GVC trade decomposition** and returns a tidy table of bilateral and/or total trade components, decomposing gross exports into:

- **DAVAX**: domestic value added absorbed abroad,
- **GVC**: the global value chain (cross-border) component of exports,
- and a **tripartite split of GVC trade** into:
  - **GVC_PF**: pure forward GVC trade,
  - **GVC_TS**: two-sided (multi-country) GVC trade,
  - **GVC_PB**: pure backward GVC trade.

The function is designed to work directly on an InTrade IO object and produces results at different reporting granularities through the `selector` argument:

- **mode** controls whether results are computed as:
  - bilateral flows *(exporter → importer)*,
  - totals by exporter *(summing across importers)*,
  - or both.
- **granularity** controls whether results are reported:
  - aggregated across sectors (`sector="ALL"`),
  - by exporter sector (`sector=sectors[i]`),
  - or both.

In addition, if `measures=True`, the function computes and attaches a set of **summary indicators** (shares and a “forwardness” measure) computed on **exporter totals** (by exporter and sector) and merged back into all rows.

---

**Usage**

`BMT_trade(io, selector="all_all", measures=True)`

---

**Arguments**

`BMT_trade(io, selector="all_all", measures=True)`

- `io` : `dict`
  InTrade IO dictionary (BM-style IO object). It must contain, at minimum, the core matrices and dimension metadata used by the decomposition. In the current implementation the function expects:

  - Core arrays/matrices:
    - `"Z"` : intermediate transactions matrix
    - `"Y"` : final demand matrix (country destinations)
    - `"A"` : technical coefficients matrix
    - `"B"` : Leontief inverse (used elsewhere in the IO object; not required by all steps here)
    - `"V"` : value-added coefficients vector (country–sector)
    - `"VA"` : value-added vector (optional here; kept for consistency)
    - `"X"` : gross output vector (optional here; kept for consistency)

  - Names and dimensions:
    - `io["names"]["c_names"]` : list of country names/codes (length `G`)
    - `io["names"]["s_names"]` : list of sector names/codes (length `N`)
    - `io["dims"]["C"]` : number of countries `G`
    - `io["dims"]["S"]` : number of sectors per country `N`
    - `io["dims"]["CS"]` : total country–sector accounts `GN = G×N`

  - Optional:
    - `io["country_codes"]` : mapping to allow string country identifiers (e.g. `"CHN"`, `"USA"`) to be converted into numeric ids.
      *(Note: in the current version this is prepared via an internal helper but not exposed as a user argument.)*

- `selector` : `str`, default `"all_all"`
  Controls the output detail level with the format:

  `mode_granularity`

  where:

  - `mode ∈ {"bilateral", "total", "all"}`
  - `granularity ∈ {"agg", "sectoral", "all"}`

  Examples:

  - `"bilateral_agg"`
    Bilateral exporter→importer results aggregated across sectors (`sector="ALL"`).

  - `"bilateral_sectoral"`
    Bilateral exporter→importer results by exporter sector.

  - `"total_agg"`
    Totals by exporter (importer is `NaN`), aggregated across sectors (`sector="ALL"`).

  - `"total_sectoral"`
    Totals by exporter and sector (importer is `NaN`).

  - `"all_all"`
    Full output: bilateral + totals, and aggregated + sectoral.

- `measures` : `bool`, default `True`
  If `True`, computes summary measures on exporter totals (exporter, sector) and merges them back into every output row:

  - `share_GVC_trade` = `GVC / E`
  - `share_PF_trade`  = `GVC_PF / GVC`
  - `share_TS_trade`  = `GVC_TS / GVC`
  - `share_PB_trade`  = `GVC_PB / GVC`
  - `forward_trade`   = `(GVC_PF − GVC_PB) / GVC`

---

**Details**

1. **Selector parsing (output configuration)**

The function reads `selector="mode_granularity"` and activates the corresponding output blocks:

- `want_bilateral` and/or `want_total`
- `want_agg` and/or `want_sectoral`

This allows a single call to produce compact totals or the full matrix of bilateral × sector outcomes.

2. **Core objects and dimensions**

The function pulls the IO core matrices and dimension metadata from the `io` dictionary, including:

- `G` (countries), `N` (sectors), and `GN` (country×sector accounts),
- country and sector names used to label the output.

3. **Domestic Leontief inverses**

A key ingredient is a list of **country-specific domestic Leontief inverses**:

- For each country `g`, compute:

  `L_g = (I - A_gg)^{-1}`

where `A_gg` is the domestic block of the technical coefficient matrix for country `g`. This provides within-country propagation required to build the decomposition terms.

4. **Precomputations (BMT2025 components)**

To speed up the bilateral loop, two main precomputations are performed:

- **Import intensity by exporter country**
  For each exporter `s`, compute by-sector import intensity:

  `imp_s = Σ_{t≠s} colSums(A_ts)`

- **Exports from a country to “all others” by importer**
  For each importer `r`, compute:

  `Σ_{j≠r} e_rj`

where `e_rj` is the exporter-sector gross export vector from `r` to `j`.

5. **Bilateral loop (exporter s, importer r)**

For each ordered pair `(s,r)` with `r ≠ s`, the function builds:

- `e_sr` : exporter-sector gross exports (intermediate + final demand),
- `q_final` : domestic production needed to satisfy exporter’s final-absorption pathway,
- `q_two` : production related to the two-sided (multi-country) pathway.

From these, it computes (as vectors by exporter sector):

- `DAVAX_vec = v_s * q_final`
- `PB_vec    = imp_s * q_final`
- `TS_vec    = imp_s * q_two`
- `GVC_vec   = e_sr - DAVAX_vec`
- `PF_vec    = GVC_vec - PB_vec - TS_vec`

These sectoral vectors can be stored either as sectoral rows or aggregated to scalars (summing over sectors), depending on `selector`.

At the same time, the function accumulates exporter totals:

- exporter-level totals (aggregated across sectors),
- and exporter×sector totals (sectoral).

6. **Total rows (by exporter)**

If `mode` includes totals, the function appends rows with:

- `mode="total"`
- `importer=np.nan`

and the same decomposition columns, either aggregated or sectoral.

7. **Measures (optional shares and forwardness)**

If `measures=True`, the function computes exporter-total measures for:

- `sector="ALL"` and sectoral entries,
then merges them back into the output table by `["exporter","sector"]`, so every row carries the same exporter-sector totals and shares.

---

**Returns**

`pandas.DataFrame` always containing:

- `"mode"` : `{"bilateral","total"}`
- `"exporter"` : exporter country label
- `"importer"` : importer country label (or `NaN` for totals)
- `"sector"` : `"ALL"` or exporter sector label

and decomposition columns (depending on selector, but typically):

- `"E"` : gross exports (intermediate + final demand)
- `"DAVAX"` : domestic VA absorbed abroad
- `"GVC"` : GVC-related exports (`E − DAVAX`)
- `"GVC_PF"` : pure forward GVC trade
- `"GVC_TS"` : two-sided GVC trade
- `"GVC_PB"` : pure backward GVC trade

If `measures=True`, additional columns are included:

- `"E_s"`, `"GVC_s"`, `"GVC_PF_s"`, `"GVC_TS_s"`, `"GVC_PB_s"` (exporter totals by sector)
- `"share_GVC_trade"`, `"share_PF_trade"`, `"share_TS_trade"`, `"share_PB_trade"`, `"forward_trade"`

---

**Example**

```python
from intrade import BMT_trade

# io is an InTrade IO dictionary (e.g., produced by obj_IO / loaders)
# Example 1: full output (bilateral + totals, agg + sectoral)
res = BMT_trade(io, selector="all_all", measures=True)

# Example 2: exporter totals only, aggregated across sectors
tot = BMT_trade(io, selector="total_agg", measures=True)

# Example 3: bilateral by sector
bil_sec = BMT_trade(io, selector="bilateral_sectoral", measures=False)

print(res.head())
print(tot.head())
```

---

**Notes**

The function assumes that countries are indexed in blocks of size N (sectors) in all country×sector matrices.

Domestic inverses are computed country-by-country ((I - A_gg)^{-1}), so the decomposition uses within-country propagation combined with cross-country technical links through the relevant blocks of A.

The output is returned in a tidy long format so it can be directly used in reporting, plotting, and further aggregation workflows.

---