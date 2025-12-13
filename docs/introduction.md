# Wprowadzenie do Fixell

## Co to jest Fixell?

Fixell to narzędzie do zdalnej naprawy systemów Linux (szczególnie Fedora, Ubuntu, Debian) w trybie awaryjnym, wykorzystujące modele AI przez Ollama.

## Problem

Gdy system Linux nie startuje lub ma poważne problemy:
- Nie masz dostępu do przeglądarki
- Nie możesz łatwo szukać rozwiązań
- Tryb awaryjny ma ograniczone możliwości
- Potrzebujesz eksperta

## Rozwiązanie

Fixell pozwala:
1. Połączyć się z serwerem AI na innym komputerze
2. Opisać problem w naturalnym języku
3. Otrzymać propozycje komend diagnostycznych
4. Wykonać komendy z potwierdzeniem
5. AI analizuje wyniki i proponuje rozwiązanie

## Kluczowe cechy

- **Minimalny klient** - działa w trybie awaryjnym (tylko bash)
- **Bezpieczeństwo** - każda komenda wymaga potwierdzenia
- **AI ekspert** - modele wyspecjalizowane w Linux
- **Offline** - Ollama działa lokalnie, bez internetu
- **Open source** - MIT license

## Przypadki użycia

1. **System nie bootuje** - diagnoza i naprawa bootloadera
2. **Brak miejsca na dysku** - znajdowanie i czyszczenie
3. **Problemy z siecią** - konfiguracja i debugowanie
4. **Uszkodzone pakiety** - naprawa RPM/APT
5. **Problemy z GPU** - sterowniki NVIDIA/AMD
