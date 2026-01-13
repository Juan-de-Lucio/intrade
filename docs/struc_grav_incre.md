<a id="struc_grav_incre"></a>
# struc_grav_incre

---


**Description**

Counterfactual: trade cost increase between country groups.

`struc_grav_incre` is a wrapper around `struc_grav_cf` for the scenario: One group of countries (countries1) increases its bilateral trade costs
with another group (countries2) by a given percentage (increase).

It estimates a structural gravity model (PPML), reconstructs the baseline, and solves the general equilibrium counterfactual using exact-hat algebra.

---

**Usage**

`struc_grav_incre(
    data,
    variables,
    countries1,
    countries2,
    ref_country,
    increase,
    sigma=7.0,
    verbose=True,
)`

---

**Arguments**

- `data` (DataFrame)
: Bilateral trade data with gravity covariates (see `struc_grav_cf`).

- `variables` (list[str])
: Names of baseline gravity covariates included in the PPML (e.g., `['LN_DIST', 'CNTG', 'LANG', 'BRDR']`).

- `countries1`, `countries2` (list[str])
: Lists of country codes defining the two groups whose bilateral trade costs are changed.

- `ref_country` (str)
: Reference importer for fixed effects.

- `increase` (float)
: Percentage increase in trade costs between `countries1` and `countries2`.

- `sigma` (float, default 7.0)
: Elasticity of substitution.

- `verbose` (bool, default True)
: Print estimation output and consistency checks.

---

**Value**

A DataFrame with one row per country and columns:

- `"Country"`
- `"Export%"`
- `"Real_Income%"`
- `"Output%"`
- `"Cons_Price%"`

representing percentage changes between baseline and counterfactual.

---

**Example**

```python
EU = ["AUT","BEL","DEU","ESP", ...]  # list of EU codes

res_incre = struc_grav_incre(
    data=df,
    variables=['LN_DIST', 'CNTG', 'LANG', 'BRDR'],
    countries1=['GBR'],
    countries2=EU,
    ref_country='DEU',
    increase=10.0,
    sigma=7.0,
)
```

---