
all: x11-to-led

x11-to-led: x11-to-led.c
	$(CC) -lX11 -o $@ $<

.PHONY: build-depends
build-depends:
	sudo apt install -y python3-pypcap

.PHONY: test
test: check.static

.PHONY: check.static
check.static:
	flake8
