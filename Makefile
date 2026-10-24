PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
LEAN_BIN ?= $(CURDIR)/.tools/lean-4.35.0-darwin_aarch64/bin
BOOTSTRAP_PYTHON ?= python3.12

.PHONY: setup check check-formal manifest test reproduce baseline viewer display-data search proof verify-formal

.venv/bin/python:
	$(BOOTSTRAP_PYTHON) -m venv .venv

setup: .venv/bin/python
	.venv/bin/python -m ensurepip --upgrade
	.venv/bin/python -m pip install --disable-pip-version-check -r requirements.lock
	.venv/bin/python -m pip install --disable-pip-version-check --no-deps --no-build-isolation -e .

check:
	$(PYTHON) scripts/check.py

check-formal:
	$(PYTHON) scripts/check.py --formal

manifest:
	$(PYTHON) scripts/package_release.py --manifest-only

test:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) formal/diagnostics/direct_ricci_check.py

reproduce:
	$(PYTHON) -m warpproof reproduce --output results/paper-reproduction.json

baseline:
	$(PYTHON) -m warpproof evaluate candidates/rodal-baseline.json --output results/baseline.json

viewer:
	$(PYTHON) -m warpproof render-data candidates/rodal-baseline.json --output web/default-result.js

search:
	$(PYTHON) -m warpproof search --iterations 8 --output candidates/search-example.json

proof:
	cd formal && export PATH="$(LEAN_BIN):$$PATH" && lake build && lake env lean Audit.lean

# Deliberately nonzero until all certification obligations are implemented.
verify-formal:
	$(PYTHON) -m warpproof verify --require-formal

display-data:
	$(PYTHON) scripts/build_optics.py
	$(PYTHON) scripts/build_sky.py --catalogue web/stars.json
