<a id="struc_grav_inout"></a>
# struc_grav_inout

Counterfactual: entry or exit from a regional trade agreement (RTA)

---

**Description**

struc_grav_inout is a wrapper around struc_grav_cf for the scenario:

One country enters or exits a regional trade agreement (RTA) formed by
a group of countries (countries1).

---

**Usage**

`struc_grav_inout(
    data,
    variables,
    countries1,
    countries2,
    ref_country,
    sigma=7.0,
    verbose=True)`

---

**Arguments**

`countries1` (list[str])
: List of RTA member countries in the baseline.

`countries2` (list[str])
: List containing the country that enters or exits.

Other arguments as in `struc_grav_incre`.

---

**Value**

Same as `struc_grav_incre`.

---


**Example**

```python
# Example: Turkey enters an RTA currently formed by EU countries

# Baseline RTA members (e.g. EU27 in the data)
EU_RTA = [
    "AUT","BEL","BGR","HRV","CYP","CZE","DNK","EST","FIN","FRA",
    "DEU","GRC","HUN","IRL","ITA","LVA","LTU","LUX","MLT","NLD",
    "POL","PRT","ROU","SVK","SVN","ESP","SWE"
]

# Country that enters or exits the RTA
TURKEY = ["TUR"]

res_inout = struc_grav_inout(
    data=df,                               # bilateral trade + gravity covariates
    variables=["LN_DIST", "CNTG", "LANG", "BRDR"],
    countries1=EU_RTA,                     # current RTA members in the baseline
    countries2=TURKEY,                     # country that joins or leaves the RTA
    ref_country="DEU",                     # reference importer for fixed effects
    sigma=7.0,
    verbose=True,
)

# Interpretation:
# - If "TUR" is NOT in EU_RTA, this scenario is "Turkey joins the RTA".
# - If "TUR" IS already in EU_RTA, this scenario is "Turkey exits the RTA".

print(res_inout.head())
```

---