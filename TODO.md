mam problem z komputerem i chciałbym aby w trybie awarynnym w fedora naprawić ten problem poprzez komunikacje z modelem ollama gdzie jest qwen 14b
chciałbym aby ten skrypt uruchomiony miał jak najmniej linijek, ale żeby wystarczył po uruchomieniu aby połączyć się z usługą na drugim komputerzez, gdzie będę mógł realziować naprawe, jeśli mam dostep do drugiego komputera, np uruchamiam komende gdzie podaje hosta lokalnego z portem i już to działa w trybie shellowego klienta, gdzie moge z tą usługą realziwoac zadani anprawcze ssystemu, dwozolone jest sprawdzanie komputera ale z potwierdzaniem przez usera, czy wysyałać te dane, czy zac pytanie/inną komendę

najważniejsze jest to, że na tym docelowym okmputerze powinna znajdować się uslgua uruchamiana na czas naprawy, aby działał w oparciu o ollama i qwen 14b lub inny model, ktory jest wyspecjalizowany w systemach linux i bedzie s wtsanie naprawić problem, dodatkowo pozwalaj mi na komputerze nvidia w tej usludze rownież zadawać pytania i kazać np wykonywać akcje na tym docelowym komputerze z fedora, aby na tym server i client człowiek mógł decydować i wklejać własne zapytania i pomysły
fixer.sh nvidia:8088

zrob w docker compose taki test, gdzie jeden to klient, drugi to server a ollama jest brana z lokalnego , zakomentuj ollame w docker conpose, na szelki wypadek, aby bezposrednio korzystac z lokalnego srodowiska


 pryzgotuj makefile i prztetsuj, wykonaj testy e2e polaczenia, przttesuj funkconalnosc i poproawnosc generowanych komend z qen, zrob liste przydtanych dopasowanych do komputera servera modeli, ktore mozna w tym zastosowaniu uzyc
Stworz poszerozną dokumentacje w folderzze docs, badges, bo to paczka python, przygotuj klienta, ktory mozna by uzyc poprzez brak skryptu a jedynie wykorzystac systemowe komenydy, np poprzez curl, aalbo inne, zaproponuj, aby mozliwe bylo w pierwszym kroku pobranie klienta i potem automatcyzny start shell interactive po stronie clietn