#!/usr/bin/env python3
"""Testy jednostkowe dla Fixell"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestServerFunctions:
    """Testy funkcji serwera"""
    
    def test_system_prompt_contains_cmd_prefix(self):
        """Sprawdź czy system prompt zawiera instrukcję o prefiksie CMD:"""
        from fixell.server import SYSTEM_PROMPT
        assert "CMD:" in SYSTEM_PROMPT
    
    def test_system_prompt_mentions_linux(self):
        """Sprawdź czy system prompt wspomina o Linux"""
        from fixell.server import SYSTEM_PROMPT
        assert "Linux" in SYSTEM_PROMPT or "linux" in SYSTEM_PROMPT
    
    def test_default_port(self):
        """Sprawdź domyślny port"""
        from fixell.server import DEFAULT_PORT
        assert DEFAULT_PORT == 8088
    
    def test_default_model(self):
        """Sprawdź domyślny model"""
        from fixell.server import DEFAULT_MODEL
        assert "qwen" in DEFAULT_MODEL.lower() or DEFAULT_MODEL

class TestClientFunctions:
    """Testy funkcji klienta"""
    
    def test_parse_host_port(self):
        """Sprawdź parsowanie host:port"""
        from fixell.client import parse_address
        host, port = parse_address("nvidia:8088")
        assert host == "nvidia"
        assert port == 8088
    
    def test_parse_host_port_default(self):
        """Sprawdź domyślny port"""
        from fixell.client import parse_address
        host, port = parse_address("nvidia")
        assert host == "nvidia"
        assert port == 8088

class TestCommandParsing:
    """Testy parsowania komend"""
    
    def test_extract_commands_from_response(self):
        """Sprawdź wyciąganie komend z odpowiedzi AI"""
        from fixell.utils import extract_commands
        
        response = """Aby zdiagnozować problem, wykonaj:
CMD: journalctl -xb
Następnie sprawdź:
CMD: systemctl status
"""
        commands = extract_commands(response)
        assert len(commands) == 2
        assert "journalctl" in commands[0]
        assert "systemctl" in commands[1]
    
    def test_no_commands_in_response(self):
        """Sprawdź odpowiedź bez komend"""
        from fixell.utils import extract_commands
        
        response = "Proszę opisać problem dokładniej."
        commands = extract_commands(response)
        assert len(commands) == 0

class TestSafetyChecks:
    """Testy bezpieczeństwa"""
    
    def test_dangerous_command_detection(self):
        """Sprawdź wykrywanie niebezpiecznych komend"""
        from fixell.utils import is_dangerous_command
        
        assert is_dangerous_command("rm -rf /") == True
        assert is_dangerous_command("rm -rf /*") == True
        assert is_dangerous_command(":(){ :|:& };:") == True
        assert is_dangerous_command("dd if=/dev/zero of=/dev/sda") == True
        
    def test_safe_command_detection(self):
        """Sprawdź że bezpieczne komendy przechodzą"""
        from fixell.utils import is_dangerous_command
        
        assert is_dangerous_command("journalctl -xb") == False
        assert is_dangerous_command("systemctl status") == False
        assert is_dangerous_command("cat /var/log/messages") == False
        assert is_dangerous_command("ls -la") == False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
