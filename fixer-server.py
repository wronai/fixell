#!/usr/bin/env python3
"""Serwer naprawczy z Ollama - uruchamia się na komputerze z GPU (nvidia)
Użycie: ./fixer-server.py [port] [model]
"""
import socket
import json
import urllib.request
import sys
import threading
import os
import logging
import base64
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Konfiguracja z .env lub domyślne
PORT = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8088))
HTTP_PORT = int(os.environ.get("HTTP_PORT", PORT + 1))
MODEL = os.environ.get("MODEL", sys.argv[2] if len(sys.argv) > 2 else "")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
LOG_DIR = os.environ.get("LOG_DIR", "logs")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
SESSION_TIMEOUT = int(os.environ.get("SESSION_TIMEOUT", 300))
AUTO_SELECT_MODEL = os.environ.get("AUTO_SELECT_MODEL", "true").lower() == "true"

# Ranking modeli dla naprawy Linux (jakość, szybkość estymowana)
# Jakość: 1-10 (10=najlepsza), Speed: 1-10 (10=najszybszy)
# Wyniki benchmarku jakości dla naprawy Linux (2024-12):
MODEL_RANKINGS = {
    # === TOP dla naprawy Linux (benchmark 10/10) ===
    "deepseek-r1:8b": {"quality": 10, "speed": 5, "vram": 5, "desc": "🏆 NAJLEPSZY do naprawy Linux!"},
    
    # === Bardzo dobre (benchmark 8-9/10) ===
    "qwen2.5:14b": {"quality": 9, "speed": 4, "vram": 10, "desc": "Bardzo dobra jakość, średni"},
    "mistral:7b": {"quality": 9, "speed": 6, "vram": 5, "desc": "Świetny do naprawy Linux"},
    "llama3.1:8b": {"quality": 9, "speed": 8, "vram": 5, "desc": "Świetny i szybki!"},
    "qwen2.5-coder:7b": {"quality": 9, "speed": 8, "vram": 4, "desc": "Świetny do kodu, szybki"},
    "mistral:7b-instruct": {"quality": 8, "speed": 5, "vram": 5, "desc": "Dobry do naprawy Linux"},
    "llava:7b": {"quality": 8, "speed": 6, "vram": 4, "desc": "Dobry, multimodalny"},
    "qwen2.5:7b": {"quality": 8, "speed": 8, "vram": 5, "desc": "Dobra jakość, szybki"},
    "qwen2.5:7b-instruct": {"quality": 8, "speed": 9, "vram": 5, "desc": "Najlepszy stosunek jakość/czas"},
    "codellama:7b": {"quality": 8, "speed": 7, "vram": 4, "desc": "Dobry do kodu"},
    
    # === Przyzwoite (benchmark 6-7/10) ===
    "deepseek-coder:6.7b": {"quality": 7, "speed": 6, "vram": 4, "desc": "OK do kodu"},
    "llava:13b": {"quality": 6, "speed": 5, "vram": 8, "desc": "Multimodalny, wolniejszy"},
    
    # === Słabe do naprawy Linux ===
    "deepseek-r1:7b": {"quality": 3, "speed": 4, "vram": 4, "desc": "Słaby do naprawy Linux"},
    "starcoder2:7b": {"quality": 2, "speed": 7, "vram": 4, "desc": "Tylko do kodu, nie do naprawy"},
    
    # === Duże modele (teoretyczne) ===
    "qwen2.5:72b": {"quality": 10, "speed": 1, "vram": 45, "desc": "Najlepsza jakość, bardzo wolny"},
    "qwen2.5:32b": {"quality": 9, "speed": 2, "vram": 20, "desc": "Świetna jakość, wolny"},
    "llama3.1:70b": {"quality": 9, "speed": 1, "vram": 42, "desc": "Świetna jakość, bardzo wolny"},
    "llama3:70b": {"quality": 9, "speed": 1, "vram": 42, "desc": "Świetna jakość, bardzo wolny"},
    "codellama:34b": {"quality": 8, "speed": 3, "vram": 20, "desc": "Dobry do kodu, wolny"},
    "codellama:13b": {"quality": 7, "speed": 5, "vram": 8, "desc": "Dobry do kodu, średni"},
    "mixtral:8x7b": {"quality": 8, "speed": 4, "vram": 26, "desc": "Dobra jakość, średni"},
    "deepseek-coder:33b": {"quality": 8, "speed": 3, "vram": 20, "desc": "Świetny do kodu, wolny"},
    
    # === Małe modele ===
    "qwen2.5:3b": {"quality": 5, "speed": 9, "vram": 2, "desc": "Podstawowa jakość, bardzo szybki"},
    "qwen2.5:1.5b": {"quality": 3, "speed": 10, "vram": 1, "desc": "Minimalna jakość, błyskawiczny"},
    "llama3:8b": {"quality": 6, "speed": 8, "vram": 5, "desc": "Przyzwoita jakość, szybki"},
    "deepseek-r1:1.5b": {"quality": 2, "speed": 10, "vram": 1, "desc": "Minimalna jakość, błyskawiczny"},
}

