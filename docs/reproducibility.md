# Reproduce and inspect the release

The standard core requires Python 3.11+ and NumPy. `requirements-core.txt` pins the tested NumPy version. `pyproject.toml` declares the compatible core package range. Run commands from the repository root.

```bash
python -m pip install -r requirements-core.txt
python -m unittest discover -s tests -v
python scripts/verify.py
node scripts/check_dashboard.cjs
```

The verifier does not overwrite frozen research. It reconstructs all 499 curves, every core-tenor repricing identity, 36 analytical price/yield cases, risk, carry, the bounded hedge and temporal forecast metrics, then checks executed notebook evidence, the independent Excel receipt and every release-manifest digest. A failed hash after intentional rebuilding means the release must be re-reviewed and re-packaged; it must not be ignored.

## Regeneration order

```bash
python scripts/build.py
python scripts/build_dashboard.py
python scripts/build_figures.py
node scripts/render_figures.mjs
python scripts/build_notebooks.py
python scripts/run_notebooks.py
node scripts/build_workbook.mjs
python scripts/build_report.py
python scripts/package_release.py
python scripts/verify.py
```

Core build and dashboard generation use ordinary Python/NumPy. Vector figures and the paper use ReportLab; DOCX uses python-docx. `requirements-report.txt` records tested versions. Report construction requires licensed Times New Roman fonts supplied by the user's environment; set `P4_TIMES_FONT_DIR` to their directory. Fonts are not redistributed.

The spreadsheet authoring script uses the OpenAI primary runtime's `@oai/artifact-tool` package; PNG rendering uses its bundled Sharp. They are authoring dependencies, not core verification requirements or a claim that these packages are public npm dependencies. Published Excel formulas and cached results are independently inspectable without that runtime. The workbook contains an Excel-native two-input What-If Data Table. Bundled LibreOffice recalculation verified its base and non-base results; native Microsoft Excel GUI execution is a separately recorded check, not assumed.

Each notebook starts with a fresh namespace and calls reusable package functions. `run_notebooks.py` captures standard display MIME bundles without a Jupyter service. Native Jupyter execution requires IPython and is not what the supplied runner claims. Embedded PNGs avoid GitHub's inconsistent inline-SVG and currency-math rendering.

## Artifact identity

`artifacts/release/research.json` records source receipts, configuration hash, engine-code hash, environment and deterministic run ID. `published_at` is a build clock; `as_of` is the source cutoff. The containing GitHub commit identifies the exact source/export revision. The file manifest hashes immutable released source, figures, notebooks and deliverables. Separate mutable market receipts and local review intermediates are excluded by an explicit policy.

Source CSVs and complete core data are included. No download or API key is required for the frozen study. Source dates are not security settlement dates, and a source file retrieved in 2026 does not prove that exact vintage was historically available.
