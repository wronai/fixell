# Rozwiązywanie problemów

## Problemy z połączeniem

### "Błąd połączenia" przy uruchamianiu klienta

```bash
# Sprawdź czy serwer działa
nc -zv server 8088

# Sprawdź firewall
sudo firewall-cmd --list-all

# Sprawdź czy port jest otwarty
ss -tlnp | grep 8088
```

### Timeout przy odpowiedziach

```bash
# Zwiększ timeout w kliencie
export FIXELL_TIMEOUT=120

# Sprawdź czy Ollama odpowiada
curl http://localhost:11434/api/tags
```

## Problemy z Ollama

### "Błąd Ollama: Connection refused"

```bash
# Uruchom Ollama
ollama serve

# Lub przez systemd
sudo systemctl start ollama
```

### Model nie odpowiada

```bash
# Sprawdź czy model jest pobrany
ollama list

# Pobierz model
ollama pull qwen2.5:14b

# Test modelu
ollama run qwen2.5:14b "Test"
```

### Brak pamięci GPU

```bash
# Użyj mniejszego modelu
ollama pull qwen2.5:7b

# Lub uruchom na CPU
OLLAMA_NUM_GPU=0 ollama serve
```

## Problemy z klientem bash

### "/dev/tcp: No such file or directory"

Bash musi być skompilowany z obsługą /dev/tcp. Alternatywy:

```bash
# Użyj netcat
nc server 8088

# Lub Python klienta
pip install fixell
fixell-client server:8088
```

### Komendy nie wykonują się

```bash
# Sprawdź uprawnienia
chmod +x fixer.sh

# Uruchom z bash
bash fixer.sh server:8088
```

## Problemy z Docker

### "host.docker.internal" nie działa

```bash
# Linux wymaga extra_hosts
# W docker-compose.yml:
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### Kontener nie widzi Ollama

```bash
# Sprawdź czy Ollama nasłuchuje na wszystkich interfejsach
OLLAMA_HOST=0.0.0.0 ollama serve

# Lub użyj host network
docker run --network host fixell-server
```

## Logi i debugowanie

### Włącz verbose mode

```bash
# Serwer
DEBUG=1 fixell-server

# Klient
DEBUG=1 ./fixer.sh server:8088
```

### Sprawdź logi

```bash
# Logi Ollama
journalctl -u ollama -f

# Logi Docker
docker-compose logs -f
```
