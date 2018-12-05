
all: x11-to-led

x11-to-led: x11-to-led.c
	$(CC) -lX11 -o $@ $<

.PHONY: test
test: check.static

.PHONY: check.static
check.static:
	flake8
