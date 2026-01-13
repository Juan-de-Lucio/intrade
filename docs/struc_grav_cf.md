<a id="struc_grav_cf"></a>
# struc_grav_cf

---

**Description**

struc_grav_cf estimates a structural gravity model with PPML and performs a general-equilibrium counterfactual analysis using exact hat algebra.

The function:

1. Estimates a baseline PPML gravity equation with exporter and importer fixed effects and standard gravity covariates.

2. Reconstructs baseline bilateral trade and multilateral resistance terms.

3. Builds a counterfactual trade-cost matrix depending on the scenario (selection).

4. Solves the general-equilibrium counterfactual system using an external solver (solve_system_Ti).

5. Returns country-level percentage changes in exports, real income, output and consumption prices.

It is designed to implement counterfactual exercises such as increases in bilateral trade costs, “as if” FTA scenarios, or changes in RTA membership.

---

**Usage**

`struc_grav_cf(data: pd.DataFrame, variables: list[str], countries1: list[str], countries2: list[str], countries3: list[str], ref_country: str, increase: float = 0.0, selection: int = 1, sigma: float = 7.0, verbose: bool = True,)`

---

**Arguments**


- data (pandas.DataFrame)
Bilateral trade dataset in long format. Must contain at least the following columns:

  - exporter – exporter country code (e.g. ISO3).

  - importer – importer country code.

  - trade – bilateral exports from exporter to importer.
  It must also include all gravity covariates listed in variables (e.g. distance, contiguity, common language, border).

- variables (list[str])
List of baseline gravity covariates to be included linearly in the PPML regression.
Typical example: ['LN_DIST', 'CNTG', 'LANG', 'BRDR']


Additional dummies for the counterfactual scenario are constructed internally and appended to this list.

- countries1 (list[str])
First group of countries used to define the counterfactual:

  - For selection = 1: countries whose trade costs increase against countries2.

  - For selection = 2: reference group in the “as if” FTA scenario.

  - For selection = 3: base RTA membership group.

- countries2 (list[str])
Second group of countries used for the counterfactual:

  - For selection = 1: partner group against which trade costs for countries1 increase.

  - For selection = 2: first comparison group in the “as if” FTA scenario.

  - For selection = 3: the country potentially entering or exiting the RTA (only countries2[0] is used).

- countries3 (list[str])
Third group of countries, only used when selection = 2:

  - For selection = 2: second comparison group in the “as if” FTA scenario.

  - Ignored for selection = 1 and selection = 3.

- ref_country (str)
Reference importer for importer fixed effects.
The dummy imp_fe_ref_country is dropped from the regression to avoid collinearity.
Must match one of the country codes appearing in importer.

- increase (float, default 0.0)
Percentage increase in trade costs for the special bilateral relations defined by (countries1, countries2) when selection = 1.
Ignored for selection = 2 and selection = 3.

- selection (int, default 1)
Type of counterfactual experiment:

  - 1 – Trade-cost increase between countries1 and countries2.
  A special dummy BRDR_{len(countries1)}{countries2[0]} is created and its coefficient is scaled by (1 + increase/100) in the counterfactual.

  - 2 – “As if” FTA scenario.
  Two dummies are created:

      sh_{countries2[0]}_FTA

      sh_{countries3[0]}_FTA
      to mimic different FTA treatment of countries2 and countries3 vis-à-vis countries1.

  - 3 – RTA entry/exit.
  An RTA dummy is defined among countries1 (excluding domestic flows) and copied to FTA. Then countries2[0] is made to enter or exit this RTA in the counterfactual.

- sigma (float, default 7.0)
Elasticity of substitution in the CES demand structure.
It affects the exact-hat algebra and the construction of the trade-cost ratio matrix (T_cf / T_bsln)^(1/(1 - sigma)).

- verbose (bool, default True)
If True, prints:

  - PPML regression summary,

  - basic checks for equality between observed and predicted total trade,

  - equilibrium consistency checks for the counterfactual (q_c, E_c, etc.),

  - and the final country-level summary.