def get_available_models():
    """Pobierz listę dostępnych modeli z Ollama"""
    try:
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception as e:
        print(f"⚠️  Nie można połączyć z Ollama ({OLLAMA_HOST}): {e}")
        return []

def benchmark_model(model_name, test_prompt="Odpowiedz jednym słowem: Linux"):
    """Zmierz czas odpowiedzi modelu"""
    try:
        start = time.time()
        data = json.dumps({"model": model_name, "prompt": test_prompt, "stream": False}).encode()
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/generate", data=data, 
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
        elapsed = time.time() - start
        tokens = result.get("eval_count", 10)
        return {"time": elapsed, "tokens": tokens, "tps": tokens / elapsed if elapsed > 0 else 0, "response": result.get("response", "")}
    except Exception as e:
        return {"time": -1, "tokens": 0, "tps": 0, "error": str(e), "response": ""}

# Pytania testowe do oceny jakości modelu w kontekście naprawy Linux
LINUX_TEST_QUESTIONS = [
    {
        "question": "System Fedora nie startuje, zatrzymuje się na logo. Podaj komendy diagnostyczne.",
        "expected_keywords": ["journalctl", "dmesg", "systemctl", "boot", "CMD:"],
        "weight": 2.0
    },
    {
        "question": "Dysk jest pełny, system read-only. Jak to naprawić?",
        "expected_keywords": ["df", "du", "rm", "journal", "clean", "CMD:"],
        "weight": 1.5
    },
    {
        "question": "Brak połączenia sieciowego po aktualizacji. Co sprawdzić?",
        "expected_keywords": ["ip", "nmcli", "NetworkManager", "ping", "systemctl", "CMD:"],
        "weight": 1.5
    },
    {
        "question": "Usługa nginx nie startuje. Jak zdiagnozować?",
        "expected_keywords": ["systemctl", "status", "journalctl", "nginx", "CMD:"],
        "weight": 1.0
    },
    {
        "question": "Kernel panic po aktualizacji. Jak przywrócić poprzedni kernel?",
        "expected_keywords": ["grub", "kernel", "dracut", "boot", "CMD:"],
        "weight": 2.0
    }
]

