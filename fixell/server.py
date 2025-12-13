#!/usr/bin/env python3
"""Serwer naprawczy Fixell z integracją Ollama"""
import socket
import json
import urllib.request
import sys
import threading
import os

DEFAULT_PORT = 8088
DEFAULT_MODEL = "qwen2.5:14b"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

SYSTEM_PROMPT = """Jesteś ekspertem od naprawy systemów Linux (szczególnie Fedora, Ubuntu, Debian).
Gdy proponujesz komendę do wykonania na zdalnym komputerze, poprzedź ją prefiksem CMD: (jedna komenda na linię).
Przykład: CMD: journalctl -xb --no-pager | tail -50

Zasady:
1. Bądź zwięzły i konkretny
2. Najpierw diagnozuj (logi, status usług), potem naprawiaj
3. Pytaj o szczegóły gdy potrzeba
4. Ostrzegaj przed ryzykownymi operacjami
5. Odpowiadaj po polsku"""

def ask_ollama(context, model=DEFAULT_MODEL):
    """Wyślij zapytanie do Ollama"""
    try:
        data = json.dumps({
            "model": model, 
            "prompt": f"{SYSTEM_PROMPT}\n{context}\n[Asystent]:", 
            "stream": False
        }).encode()
        req = urllib.request.Request(
            f"{OLLAMA_HOST}/api/generate", 
            data=data, 
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())["response"]
    except Exception as e:
        return f"Błąd Ollama: {e}"

class FixellServer:
    """Serwer naprawczy Fixell"""
    
    def __init__(self, port=DEFAULT_PORT, model=DEFAULT_MODEL):
        self.port = port
        self.model = model
        self.clients = []
        self.server = None
    
    def handle_client(self, conn, addr):
        """Obsługa połączenia klienta"""
        print(f"[+] Klient: {addr}")
        context = ""
        conn.sendall(b"=== FIXELL SERVER CONNECTED ===\nOpisz problem lub wpisz 'help'\n---END---\n")
        
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
                    
                    if line.startswith("RESULT:"):
                        context += f"\n[Wynik komendy]: {line[7:]}"
                        continue
                    elif line.startswith("SKIP:"):
                        context += "\n[Użytkownik pominął komendę]"
                        continue
                    elif line.startswith("USER:"):
                        line = line[5:]
                    elif line.startswith("LOCAL:"):
                        print(f"[OPERATOR]: {line[6:]}")
                        context += f"\n[Operator serwera]: {line[6:]}"
                        response = ask_ollama(context, self.model)
                        context += f"\n[Asystent]: {response}"
                        conn.sendall(f"{response}\n---END---\n".encode())
                        continue
                    
                    context += f"\n[Użytkownik zdalny]: {line}"
                    print(f"[KLIENT]: {line}")
                    response = ask_ollama(context, self.model)
                    context += f"\n[Asystent]: {response}"
                    print(f"[AI]: {response[:100]}...")
                    conn.sendall(f"{response}\n---END---\n".encode())
            except Exception as e:
                print(f"[-] Błąd: {e}")
                break
        conn.close()
        print(f"[-] Rozłączono: {addr}")
    
    def server_input(self):
        """Pozwala operatorowi serwera wysyłać komendy"""
        print("\n[SERWER] Wpisz komendę dla AI (prefix 'to:' wysyła do klienta):")
        while True:
            try:
                cmd = input("SERVER> ")
                if cmd.startswith("to:") and self.clients:
                    for c in self.clients:
                        try:
                            c.sendall(f"[OPERATOR]: {cmd[3:]}\n---END---\n".encode())
                        except:
                            pass
            except:
                break
    
    def run(self):
        """Uruchom serwer"""
        print(f"=== FIXELL SERVER ===")
        print(f"Port: {self.port} | Model: {self.model} | Ollama: {OLLAMA_HOST}")
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("0.0.0.0", self.port))
        self.server.listen(5)
        print(f"Nasłuchiwanie na porcie {self.port}...")
        
        threading.Thread(target=self.server_input, daemon=True).start()
        
        while True:
            conn, addr = self.server.accept()
            self.clients.append(conn)
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    model = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MODEL
    server = FixellServer(port, model)
    server.run()

if __name__ == "__main__":
    main()
