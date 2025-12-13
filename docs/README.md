# Dokumentacja Fixell

## Spis treści

- [Wprowadzenie](introduction.md)
- [Instalacja](installation.md)
- [Użycie](usage.md)
- [Modele AI](models.md)
- [API](api.md)
- [Bezpieczeństwo](security.md)
- [Rozwiązywanie problemów](troubleshooting.md)

## Szybki start

```bash
# Instalacja
pip install fixell

# Serwer (na maszynie z GPU)
fixell-server 8088 qwen2.5:14b

# Klient (na maszynie z problemem)
fixell-client nvidia:8088
```

## Architektura

```
┌─────────────────────┐         ┌─────────────────────┐
│ Komputer z problemem│         │  Serwer z GPU       │
│  (Fedora/Ubuntu)    │         │  (nvidia)           │
│                     │         │                     │
│  ┌───────────────┐  │  TCP    │  ┌───────────────┐  │
│  │ fixell-client │──┼────────►│  │ fixell-server │  │
│  └───────────────┘  │  :8088  │  └───────┬───────┘  │
│         │           │         │          │          │
│         ▼           │         │          ▼          │
│  Wykonuje komendy   │         │  ┌───────────────┐  │
│  (z potwierdzeniem) │         │  │    Ollama     │  │
│                     │         │  │  qwen2.5:14b  │  │
│                     │         │  └───────────────┘  │
└─────────────────────┘         └─────────────────────┘
```
