# API Fixell

## Protokół komunikacji

Fixell używa prostego protokołu tekstowego przez TCP:

### Format wiadomości

```
[PREFIX:]treść\n
```

### Prefiksy

| Prefix | Kierunek | Opis |
|--------|----------|------|
| (brak) | klient→serwer | Pytanie użytkownika |
| `USER:` | klient→serwer | Dodatkowe pytanie |
| `RESULT:` | klient→serwer | Wynik wykonanej komendy |
| `SKIP:` | klient→serwer | Użytkownik pominął komendę |
| `LOCAL:` | klient→serwer | Wiadomość od operatora |
| `CMD:` | serwer→klient | Proponowana komenda |
| `---END---` | serwer→klient | Koniec odpowiedzi |

### Przykładowa sesja

```
# Klient łączy się
< === FIXELL SERVER CONNECTED ===
< Opisz problem lub wpisz 'help'
< ---END---

# Klient wysyła pytanie
> System nie startuje

# Serwer odpowiada
< Sprawdźmy logi systemd:
< CMD: journalctl -xb --no-pager | tail -50
< ---END---

# Klient wykonuje komendę i wysyła wynik
> RESULT:-- Journal begins at Mon 2024-01-01...

# Serwer analizuje
< Widzę błąd z nvidia. Spróbuj:
< CMD: systemctl disable nvidia-persistenced
< ---END---
```

## Python API

### Server

```python
from fixell import FixellServer

server = FixellServer(port=8088, model="qwen2.5:14b")
server.run()
```

### Client

```python
from fixell import FixellClient

client = FixellClient("nvidia", 8088)
client.connect()
client.send("Mój system nie startuje")
response = client.receive()
print(response)
```

### Utilities

```python
from fixell.utils import extract_commands, is_dangerous_command

response = "Sprawdź logi: CMD: journalctl -xb"
commands = extract_commands(response)
# ['journalctl -xb']

is_dangerous_command("rm -rf /")
# True

is_dangerous_command("journalctl -xb")
# False
```

## REST API (opcjonalne)

Jeśli uruchomisz serwer HTTP:

### Endpoints

```
POST /api/ask
Content-Type: application/json

{
  "message": "System nie startuje",
  "context": "poprzednie wiadomości..."
}

Response:
{
  "response": "Sprawdźmy logi...",
  "commands": ["journalctl -xb"]
}
```

## Klient curl (minimalistyczny)

```bash
# Jednorazowe pytanie
echo "System nie startuje" | nc server 8088

# Interaktywna sesja
nc server 8088
```
