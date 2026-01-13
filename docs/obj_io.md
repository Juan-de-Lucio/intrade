<a id="obj_io"></a>
# obj_IO

---

**Description**

Build a complete input–output (IO) object from a harmonised MRIO dictionary.

This function takes the output of the loader functions (`load_ADB`, `load_TIVA`, `load_EORA`, `load_FIGARO`, `load_GLORIA`, `load_WIOD`, `load_Test`, …), which provide a harmonised MRIO table and its dimensions, and constructs a set of NumPy arrays commonly used in IO-analysis and trade-in-value-added (TiVA) decompositions:

- **Intermediate use and coefficients**
  - `Z`, `Zd`, `Zm`  – intermediate input matrix and domestic/foreign splits.
  - `A`, `Ad`, `Am`  – technical coefficients matrix and domestic/foreign splits.
  - `B`, `Bd`, `Bm`  – global Leontief inverse and domestic/foreign splits.
  - `L`             – local/domestic Leontief inverse based on `Ad`.

- **Final demand**
  - `Y`             – final demand by destination country.
  - `Yd`, `Ym`      – domestic and foreign final demand.
  - `Yfd`           – detailed final demand (country × component).

- **Value added and output**
  - `VA`            – value added in levels.
  - `X`             – gross output.
  - `V`             – value-added coefficients vector.
  - `W`             – diagonal matrix of value-added coefficients.

- **Exports**
  - `EXGR`          – gross bilateral exports (intermediates + final).
  - `E`             – diagonal matrix of total exports by country–sector.
  - `Efd`           – exports of final goods.
  - `Eint`          – exports of intermediates.
  - `ESR`           – total exports (intermediate + final), by destination.

In addition, it returns two metadata dictionaries:
- `dims` with basic dimensions (`C`, `S`, `FD`, `CS`, `CFD`),
- `names` with country, sector and final-demand labels.

---

**Usage**

`obj_IO(dic)`

---

**Arguments**

- `dic` : `dict`
  Harmonised MRIO dictionary as returned by the loader functions, with at least:
  - `"df"`   : `pandas.DataFrame`
    Input–output table in harmonised format.
    Rows: country–sector (`CS = C × S`).
    Columns:
      1. All intermediate-use blocks (`CS` columns)
      2. All final demand columns (`CFD` columns)
      3. One total output column
      - `"C"`    : `int` – number of countries/regions.
      - `"S"`    : `int` – number of sectors per country.
      - `"FD"`   : `int` – number of final-demand categories per country.
      - `"CS"`   : `int` – `C × S`, total number of country–sector pairs.
      - `"CFD"`  : `int` – `C × FD`, total number of country–final-demand pairs.

---

**Details**

The function assumes that the MRIO dictionary has already been harmonised to a common layout:

- The **intermediate-use block** `Z` is taken as:
  - `Z = df.iloc[0:CS, 0:CS]` (shape `CS × CS`).
- The **detailed final demand** matrix `Yfd` is taken as:
  - `Yfd = df.iloc[0:CS, CS:CS+CFD]` (shape `CS × CFD`).

From this, the function:

1. **Builds domestic/foreign selectors**

   Using Kronecker products and ones matrices, it constructs:
   - `block_diag1_CSxCS` : block-diagonal selector (domestic links),
   - `block_diag0_CSxCS` : complement (foreign links),
   - `block_diag1_CSxC`  : domestic selector for `CS × C`,
   - `block_diag0_CSxC`  : foreign selector for `CS × C`.

2. **Extracts names and dimensions**

   From the column labels (e.g. `"USA_1"`, `"DEU_3"`), it recovers:
   - `c_names` : unique country codes (ISO3 or ISO3-like),
   - `s_names` : sector indices (usually `"1"`, `"2"`, …),
   - `cs_names`: full country–sector labels,
   - from `Yfd`, the final-demand labels `fd_names` and `cfd_names`.

3. **Computes value added and output**

   - `VA` is computed as total uses (intermediate + final demand) minus intermediate uses.
   - `X` is the row sum of the intermediate + final-demand block, i.e. gross output.

4. **Constructs intermediate matrices**

   - `Z` is converted to a NumPy array (`CS × CS`).
   - Domestic and foreign parts:
     - `Zd = Z * block_diag1_CSxCS`
     - `Zm = Z * block_diag0_CSxCS`

5. **Technical coefficients and Leontief inverses**

   - Builds `x_hat_inv = pinv(diag(X))` to handle zero outputs.
   - Technical coefficients:
     - `A = Z @ x_hat_inv`
     - `Ad = A * block_diag1_CSxCS`
     - `Am = A * block_diag0_CSxCS`
   - Leontief inverses:
     - `L  = (I - Ad)^{-1}` (local/domestic)
     - `B  = (I - A)^{-1}`  (global)
     - `Bd = B * block_diag1_CSxCS`
     - `Bm = B * block_diag0_CSxCS`

6. **Final demand by country**

   - Aggregates `Yfd` by destination country, using the country code in the column labels:
     - `Y` is `CS × C`, with column order matching `c_names`.
   - Domestic and foreign splits:
     - `Yd = Y * block_diag1_CSxC`
     - `Ym = Y * block_diag0_CSxC`

