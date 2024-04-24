PYTHON=python3.11

.PHONY: help
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help         Show this help message"
	@echo "  format-check Check code formatting"
	@echo "  format       Format code"
	@echo "  lint         Check code quality"
	@echo "  test         Run tests"
	@echo "  py2c         Convert Python code to C"
	@echo "  config2bin   Convert configuration file to binary"
	@echo "  build        Build the project"
	@echo "  install      Install the project"
	@echo ""
	@echo "Radon Software Foundation - https://radon-project.github.io/"

.PHONY: format-check
format-check:
	@ruff format --check .

.PHONY: format
format:
	@ruff format .

.PHONY: lint
lint:
	@ruff check .

.PHONY: test
test:
	$(PYTHON) test.py run

.PHONY: py2c
py2c:
	@# Need to test it.
	@echo "Command in development"
	@# $(PYTHON) -m cython -3 -a radon.py -o radon.c --embed -I/usr/include/python3.11

.PHONY: config2bin
config2bin:
	@echo "Command in development"

.PHONY: build
build:
	@echo "Command in development"

.PHONY: install
install:
	@echo "Command in development"
