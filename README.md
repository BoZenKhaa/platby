# Platby
Rozesílání platebních emailů s QR kódy z g-tabulek

## Hlášení chyb
Pro nahlášení chyby můžete založit [issue](https://github.com/BoZenKhaa/platby/issues)

## Použití pro novou jednotku
Velmi stručně:
1. Vytvoř google tabulku s emaily, např. exportem ze skautisu.
2. Povol připojení aplikaci k tabulce (viz níže)
3. Vytvoř nastavení platby v souboru `config.cfg` podle příkladu. 
4. Vytvoř html template textu emailu ulož ho do souboru  např. `html_email_template.html`. V templatu lze používat názvy proměných ve složených závorkách `{promena}`.
5. Vytvoř a rozešli emaily pomocí Jupyter notebooku `prispevky.ipynb`.

## Použití pro opakované rozesílání

1. [ ] Vlož export ze skautisu do tabulky 4PVS->Příspěvky->Platby píspěvků.
2. [ ] Vyfiltruj záznamy: 
   1. jen "řádné členství", nikoliv "hostování", na podzim ani "řádné členství bez poplatku středisku" - je třeba kouknout do registrace
   4. vyfiltrovat Zlatou Kotvu
   5. odstranit duplicitní řádky v exportu, např. pomocí conditional formatting, `=COUNTIF(D:D; D1)>1`
2. [ ] Otevři `config_prispevky.cfg` a zkontroluj nastavení, především:
   1. `amount_due` - název sloupce s částkou k úhradě
   2. `subject` - předmět emailu
   3. `ss_prefix` - prefix pro specifický symbol platby
   4. `message_template` - template zprávy platby
5. [ ] Otevři template emailu vybraný v configu a zkontroluj text emailu
3. [ ] Otevři notebook `prispevky.ipynb` a nastav:
   1. `sheet_name` na název listu v tabulce
   2. Proklikej bunky, vyres problemy. Nastav správné množství kontatů, na které se má výzva k platbě poslat - asi nejméně 2, max 4.
   3. Koukni na vygenerovany testovaci email
   4. Je-li vše v pořádku, spusť rozesílání


### Vytvoření přihlašovacích údajů k google api pro čtení tabulek a posílání emailů
To allow access:
1. go to https://console.cloud.google.com, enable g-sheet and g-mail apis
2. go to OAuth consent screen -> internal -> fill fields and continue
3. go to Credentials -> Create credentials -> OAuth client ID -> fill fields -> download json
