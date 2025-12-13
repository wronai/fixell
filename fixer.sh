#!/bin/bash
# Minimalny klient do zdalnej naprawy systemu Linux
# Użycie: ./fixer.sh host:port

[[ -z "$1" ]] && echo "Użycie: $0 host:port" && exit 1
HOST="${1%:*}"; PORT="${1#*:}"
exec 3<>/dev/tcp/$HOST/$PORT || { echo "Błąd połączenia"; exit 1; }

echo "Połączono z $HOST:$PORT - wpisz pytanie lub 'exit'"
while true; do
    read -p "> " CMD
    [[ "$CMD" == "exit" ]] && break
    echo "$CMD" >&3
    while IFS= read -r -t 2 LINE <&3; do
        [[ "$LINE" == "---END---" ]] && break
        if [[ "$LINE" == "CMD:"* ]]; then
            echo -e "\n[SERWER PROPONUJE KOMENDĘ]: ${LINE#CMD:}"
            read -p "Wykonać? (t/n/q pytanie): " CONFIRM
            if [[ "$CONFIRM" == "t" ]]; then
                RESULT=$(eval "${LINE#CMD:}" 2>&1)
                echo "RESULT:$RESULT" >&3
                echo "$RESULT"
            elif [[ "$CONFIRM" == "q" ]]; then
                read -p "Twoje pytanie: " Q
                echo "USER:$Q" >&3
            else
                echo "SKIP:" >&3
            fi
        else
            echo "$LINE"
        fi
    done
done
exec 3<&-
