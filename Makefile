PYTHON=python3.11

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
	# Need to test it.
	$(PYTHON) -m cython -3 -a radon.py -o radon.c --embed -I/usr/include/python3.11

.PHONY: config2bin
config2bin:

.PHONY: build
build:

..PHONY: install
install:
