<a id="KWW"></a>
# KWW

---

**Description**

Aggregates the detailed Wang–Wei–Zhu (WWZ) decomposition into a smaller set of Koopman–Wang–Wei (KWW)-style components.

Starting from the 16 WWZ terms produced by WWZ(io, agg), this function groups them into 9 economically meaningful categories plus a total, either in levels (same units as gross exports) or as percentage shares of total exports for each flow.

---

**Usage**

`KWW(io, agg ="", shares: bool = False)`

---

**Arguments**

io (dict)
World input–output object to be passed to WWZ. It must be compatible with your WWZ function, i.e.
WWZ(io, agg) returns a pandas.DataFrame whose columns are the 16 WWZ components:

["DVA_FIN", "DVA_INT", "DVA_INTrex1", "DVA_INTrex2", "DVA_INTrex3", "RDV_FIN1", "RDV_FIN2", "RDV_INT", "DDC_FIN", "DDC_INT", "MVA_FIN", "OVA_FIN", "MVA_INT", "OVA_INT", "MDC", "ODC"].

agg (str, optional, default "")
Optional aggregation level passed directly to WWZ(io, agg).
It controls at which level the KWW components are reported:

- "" (default): origin country–sector × destination country.
- "ORI": by origin country.
- "DES": by destination country.
- "SEC": by origin sector.
- "ORI-SEC": by origin country–sector pair.

The exact meaning of agg is the same as in WWZ.

shares (bool, optional, default False)

- If False: the function returns levels – the KWW components in the same units as the underlying WWZ decomposition (typically monetary units).
- If True: the function returns shares in percent of each KWW component in total gross exports for each observation. In this case, the Tot column will be exactly 100 for every row.

---

**Details**

The function first calls:

WWZ_c = WWZ(io, agg)


to obtain the full WWZ decomposition, with rows representing origin–destination flows (or their aggregates, depending on agg) and columns representing the 16 WWZ terms.

It then maps the 16 WWZ components into the KWW-style groups using the following mapping:

Domestic value added:

  - "DVA_FIN" → "DVA_FIN"
  Domestic VA in final goods exports.
  - "DVA_INT" → "DVA_INT"
  Domestic VA in intermediate exports absorbed by the direct importer.
  - "DVA_INTrex1" → "DVA_INT"
  DVA in intermediates via direct importer to 3rd-country domestic use.
  - "DVA_INTrex2" → "DVA_INTrex"
  DVA in intermediates via direct importer to 3rd-country final exports.
  - "DVA_INTrex3" → "DVA_INTrex"
  DVA in intermediates via direct importer to 3rd-country intermediates.

Returned domestic value added:

  - "RDV_FIN1" → "RDV_FIN"
  Returned DVA in final imports from the direct importer.
  - "RDV_FIN2" → "RDV_FIN"
  Returned DVA in final imports via third countries.
  - "RDV_INT" → "RDV_INT"
  Returned DVA in intermediate imports used domestically.

Double-counted domestic content:

  - "DDC_FIN" → "DDC"
  Double-counted DVA in final exports.
  - "DDC_INT" → "DDC"
  Double-counted DVA in intermediate exports.

Foreign value added:

  - "MVA_FIN" → "FVA_FIN"
  Foreign VA in final goods exports (direct importer).
  - "OVA_FIN" → "FVA_FIN"
  “Other countries’” VA in final goods exports (via third countries).
  - "MVA_INT" → "FVA_INT"
  Foreign VA in intermediate exports (direct importer).
  - "OVA_INT" → "FVA_INT"
  “Other countries’” VA in intermediate exports.

Foreign double counting:

  - "MDC" → "FDC"
  Multilateral double-counting.
  - "ODC" → "FDC"

Other double-counting.

The 16 WWZ columns are grouped according to this mapping and summed, yielding 9 KWW-style components. The function then adds:

"Tot": the row-wise sum of all KWW components:

- If shares=False: Tot equals total gross exports (in levels).
- If shares=True: the KWW components are divided by Tot and multiplied by 100, so Tot = 100 for each row.

The final DataFrame keeps the same index as WWZ(io, agg) (e.g. origin–sector–destination or any aggregated level chosen via agg), but with fewer, more interpretable columns.

---

**Returns**

KWW_c (pandas.DataFrame)

DataFrame with the same index as WWZ(io, agg) and the following columns, in this order:

  - "DVA_FIN"
  Domestic value added in final goods exports.

  - "DVA_INT"
  Domestic value added in intermediate exports absorbed by the direct importer, including DVA_INT and DVA_INTrex1.

  - "DVA_INTrex"
  Domestic value added in intermediate exports that are re-exported (third-country use), combining DVA_INTrex2 and DVA_INTrex3.

  - "RDV_FIN"
  Returned domestic value added in final goods.

  - "RDV_INT"
  Returned domestic value added in intermediates.

  - "DDC"
  Double-counted domestic content (from DDC_FIN and DDC_INT).

  - "FVA_FIN"
  Foreign value added in final goods exports (direct and via other countries).

  - "FVA_INT"
  Foreign value added in intermediate exports.

  - "FDC"
  Foreign-related double-counting (multilateral and other).

  - "Tot"

Total over all KWW components:

  - If shares=False: total gross exports (levels).

  - If shares=True: Tot = 100 for every row (percent shares).

---

**Example**

```python
from intrade import load_TIVA, obj_IO, KWW

# 1. Load data and build IO object
tiva_dic = load_TIVA(dire="/path/to/ICIO/", year=2015, typ="extended")
wio = obj_IO(tiva_dic)

# 2. KWW-style decomposition at origin country–sector × destination country level (levels)
kww_levels = KWW(wio, agg="", shares=False)

# 3. KWW-style decomposition aggregated by origin country (shares)
kww_origin_shares = KWW(wio, agg="ORI", shares=True)

# 4. Inspect domestic vs foreign content in gross exports
kww_levels[["DVA_FIN", "DVA_INT", "FVA_FIN", "FVA_INT"]].head()
```

---