<a id="index"></a>
# Index


- [InTrade-package](intrade-package.md#intrade-package) — Package description

[**1- Data Loading Functions**](DLF.md#DLF)

- [load_Test](load_test.md#load_test) — Load test/example datasets
- [load_ADB](load_adb.md#load_adb) — Load Asian Development Bank (ADB) MRIO data
- [load_EORA](load_eora.md#load_eora) — Load Eora26 MRIO data
- [load_FIGARO](load_figaro.md#load_figaro) — Load FIGARO input–output tables
- [load_GLORIA](load_gloria.md#load_gloria) — Load GLORIA MRIO data
- [load_TIVA](load_tiva.md#load_tiva) — Load OECD TiVA (Trade in Value Added) data
- [load_WIOD](load_wiod.md#load_wiod) — Load WIOD (World Input–Output Database) data
- [aggregate](aggregate.md#aggregate) — Country level aggregation

[**2- Create Objects Functions**](COF.md#COF)

- [obj_IO](obj_io.md#obj_io) — Create input–output object
- [obj_Grav](obj_grav.md#obj_grav) — Create gravity object
- [obj_Grav_panel](obj_grav_panel.md#obj_grav_panel) — Create gravity panel object (multi-year)


[**3.A- Input - Output Analysis Functions**](IOAF.md#IOAF)

- [KWW](KWW.md#KWW) — Aggregate WWZ terms into Koopman–Wang–Wei components
- [WWZ](WWZ.md#WWZ) — Wang–Wei–Zhu value-added trade decomposition
- [BM](BM.md#BM) — Borin-Mancini VA export decomposition from WIO dict
- [BMT_trade](bmt_trade.md#bmt_trade) — Borin-Mancini-Taglioni trade participation decomposition
- [BMT_output](bmt_output.md#bmt_output) — Borin-Mancini-Taglioni output participation decomposition
- [stream](stream.md#stream) — Compute upstream/downstream indices by country–sector


[**3.B- Gravity Analysis Functions**](GAF.md#GAF)

- [struc_grav_cf](struc_grav_cf.md#struc_grav_cf) — Core structural gravity + exact-hat counterfactual engine
- [struc_grav_incre](struc_grav_incre.md#struc_grav_incre) — Structural gravity counterfactual: trade cost increase
- [struc_grav_asif](struc_grav_asif.md#struc_grav_asif) — Structural gravity counterfactual: “as-if” FTA scenario
- [struc_grav_inout](struc_grav_inout.md#struc_grav_inout) — Structural gravity counterfactual: entry/exit in RTA
- [grav_panel](grav_panel.md#grav_panel) — Panel gravity PPML with flexible fixed effects
- [solve_system_Ti](solve_system_Ti.md#solve_system_Ti) — Equilibrium system for exact-hat algebra (used by `struc_grav_cf`)


---