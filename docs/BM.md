<a id="BM"></a>
# BM

---

**Description**

Borin & Mancini (2023) VA export decomposition from a WIO dictionary. `BM` computes a Borin & Mancini (2023) decomposition of exports
into Domestic Value Added (DVA), Foreign Value Added (FVA), and detailed intermediate channels, starting from a **WIO dictionary** built from an
MRIO table.

It reproduces, in Python, the logic of an MRIO-based decomposition as in Borin & Mancini (2023), but using the matrix objects already contained in `wio`.

---

**Usage**

`BM(wio)`

---

**Arguments**

- `wio` (dict): A dictionary containing the main input–output matrices and vectors, with keys:

  **Matrices** (shape CS × CS unless stated otherwise):

  - `"Z"`, `"Zd"`, `"Zm"`: intermediate input matrices
  - `"A"`, `"Ad"`, `"Am"`: technical coefficient matrices
  - `"B"`, `"Bd"`, `"Bm"`: Leontief inverse matrices
  - `"Ld"`: local (domestic) Leontief inverse
  - `"Yfd"`: final demand with components (CS × CFD)
  - `"Y"`, `"Yd"`, `"Ym"`: final demand (total / domestic / foreign), shape CS × C
  - `"W"`: diagonalised value-added coefficients matrix (CS × CS)
  - `"E"`: diagonalised gross exports (CS × CS)

  **Vectors**:

  - `"VA"`: value added (CS × 1)
  - `"V"`: value added coefficients (CS × 1)
  - `"X"`: gross output (CS × 1)
  - `"EXGR"`: gross bilateral exports (CS × C)

  **Meta information**:

  - `"dims"`: dictionary with at least `"C"`, `"S"`, `"CS"`
  - `"names"`: dictionary with country and sector labels

---

**Details**


The function:

1. Extracts `C`, `S`, `CS` from `wio["dims"]`.
2. Wraps key matrices (`Z`, `A`, `B`, `Y`) into a lightweight class to operate with country-level sub-blocks (or uses plain numpy arrays with equivalent logic).
3. Reconstructs the Borin & Mancini (2023) decomposition of exports into:
   - `DAVAX1`, `DAVAX2`: domestic VA embodied in gross exports, different channels.
   - `REX1`, `REX2`, `REX3`, `REF1`, `REF2`: re-export and re-import channels.
   - `FVA`: foreign value added in exports.
   - `PDC1`, `PDC2`: (partial) double counting components.
4. Returns two DataFrames:
   - `ed_es`: decomposition by exporting sectors.
   - `ed_os`: decomposition by origin sectors.

Each DataFrame contains columns for each exporter `s`, importer `r`, and sector `i`:

- `s`: exporter country index
- `r`: partner country index ($\neq$ s)
- `breakdown`: "es" or "os"
- `i`: sector index of the exporter (or origin)
- `exports`: gross exports for that triplet
- `davax1`, `davax2`, `rex1`, `rex2`, `rex3`, `ref1`, `ref2`, `fva`, `pdc1`, `pdc2`: decomposition components

**Value**

- `ed_es` (pandas.DataFrame): Decomposition by exporting sectors.
- `ed_os` (pandas.DataFrame): Decomposition by origin sectors.

Each row corresponds to a (exporter, importer, sector) combination and contains a detailed decomposition of gross exports.

---


**Example**

```python
from intrade import BM, build_wio_from_raw  # hypothetical

wio = build_wio_from_raw(Z, Y, VA, country_names, sector_names)
ed_es, ed_os = BM(wio)

# Aggregate DVA and FVA by exporter
dva_by_exp = ed_es.groupby("s")[["davax1", "davax2"]].sum()
fva_by_exp = ed_es.groupby("s")[["fva"]].sum()
```

---