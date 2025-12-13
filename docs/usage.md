# Użycie Fixell

## Podstawowe użycie

### Uruchomienie serwera

```bash
# Domyślne ustawienia (port 8088, model qwen2.5:14b)
fixell-server

# Lub z parametrami
fixell-server 8088 qwen2.5:14b

# Lub przez Makefile
make run-server PORT=8088 MODEL=qwen2.5:14b
```

### Połączenie klienta

```bash
# Skrypt bash
./fixer.sh nvidia:8088

# Python
fixell-client nvidia:8088

# Makefile
make run-client SERVER_HOST=nvidia PORT=8088
```

## Tryb awaryjny Fedora

### Krok 1: Przygotowanie USB

Na działającym komputerze:
```bash
# Pobierz skrypt klienta na USB
curl -O https://raw.githubusercontent.com/wronai/fixell/main/fixer.sh
cp fixer.sh /media/usb/
```

### Krok 2: Boot w trybie awaryjnym

1. Uruchom komputer
2. W GRUB naciśnij `e` aby edytować
3. Dodaj `systemd.unit=rescue.target` do linii linux
4. Naciśnij `Ctrl+X` aby uruchomić

### Krok 3: Połączenie z serwerem

```bash
# Zamontuj USB
mount /dev/sdb1 /mnt

# Uruchom klienta
/mnt/fixer.sh 192.168.1.100:8088
```

## Interakcja z AI

### Opisywanie problemu

```
> Mój system nie startuje, zatrzymuje się na logo Fedora

[AI odpowiada i proponuje komendy diagnostyczne]

[SERWER PROPONUJE KOMENDĘ]: journalctl -xb --no-pager | tail -100
Wykonać? (t/n/q pytanie): t

[Wynik komendy jest wysyłany do AI]

[AI analizuje i proponuje rozwiązanie]
```

### Opcje przy komendach

- **t** - Tak, wykonaj komendę
- **n** - Nie, pomiń komendę
- **q** - Zadaj własne pytanie

### Przykładowe sesje

#### Problem z bootowaniem

```
> System zatrzymuje się na "Starting Plymouth Boot Screen"

[AI]: Sprawdźmy logi systemd. Wykonaj:
CMD: journalctl -xb -p err

> t
[wynik...]

[AI]: Widzę błąd z nvidia-persistenced. Spróbuj:
CMD: systemctl disable nvidia-persistenced
CMD: dracut -f

> t
[wynik...]

[AI]: Zrestartuj system: CMD: reboot
```

#### Brak miejsca na dysku

```
> System jest read-only, nie mogę nic zapisać

[AI]: Sprawdźmy miejsce na dysku:
CMD: df -h

> t
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   50G     0 100% /

[AI]: Dysk jest pełny. Znajdźmy duże pliki:
CMD: du -sh /var/log/* | sort -h | tail -10

> t
[wynik...]

[AI]: Wyczyść stare logi:
CMD: journalctl --vacuum-size=100M
```

## Operator serwera

Po uruchomieniu `make run-server` operator może kontrolować sesje i wysyłać komendy do klientów.

### Dostępne komendy

| Komenda | Opis |
|---------|------|
| `run: <cmd>` | Wyślij komendę do **automatycznego** wykonania (bez potwierdzenia klienta) |
| `exec: <cmd>` | Wyślij komendę z **potwierdzeniem** (klient pyta t/n) |
| `to: <msg>` | Wyślij wiadomość tekstową do klientów |
| `status` | Pokaż liczbę aktywnych klientów i sesji HTTP |
| `config` | Pokaż aktualną konfigurację (porty, model, ścieżki) |
| `help` | Pokaż pomoc |

### Przykłady użycia

```bash
# Automatyczne wykonanie komendy na kliencie (bez pytania)
SERVER> run: uname -a
[EXEC->KLIENT] uname -a
# Klient wykonuje i wysyła wynik automatycznie

# Komenda z potwierdzeniem (klient musi zaakceptować)
SERVER> exec: systemctl restart NetworkManager
[CMD->KLIENT] systemctl restart NetworkManager
# Klient widzi: "[KOMENDA]: systemctl restart NetworkManager"
# Klient pyta: "Wykonać? (t/n):"

# Wysłanie wiadomości do klienta
SERVER> to: Sprawdzam logi, proszę czekać...
# Klient widzi: "[OPERATOR]: Sprawdzam logi, proszę czekać..."

# Sprawdzenie statusu
SERVER> status
# Aktywnych klientów: 2, sesji HTTP: 1

# Wyświetlenie konfiguracji
SERVER> config
# PORT=8088, HTTP_PORT=8089, MODEL=qwen2.5:14b
# OLLAMA_HOST=http://localhost:11434, LOG_DIR=logs
```

### Różnica między `run:` a `exec:`

- **`run:`** - komenda wykonuje się **natychmiast** bez pytania użytkownika. Używaj do bezpiecznych komend diagnostycznych (np. `uname -a`, `df -h`, `cat /etc/os-release`).

- **`exec:`** - klient **pyta o potwierdzenie** przed wykonaniem. Używaj do komend modyfikujących system (np. `systemctl restart`, `dnf install`, `rm`).

### Logi sesji

Wszystkie sesje są zapisywane w katalogu `logs/`:

| Plik | Opis |
|------|------|
| `fixell_YYYYMMDD_HHMMSS.log` | Główny log serwera (techniczny) |
| `session_IP_YYYYMMDD.log` | Log sesji (skrócony) |
| `conversation_IP_YYYYMMDD.md` | **Pełna konwersacja** w formacie Markdown |

Podgląd logów na żywo:
```bash
make logs
# lub
tail -f logs/*.log
```

## Konfiguracja

### Zmienne środowiskowe

```bash
export OLLAMA_HOST=http://192.168.1.50:11434
export FIXELL_MODEL=qwen2.5:14b
export FIXELL_PORT=8088
```

### Plik konfiguracyjny

```bash
# ~/.fixellrc
OLLAMA_HOST=http://localhost:11434
MODEL=qwen2.5:14b
PORT=8088
```
