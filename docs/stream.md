<a id="stream"></a>
# stream

---

**Description**

Computes upstream and downstream indices for each country–sector in a world input–output (WIO) table.

The function uses the foreign-use technical coefficients matrix and gross output to quantify:

how downstream a country–sector is in the global value chain (how many further production stages it feeds into), and

how upstream it is (how many upstream stages are embodied in its own production).

These indices are based on Leontief-type formulas of the form: $$(I - A)^{-1}\,\mathbf{1}$$

applied to the foreign part of the technical coefficients.

---

**Usage**

`stream(wio)`

---

**Arguments**

- wio (dict)
Input–output object, typically created by obj_IO, with at least:

- wio["Am"] : np.ndarray of shape (CS, CS)
Foreign-use technical coefficients matrix (off-diagonal part of A).

- wio["X"] : np.ndarray of length CS
Gross output by country–sector (levels).

- wio["dims"]["CS"] : int
Total number of country–sector combinations (CS = C × S).

- wio["names"]["cs_names"] : array-like of length CS
Labels for country–sector rows/columns, e.g. "USA_1", "DEU_3", …

---

**Details**

For each country–sector (indexed 1,…,CS), the function constructs two scalar indices:

1. **Downstream** index (down)

Defined as:

$$
\text{down}
\;=\;
\bigl(I - A_m^{\top}\bigr)^{-1}\,\mathbf{1},
$$

where:

- $A_m$
 is the foreign-use technical coefficients matrix (Am),
- $A_m^{\top}$ is its transpose,
- $I$ is the identity matrix of size CS × CS,
- $1$ is a CS × 1 vector of ones.

-Intuition-: this measures how much further production (downstream uses) is triggered by one extra unit across the whole system via foreign linkages.

2. **Upstream** index (up)

First builds a scaled version of $A_m^\top$  using output X:

- Let X be the gross output vector (length CS).

- A row-normalised variant of $A_m^\top$  is constructed as:

$$
A_{\text{scaled}} \;=\; \frac{\bigl(A_m^\top \odot X\bigr)^\top}{X + \varepsilon},
$$

where a small $\varepsilon$ = 1e-10 avoids division by zero and any resulting NaNs are replaced by zero.

The upstream index is then:

$$\text{up} = (I - A_{\text{scaled}})^{-1}\,\mathbf{1}$$

Intuition: this captures how many upstream stages (foreign-sourced links) are embodied in the production of each country–sector, after normalising by its own scale of output.

Computation steps:

1. Extract Am, X, CS and cs_names from wio and perform basic shape checks.

2. Build the identity matrix I of size CS × CS.

3. Compute the downstream index: result_down = solve(I - Am.T, 1).

4. Construct a scaled version of Am.T using X, remove any NaNs, and compute the upstream index:
result_up = solve(I - A_transposed_scaled, 1).

5. Wrap the results into a pandas.DataFrame with index cs_names and columns "up" and "down".

---

**Returns**

result (pandas.DataFrame)

A DataFrame with one row per country–sector and two columns:

Index:
  - cs_names (e.g. "USA_1", "DEU_5", "CHN_12", …).

Columns:

  - "up"
  Upstream stream index for each country–sector (higher values indicate a more upstream position through foreign linkages).

  - "down"
  Downstream stream index for each country–sector (higher values indicate a more downstream position, feeding many additional stages).

---

**Example**

```python
import numpy as np
import pandas as pd
from intrade import load_TIVA, obj_IO, stream

# 1. Load an ICIO/TiVA table and build the IO object
tiva_dic = load_TIVA(dire="/path/to/ICIO/", year=2015, typ="extended")
wio = obj_IO(tiva_dic)

# 2. Compute upstream and downstream indices
sd = stream(wio)

# 3. Inspect a few country–sectors
print(sd.head())

# 4. Example: sort sectors by downstreamness in Germany
sd_DEU = sd[sd.index.str.startswith("DEU_")].sort_values("down", ascending=False)
print(sd_DEU.head())
```

---

<hr style="border:1px solid blue; margin-top: 0; margin-bottom: 0;">


<div id="" style="font-size:50px; text-align:center; padding:10px 0; margin:0;">
</div>