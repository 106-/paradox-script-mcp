.PHONY: install serve test lint format clean help

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Setup:"
	@echo "  install    - Install dependencies"
	@echo ""
	@echo "Development:"
	@echo "  serve      - Start server with hot reload (port 8000)"
	@echo ""
	@echo "Quality:"
	@echo "  test       - Run tests"
	@echo "  lint       - Run linter"
	@echo "  format     - Format code"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean      - Remove cache files"

install:
	uv pip install -e .

# Hot reload server (watches .py and .yml files)
# Connect via .mcp.json url: http://localhost:8000/mcp
serve:
	uv run uvicorn paradox_script_mcp.server:app --reload --reload-include "*.yml" --host 0.0.0.0 --port 8000

test:
	uv run pytest

lint:
	uv run ruff check src/

format:
	uv run ruff format src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
