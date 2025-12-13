.PHONY: all build test test-e2e test-unit run-server run-client docker-build docker-up docker-down clean install dev lint help init-env

# Wczytaj .env jeśli istnieje
-include .env
export

# Konfiguracja (domyślne wartości jeśli nie ma w .env)
PORT ?= 8088
HTTP_PORT ?= 8089
MODEL ?= qwen2.5:14b
OLLAMA_HOST ?= http://localhost:11434
SERVER_HOST ?= localhost
LOG_DIR ?= logs
LOG_LEVEL ?= INFO
SESSION_TIMEOUT ?= 300

help:
	@echo "Fixell - Zdalna naprawa systemu Linux z AI"
	@echo ""
	@echo "Użycie:"
	@echo "  make install      - Instalacja paczki Python"
	@echo "  make dev          - Instalacja w trybie deweloperskim"
	@echo "  make run-server   - Uruchom serwer naprawczy"
	@echo "  make run-client   - Uruchom klienta"
	@echo "  make test         - Uruchom wszystkie testy"
	@echo "  make test-e2e     - Uruchom testy E2E"
	@echo "  make test-unit    - Uruchom testy jednostkowe"
	@echo "  make docker-build - Zbuduj obrazy Docker"
	@echo "  make docker-up    - Uruchom środowisko Docker"
	@echo "  make docker-down  - Zatrzymaj środowisko Docker"
	@echo "  make lint         - Sprawdź jakość kodu"
	@echo "  make clean        - Wyczyść pliki tymczasowe"
	@echo "  make init-env     - Utwórz plik .env z domyślnymi wartościami"

all: install

init-env:
	@if [ ! -f .env ]; then \
		echo "Tworzę plik .env..."; \
		echo "# Fixell - Konfiguracja serwera" > .env; \
		echo "PORT=8088" >> .env; \
		echo "HTTP_PORT=8089" >> .env; \
		echo "MODEL=qwen2.5:14b" >> .env; \
		echo "OLLAMA_HOST=http://localhost:11434" >> .env; \
		echo "SERVER_HOST=$$(hostname -I | awk '{print $$1}')" >> .env; \
		echo "" >> .env; \
		echo "# Logowanie" >> .env; \
		echo "LOG_DIR=logs" >> .env; \
		echo "LOG_LEVEL=INFO" >> .env; \
		echo "" >> .env; \
		echo "# Sesje" >> .env; \
		echo "SESSION_TIMEOUT=300" >> .env; \
		echo "Utworzono .env z IP: $$(hostname -I | awk '{print $$1}')"; \
	else \
		echo ".env już istnieje"; \
	fi

show-config:
	@echo "=== Aktualna konfiguracja ==="
	@echo "PORT=$(PORT)"
	@echo "HTTP_PORT=$(HTTP_PORT)"
	@echo "MODEL=$(MODEL)"
	@echo "OLLAMA_HOST=$(OLLAMA_HOST)"
	@echo "SERVER_HOST=$(SERVER_HOST)"
	@echo "LOG_DIR=$(LOG_DIR)"
	@echo "LOG_LEVEL=$(LOG_LEVEL)"
	@echo "SESSION_TIMEOUT=$(SESSION_TIMEOUT)"

logs:
	@tail -f $(LOG_DIR)/*.log 2>/dev/null || echo "Brak logów w $(LOG_DIR)"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

run-server: kill-port
	@echo "Uruchamiam serwer na porcie $(PORT) z modelem $(MODEL)..."
	OLLAMA_HOST=$(OLLAMA_HOST) python3 fixer-server.py $(PORT) $(MODEL)

kill-port:
	@-lsof -ti :$(PORT) | xargs -r kill 2>/dev/null || true
	@-lsof -ti :$$(($(PORT)+1)) | xargs -r kill 2>/dev/null || true

run-client:
	@echo "Łączę z $(SERVER_HOST):$(PORT)..."
	./fixer.sh $(SERVER_HOST):$(PORT)

# Testy
test: test-unit test-e2e

test-unit:
	@echo "=== Testy jednostkowe ==="
	python3 -m pytest tests/test_unit.py -v

test-e2e:
	@echo "=== Testy E2E ==="
	python3 tests/test_e2e.py

test-connection:
	@echo "=== Test połączenia z Ollama ==="
	@curl -s $(OLLAMA_HOST)/api/tags | python3 -c "import sys,json; d=json.load(sys.stdin); print('Dostępne modele:', [m['name'] for m in d.get('models',[])])" || echo "Błąd: Ollama niedostępna na $(OLLAMA_HOST)"

test-model:
	@echo "=== Test modelu $(MODEL) ==="
	@curl -s $(OLLAMA_HOST)/api/generate -d '{"model":"$(MODEL)","prompt":"Odpowiedz jednym słowem: Linux","stream":false}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('response','Błąd'))"

# Docker
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Jakość kodu
lint:
	@echo "=== Sprawdzanie jakości kodu ==="
	python3 -m flake8 fixell/ tests/ --max-line-length=120 || true
	python3 -m mypy fixell/ --ignore-missing-imports || true

format:
	python3 -m black fixell/ tests/
	python3 -m isort fixell/ tests/

# Czyszczenie
clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache __pycache__ .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Publikacja
build-dist:
	python3 -m build

publish-test:
	python3 -m twine upload --repository testpypi dist/*

publish:
	python3 -m twine upload dist/*