---

**Details**

The function proceeds in several steps:

1. Input checks

2. Works on a copy of data (the original DataFrame is not modified).

3. Verifies that all countries listed in countries1, countries2, countries3 appear in at least one of exporter or importer.
If any code is missing, a ValueError is raised listing the missing countries.

4. Baseline variables and fixed effects

5. Constructs a border dummy BRDR (1 = international, 0 = domestic).

6. Computes:

- output – total exports by country: sum(trade) over exporter.

- expndr – total expenditure by country: sum(trade) over importer.

7. Creates exporter and importer fixed effects using dummy variables:

- exp_fe_XXX for each exporter.

- imp_fe_XXX for each importer.

8. Computes an additional parameter phi only for intra-national flows:

- phi = expndr / output


for pairs where exporter == importer.

- Scenario-specific dummies (selection)

selection = 1
  Defines:
  - BRDR_{len(countries1)}{countries2[0]} equal to 1 when trade is between countries1 and countries2 (in either direction).
  This dummy is then subtracted from the common border dummy BRDR so that its effect is captured separately.

selection = 2 (“as if” FTA scenario)
  Defines:

  - sh_{countries2[0]}_FTA = 1 if trade between countries1 and countries2,

  - sh_{countries3[0]}_FTA = 1 if trade between countries1 and countries3.

  - Both dummies are subtracted from BRDR to avoid double counting.

selection = 3 (RTA entry/exit)

  - Constructs RTA = 1 for international flows within countries1.

  - Sets FTA = RTA.

  -In the counterfactual, countries2[0] is either added to or removed from the RTA membership when building the NRTA dummy.

In all cases, the list columns_names combines the baseline variables in variables with the additional scenario-specific dummies that enter the PPML equation.

9. PPML estimation

    Selects all exporter FE dummies (^exp_fe_) and all importer FE dummies (^imp_fe_), dropping the importer FE for ref_country.

  Builds the regressor matrix:

    X = data[columns_names + exp_fe_cols + imp_fe_cols]
    y = data["trade"]


  Estimates a Poisson GLM with robust (HC3) standard errors:

    model = sm.GLM(y, X, family=sm.families.Poisson())
    results = model.fit(cov_type="HC3")


10. Baseline reconstruction (BLN)

    Multiplies each exporter FE dummy exp_fe_i by exp($\beta$_exp_fe_i) and each importer FE dummy imp_fe_j (except ref_country) by exp($\beta$_imp_fe_j).

  Sums all exporter FEs and importer FEs:

    all_exp_fes_0 = sum(exp_fe_*)
    all_imp_fes_0 = sum(imp_fe_*)


  Reconstructs bilateral trade-cost indices in levels:

    t_ij_BLN = exp( $\sum$ $\beta$_k * X_k )


  over all covariates in columns_names.

  Sets:

    output_BLN = output
    expndr_BLN = expndr


  Chooses expndr_ref as the mean expenditure of the reference importer (ref_country), and constructs outward and inward multilateral resistances:

    omr_BLN = output_BLN * expndr_ref / all_exp_fes_0
    imr_BLN = expndr_BLN / (all_imp_fes_0 * expndr_ref)


  Predicted baseline trade is:

    trade_BLN = output_BLN * expndr_BLN * t_ij_BLN / (imr_BLN * omr_BLN)


When verbose=True, it checks that the sum of observed and predicted trade differ by less than 0.1% and prints a warning otherwise.

Counterfactual trade costs
Depending on selection, the counterfactual trade-cost matrix t_ij_CFL is constructed as:

Selection 1 (trade-cost increase):

```python
# special is the scenario dummy (last in columns_names)


        t_ij_CFL = np.exp(
            sum(
                params.loc[var, "beta_hat"] * data[var]
                for var in columns_names[:-1]
            )
            + (1 + increase / 100.0)
            * params.loc[special, "beta_hat"]
            * data[special]
        )
```

