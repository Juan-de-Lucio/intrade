<a id="grav_panel"></a>
# grav_panel

---


**Description**

Panel gravity estimation with flexible fixed effects (PPML). `grav_panel` estimates a panel gravity model using PPML (statsmodels.GLM
with Poisson family) and flexible combinations of fixed effects:

* Exporter (e)
* Importer (i)
* Border-year (y)
* Exporter-year (ey)
* Importer-year (iy)
* Exporter-importer pair (ei)

It is designed for large bilateral panel datasets and returns the fitted
model plus a cleaned regressor matrix and FE information.

---

**Usage**

`grav_panel(data: pd.DataFrame, fe: Iterable[str], ref_country: Union[str, None] = None, verbose: bool = True)`

---

**Arguments**

`data` (pandas.DataFrame)
: Bilateral panel trade data in long format, with at least:
  - `exporter`: exporter country code
  - `importer`: importer country code
  - `year`: time identifier
  - `trade`: bilateral trade flow $X_{ijt}$

`fe` (iterable of str)
: Codes indicating which fixed effects to include:
  - `'e'`: exporter FE
  - `'i'`: importer FE
  - `'y'`: time–border FE
  - `'ey'`: exporter-year FE
  - `'iy'`: importer-year FE
  - `'ei'`: exporter-importer FE

`ref_country` (str or None, default None)
: Reference country whose FEs are dropped to avoid collinearity. If None, one exporter is randomly selected.

`verbose` (bool, default True)
: If True, prints basic information and the PPML summary.

---

**Details**

The function:

1. Checks required columns: `"exporter"`, `"importer"`, `"year"`, `"trade"`.
2. Constructs border dummy `BRDR` (1 for international, 0 for domestic).
3. Computes exporter output and importer expndr (total exports and imports).
4. Builds the requested dummy matrices for FEs using `pandas.get_dummies`.
5. Drops redundant columns involving the reference country and, if present, the baseline `BRDR_y_fe_0`.
6. Estimates: $$E[X_{ijt}] = \exp(X_{ijt}\beta)$$ via PPML with robust (HC3) covariance.

---

**Value**

A dictionary with:

- `"results"`: statsmodels GLMResults object
- `"params"`: DataFrame with `beta_hat`, `std_err`, `p_value`
- `"data"`: original data with added FE dummies and constructed variables
- `"X"`: final regressor matrix used in estimation
- `"y"`: dependent variable (trade)
- `"ref_country"`: reference country actually used
- `"fe"`: set of FE codes used
- `"n_fe"`: number of FE dummies included in X

---


**Example**

```python

from intrade import grav_panel

out = grav_panel(
    data=df_panel,
    fe=['ey', 'iy'],
    ref_country='USA',
    verbose=True,
)

print(out["results"].summary())
coef_table = out["params"]

out = grav_panel(
    data,
    fe=['ey', 'iy'],
    ref_country=None,
    verbose=True,
)
```

---