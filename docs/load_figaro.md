<a id="load_figaro"></a>
# load_FIGARO

---

**Description**

`load_FIGARO` reads a Eurostat FIGARO inter-country input–output (IC-IO) matrix for a given year and layout (industry-by-industry or product-by-product), infers the main IC-IO dimensions (number of countries, sectors/products, and final-demand components), and converts country codes from **ISO2** to **ISO3** using an internal mapping.

FIGARO row/column labels are assumed to start with a 2-letter country code (e.g. `"ES..."`, `"DE..."`, `"US..."`), plus a specific code for the rest of the world (`"FIGW1"`), which is harmonised to `"RW"` and then converted to a pseudo-ISO3 code `"ROW"`.

The function returns a cleaned DataFrame with country–sector (or country–product) labels of the form `"ISO3_k"`, where `k = 1, 2, …, S` is a sector/product index in natural order.

---

**Usage**

`load_FIGARO(dire, year, typ="ind")`

---

**Arguments**

`load_FIGARO(dire, year, typ="ind")`

- `dire` : `str` or `pathlib.Path`
  Directory where the FIGARO CSV files are stored, e.g.
  `"path/to/Figaro/raw/IO_industry"` or `"path/to/Figaro/raw/IO_product"`.
  It should **not** include a trailing slash, since the function constructs the full path internally using `"/"`.

- `year` : `int`
  Reference year of the FIGARO IC-IO data (typically between 2010 and 2020, depending on the specific edition).

- `typ` : `{"ind", "prod"}`, default `"ind"`
  Type of FIGARO table to load:
  - `"ind"`  : industry-by-industry IO table.
  - `"prod"` : product-by-product IO table.

---

**Details**

The function runs through the following steps:

1. **Local ISO2 → ISO3 mapping**
   A local dictionary `iso2_to_iso3` is defined inside the function, covering a wide range of ISO2 codes and their ISO3 equivalents (e.g. `"ES" → "ESP"`, `"DE" → "DEU"`, `"US" → "USA"`). It also includes a mapping for `"RW" → "ROW"` so that the rest-of-world code is standardised.

2. **Read the FIGARO IC-IO CSV file**
   The input CSV file is read with:
   ```python
   df = pd.read_csv(
       dire + "/matrix_eu-ic-io_" + typ + "-by-" + typ + "_24ed_" + str(year) + ".csv",
       index_col=0,
   )
so the directory dire should match the structure used by Eurostat (e.g. ".../IO_industry" for typ="ind").
The first column is used as the index.

  The function assumes there are a number of “additional” rows outside the country–sector block (e.g. taxes, value added, other aggregates), which it sets as: `filas_adic = 6`

3. **Infer sectors/products (S) and final-demand components (FD)**

  Using a reference country in ISO2 format (ref = "US"), the function infers:

- S: number of sectors/products per country, as: `S = int(df.T.filter(like="US").shape[1])`
- SplusFD: total number of columns corresponding to the reference country (sectors/products + final demand): `SplusFD = int(df.filter(like="US").shape[1])`
- FD = SplusFD - S`: number of final-demand components per country.

With filas_adic additional rows, it then computes:

- C = (n_rows - filas_adic) / S : number of countries/regions.
- CS = C × S : total number of country–sector (or country–product) combinations.
- CFD = C × FD : total number of country–final-demand combinations.

4. **Harmonise rest-of-world code ("FIGW1" → "RW") in column labels**
FIGARO uses "FIGW1" as the code for the rest of the world. The function:

```python
for columna in df.columns:
    if columna.startswith("FIGW1"):
        new_name = "RW" + columna[len("FIGW1"):]
        df.rename(columns={columna: new_name}, inplace=True)
```
This makes the rest-of-world block consistent with the ISO2→ISO3 mapping.

5. **Build a mapping from FIGARO sector labels to sector indices 1..S**
Using the columns belonging to the reference country ref = "US", the function extracts the original sector codes:

```python

news_names = []
for columna in df.filter(like=ref).columns:
    new_name = str(columna)[2:]  # strip first two characters (ISO2)
    news_names.append(new_name)

diccionario_mapeo = {name: i + 1 for i, name in enumerate(news_names)}
This maps each original FIGARO sector/product code (e.g. "A01", "B05") to a sector index 1..S.
```
6. **Convert country codes from ISO2 to ISO3 in columns**
For each column label:

