
all: x11-to-led

x11-to-led: x11-to-led.c
	$(CC) -lX11 -o $@ $<

test: check.static

check.static:
	flake8
