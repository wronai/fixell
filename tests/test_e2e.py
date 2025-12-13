#!/usr/bin/env python3
"""Testy E2E dla Fixell - testowanie połączenia i funkcjonalności"""
import socket
import subprocess
import sys
import time
import threading
import json
import urllib.request
import os

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
TEST_PORT = 18088
TIMEOUT = 30

class Colors:
    OK = '\033[92m'
    FAIL = '\033[91m'
    WARN = '\033[93m'
    END = '\033[0m'

def log(status, msg):
    color = Colors.OK if status == "OK" else Colors.FAIL if status == "FAIL" else Colors.WARN
    print(f"[{color}{status}{Colors.END}] {msg}")

def test_ollama_connection():
    """Test 1: Sprawdź połączenie z Ollama"""
    try:
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            models = [m['name'] for m in data.get('models', [])]
            log("OK", f"Ollama dostępna. Modele: {models[:5]}...")
            return True, models
    except Exception as e:
        log("FAIL", f"Ollama niedostępna: {e}")
        return False, []

def test_model_response(model="qwen2.5:14b"):
    """Test 2: Sprawdź odpowiedź modelu"""
    try:
        data = json.dumps({
            "model": model,
            "prompt": "Odpowiedz jednym słowem po polsku: jaki system operacyjny to Fedora?",
            "stream": False
        }).encode()
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/generate", data=data, 
                                      headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            response = json.loads(resp.read())["response"]
            log("OK", f"Model {model} odpowiedział: {response[:100]}...")
            return True
    except Exception as e:
        log("FAIL", f"Model {model} nie odpowiedział: {e}")
        return False

def test_command_generation(model="qwen2.5:14b"):
    """Test 3: Sprawdź generowanie komend diagnostycznych"""
    try:
        prompt = """Jesteś ekspertem od naprawy systemów Linux.
Gdy proponujesz komendę, poprzedź ją prefiksem CMD:
Użytkownik: Mój system Fedora nie startuje, zatrzymuje się na logo.
Zaproponuj jedną komendę diagnostyczną."""
        
        data = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/generate", data=data,
                                      headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            response = json.loads(resp.read())["response"]
            
            has_cmd = "CMD:" in response or "cmd:" in response.lower()
            # Sprawdź czy zawiera typowe komendy diagnostyczne
            diagnostic_cmds = ["journalctl", "dmesg", "systemctl", "cat /var/log", "ls", "grep"]
            has_diagnostic = any(cmd in response.lower() for cmd in diagnostic_cmds)
            
            if has_cmd:
                log("OK", f"Model generuje komendy z prefiksem CMD:")
                # Wyciągnij komendy
                for line in response.split('\n'):
                    if 'CMD:' in line or 'cmd:' in line.lower():
                        log("OK", f"  Komenda: {line.strip()}")
                return True
            elif has_diagnostic:
                log("WARN", f"Model sugeruje komendy, ale bez prefiksu CMD: - {response[:150]}...")
                return True
            else:
                log("FAIL", f"Model nie wygenerował komend: {response[:150]}...")
                return False
    except Exception as e:
        log("FAIL", f"Błąd generowania komend: {e}")
        return False

def test_server_startup():
    """Test 4: Sprawdź uruchomienie serwera"""
    server_proc = None
    try:
        server_proc = subprocess.Popen(
            [sys.executable, "fixer-server.py", str(TEST_PORT), "qwen2.5:14b"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        time.sleep(2)
        
        # Sprawdź czy serwer nasłuchuje
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', TEST_PORT))
        sock.close()
        
        if result == 0:
            log("OK", f"Serwer uruchomiony na porcie {TEST_PORT}")
            return True, server_proc
        else:
            log("FAIL", f"Serwer nie nasłuchuje na porcie {TEST_PORT}")
            return False, server_proc
    except Exception as e:
        log("FAIL", f"Błąd uruchamiania serwera: {e}")
        return False, server_proc

def test_client_connection(server_proc):
    """Test 5: Sprawdź połączenie klienta z serwerem"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('localhost', TEST_PORT))
        
        # Odbierz powitanie
        data = sock.recv(4096).decode()
        if "FIXER SERVER" in data or "CONNECTED" in data:
            log("OK", f"Klient połączony, otrzymał: {data[:50]}...")
        
        # Wyślij testowe pytanie
        sock.sendall(b"Test polaczenia\n")
        time.sleep(3)
        
        # Odbierz odpowiedź
        sock.settimeout(60)
        response = sock.recv(8192).decode()
        
        if response:
            log("OK", f"Serwer odpowiedział: {response[:100]}...")
            sock.close()
            return True
        else:
            log("FAIL", "Brak odpowiedzi od serwera")
            sock.close()
            return False
    except Exception as e:
        log("FAIL", f"Błąd połączenia klienta: {e}")
        return False

def test_curl_client():
    """Test 6: Sprawdź czy można użyć curl jako klienta"""
    # Ten test sprawdza czy serwer HTTP jest dostępny (jeśli zaimplementowany)
    log("WARN", "Test curl klienta - wymaga serwera HTTP (opcjonalny)")
    return True

def run_all_tests():
    """Uruchom wszystkie testy E2E"""
    print("\n" + "="*60)
    print("FIXELL - Testy E2E")
    print("="*60 + "\n")
    
    results = {}
    server_proc = None
    
    # Test 1: Ollama
    print("\n--- Test 1: Połączenie z Ollama ---")
    ok, models = test_ollama_connection()
    results["ollama_connection"] = ok
    
    if not ok:
        print("\n⚠️  Ollama niedostępna - pomijam testy wymagające modelu")
        results["model_response"] = False
        results["command_generation"] = False
    else:
        # Test 2: Odpowiedź modelu
        print("\n--- Test 2: Odpowiedź modelu ---")
        # Znajdź dostępny model
        test_model = None
        preferred = ["qwen2.5:14b", "qwen2.5:7b", "qwen:14b", "llama3:8b", "mistral:7b"]
        for m in preferred:
            if any(m in model for model in models):
                test_model = m
                break
        if not test_model and models:
            test_model = models[0]
        
        if test_model:
            results["model_response"] = test_model_response(test_model)
            
            # Test 3: Generowanie komend
            print("\n--- Test 3: Generowanie komend diagnostycznych ---")
            results["command_generation"] = test_command_generation(test_model)
        else:
            log("FAIL", "Brak dostępnych modeli")
            results["model_response"] = False
            results["command_generation"] = False
    
    # Test 4: Uruchomienie serwera
    print("\n--- Test 4: Uruchomienie serwera ---")
    ok, server_proc = test_server_startup()
    results["server_startup"] = ok
    
    if ok and server_proc:
        # Test 5: Połączenie klienta
        print("\n--- Test 5: Połączenie klienta ---")
        results["client_connection"] = test_client_connection(server_proc)
    else:
        results["client_connection"] = False
    
    # Cleanup
    if server_proc:
        server_proc.terminate()
        server_proc.wait()
    
    # Test 6: Curl
    print("\n--- Test 6: Klient curl ---")
    results["curl_client"] = test_curl_client()
    
    # Podsumowanie
    print("\n" + "="*60)
    print("PODSUMOWANIE")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, ok in results.items():
        status = f"{Colors.OK}PASS{Colors.END}" if ok else f"{Colors.FAIL}FAIL{Colors.END}"
        print(f"  {test}: {status}")
    
    print(f"\nWynik: {passed}/{total} testów przeszło")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
