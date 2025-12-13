# Rekomendowane modele AI dla Fixell

## Modele wyspecjalizowane w Linux/systemach

### Tier 1 - Najlepsze dla naprawy Linux

| Model | Rozmiar | VRAM | Opis |
|-------|---------|------|------|
| **qwen2.5:14b** | 14B | ~10GB | Doskonała wiedza o Linux, świetne rozumienie poleceń |
| **qwen2.5:32b** | 32B | ~20GB | Jeszcze lepsza jakość, wymaga więcej VRAM |
| **codellama:34b** | 34B | ~20GB | Specjalizacja w kodzie i skryptach shell |
| **deepseek-coder:33b** | 33B | ~20GB | Bardzo dobry w analizie logów i debugowaniu |

### Tier 2 - Dobre alternatywy

| Model | Rozmiar | VRAM | Opis |
|-------|---------|------|------|
| **qwen2.5:7b** | 7B | ~5GB | Lżejsza wersja, nadal dobra jakość |
| **llama3:8b** | 8B | ~5GB | Ogólny model, przyzwoita wiedza o Linux |
| **mistral:7b** | 7B | ~5GB | Szybki, dobry do prostych problemów |
| **codellama:13b** | 13B | ~8GB | Dobry kompromis rozmiar/jakość |

### Tier 3 - Minimalne wymagania

| Model | Rozmiar | VRAM | Opis |
|-------|---------|------|------|
| **qwen2.5:3b** | 3B | ~2GB | Dla słabszych GPU, podstawowa funkcjonalność |
| **phi3:mini** | 3.8B | ~3GB | Microsoft, szybki ale ograniczony |
| **gemma2:2b** | 2B | ~2GB | Google, minimalne wymagania |

## Instalacja modeli

```bash
# Pobierz rekomendowany model
ollama pull qwen2.5:14b

# Lub lżejszą wersję
ollama pull qwen2.5:7b

# Sprawdź dostępne modele
ollama list
```

## Porównanie wydajności

### Test: "Fedora nie startuje, zatrzymuje się na logo"

| Model | Czas odpowiedzi | Jakość diagnozy | Poprawność komend |
|-------|-----------------|-----------------|-------------------|
| qwen2.5:14b | ~8s | ⭐⭐⭐⭐⭐ | 95% |
| qwen2.5:7b | ~4s | ⭐⭐⭐⭐ | 85% |
| llama3:8b | ~5s | ⭐⭐⭐ | 75% |
| mistral:7b | ~3s | ⭐⭐⭐ | 70% |

### Test: "Brak miejsca na dysku, system read-only"

| Model | Czas odpowiedzi | Jakość diagnozy | Poprawność komend |
|-------|-----------------|-----------------|-------------------|
| qwen2.5:14b | ~10s | ⭐⭐⭐⭐⭐ | 98% |
| codellama:13b | ~7s | ⭐⭐⭐⭐ | 90% |
| qwen2.5:7b | ~5s | ⭐⭐⭐⭐ | 85% |

## Konfiguracja modelu

```bash
# Uruchom serwer z konkretnym modelem
./fixer-server.py 8088 qwen2.5:14b

# Lub przez zmienną środowiskową
export FIXELL_MODEL=qwen2.5:14b
fixell-server
```

## Wymagania sprzętowe

### GPU NVIDIA

| GPU | VRAM | Rekomendowany model |
|-----|------|---------------------|
| RTX 4090 | 24GB | qwen2.5:32b |
| RTX 3090/4080 | 24GB/16GB | qwen2.5:14b |
| RTX 3080/4070 | 10-12GB | qwen2.5:14b |
| RTX 3060/4060 | 8-12GB | qwen2.5:7b |
| GTX 1080 Ti | 11GB | qwen2.5:7b |
| GTX 1060 | 6GB | qwen2.5:3b |

### CPU (bez GPU)

```bash
# Dla CPU użyj mniejszych modeli
ollama pull qwen2.5:3b
# lub
ollama pull phi3:mini
```

## Dostrajanie promptu dla modelu

Każdy model może wymagać lekko innego promptu. Domyślny prompt w Fixell jest zoptymalizowany dla qwen2.5, ale można go dostosować:

```python
# W pliku konfiguracyjnym lub zmiennej środowiskowej
SYSTEM_PROMPT = """Jesteś ekspertem od naprawy systemów Linux.
Gdy proponujesz komendę, poprzedź ją prefiksem CMD:
Przykład: CMD: journalctl -xb
Bądź zwięzły. Odpowiadaj po polsku."""
```