7. **Value-added coefficients**

   - Computes WWZ-style value-added coefficients:
     - `V = [1' (I - A)]'` (shape `CS × 1`), cleaned of NaNs.
   - Builds the diagonal matrix:
     - `W = diag(V)`.

8. **Gross bilateral exports**

   - Loops over country blocks to build:
     - `Zm_meld` (shape `CS × C`): foreign intermediate exports by origin sector and destination country.
   - Gross bilateral exports:
     - `EXGR = Zm_meld + Ym`  (intermediate + final exports).
   - Total exports by country–sector:
     - `E = diag(EXGR.sum(axis=1))`.

9. **Export decomposition: final vs intermediate**

   - Stacks `[Z | Y]` horizontally into `z` (shape `CS × (CS + C)`).
   - For each destination country:
     - `Efd` collects exports of final goods,
     - `Eint` collects exports of intermediates,
     - `ESR = Efd + Eint` is total exports.

10. **Metadata**

    Finally, it stores:
    - `dims = {"C", "S", "FD", "CS", "CFD}`,
    - `names = {"c_names", "s_names", "fd_names", "cs_names", "cfd_names"}`.

All arrays are NumPy `ndarray` objects; labels and dimensions are preserved in the `names` and `dims` dictionaries, respectively.

---

**Returns**

- `io_dic` : `dict`
  A dictionary with IO-related matrices and metadata:

  - Intermediate use and coefficients:
    - `"Z"`   : `ndarray` (`CS × CS`) – intermediate inputs.
    - `"Zd"`  : `ndarray` (`CS × CS`) – domestic intermediate inputs.
    - `"Zm"`  : `ndarray` (`CS × CS`) – foreign intermediate inputs.
    - `"A"`   : `ndarray` (`CS × CS`) – technical coefficients.
    - `"Ad"`  : `ndarray` (`CS × CS`) – domestic coefficients.
    - `"Am"`  : `ndarray` (`CS × CS`) – foreign coefficients.
    - `"B"`   : `ndarray` (`CS × CS`) – global Leontief inverse.
    - `"Bd"`  : `ndarray` (`CS × CS`) – domestic part of `B`.
    - `"Bm"`  : `ndarray` (`CS × CS`) – foreign part of `B`.
    - `"L"`   : `ndarray` (`CS × CS`) – domestic Leontief inverse (`Ad`).

  - Final demand:
    - `"Y"`   : `ndarray` (`CS × C`)       – final demand by destination country.
    - `"Yd"`  : `ndarray` (`CS × C`)       – domestic part of final demand.
    - `"Ym"`  : `ndarray` (`CS × C`)       – foreign part of final demand.
    - `"Yfd"` : `ndarray` (`CS × CFD`)     – detailed final demand by component.

  - Value added and output:
    - `"VA"`  : `ndarray` (`CS × 1`)       – value added in levels.
    - `"V"`   : `ndarray` (`CS × 1`)       – value-added coefficients.
    - `"W"`   : `ndarray` (`CS × CS`)      – diagonal matrix of `V`.
    - `"X"`   : `ndarray` (`CS × 1`)       – gross output.

  - Exports:
    - `"EXGR"`: `ndarray` (`CS × C`)       – gross bilateral exports.
    - `"E"`   : `ndarray` (`CS × CS`)      – diagonal total exports (`Ē`).
    - `"Efd"` : `ndarray` (`CS × C`)       – exports of final goods.
    - `"Eint"`: `ndarray` (`CS × C`)       – exports of intermediates.
    - `"ESR"` : `ndarray` (`CS × C`)       – total exports (intermediate + final).

  - Metadata:
    - `"dims"`  : `dict` with keys `"C"`, `"S"`, `"FD"`, `"CS"`, `"CFD"`.
    - `"names"` : `dict` with keys `"c_names"`, `"s_names"`, `"fd_names"`, `"cs_names"`, `"cfd_names"`.

---

**Example**

```python
import pandas as pd
from intrade import load_TIVA, obj_IO   # example import

# 1. Load and harmonise an ICIO/TiVA table (e.g. OECD ICIO extended 2018)
tiva_dic = load_TIVA(dire="path/to/ICIO/raw/", year=2018, typ="extended")

# `tiva_dic` contains:
#   - "df": harmonised IO DataFrame
#   - "C", "S", "FD", "CS", "CFD": dimensions

# 2. Build the full IO object
io_dic = obj_IO(tiva_dic)

# 3. Access standard matrices for further analysis
Z   = io_dic["Z"]     # intermediate inputs
A   = io_dic["A"]     # technical coefficients
B   = io_dic["B"]     # Leontief inverse
Y   = io_dic["Y"]     # final demand by country
EXGR = io_dic["EXGR"] # gross bilateral exports
V   = io_dic["V"]     # value-added coefficients

# 4. Use dimensions and labels
C    = io_dic["dims"]["C"]
S    = io_dic["dims"]["S"]
cids = io_dic["names"]["c_names"]
sids = io_dic["names"]["s_names"]

```

---