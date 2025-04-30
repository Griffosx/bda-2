.PHONY: test test-cov clean

# Python path to ensure src directory is in the path
PYTHONPATH := $(shell pwd)/src

test:
	PYTHONPATH=$(PYTHONPATH) pytest tests/ -v

test-cov:
	PYTHONPATH=$(PYTHONPATH) pytest tests/ --cov=src --cov-report=term-missing -v