def benchmark_quality(model_name, verbose=True):
    """Benchmark jakości odpowiedzi modelu na pytania o naprawę Linux"""
    if verbose:
        print(f"\n📊 Benchmark jakości: {model_name}")
        print("-" * 50)
    
    total_score = 0
    total_weight = 0
    total_time = 0
    results = []
    
    prompt_prefix = """Jesteś ekspertem od naprawy systemów Linux.
NIE ZADAWAJ PYTAŃ - od razu proponuj komendy diagnostyczne.
Każdą komendę poprzedź prefiksem CMD: (jedna komenda na linię).
Bądź zwięzły. Odpowiadaj po polsku.

Użytkownik: """
    
    for i, test in enumerate(LINUX_TEST_QUESTIONS, 1):
        if verbose:
            print(f"  Test {i}/{len(LINUX_TEST_QUESTIONS)}: ", end="", flush=True)
        
        full_prompt = prompt_prefix + test["question"]
        bench = benchmark_model(model_name, full_prompt)
        
        if bench["time"] < 0:
            if verbose:
                print("❌ błąd")
            continue
        
        response = bench["response"].lower()
        total_time += bench["time"]
        
        # Oblicz score na podstawie słów kluczowych
        found_keywords = sum(1 for kw in test["expected_keywords"] if kw.lower() in response)
        keyword_score = found_keywords / len(test["expected_keywords"])
        
        # Bonus za CMD: w odpowiedzi
        cmd_bonus = 0.2 if "cmd:" in response else 0
        
        # Kara za pytania zamiast komend
        question_penalty = -0.3 if "?" in bench["response"] and "cmd:" not in response else 0
        
        # Finalny score (0-1)
        score = min(1.0, max(0, keyword_score + cmd_bonus + question_penalty))
        weighted_score = score * test["weight"]
        
        total_score += weighted_score
        total_weight += test["weight"]
        
        results.append({
            "question": test["question"][:40],
            "score": score,
            "keywords_found": found_keywords,
            "keywords_total": len(test["expected_keywords"]),
            "time": bench["time"],
            "has_cmd": "cmd:" in response
        })
        
        if verbose:
            stars = "⭐" * int(score * 5)
            cmd_mark = "✓CMD" if "cmd:" in response else "✗CMD"
            print(f"{stars:5} {cmd_mark} ({bench['time']:.1f}s)")
    
    # Oblicz końcowy wynik
    final_score = (total_score / total_weight * 10) if total_weight > 0 else 0
    avg_time = total_time / len(LINUX_TEST_QUESTIONS) if LINUX_TEST_QUESTIONS else 0
    
    if verbose:
        print("-" * 50)
        print(f"  📈 Wynik końcowy: {final_score:.1f}/10")
        print(f"  ⏱️  Średni czas: {avg_time:.1f}s")
    
    return {
        "model": model_name,
        "score": final_score,
        "avg_time": avg_time,
        "total_time": total_time,
        "results": results
    }

def run_quality_benchmark(models_to_test=None):
    """Uruchom benchmark jakości dla modeli 7b-14b"""
    available = get_available_models()
    
    if not available:
        print("❌ Brak dostępnych modeli!")
        return []
    
    # Filtruj modele 7b-14b jeśli nie podano listy
    if models_to_test is None:
        models_to_test = []
        for m in available:
            # Szukaj modeli 7b, 8b, 13b, 14b
            m_lower = m.lower()
            if any(size in m_lower for size in ["7b", "8b", "13b", "14b", "6.7b", "6b"]):
                models_to_test.append(m)
    
    if not models_to_test:
        print("❌ Brak modeli 7b-14b do testowania!")
        print("   Dostępne modele:", available[:5])
        return []
    
    print("\n" + "="*60)
    print("🧪 BENCHMARK JAKOŚCI MODELI (naprawa Linux)")
    print("="*60)
    print(f"Testowane modele ({len(models_to_test)}): {', '.join(models_to_test)}")
    print(f"Pytań testowych: {len(LINUX_TEST_QUESTIONS)}")
    
    results = []
    for model in models_to_test:
        result = benchmark_quality(model, verbose=True)
        results.append(result)
    
    # Podsumowanie
    print("\n" + "="*60)
    print("📊 PODSUMOWANIE BENCHMARKU")
    print("="*60)
    
    # Sortuj po score
    results.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"\n{'Model':<30} {'Jakość':>10} {'Śr. czas':>10}")
    print("-" * 52)
    for r in results:
        score_bar = "█" * int(r["score"]) + "░" * (10 - int(r["score"]))
        print(f"{r['model']:<30} {score_bar} {r['score']:>4.1f}/10 {r['avg_time']:>6.1f}s")
    
    if results:
        best = results[0]
        print(f"\n🏆 Najlepszy model: {best['model']} ({best['score']:.1f}/10)")
        
        # Znajdź najlepszy stosunek jakość/czas
        best_ratio = max(results, key=lambda x: x["score"] / (x["avg_time"] + 1))
        if best_ratio["model"] != best["model"]:
            print(f"⚡ Najlepszy stosunek jakość/czas: {best_ratio['model']}")
    
    return results

