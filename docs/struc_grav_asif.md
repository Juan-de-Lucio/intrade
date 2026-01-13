<a id="struc_grav_asif"></a>
# struc_grav_asif

---


**Description**

“As-if” FTA counterfactual

`struc_grav_asif` is a wrapper around `struc_grav_cf` for scenarios where a
country (or group) is made to have the same trade cost treatment as
another group vis-à-vis a reference group (e.g. UK “as if” it were in the EU
for FTA purposes).

---

**Usage**

`struc_grav_asif(
    data,
    variables,
    countries1,
    countries2,
    countries3,
    ref_country,
    sigma=7.0,
    verbose=True,
)`


---

**Arguments**

Same as `struc_grav_incre`, but with an additional group `countries3` used to define the "benchmark" FTA treatment.

---

**Value**

Same structure as `struc_grav_incre` (country-level percentage changes).

---


**Example**

```python
# Example: UK treated "as if" it had the same FTA status as Norway vis-à-vis the EU

# Reference group (e.g. EU27)
EU = [
    "AUT","BEL","BGR","HRV","CYP","CZE","DNK","EST","FIN","FRA",
    "DEU","GRC","HUN","IRL","ITA","LVA","LTU","LUX","MLT","NLD",
    "POL","PRT","ROU","SVK","SVN","ESP","SWE"
]

# Benchmark FTA partner with the EU (e.g. Norway in the EEA)
EFTA_NOR = ["NOR"]

# Country (or group) we want to treat "as if" it had the same FTA treatment
UK = ["GBR"]

res_asif = struc_grav_asif(
    data=df,                               # bilateral trade + gravity covariates
    variables=["LN_DIST", "CNTG", "LANG", "BRDR"],
    countries1=EU,                         # reference group (EU)
    countries2=UK,                         # country to be treated "as if"
    countries3=EFTA_NOR,                  # benchmark FTA treatment (Norway–EU)
    ref_country="DEU",                     # reference importer for fixed effects
    sigma=7.0,
    verbose=True,
)

# 'res_asif' is a country-level summary with Export%, Real_Income%, etc.
print(res_asif)
```


---