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
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Konfiguracja z .env lub domyślne
PORT = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8088))
HTTP_PORT = int(os.environ.get("HTTP_PORT", PORT + 1))
MODEL = os.environ.get("MODEL", sys.argv[2] if len(sys.argv) > 2 else "qwen2.5:14b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
LOG_DIR = os.environ.get("LOG_DIR", "logs")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
SESSION_TIMEOUT = int(os.environ.get("SESSION_TIMEOUT", 300))

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

SYSTEM_PROMPT = """Jesteś ekspertem od naprawy systemów Linux (szczególnie Fedora).
Gdy proponujesz komendę do wykonania na zdalnym komputerze, poprzedź ją prefiksem CMD: (jedna komenda na linię).
Bądź zwięzły. Najpierw diagnozuj, potem naprawiaj. Pytaj o logi i status usług.
Odpowiadaj po polsku."""

CLIENT_SCRIPT = '''#!/bin/bash
# Fixell Client - pobrano z serwera
HOST="${1%:*}"; PORT="${1#*:}"
[[ -z "$HOST" ]] && echo "Użycie: $0 host:port" && exit 1
exec 3<>/dev/tcp/$HOST/$PORT || { echo "Błąd połączenia"; exit 1; }
echo "Połączono z $HOST:$PORT"
while IFS= read -r -t 2 L <&3; do [[ "$L" == "---END---" ]] && break; echo "$L"; done
while read -p "> " CMD; do
    [[ "$CMD" == "exit" ]] && break
    echo "$CMD" >&3
    while IFS= read -r -t 30 L <&3; do
        [[ "$L" == "---END---" ]] && break
        if [[ "$L" == CMD:* ]]; then
            echo -e "\n[KOMENDA]: ${L#CMD:}"
            read -p "Wykonać? (t/n): " C
            [[ "$C" == "t" ]] && { R=$(eval "${L#CMD:}" 2>&1); echo "$R"; echo "RESULT:$R" >&3; } || echo "SKIP:" >&3
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
            
            response = ask_ollama(session["context"])
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
            response = ask_ollama(session["context"])
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

def ask_ollama(context):
    try:
        data = json.dumps({"model": MODEL, "prompt": f"{SYSTEM_PROMPT}\n{context}\n[Asystent]:", "stream": False}).encode()
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
                
                if line.startswith("RESULT:"):
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
    logger.info("[SERWER] Wpisz komendę dla AI (prefix 'to:' wysyła do klienta):")
    while True:
        try:
            cmd = input("SERVER> ")
            if cmd.startswith("to:") and clients:
                for c in clients:
                    try:
                        c.sendall(f"[OPERATOR]: {cmd[3:]}\n---END---\n".encode())
                        logger.info(f"[OPERATOR->KLIENT] {cmd[3:]}")
                    except:
                        pass
            elif cmd == "status":
                logger.info(f"Aktywnych klientów: {len(clients)}")
            elif cmd == "config":
                logger.info(f"PORT={PORT}, HTTP_PORT={HTTP_PORT}, MODEL={MODEL}")
                logger.info(f"OLLAMA_HOST={OLLAMA_HOST}, LOG_DIR={LOG_DIR}")
        except:
            break

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