Selection 2 (“as if” FTA):
the coefficient for sh_{countries3[0]}_FTA is used and applied to both FTA dummies.

Selection 3 (RTA entry/exit):
RTA membership is modified via NRTA, and:

```python
        t_ij_CFL = np.exp(
            sum(params.loc[var, "beta_hat"] * data[var] for var in variables)
            + params.loc["FTA", "beta_hat"] * data["FTA"]
            + params.loc["RTA", "beta_hat"] * data["NRTA"]
        )
```

The ratio matrix used in the exact-hat algebra is:

```python
T_ratio = (T_cf / T_bsln) ** (1 / (1 - sigma))
```

11. Exact hat algebra solution

    Constructs:

    trade_BLN_mat (n×n): matrix of baseline bilateral trade (exporter × importer).

    T_bsln and T_cf: baseline and counterfactual trade costs as (n×n).

    Computes:

      q   = row sums of trade_BLN_mat  # exports + domestic
      phi = column sums / q
      TI  = (phi - 1) * q              # trade imbalance
      E   = q + TI
      pi  = trade_BLN_mat / (1 $\otimes$ E')   # expenditure shares


    Solves the system for the vector of “hats” x using an external function:

    ```python
    sol = optimize.root(
        solve_system_Ti,
        x0,  # typically ones
        args=(T_ratio, q, TI, pi, sigma),
        method="df-sane",
    )
    x = sol.x
    ```

From x, obtains:
  - hat_Y – output hats,
  - hat_p – price hats,
  - hat_PInd – counterfactual price indices,
  - hat_pi – counterfactual expenditure shares,
  - trade_c – counterfactual bilateral trade matrix.

Basic consistency checks (check_q_c, check_E_c, check_WTI) are printed when verbose=True.

Percentage changes and output

Baseline and counterfactual aggregates:

export_bsln and export_c – aggregate exports by country.

Country-level percentage changes:

  - x_per      = (x - 1) * 100
  - exp_per    = (export_c / export_bsln - 1) * 100
  - PInd_per   = (hat_PInd ** (1 / (1 - sigma)) - 1) * 100
  - welfare_direct = (hat_Y / hat_PInd ** (1 / (1 - sigma)) - 1) * 100


trade_c is reshaped back into a long DataFrame trade_FLL and merged with data for possible further analysis.

---


**Returns**

- summary (pandas.DataFrame)
A country-level summary with one row per exporter country and the following columns:

  - Country – country code (same ordering as exporters in the original data).

  - Export% – percentage change in total exports (counterfactual vs. baseline).

  - Real_Income% – percentage change in real income (direct welfare measure).

  - Output% – percentage change in output.

  - Cons_Price% – percentage change in the consumption price index.

Internally (within the function), the bilateral counterfactual trade flows are also merged back into the data DataFrame under the column trade_FLL, but this enriched DataFrame is not returned unless you modify the function to do so.

---

**Example**

```python
import pandas as pd
from intrade.grav import struc_grav_cf  # adjust to your package structure

# Example: EU–UK trade-cost increase of 10%

# 1. Load or construct a bilateral trade dataset
# Required columns: exporter, importer, trade, LN_DIST, CNTG, LANG, BRDR, ...
data = pd.read_csv("bilateral_trade_example.csv")

# 2. Define baseline covariates and country groups
variables = ["LN_DIST", "CNTG", "LANG", "BRDR"]

EU = ["AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN",
      "FRA", "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX",
      "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE"]

countries1 = EU
countries2 = ["GBR"]
countries3 = []          # not used for selection = 1
ref_country = "DEU"      # importer FE reference

# 3. Run the structural gravity + counterfactual analysis
summary = struc_grav_cf(
    data=data,
    variables=variables,
    countries1=countries1,
    countries2=countries2,
    countries3=countries3,
    ref_country=ref_country,
    increase=10.0,   # 10% trade-cost increase
    selection=1,
    sigma=7.0,
    verbose=True,
)

# 4. Inspect country-level percentage changes
print(summary.head())
```

---