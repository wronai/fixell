#!/bin/bash
# Serwer naprawczy z Ollama - uruchamia się na komputerze z GPU (nvidia)
# Użycie: ./fixer-server.sh [port] [model]

PORT="${1:-8088}"
MODEL="${2:-qwen2.5:14b}"
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

echo "=== FIXER SERVER ==="
echo "Port: $PORT | Model: $MODEL | Ollama: $OLLAMA_HOST"

SYSTEM_PROMPT="Jesteś ekspertem od naprawy systemów Linux (szczególnie Fedora). 
Gdy proponujesz komendę do wykonania, poprzedź ją prefiksem CMD: (jedna komenda na linię).
Bądź zwięzły. Najpierw diagnozuj, potem naprawiaj. Pytaj o logi i status usług.
Odpowiadaj po polsku."

handle_client() {
    echo "Klient połączony"
    CONTEXT=""
    
    while IFS= read -r LINE; do
        [[ -z "$LINE" ]] && continue
        
        if [[ "$LINE" == "RESULT:"* ]]; then
            CONTEXT+="\n[Wynik komendy]: ${LINE#RESULT:}"
            continue
        elif [[ "$LINE" == "SKIP:"* ]]; then
            CONTEXT+="\n[Użytkownik pominął komendę]"
            continue
        elif [[ "$LINE" == "USER:"* ]]; then
            LINE="${LINE#USER:}"
        fi
        
        CONTEXT+="\n[Użytkownik]: $LINE"
        
        RESPONSE=$(curl -s "$OLLAMA_HOST/api/generate" \
            -d "{\"model\":\"$MODEL\",\"prompt\":\"$SYSTEM_PROMPT\n$CONTEXT\n[Asystent]:\",\"stream\":false}" \
            | jq -r '.response // "Błąd połączenia z Ollama"')
        
        CONTEXT+="\n[Asystent]: $RESPONSE"
        echo -e "$RESPONSE"
        echo "---END---"
    done
}

echo "Nasłuchiwanie na porcie $PORT..."
while true; do
    nc -l -p $PORT -c 'bash -c "handle_client"' 2>/dev/null || \
    socat TCP-LISTEN:$PORT,reuseaddr,fork EXEC:"$0 --handler"
done
