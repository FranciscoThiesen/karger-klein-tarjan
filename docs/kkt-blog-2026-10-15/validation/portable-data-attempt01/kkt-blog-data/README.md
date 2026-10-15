# Replot the KKT blog charts

This portable download contains the exact accepted chart generator, a thin CSV replot entry point, and the eight exported chart tables. It uses no native executable, build objects, original-machine filesystem paths, benchmark collector, network data or raw-study imports.

With Python 3.9 or newer and matplotlib available:

```sh
python3 -m pip install -r requirements.txt
python3 -B replot_charts.py --output-dir replotted
```

The output directory must be new. It produces five desktop and five mobile views, each as SVG plus a retina PNG, with a receipt. `plot_results.py` is an unchanged source copy; replot calls only its `render()` function. It never calls the original raw-evidence `data()` or `main()` functions. The original environment used matplotlib 3.9.4 and DejaVu Sans. Font/library differences can change raster bytes or text metrics on another machine; inspect the new figures there. The provided publication assets were already reviewed.

`provenance.json` binds all included source/table bytes and records public repository-relative evidence paths and hashes. Those hashes identify the completed studies; the native source/build/raw evidence is not bundled here. This is reproducibility from exported chart tables, not a replay of native correctness certificates, independent raw audits, or benchmark execution. The original provenance digest is retained. No new timing, model fitting, aggregation, trimming or historical pooling occurs during replot.

See `data/README.md` for columns, units, graph/clock distinctions and the finite-fit and counter limitations. Full ranges and graph medians are retained. The endpoint table includes every solver, including cases where KKT loses. Wall and CPU are separate clocks; the verifier counters are not a CPU-time decomposition.
