<a id="bmt_output"></a>
# BMT_output

---

**Description**

`BMT_output` implements the **BMT2025 output-based tripartite GVC decomposition** and returns a tidy table that decomposes **gross output** into domestic vs. trade-related components, including a tripartite split of the GVC-related part. Conceptually, the function decomposes each country’s (and optionally each country–sector’s) gross output `X` into:

- **DomX**: output driven by **domestic final demand**,
- **GVC_X**: output that is part of **global value chain (GVC) activity**,
- **TradX**: residual “traditional” trade/output component (everything not explained by DomX or GVC_X),

with **GVC_X** further decomposed into the BMT2025 tripartite components:

- **GVC_PF_X**: pure forward GVC output,
- **GVC_TS_X**: two-sided GVC output (with a split into imported vs. domestic propagation parts),
- **GVC_PB_X**: pure backward GVC output.

Unlike `BMT_trade`, this routine is **not bilateral**: it does not return exporter→importer pairs. Instead, it produces **country totals** and/or **country×sector** results, controlled by the `selector` argument. If `measures=True`, it also adds row-wise participation indicators (shares and a forwardness measure).

---

**Usage**

`BMT_output(io, selector="all_all", measures=True)`

---

**Arguments**

`BMT_output(io, selector="all_all", measures=True)`

- `io` : `dict`
  InTrade IO dictionary (BM-style IO object). The function requires at least:

  - Core arrays/matrices:
    - `"A"` : technical coefficients matrix, shape `(GN, GN)`
    - `"B"` : global Leontief inverse, shape `(GN, GN)` (used for FVA-intensity terms)
    - `"Y"` : final demand by destination country, shape `(GN, G)`
    - `"Z"` : intermediate flows, shape `(GN, GN)` (used to build export-to-foreign vectors)
    - `"X"` : gross output vector, shape `(GN,)`
    - `"V"` : value-added coefficients vector, shape `(GN,)` (typically `VA/X`)
    - `"VA"` : value-added vector (optional here; kept for IO consistency)

  - Names and dimensions (InTrade-style):
    - `io["names"]["c_names"]` : list of country names/codes (length `G`)
    - `io["names"]["s_names"]` : list of sector names/codes (length `N`)
    - `io["dims"]["C"]` : number of countries `G`
    - `io["dims"]["S"]` : number of sectors per country `N`
    - `io["dims"]["CS"]` : total country–sector accounts `GN = G×N`

- `selector` : `str`, default `"all_all"`
  Output selector with format:

  `mode_granularity`

  where:

  - `mode ∈ {"total","all"}`
  - `granularity ∈ {"agg","sectoral","all"}`

  Examples:

  - `"total_agg"`
    One row per country (sector = `"ALL"`).

  - `"total_sectoral"`
    One row per country×sector.

  - `"all_all"`
    Returns BOTH aggregated + sectoral rows in the same dataframe.

  *Note:* output-based BMT2025 has no bilateral dimension. The `mode` field is included mainly for consistency with `BMT_trade`; in this function, `total` and `all` behave equivalently.

- `measures` : `bool`, default `True`
  If `True`, adds participation indicators computed **row-wise**:

  - `share_GVC_output` = `GVC_X / X`
  - `share_PF_output`  = `GVC_PF_X / GVC_X`
  - `share_TS_output`  = `GVC_TS_X / GVC_X`
  - `share_PB_output`  = `GVC_PB_X / GVC_X`
  - `forward_output`   = `(GVC_PF_X − GVC_PB_X) / GVC_X`

---

**Details**

1. **Selector parsing (reporting level)**

The function reads `selector="mode_granularity"` and activates:

- aggregated country rows (`sector="ALL"`) if `granularity` includes `"agg"`,
- country×sector rows if `granularity` includes `"sectoral"`.

2. **Domestic Leontief inverses**

For each country `g`, a domestic Leontief inverse is computed:

`L_g = (I - A_gg)^{-1}`