def select_model_interactive(available_models):
    """Interaktywny wybór modelu przez użytkownika"""
    print("\n" + "="*60)
    print("🔍 WYKRYWANIE OPTYMALNEGO MODELU LLM")
    print("="*60)
    
    if not available_models:
        print("❌ Brak dostępnych modeli w Ollama!")
        print(f"   Uruchom: ollama pull qwen2.5:7b")
        sys.exit(1)
    
    # Filtruj modele które znamy
    known_models = []
    unknown_models = []
    for m in available_models:
        base_name = m.split(":")[0] + ":" + m.split(":")[-1] if ":" in m else m
        if base_name in MODEL_RANKINGS or m in MODEL_RANKINGS:
            known_models.append(m)
        else:
            unknown_models.append(m)
    
    print(f"\n📦 Dostępne modele ({len(available_models)}):")
    
    # Sortuj znane modele po jakości
    def get_quality(m):
        base = m.split(":")[0] + ":" + m.split(":")[-1] if ":" in m else m
        return MODEL_RANKINGS.get(base, MODEL_RANKINGS.get(m, {"quality": 5}))["quality"]
    
    known_models.sort(key=get_quality, reverse=True)
    
    all_sorted = known_models + unknown_models
    
    for i, m in enumerate(all_sorted, 1):
        base = m.split(":")[0] + ":" + m.split(":")[-1] if ":" in m else m
        info = MODEL_RANKINGS.get(base, MODEL_RANKINGS.get(m, None))
        if info:
            stars = "⭐" * info["quality"]
            speed = "🚀" * (info["speed"] // 3 + 1)
            print(f"  {i}. {m:25} {stars:12} {speed} ({info['desc']})")
        else:
            print(f"  {i}. {m:25} (nieznany)")
    
    # Znajdź najlepszy i najszybszy
    best_quality = known_models[0] if known_models else all_sorted[0]
    fastest = None
    for m in known_models:
        base = m.split(":")[0] + ":" + m.split(":")[-1] if ":" in m else m
        info = MODEL_RANKINGS.get(base, MODEL_RANKINGS.get(m, None))
        if info and (fastest is None or info["speed"] > MODEL_RANKINGS.get(fastest, {"speed": 0})["speed"]):
            fastest = m
    
    if not fastest:
        fastest = all_sorted[-1] if all_sorted else best_quality
    
    print(f"\n🏆 Rekomendacje:")
    print(f"   [B] Najlepsza jakość: {best_quality}")
    print(f"   [S] Najszybszy:       {fastest}")
    print(f"   [T] Test szybkości (benchmark)")
    print(f"   [Q] Test jakości dla naprawy Linux (7b-14b)")
    print(f"   [1-{len(all_sorted)}] Wybierz ręcznie")
    
    while True:
        choice = input("\n👉 Wybierz model [B/S/T/Q/numer]: ").strip().upper()
        
        if choice == "B":
            return best_quality
        elif choice == "S":
            return fastest
        elif choice == "T":
            print("\n⏱️  Uruchamiam benchmark szybkości...")
            results = []
            for m in all_sorted[:5]:  # Max 5 modeli
                print(f"   Testuję {m}...", end=" ", flush=True)
                bench = benchmark_model(m)
                if bench["time"] > 0:
                    print(f"✓ {bench['tps']:.1f} tok/s ({bench['time']:.1f}s)")
                    results.append((m, bench))
                else:
                    print(f"✗ błąd")
            
            if results:
                results.sort(key=lambda x: x[1]["tps"], reverse=True)
                print(f"\n🥇 Najszybszy: {results[0][0]} ({results[0][1]['tps']:.1f} tok/s)")
                return results[0][0]
            continue
        elif choice == "Q":
            # Benchmark jakości dla modeli 7b-14b
            quality_results = run_quality_benchmark()
            if quality_results:
                best = quality_results[0]
                use_best = input(f"\n🏆 Użyć najlepszego ({best['model']})? [T/n]: ").strip().lower()
                if use_best != "n":
                    return best["model"]
            continue
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(all_sorted):
                return all_sorted[idx]
        
        print("❌ Nieprawidłowy wybór, spróbuj ponownie")

# Utwórz katalog logów
os.makedirs(LOG_DIR, exist_ok=True)

# Konfiguracja logowania
log_file = os.path.join(LOG_DIR, f"fixell_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('fixell')

def get_local_ip():
    """Pobierz lokalne IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

LOCAL_IP = get_local_ip()

def log_session(client_addr, message_type, content):
    """Zapisz log sesji do osobnego pliku"""
    session_file = os.path.join(LOG_DIR, f"session_{client_addr[0].replace('.', '_')}_{datetime.now().strftime('%Y%m%d')}.log")
    with open(session_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} [{message_type}] {content}\n")

def log_conversation(client_addr, role, content):
    """Zapisz pełną konwersację do osobnego pliku - czytelny format"""
    conv_file = os.path.join(LOG_DIR, f"conversation_{client_addr[0].replace('.', '_')}_{datetime.now().strftime('%Y%m%d')}.md")
    with open(conv_file, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime('%H:%M:%S')
        if role == "USER":
            f.write(f"\n---\n### [{timestamp}] 👤 Użytkownik:\n{content}\n")
        elif role == "AI":
            f.write(f"\n### [{timestamp}] 🤖 AI:\n{content}\n")
        elif role == "CMD_RESULT":
            f.write(f"\n### [{timestamp}] 💻 Wynik komendy:\n```\n{content}\n```\n")
        elif role == "CMD_SKIP":
            f.write(f"\n### [{timestamp}] ⏭️ Komenda pominięta\n")
        elif role == "OPERATOR":
            f.write(f"\n### [{timestamp}] 👨‍💻 Operator:\n{content}\n")
        elif role == "CONNECT":
            f.write(f"\n# Sesja naprawcza - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Klient:** {client_addr[0]}:{client_addr[1]}\n")
        elif role == "DISCONNECT":
            f.write(f"\n---\n**Sesja zakończona:** {timestamp}\n")

SYSTEM_PROMPT_SHELL = """Jesteś ekspertem od naprawy systemów Linux (Fedora, Ubuntu, Debian).

ZASADY:
1. NIE ZADAWAJ PYTAŃ - od razu proponuj komendy diagnostyczne
2. Każdą komendę poprzedź prefiksem CMD: (jedna komenda na linię)
3. Zacznij od podstawowej diagnostyki: logi, dysk, usługi
4. Analizuj wyniki i proponuj kolejne kroki lub naprawę
5. Bądź zwięzły i konkretny

Gdy użytkownik opisuje problem, OD RAZU daj komendy diagnostyczne:
CMD: journalctl -xb --no-pager | tail -100
CMD: systemctl --failed
CMD: df -h
CMD: dmesg | tail -50

Odpowiadaj po polsku. Nie pytaj - działaj."""

SYSTEM_PROMPT_CURL = """Jesteś ekspertem od naprawy systemów Linux (Fedora, Ubuntu, Debian).

ZASADY:
1. NIE ZADAWAJ PYTAŃ - od razu proponuj komendy diagnostyczne
2. Podawaj GOTOWE komendy curl do skopiowania
3. Zacznij od podstawowej diagnostyki
4. Analizuj wyniki i proponuj kolejne kroki

Format komendy:
curl -X POST http://{server}/result -d "$(<KOMENDA>)"

Gdy użytkownik opisuje problem, OD RAZU daj gotowe komendy:
curl -X POST http://{server}/result -d "$(journalctl -xb --no-pager | tail -100)"
curl -X POST http://{server}/result -d "$(systemctl --failed)"
curl -X POST http://{server}/result -d "$(df -h)"

Odpowiadaj po polsku. Nie pytaj - działaj."""

CLIENT_SCRIPT = '''#!/bin/bash
# Fixell Client - pobrano z serwera
HOST="${1%:*}"; PORT="${1#*:}"
[[ -z "$HOST" ]] && echo "Użycie: $0 host:port" && exit 1
exec 3<>/dev/tcp/$HOST/$PORT || { echo "Błąd połączenia"; exit 1; }
echo "Połączono z $HOST:$PORT"

send_result() {
    # Wysyła wynik zakodowany w base64 aby zachować wieloliniowość
    local R="$1"
    local B64=$(echo "$R" | base64 -w 0)
    echo "RESULT64:$B64" >&3
}

while IFS= read -r -t 2 L <&3; do [[ "$L" == "---END---" ]] && break; echo "$L"; done
while true; do
    while IFS= read -r -t 0.5 L <&3 2>/dev/null; do
        [[ "$L" == "---END---" ]] && break
        if [[ "$L" == EXEC:* ]]; then
            ECMD="${L#EXEC:}"
            echo -e "\n[AUTO-EXEC]: $ECMD"
            R=$(eval "$ECMD" 2>&1)
            echo "$R"
            send_result "$R"
        elif [[ "$L" == CMD:* ]]; then
            echo -e "\n[KOMENDA]: ${L#CMD:}"
            read -p "Wykonać? (t/n): " C
            [[ "$C" == "t" ]] && { R=$(eval "${L#CMD:}" 2>&1); echo "$R"; send_result "$R"; } || echo "SKIP:" >&3
        else echo "$L"; fi
    done
    read -t 1 -p "> " CMD || continue
    [[ -z "$CMD" ]] && continue
    [[ "$CMD" == "exit" ]] && break
    echo "$CMD" >&3
    while IFS= read -r -t 30 L <&3; do
        [[ "$L" == "---END---" ]] && break
        if [[ "$L" == EXEC:* ]]; then
            ECMD="${L#EXEC:}"
            echo -e "\n[AUTO-EXEC]: $ECMD"
            R=$(eval "$ECMD" 2>&1)
            echo "$R"
            send_result "$R"
        elif [[ "$L" == CMD:* ]]; then
            echo -e "\n[KOMENDA]: ${L#CMD:}"
            read -p "Wykonać? (t/n): " C
            [[ "$C" == "t" ]] && { R=$(eval "${L#CMD:}" 2>&1); echo "$R"; send_result "$R"; } || echo "SKIP:" >&3
        else echo "$L"; fi
    done
done
exec 3<&-
'''

# Przechowuj kontekst sesji HTTP per IP
http_sessions = {}

class ClientHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass
    
    def do_POST(self):
        """Obsługa zapytań POST - prosty tryb curl"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8').strip() if content_length > 0 else ""
        client_ip = self.client_address[0]
        
        if self.path == "/ask":
            # Proste pytanie: curl -X POST http://server:8089/ask -d "opis problemu"
            if not body:
                self.send_response(400)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Brak pytania. Uzycie: curl -X POST http://server:8089/ask -d 'opis problemu'")
                return
            
            # Pobierz lub utwórz kontekst sesji
            if client_ip not in http_sessions:
                http_sessions[client_ip] = {"context": "", "last_cmd": None}
                log_conversation((client_ip, 0), "CONNECT", "")
            
            session = http_sessions[client_ip]
            session["context"] += f"\n[Użytkownik]: {body}"
            
            logger.info(f"[HTTP/ASK] {client_ip}: {body}")
            log_conversation((client_ip, 0), "USER", body)
            
            response = ask_ollama(session["context"], mode="curl")
            session["context"] += f"\n[Asystent]: {response}"
            
            logger.info(f"[HTTP/AI] {response[:100]}...")
            log_conversation((client_ip, 0), "AI", response)
            
            # Wyciągnij komendy CMD:
            commands = [line.strip()[4:].strip() for line in response.split('\n') if line.strip().startswith("CMD:")]
            if commands:
                session["last_cmd"] = commands[0]
            
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        elif self.path == "/result":
            # Wyślij wynik komendy: curl -X POST http://server:8089/result -d "wynik komendy"
            if client_ip not in http_sessions:
                self.send_response(400)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Brak aktywnej sesji. Najpierw wyslij /ask")
                return
            
            session = http_sessions[client_ip]
            session["context"] += f"\n[Wynik komendy]: {body}"
            
            logger.info(f"[HTTP/RESULT] {client_ip}: {body[:100]}...")
            log_conversation((client_ip, 0), "CMD_RESULT", body)
            
            # AI analizuje wynik
            response = ask_ollama(session["context"], mode="curl")
            session["context"] += f"\n[Asystent]: {response}"
            
            logger.info(f"[HTTP/AI] {response[:100]}...")
            log_conversation((client_ip, 0), "AI", response)
            
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        elif self.path == "/reset":
            # Reset sesji: curl -X POST http://server:8089/reset
            if client_ip in http_sessions:
                log_conversation((client_ip, 0), "DISCONNECT", "")
                del http_sessions[client_ip]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Sesja zresetowana")
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Nieznany endpoint")
    
    def do_GET(self):
        if self.path in ["/get", "/client", "/fixer.sh"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/x-shellscript")
            self.send_header("Content-Disposition", "attachment; filename=fixer.sh")
            self.end_headers()
            self.wfile.write(CLIENT_SCRIPT.encode())
            logger.info(f"[HTTP] Klient pobrany przez {self.client_address[0]}")
        elif self.path == "/run":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(CLIENT_SCRIPT.encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "model": MODEL, "sessions": len(http_sessions)}).encode())
        else:
            host = self.headers.get('Host', f'{get_local_ip()}:{HTTP_PORT}')
            server_ip = host.split(':')[0] if ':' in host else host
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"""Fixell Server - API

=== Tryb interaktywny (skrypt) ===
  curl -O http://{host}/get && chmod +x fixer.sh && ./fixer.sh {server_ip}:{PORT}

=== Tryb prosty (curl) ===
  # Zadaj pytanie:
  curl -X POST http://{host}/ask -d "moj system nie startuje"
  
  # Wyslij wynik komendy:
  curl -X POST http://{host}/result -d "$(journalctl -xb | tail -50)"
  
  # Reset sesji:
  curl -X POST http://{host}/reset

=== Healthcheck ===
  curl http://{host}/health
""".encode())

