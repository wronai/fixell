#!/usr/bin/env python3
"""Funkcje pomocnicze dla Fixell"""
import re

DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+/\*",
    r"rm\s+-rf\s+\*",
    r"dd\s+if=.*of=/dev/[sh]d",
    r"mkfs\.",
    r":\(\)\{\s*:\|:&\s*\};:",  # fork bomb
    r">\s*/dev/[sh]d",
    r"chmod\s+-R\s+777\s+/",
    r"chown\s+-R.*:\s*/",
    r"wget.*\|\s*sh",
    r"curl.*\|\s*sh",
    r"wget.*\|\s*bash",
    r"curl.*\|\s*bash",
]

def extract_commands(response):
    """Wyciągnij komendy z odpowiedzi AI (linie zaczynające się od CMD:)"""
    commands = []
    for line in response.split('\n'):
        line = line.strip()
        if line.upper().startswith("CMD:"):
            cmd = line[4:].strip()
            if cmd:
                commands.append(cmd)
    return commands

def is_dangerous_command(cmd):
    """Sprawdź czy komenda jest potencjalnie niebezpieczna"""
    cmd_lower = cmd.lower()
    
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower):
            return True
    
    # Dodatkowe sprawdzenia
    if "rm -rf /" in cmd and not cmd.startswith("#"):
        return True
    
    return False

def sanitize_output(output, max_length=4000):
    """Przytnij i oczyść output"""
    if len(output) > max_length:
        output = output[:max_length] + "\n... (przycięto)"
    return output

def format_command_result(cmd, output, exit_code=0):
    """Sformatuj wynik komendy"""
    status = "OK" if exit_code == 0 else f"BŁĄD (kod: {exit_code})"
    return f"[{status}] {cmd}\n{output}"
