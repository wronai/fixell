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

Operator na serwerze może:

1. **Obserwować sesję** - widzi wszystkie pytania i odpowiedzi
2. **Wysyłać wiadomości** - prefix `to:` wysyła do klienta
3. **Interweniować** - może przerwać lub pomóc

```
SERVER> to: Sprawdź też czy masz backup przed tą operacją
[wiadomość wysłana do klienta]
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