def run_http_server():
    httpd = HTTPServer(("0.0.0.0", HTTP_PORT), ClientHandler)
    logger.info(f"HTTP serwer na porcie {HTTP_PORT} (curl http://{LOCAL_IP}:{HTTP_PORT}/get)")
    httpd.serve_forever()

def ask_ollama(context, mode="shell"):
    """Zapytaj Ollama - mode: 'shell' lub 'curl'"""
    try:
        if mode == "curl":
            prompt_template = SYSTEM_PROMPT_CURL.replace("{server}", f"{LOCAL_IP}:{HTTP_PORT}")
        else:
            prompt_template = SYSTEM_PROMPT_SHELL
        
        data = json.dumps({"model": MODEL, "prompt": f"{prompt_template}\n{context}\n[Asystent]:", "stream": False}).encode()
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/generate", data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())["response"]
    except Exception as e:
        return f"Błąd Ollama: {e}"

def handle_client(conn, addr):
    logger.info(f"[+] Klient połączony: {addr}")
    log_session(addr, "CONNECT", f"Nowe połączenie z {addr}")
    log_conversation(addr, "CONNECT", "")
    context = ""
    conn.sendall(b"=== FIXER SERVER CONNECTED ===\nOpisz problem lub wpisz 'help'\n---END---\n")
    
    buffer = ""
    while True:
        try:
            data = conn.recv(4096).decode()
            if not data:
                break
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith("RESULT64:"):
                    # Wynik zakodowany w base64 (wieloliniowy)
                    try:
                        result = base64.b64decode(line[9:]).decode('utf-8', errors='replace')
                    except:
                        result = line[9:]
                    context += f"\n[Wynik komendy]:\n{result}"
                    log_session(addr, "RESULT", result[:500])
                    log_conversation(addr, "CMD_RESULT", result)
                    logger.info(f"[RESULT] {addr}: {result[:100]}...")
                    continue
                elif line.startswith("RESULT:"):
                    # Stary format (jednoliniowy) - zachowany dla kompatybilności
                    result = line[7:]
                    context += f"\n[Wynik komendy]: {result}"
                    log_session(addr, "RESULT", result[:500])
                    log_conversation(addr, "CMD_RESULT", result)
                    logger.debug(f"[RESULT] {addr}: {result[:100]}...")
                    continue
                elif line.startswith("SKIP:"):
                    context += "\n[Użytkownik pominął komendę]"
                    log_session(addr, "SKIP", "Komenda pominięta")
                    log_conversation(addr, "CMD_SKIP", "")
                    continue
                elif line.startswith("USER:"):
                    line = line[5:]
                elif line.startswith("LOCAL:"):
                    logger.info(f"[OPERATOR]: {line[6:]}")
                    log_session(addr, "OPERATOR", line[6:])
                    log_conversation(addr, "OPERATOR", line[6:])
                    context += f"\n[Operator serwera]: {line[6:]}"
                    response = ask_ollama(context)
                    context += f"\n[Asystent]: {response}"
                    log_session(addr, "AI", response)
                    log_conversation(addr, "AI", response)
                    conn.sendall(f"{response}\n---END---\n".encode())
                    continue
                
                context += f"\n[Użytkownik zdalny]: {line}"
                logger.info(f"[KLIENT] {addr}: {line}")
                log_session(addr, "USER", line)
                log_conversation(addr, "USER", line)
                response = ask_ollama(context)
                context += f"\n[Asystent]: {response}"
                logger.info(f"[AI] {response[:100]}...")
                log_session(addr, "AI", response)
                log_conversation(addr, "AI", response)
                conn.sendall(f"{response}\n---END---\n".encode())
        except Exception as e:
            logger.error(f"[-] Błąd klienta {addr}: {e}")
            log_session(addr, "ERROR", str(e))
            break
    conn.close()
    logger.info(f"[-] Rozłączono: {addr}")
    log_session(addr, "DISCONNECT", "Sesja zakończona")
    log_conversation(addr, "DISCONNECT", "")

