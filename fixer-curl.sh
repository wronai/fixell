#!/bin/bash
# Ultra-minimalny klient Fixell - używa tylko curl/nc
# Pobierz i uruchom: curl -sL URL | bash -s -- server:8088

HOST="${1%:*}"; PORT="${1#*:}"
[[ -z "$HOST" ]] && echo "Użycie: $0 host:port" && exit 1

echo "Łączę z $HOST:$PORT..."

# Funkcja do komunikacji
chat() {
    local msg="$1"
    echo "$msg" | nc -w 30 "$HOST" "$PORT" 2>/dev/null | while IFS= read -r line; do
        [[ "$line" == "---END---" ]] && break
        echo "$line"
    done
}

# Powitanie
chat ""

# Pętla interaktywna
while read -p "> " cmd; do
    [[ "$cmd" == "exit" ]] && break
    [[ -z "$cmd" ]] && continue
    
    response=$(chat "$cmd")
    echo "$response"
    
    # Szukaj komend CMD:
    echo "$response" | grep -i "^CMD:" | while read -r cmdline; do
        proposed="${cmdline#CMD:}"
        proposed="${proposed#cmd:}"
        proposed="${proposed# }"
        echo -e "\n[KOMENDA]: $proposed"
        read -p "Wykonać? (t/n): " confirm
        if [[ "$confirm" == "t" ]]; then
            result=$(eval "$proposed" 2>&1)
            echo "$result"
            chat "RESULT:$result" >/dev/null
        fi
    done
done