where `A_gg` is the domestic block of `A` for country `g`. These domestic inverses are used repeatedly in the construction of the BMT2025 output terms.

3. **Exports-to-foreign vector e\_s\***

A central building block is the exporter-sector vector of shipments to foreign users:

`e_s* = Z_s,foreign + Y_s,foreign`

computed as:

- row sums of intermediate flows from `s` to **foreign sectors**,
- plus row sums of final demand from `s` to **foreign countries**,

implemented robustly with `np.ix_` to preserve 2D slices.

4. **Precompute foreign-output propagation by country**

For each country `r`, the function precomputes:

`Xexp_r = L_rr @ e_r*`

which represents domestic production in `r` needed to satisfy `r`’s shipments to foreign destinations. This is used inside the pure-forward term for every exporter `s`.

5. **Tripartite GVC output decomposition**

For each country `s` (and each sector within `s`), the function computes:

- **Pure forward (PF)**: constructed as a sum over partner countries `r ≠ s`, combining direct cross-border propagation via `A_sr @ Xexp_r` and domestic amplification through `A_ss` and `L_ss`.
- **Pure backward (PB)**: constructed from “foreign value-added intensity” terms, using:
  - a **global** intensity component based on `v_j' B_js`,
  - and a **one-border** adjustment based on `v_j' L_jj A_js L_ss`,
  combined with total vs. domestic final demand (`Y_s_tot` and `Y_ss`).
- **Two-sided (TS)**: defined as the remainder of GVC activity not accounted for by PF and PB, and split into:
  - `GVC_TSImp` : imported/intensity part,
  - `GVC_TSDom` : domestic propagation part,
  with `GVC_TS_X = GVC_TSImp + GVC_TSDom`.

Then:

`GVC_X = GVC_PF_X + GVC_PB_X + GVC_TS_X`

6. **Domestic output and residual traditional component**

Domestic-demand-driven output is computed as:

`DomX = v_s * (L_ss @ Y_ss)`

and the residual traditional component is:

`TradX = X - DomX - GVC_X`

7. **Measures (optional row-wise shares and forwardness)**

If `measures=True`, the function adds row-wise indicators summarizing GVC participation in output and the forward/backward balance.

---

**Returns**

`pandas.DataFrame` always including:

- `"mode"` : `"total"` (kept for consistency)
- `"country"` : country label
- `"sector"` : sector label or `"ALL"`

and decomposition columns:

- `"X"` : gross output
- `"DomX"` : output driven by domestic final demand
- `"TradX"` : residual “traditional” component
- `"GVC_PF_X"` : pure forward GVC output
- `"GVC_PB_X"` : pure backward GVC output
- `"GVC_TSImp"` : imported/intensity part of two-sided GVC output
- `"GVC_TSDom"` : domestic propagation part of two-sided GVC output
- `"GVC_TS_X"` : total two-sided GVC output
- `"GVC_X"` : total GVC-related output

If `measures=True`, also includes:

- `"share_GVC_output"`, `"share_PF_output"`, `"share_TS_output"`, `"share_PB_output"`, `"forward_output"`

---

**Example**

```python
from intrade import BMT_output

# io is an InTrade IO dictionary (e.g., produced by obj_IO / loaders)

# Example 1: full output (country totals + country×sector)
res = BMT_output(io, selector="all_all", measures=True)

# Example 2: country totals only
tot = BMT_output(io, selector="total_agg", measures=True)

# Example 3: country×sector only (no measures)
sec = BMT_output(io, selector="total_sectoral", measures=False)

print(res.head())
print(tot.head())
print(sec.head())
```


---

**Notes**

The function assumes that countries are stored in contiguous blocks of size N in all country×sector arrays.

B (the global Leontief inverse) is required to construct the foreign value-added intensity term used in the pure-backward component.

Output-based BMT2025 has no bilateral dimension; results are reported as country totals and/or country×sector rows.


---