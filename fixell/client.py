#!/usr/bin/env python3
"""Klient Fixell do połączenia z serwerem naprawczym"""
import socket
import sys
import os

DEFAULT_PORT = 8088

def parse_address(address):
    """Parsuj adres host:port"""
    if ":" in address:
        host, port = address.rsplit(":", 1)
        return host, int(port)
    return address, DEFAULT_PORT

class FixellClient:
    """Klient Fixell"""
    
    def __init__(self, host, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.sock = None
    
    def connect(self):
        """Połącz z serwerem"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(120)
        self.sock.connect((self.host, self.port))
        print(f"Połączono z {self.host}:{self.port}")
        
        # Odbierz powitanie
        welcome = self.receive()
        print(welcome)
    
    def send(self, message):
        """Wyślij wiadomość"""
        self.sock.sendall(f"{message}\n".encode())
    
    def receive(self):
        """Odbierz odpowiedź do ---END---"""
        buffer = ""
        while True:
            try:
                data = self.sock.recv(4096).decode()
                if not data:
                    break
                buffer += data
                if "---END---" in buffer:
                    return buffer.replace("---END---", "").strip()
            except socket.timeout:
                break
        return buffer.strip()
    
    def interactive(self):
        """Tryb interaktywny"""
        print("Wpisz pytanie lub 'exit' aby zakończyć")
        while True:
            try:
                cmd = input("> ").strip()
                if cmd.lower() == "exit":
                    break
                if not cmd:
                    continue
                
                self.send(cmd)
                response = self.receive()
                
                # Przetwórz odpowiedź - szukaj komend CMD:
                for line in response.split('\n'):
                    if line.strip().startswith("CMD:"):
                        cmd_to_run = line.strip()[4:].strip()
                        print(f"\n[SERWER PROPONUJE]: {cmd_to_run}")
                        confirm = input("Wykonać? (t/n/q pytanie): ").strip().lower()
                        
                        if confirm == 't':
                            import subprocess
                            try:
                                result = subprocess.run(cmd_to_run, shell=True, 
                                                       capture_output=True, text=True, timeout=60)
                                output = result.stdout + result.stderr
                                print(output)
                                self.send(f"RESULT:{output[:4000]}")
                            except Exception as e:
                                print(f"Błąd: {e}")
                                self.send(f"RESULT:Błąd wykonania: {e}")
                        elif confirm == 'q':
                            q = input("Twoje pytanie: ")
                            self.send(f"USER:{q}")
                            print(self.receive())
                        else:
                            self.send("SKIP:")
                    else:
                        print(line)
                        
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Błąd: {e}")
                break
        
        self.sock.close()

def main():
    if len(sys.argv) < 2:
        print(f"Użycie: {sys.argv[0]} host:port")
        sys.exit(1)
    
    host, port = parse_address(sys.argv[1])
    client = FixellClient(host, port)
    client.connect()
    client.interactive()

if __name__ == "__main__":
    main()
