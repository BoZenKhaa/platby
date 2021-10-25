# Platby
Rozesílání platebních emailů s QR kódy z g-tabulek

## Hlášení chyb
Pro nahlášení chyby můžete založit [issue](https://github.com/BoZenKhaa/platby/issues)

## Použití
Velmi stručně:
1. Vytvoř google tabulku s emaily, např. exportem ze skautisu.
2. Povol připojení aplikaci k tabulce (viz níže)
3. Vytvoř nastavení platby v souboru `config.cfg` podle příkladu. 
4. Vytvoř template emailu v některém emailovém klientu a ulož ho do souboru `email_template.eml`. V templatu lze používat názvy proměných ve složených závorkách `{promena}`.
5. Vytvoř a rozešli emaily pomocí Jupyter notebooku `prispevky.ipynb`.

### Vytvoření přihlašovacích údajů k google api pro čtení tabulek a posílání emailů
To allow access:
1. go to https://console.cloud.google.com, enable g-sheet and g-mail apis
2. go to OAuth consent screen -> internal -> fill fields and continue
3. go to Credentials -> Create credentials -> OAuth client ID -> fill fields -> download json
