# Fixell - Zdalna naprawa systemu Linux z AI

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ollama](https://img.shields.io/badge/Ollama-qwen2.5-green.svg)](https://ollama.com/)
[![Linux](https://img.shields.io/badge/OS-Linux-orange.svg)](https://www.linux.org/)

Narzędzie do naprawy systemów Linux (Fedora, Ubuntu, Debian) w trybie awaryjnym poprzez komunikację z modelem AI (Ollama).

## Architektura

```
[Komputer z problemem]     [Komputer z GPU/Ollama]
     (Fedora)                    (nvidia)
        |                           |
   fixer.sh  ----TCP:8088---->  fixer-server.py
        |                           v
        v                    Ollama + qwen2.5:14b
  Wykonuje komendy           (diagnozuje i naprawia)
  (z potwierdzeniem)
```

## Szybki start

### Na komputerze z GPU (serwer):
```bash
# Upewnij się, że Ollama działa z modelem qwen2.5:14b
ollama pull qwen2.5:14b
ollama serve

# Uruchom serwer naprawczy
./fixer-server.py 8088
```

### Na komputerze z problemem (klient):
```bash
# Minimalny skrypt - wystarczy bash i /dev/tcp
./fixer.sh nvidia-host:8088
```

## Użycie w trybie awaryjnym Fedora

1. Uruchom Fedorę w trybie awaryjnym (rescue mode)
2. Skopiuj `fixer.sh` na USB lub pobierz przez sieć
3. Połącz się z serwerem: `./fixer.sh 192.168.1.100:8088`
4. Opisz problem - AI zaproponuje komendy diagnostyczne
5. Potwierdź każdą komendę przed wykonaniem (t/n/q)

## Testowanie z Docker Compose

```bash
# Ollama musi działać lokalnie na porcie 11434
docker-compose up --build

# W osobnych terminalach:
docker attach fixell-client   # interakcja jako klient
docker attach fixell-server   # podgląd serwera
```

## Instalacja

```bash
# Metoda 1: pip
pip install fixell

# Metoda 2: Ze źródeł
git clone https://github.com/wronai/fixell.git
cd fixell && pip install -e .
```

## Klient bez instalacji (one-liner)

```bash
# Opcja 1: Pobierz i uruchom skrypt
curl -sO https://raw.githubusercontent.com/wronai/fixell/main/fixer.sh && bash fixer.sh server:8088

# Opcja 2: Bezpośrednio przez netcat (ultra-minimalne)
nc server 8088

# Opcja 3: Curl one-liner
curl -sL https://raw.githubusercontent.com/wronai/fixell/main/fixer-curl.sh | bash -s -- server:8088
```

## Pliki

| Plik | Opis |
|------|------|
| `fixer.sh` | Minimalny klient bash (~30 linii) |
| `fixer-curl.sh` | Ultra-minimalny klient (curl/nc) |
| `fixell/` | Paczka Python (serwer + klient) |
| `docker-compose.yml` | Test środowiska |
| `docs/` | Pełna dokumentacja |

## Rekomendowane modele

| Model | VRAM | Jakość |
|-------|------|--------|
| qwen2.5:14b | ~10GB | ⭐⭐⭐⭐⭐ |
| qwen2.5:7b | ~5GB | ⭐⭐⭐⭐ |
| codellama:13b | ~8GB | ⭐⭐⭐⭐ |
| llama3:8b | ~5GB | ⭐⭐⭐ |

Pełna lista: [docs/models.md](docs/models.md)

## Bezpieczeństwo

- ✅ Każda komenda wymaga potwierdzenia użytkownika
- ✅ Wykrywanie niebezpiecznych komend (rm -rf /, dd, etc.)
- ✅ Operator serwera widzi wszystkie akcje
- ✅ Brak automatycznego wykonywania

## Dokumentacja

- [Wprowadzenie](docs/introduction.md)
- [Instalacja](docs/installation.md)
- [Użycie](docs/usage.md)
- [Modele AI](docs/models.md)
- [API](docs/api.md)
- [Bezpieczeństwo](docs/security.md)
