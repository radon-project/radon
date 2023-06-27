test:
	@python3.11 radon.py -s examples/functions.rn

py2c:
	# Need to test it.
	@python3.11 -m cython -3 -a radon.py -o radon.c --embed -I/usr/include/python3.11 
config2bin:

build:

install:
