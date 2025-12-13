# Bezpieczeństwo Fixell

## Model bezpieczeństwa

Fixell został zaprojektowany z myślą o bezpieczeństwie:

1. **Potwierdzanie komend** - każda komenda wymaga akceptacji użytkownika
2. **Wykrywanie niebezpiecznych komend** - automatyczne ostrzeżenia
3. **Brak automatycznego wykonywania** - pełna kontrola użytkownika
4. **Logowanie** - operator serwera widzi wszystkie akcje

## Niebezpieczne komendy

Fixell automatycznie wykrywa i ostrzega przed:

```python
# Przykłady wykrywanych wzorców
"rm -rf /"           # Usunięcie całego systemu
"rm -rf /*"          # Usunięcie wszystkiego
"dd if=... of=/dev/sda"  # Nadpisanie dysku
"mkfs.*"             # Formatowanie
":(){ :|:& };:"      # Fork bomb
"chmod -R 777 /"     # Niebezpieczne uprawnienia
"curl ... | sh"      # Wykonanie nieznanego kodu
```

## Zalecenia

### Dla użytkownika (klient)

1. **Zawsze czytaj komendy** przed wykonaniem
2. **Nie wykonuj** komend których nie rozumiesz
3. **Pytaj** (opcja `q`) gdy masz wątpliwości
4. **Rób backup** przed ryzykownymi operacjami

### Dla operatora (serwer)

1. **Monitoruj sesje** - obserwuj co robi AI
2. **Interweniuj** gdy widzisz problem
3. **Ogranicz dostęp** do serwera (firewall)
4. **Loguj sesje** dla audytu

## Sieć

### Firewall

```bash
# Ogranicz dostęp tylko do lokalnej sieci
firewall-cmd --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port port="8088" protocol="tcp" accept'
```

### VPN

Zalecane użycie VPN dla połączeń przez internet:

```bash
# WireGuard
wg-quick up wg0
./fixer.sh 10.0.0.1:8088
```

## Audyt

### Logowanie sesji

```bash
# Uruchom serwer z logowaniem
fixell-server 2>&1 | tee -a /var/log/fixell.log
```

### Przegląd logów

```bash
# Znajdź wykonane komendy
grep "CMD:" /var/log/fixell.log
```
