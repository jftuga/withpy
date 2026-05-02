PYTHON      = python3.14
NAME        = withpy
VERSION    := $(shell grep '__version__' withpy/__init__.py | sed 's/.*"\(.*\)".*/\1/')
DIST_DIR    = dist
DIST_BIN    = $(DIST_DIR)/$(NAME)
ARCHIVE     = $(NAME)-v$(VERSION).tar.xz
INSTALL_DIR = /usr/local/bin

.PHONY: all build test amalgamate dist install user-install uninstall clean run help

all: build

build:
	$(PYTHON) -m py_compile withpy/__init__.py
	$(PYTHON) -m py_compile withpy/__main__.py
	$(PYTHON) -m py_compile withpy/cli.py
	$(PYTHON) -m compileall -q withpy/commands/

test: amalgamate
	$(PYTHON) -m pytest tests/ -v

amalgamate:
	$(PYTHON) build.py
	@echo "Built $(DIST_BIN) (v$(VERSION))"

dist: amalgamate
	tar cJf $(ARCHIVE) -C $(DIST_DIR) $(NAME)
	@echo "Created $(ARCHIVE)"
	@ls -lh $(ARCHIVE)

install: amalgamate
	install -d $(INSTALL_DIR)
	install -m 755 $(DIST_BIN) $(INSTALL_DIR)/$(NAME)
	@echo "Installed $(NAME) to $(INSTALL_DIR)"

user-install: amalgamate
	install -d $(HOME)/bin
	install -m 755 $(DIST_BIN) $(HOME)/bin/$(NAME)
	@echo "Installed $(NAME) to $(HOME)/bin/"

uninstall:
	rm -f $(INSTALL_DIR)/$(NAME)
	@echo "Removed $(NAME) from $(INSTALL_DIR)"

clean:
	rm -rf $(DIST_DIR) __pycache__ .pytest_cache *.egg-info $(ARCHIVE)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

run:
	$(PYTHON) -m $(NAME)

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build         Compile-check all source files (default)"
	@echo "  test          Run pytest suite (builds amalgamated artifact first)"
	@echo "  amalgamate    Build single-file dist/$(NAME) via build.py"
	@echo "  dist          Build amalgamated + create $(NAME)-v$(VERSION).tar.xz"
	@echo "  install       Install to $(INSTALL_DIR) (requires sudo)"
	@echo "  user-install  Install to $(HOME)/bin/"
	@echo "  uninstall     Remove from $(INSTALL_DIR)"
	@echo "  clean         Remove build artifacts and caches"
	@echo "  run           Run via python -m $(NAME)"
	@echo "  help          Show this help"
