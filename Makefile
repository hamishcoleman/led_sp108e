
all: x11-to-led

BUILD_DEPENDS := \
    flake8 \
    python3-pytest \
    python3-pytest-cov \


.PHONY: build-depends
build-depends:
	sudo apt install -y $(BUILD_DEPENDS)

.PHONY: test
test: test.pytest

.PHONY: test.pytest
test.pytest:
	pytest-3 --cov=./ --cov-report=term --cov-report=html

.PHONY: check
check: check.static

.PHONY: check.static
check.static:
	flake8

x11-to-led: x11-to-led.c
	$(CC) -lX11 -o $@ $<
