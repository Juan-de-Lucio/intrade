<a id="WWZ"></a>
# WWZ

---

**Description**

Computes the Wang–Wei–Zhu (2013) value-added trade decomposition from a harmonised input–output object.
Given an IO object created by obj_IO, this function decomposes gross exports into 16 value-added and double-counting components at the origin country–sector × destination country level, with optional aggregation by origin, destination, or sector.

---

**Usage**

`WWZ(wio, agg: str = "")`

---

**Arguments**

wio (dict)
  IO object as returned by obj_IO, containing at least:

  - wio["Z"], wio["Zd"], wio["Zm"]: intermediate inputs (total / domestic / foreign)
  - wio["A"], wio["Ad"], wio["Am"]: technical coefficients (total / domestic / foreign)
  - wio["B"], wio["Bd"], wio["Bm"]: Leontief inverse (total / domestic / foreign)
  - wio["Y"], wio["Yd"], wio["Ym"]: final demand (total / domestic / foreign)
  - wio["L"]: local (domestic) Leontief inverse
  - wio["Yfd"]: full final demand by country–component
  - wio["VA"], wio["V"], wio["W"]: value added in levels, VA coefficients, and diagonal VA matrix
  - wio["X"], wio["EXGR"], wio["E"]: gross output, gross bilateral exports, and diagonal total exports
  - wio["dims"]: dictionary with dimensions {"C","S","FD","CS","CFD"}
  - wio["names"]: dictionary with name vectors ("c_names", "s_names", "fd_names", "cs_names", "cfd_names")

agg (str, optional)

Aggregation level for the decomposition. One of:

  - "" (default): no aggregation. Output is at
  origin country–sector × destination country level, with index
  "<origin_country>_<origin_sector>_<destination_country>".
  - "ORI": aggregate all components by origin country.
  Index becomes 3-letter ISO origin country codes.
  - "DES": aggregate all components by destination country.
  Index becomes 3-letter ISO destination country codes.
  - "SEC": aggregate all components by origin sector across all countries and destinations.
  Index becomes the sector identifier (middle token in the original index).
  - "ORI-SEC": aggregate by origin country–sector (collapsing destination).
  Index becomes "<origin_country>_<origin_sector>".

---

**Details**

The function implements the Wang–Wei–Zhu (2018) decomposition of gross exports into 16 components that distinguish:

  - Domestic value added in exports of final and intermediate goods,
  - Domestic value added that returns home (RDV),
  - Double-counted domestic value added (DDC),
  - Foreign and “other” countries’ value added in exports (MVA, OVA),
  - Multilateral and other double-counting terms.

Internally, WWZ:

1- Checks that all required matrices and metadata are present in wio and that CS = C × S.

2- Constructs country–sector block masks to separate domestic vs foreign flows.

3- Computes the 16 WWZ components using combinations of:

- domestic and foreign parts of the Leontief inverse,
- domestic and foreign technical coefficients,
- domestic and foreign final demand,
- value-added coefficients and gross output.

4- Stores all components in a 3-dimensional array
(origin country–sector, destination country, 16 components).

5- Converts this array into a labeled DataFrame with one row per
origin country–sector × destination country combination.

6- Optionally aggregates over origin countries, destination countries, sectors, or origin country–sector pairs depending on agg.

Term labels follow Table A2 in Wang, Wei and Zhu (2018), and the overall notation is close to Quast & Kummritz (2015, decompr package).

---

**Returns**

WWZ_df (pandas.DataFrame)

A DataFrame with 16 WWZ components for each observation.

Index:

  - If agg == "": "<origin_country>_<origin_sector>_<destination_country>".
  - If agg == "ORI": origin country ISO3 codes.
  - If agg == "DES": destination country ISO3 codes.
  - If agg == "SEC": sector identifiers.
  - If agg == "ORI-SEC": "<origin_country>_<origin_sector>".

Columns (always the same 16 components):

  - "DVA_FIN": Domestic VA in final goods exports
  - "DVA_INT": Domestic VA in intermediates absorbed by direct importer
  - "DVA_INTrex1": DVA in intermediates → direct importer → 3rd-country domestic final use
  - "DVA_INTrex2": DVA in intermediates → direct importer → final exports to 3rd countries
  - "DVA_INTrex3": DVA in intermediates → direct importer → intermediates to 3rd countries
  - "RDV_FIN1": Returned DVA in final imports from direct importer
  - "RDV_FIN2": Returned DVA in final imports via 3rd countries
  - "RDV_INT": Returned DVA in intermediate imports used domestically
  - "DDC_FIN": Double-counted DVA used in producing final exports
  - "DDC_INT": Double-counted DVA used in producing intermediate exports
  - "MVA_FIN": Foreign VA in final goods exports (direct importer)
  - "OVA_FIN": Other countries’ VA in final goods exports (via others)
  - "MVA_INT": Foreign VA in intermediate exports (direct importer)
  - "OVA_INT": Other countries’ VA in intermediate exports
  - "MDC": Multilateral double-counting
  - "ODC": Other double-counting


---

**Example**

```python

from intrade import load_TIVA, obj_IO, WWZ

# 1. Load a TiVA/ICIO table
tiva_dic = load_TIVA(dire="/path/to/ICIO/", year=2015, typ="extended")

# 2. Build the IO object with all required matrices
wio = obj_IO(tiva_dic)

# 3. Full WWZ decomposition at origin country–sector × destination country level
wwz_full = WWZ(wio)

# 4. Aggregate WWZ components by origin country
wwz_by_origin = WWZ(wio, agg="ORI")

# 5. Aggregate by origin sector
wwz_by_sector = WWZ(wio, agg="SEC")
```


---