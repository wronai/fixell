# Instalacja Fixell

## Wymagania

### Serwer (komputer z GPU)
- Python 3.8+
- Ollama z zainstalowanym modelem
- GPU NVIDIA z CUDA (opcjonalne, ale zalecane)

### Klient (komputer z problemem)
- Bash (dla `fixer.sh`)
- LUB Python 3.8+ (dla `fixell-client`)
- LUB curl/nc (dla minimalnego klienta)

## Instalacja serwera

### Metoda 1: pip (zalecana)

```bash
pip install fixell
```

### Metoda 2: Ze źródeł

```bash
git clone https://github.com/wronai/fixell.git
cd fixell
pip install -e .
```

### Metoda 3: Docker

```bash
docker pull wronai/fixell-server
docker run -p 8088:8088 -e OLLAMA_HOST=http://host.docker.internal:11434 wronai/fixell-server
```

## Instalacja Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Uruchom Ollama
ollama serve

# Pobierz model
ollama pull qwen2.5:14b
```

## Instalacja klienta

### Opcja 1: Skrypt bash (minimalna)

```bash
# Pobierz skrypt
curl -O https://raw.githubusercontent.com/wronai/fixell/main/fixer.sh
chmod +x fixer.sh

# Użyj
./fixer.sh server:8088
```

### Opcja 2: One-liner curl (bez pobierania)

```bash
# Pobierz i uruchom automatycznie
curl -s https://raw.githubusercontent.com/wronai/fixell/main/fixer.sh | bash -s -- server:8088
```

### Opcja 3: Python

```bash
pip install fixell
fixell-client server:8088
```

### Opcja 4: Netcat (ultra-minimalna)

```bash
# Interaktywna sesja przez nc
nc server 8088
```

## Weryfikacja instalacji

```bash
# Sprawdź Ollama
curl http://localhost:11434/api/tags

# Sprawdź serwer
make test-connection

# Uruchom testy E2E
make test-e2e
```

## Rozwiązywanie problemów instalacji

### Ollama nie startuje

```bash
# Sprawdź status
systemctl status ollama

# Uruchom ręcznie
ollama serve

# Sprawdź logi
journalctl -u ollama -f
```

### Brak GPU

```bash
# Użyj mniejszego modelu na CPU
ollama pull qwen2.5:3b
```

### Port zajęty

```bash
# Sprawdź co używa portu
lsof -i :8088

# Użyj innego portu
fixell-server 9000
```