def server_input(clients):
    """Pozwala operatorowi serwera wysyłać komendy do klientów"""
    logger.info("""[SERWER] Komendy:
  to: <msg>     - wyślij wiadomość do klientów
  run: <cmd>    - wyślij komendę do wykonania (klient wykona automatycznie)
  exec: <cmd>   - wyślij komendę CMD: (klient potwierdzi)
  status        - pokaż liczbę klientów
  config        - pokaż konfigurację
  help          - pokaż pomoc""")
    while True:
        try:
            cmd = input("SERVER> ")
            if cmd.startswith("to:") and clients:
                # Wyślij wiadomość
                for c in clients:
                    try:
                        c.sendall(f"[OPERATOR]: {cmd[3:]}\n---END---\n".encode())
                        logger.info(f"[OPERATOR->KLIENT] {cmd[3:]}")
                    except:
                        pass
            elif cmd.startswith("run:") and clients:
                # Wyślij komendę do natychmiastowego wykonania (bez potwierdzenia)
                shell_cmd = cmd[4:].strip()
                for c in clients:
                    try:
                        c.sendall(f"EXEC:{shell_cmd}\n---END---\n".encode())
                        logger.info(f"[EXEC->KLIENT] {shell_cmd}")
                    except:
                        pass
            elif cmd.startswith("exec:") and clients:
                # Wyślij komendę CMD: (klient potwierdzi)
                shell_cmd = cmd[5:].strip()
                for c in clients:
                    try:
                        c.sendall(f"CMD:{shell_cmd}\n---END---\n".encode())
                        logger.info(f"[CMD->KLIENT] {shell_cmd}")
                    except:
                        pass
            elif cmd == "status":
                logger.info(f"Aktywnych klientów: {len(clients)}, sesji HTTP: {len(http_sessions)}")
            elif cmd == "config":
                logger.info(f"PORT={PORT}, HTTP_PORT={HTTP_PORT}, MODEL={MODEL}")
                logger.info(f"OLLAMA_HOST={OLLAMA_HOST}, LOG_DIR={LOG_DIR}")
            elif cmd == "help":
                logger.info("to: <msg> - wiadomość, run: <cmd> - wykonaj, exec: <cmd> - z potwierdzeniem")
        except:
            break

# Wybór modelu przy starcie
if not MODEL or AUTO_SELECT_MODEL:
    available = get_available_models()
    if available:
        if MODEL and MODEL in available:
            print(f"✓ Używam modelu z konfiguracji: {MODEL}")
        else:
            MODEL = select_model_interactive(available)
            print(f"\n✓ Wybrany model: {MODEL}")
    else:
        print("❌ Ollama niedostępna lub brak modeli!")
        print(f"   Sprawdź czy Ollama działa: curl {OLLAMA_HOST}/api/tags")
        sys.exit(1)

logger.info(f"=== FIXER SERVER ===\nPort: {PORT} | Model: {MODEL} | Ollama: {OLLAMA_HOST}")
logger.info(f"Logi zapisywane do: {log_file}")
clients = []
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", PORT))
server.listen(5)
logger.info(f"Nasłuchiwanie na porcie {PORT}...")

threading.Thread(target=run_http_server, daemon=True).start()
threading.Thread(target=server_input, args=(clients,), daemon=True).start()

while True:
    conn, addr = server.accept()
    clients.append(conn)
    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
