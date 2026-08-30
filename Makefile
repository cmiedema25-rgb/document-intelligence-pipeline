PYTHON ?= python

.PHONY: install lint test benchmark sdk-test verify

install:
	$(PYTHON) -m pip install -e '.[dev]'

lint:
	ruff check .
	ruff format --check .

test:
	pytest --cov=document_intelligence --cov-report=term-missing --cov-fail-under=70 -q

benchmark:
	docintel benchmark samples/benchmark.json --report evidence/benchmark-report.json

sdk-test:
	cd sdk && npm ci && npm test

verify: lint test benchmark sdk-test