- The first two characters are interpreted as an ISO2 country code.
- These two characters are replaced with the corresponding ISO3 code using iso2_to_iso3.
For example, "ES_A01" becomes "ESP_A01", "US_A01" becomes "USA_A01".

The transformation is:

```python
new_column_names = []
for column_name in df.columns:
    first_two_letters = column_name[:2]
    new_first_two_letters = iso2_to_iso3.get(first_two_letters, first_two_letters)
    new_column_name = new_first_two_letters + column_name[2:]
    new_column_names.append(new_column_name)
df.columns = new_column_names
```

7. **Append sector indices to column labels ("ISO3_k")**
Using diccionario_mapeo, the function replaces the original sector substring at the end of each column label with a numeric index:

```python

for columna in df.columns:
    for parte_original, parte_nueva in diccionario_mapeo.items():
        if columna.endswith(parte_original):
            new_name = columna.rsplit(parte_original, 1)[0] + "_" + str(parte_nueva)
            df.rename(columns={columna: new_name}, inplace=True)
```

After this step, column labels have the form "ISO3_1", "ISO3_2", …, "ISO3_S" for the intermediate block; final-demand columns follow with their own labels.


8. **Repeat the harmonisation for rows**
The table is transposed and the same procedures are applied to row labels (now columns):

- Harmonise "FIGW1" → "RW".
- Apply ISO2→ISO3 mapping.
- Append sector indices using diccionario_mapeo.

Then the table is transposed back to its original orientation.

Natural ordering of country–sector blocks and FD components

The function ensures:

- The first CS columns correspond to all country–sector blocks, sorted in natural order using natsorted, so sector indices follow 1, 2, 3, 10, 11, ….
- The remaining columns (final demand) are similarly sorted.
This is done column-wise and then row-wise (on the transposed DataFrame) to guarantee a clean, consistent ordering.

9. **Package results**

Finally, all relevant objects are bundled into a dictionary:

```python

dic = {
    "df": df,
    "C": int(C),
    "S": int(S),
    "FD": int(FD),
    "CS": int(CS),
    "CFD": int(CFD),
}
```

---

**Returns**

dict with the following keys:

- "df" : pandas.DataFrame
  Cleaned FIGARO IC-IO matrix with:

  - Rows: country–sector (or country–product) plus a small number of extra rows (e.g. aggregates).

  - Columns: all CS country–sector intermediate-use blocks, followed by all CFD final-demand components.
  Country codes are in ISO3 (or "ROW" for rest-of-world), and sectors/products are indexed as 1..S (natural order).

- "C" : int
Number of countries/regions.

- "S" : int
Number of sectors/products per country.

- "FD" : int
Number of final-demand components per country.

- "CS" : int
Total number of country–sector combinations (C × S).

- "CFD" : int
Total number of country–final-demand combinations (C × FD).

---

**Example**

```python
from intrade import load_FIGARO

# Directory where FIGARO industry-by-industry tables are stored
figaro_ind_dir = "/path/to/Figaro/raw/IO_industry"

# Example 1: Industry-by-industry FIGARO table, year 2015
figaro_ind_2015 = load_FIGARO(dire=figaro_ind_dir, year=2015, typ="ind")

df_ind  = figaro_ind_2015["df"]
C_ind   = figaro_ind_2015["C"]
S_ind   = figaro_ind_2015["S"]
FD_ind  = figaro_ind_2015["FD"]

# Directory where FIGARO product-by-product tables are stored
figaro_prod_dir = "/path/to/Figaro/raw/IO_product"

# Example 2: Product-by-product FIGARO table, year 2018
figaro_prod_2018 = load_FIGARO(dire=figaro_prod_dir, year=2018, typ="prod")

df_prod = figaro_prod_2018["df"]
C_prod  = figaro_prod_2018["C"]
S_prod  = figaro_prod_2018["S"]

# The returned df can be transformed into a WIO structure or
# used directly for IC-IO analysis and value-added decompositions.
```


---

**Notes**

Implemented with the following with the following original files:

- 'matrix_eu-ic-io_ind-by-ind_24ed_2010.csv', ... to 'matrix_eu-ic-io_ind-by-ind_24ed_2022.csv',
- 'matrix_eu-ic-io_prod-by-prod_24ed_2010.csv', ... to  'matrix_eu-ic-io_prod-by-prod_24ed_2022.csv'


---