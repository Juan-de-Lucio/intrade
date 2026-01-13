<a id="solve_system_Ti"></a>
# solve_system_Ti

---


**Description**

Equilibrium system for exact-hat algebra.

`solve_system_Ti` implements the system of equilibrium conditions used in the exact-hat algebra solution of the structural gravity model under trade
imbalances.

It is designed to be used with a root-finding algorithm such as scipy.optimize.root, and is called inside `struc_grav_cf`.

---

**Usage**

`solve_system_Ti(x, T_ratio, q, TI, pi, sigma)`

---

**Arguments**

- `x` (ndarray, shape (n,))
: Vector of unknown "hats" (e.g., output and prices), typically initialised at ones.

- `T_ratio` (ndarray, shape (n, n))
: Matrix of trade cost ratios between counterfactual and baseline, raised to the appropriate power.

- `q` (ndarray, shape (n,))
: Vector of baseline output (or expenditure).

- `TI` (ndarray, shape (n,))
: Vector of trade imbalances.

- `pi` (ndarray, shape (n, n))
: Matrix of baseline expenditure shares.

- `sigma` (float)
: Elasticity of substitution.

---

**Details**

The function computes a vector of residuals `F` such that `F = 0` characterises the equilibrium of the counterfactual economy (market clearance + consistency with trade imbalances and shares).

It is structured so that:

- The first $n-1$ equations impose the equilibrium conditions for all countries except the numéraire.
- The last equation pins down the scale (e.g., normalisation of one hat).

The exact algebra matches the functional form of the structural gravity model and the implementation of `struc_grav_cf`.

---

**Value**

`F` (ndarray, shape (n,))
: Vector of residuals; the equilibrium is obtained when `F` is (approximately) the zero vector.

---

**Example**

```python
from scipy import optimize
from intrade import solve_system_Ti

n = T_ratio.shape[0]
x0 = np.ones(n)

sol = optimize.root(
    solve_system_Ti,
    x0,
    args=(T_ratio, q, TI, pi, sigma),
    method='df-sane',
)

x_hat = sol.x
```

---

\cleardoublepage
\phantomsection
\addcontentsline{toc}{chapter}{Index}
\printindex