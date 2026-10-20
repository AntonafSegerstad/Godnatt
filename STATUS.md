# Godnatt – aktuell status
2026-10-20

## Byggt och publicerat
Koden finns i https://github.com/AntonafSegerstad/Godnatt på main.
Kodcommit: 20c03498f37fe60c81a47e1c7e64b51c3fc2fdaf.
Render Free-tjänst skapad i My Workspace (tea-dajv1feq1p3s739let4g):
- service srv-dbbo020u01pc73edte3g
- deploy dep-dbbo02gu01pc73edtk2g: live
- https://godnatt.onrender.com
- https://dashboard.render.com/web/srv-dbbo020u01pc73edte3g
Appen svarar över HTTPS. /api/status rapporterar database=true, ai=true.
Start, manifest och service worker svarar HTTP 200. Familjer, personer, relationer, foto och livslinje är verifierade via den publika API:n. Bokskapande är öppet i uttryckligen godkänt testläge. Tre kompletta AI-böcker finns.

GitHub CI (PostgreSQL 17) är godkänd:
https://github.com/AntonafSegerstad/Godnatt/actions/runs/39442979880
18 tester godkända. AI-svaren är simulerade; ingen riktig AI-kostnad.

## Databas
Neon verifierat Free-konto. Nytt separat projekt Godnatt i Frankfurt:
- project spring-glitter-25968553
- branch br-polished-grass-baynrq60, production
- database godnatt
- role godnatt_owner
- endpoint ep-autumn-term-batuc4n4
Compute 0,25 CU. Logisk lagringskvot 512 MiB. Alla nio app-tabeller och budgetrad skapade.
Hämta anslutningen via Neon-verktyget vid behov; inga hemligheter finns i koden.
Använd DIREKT host, inte -pooler-host, eftersom bokjobb använder session advisory locks.

## Serverhemligheter
Anton godkände uttryckligen Neon till Render 2026-10-20 och lämnade en OpenAI-nyckel med uppdrag att placera den på servern. DATABASE_URL (direkt host), OPENAI_API_KEY och PUBLIC_ORIGIN är nu satta i just Godnatts Render-tjänst. Alla andra variabler och tjänster bevarades.
Den tidigare automatiska granskningens blockering är löst genom det uttryckliga godkännandet. Nycklar har inte lagts i repot, klienten eller arbetsfiler.
Läsanrop till OpenAI /models/gpt-6-luna och /models/gpt-image-2.5-flare gav 200 med den nya nyckeln. Ingen betald generering har gjorts; läsåtkomst bevisar inte ensam att bildgenerering är tillåten på kontot.
AI_PRICING_VERIFIED=false gäller fortsatt. Anton bad uttryckligen att öppna spärren för test den 2026-10-20. AI_TEST_MODE=true öppnar testläge utan att felaktigt kalla bildkostnaden verifierad. IMAGE_CALL_MAX_ORE=5000 är en försiktig reservation på 50 kr per bild, inte en bevisad högsta leverantörskostnad. Samtliga anrop reserveras atomiskt före start. Okänd kostnad behålls reserverad; inga automatiska API-återförsök. Budgetrad efter tre kompletta böcker: 50 000 öre gräns, 109 öre bokfört, inga okända reservationer.
USD_SEK_CEILING=15 används för försiktig budgeträkning. Ett strikt garanterat bildkostnadstak är inte verifierat; detta är ett fortsatt öppet testvillkor, inte en avslutad produktionskontroll.

## Publika tester
Fiktiv familj: TEST – Godnatt QA (fiktiv familj), id 31b6eeb5-1f9c-4e6e-a99b-04405821f232.
Fyra fiktiva personer, ålder 1,5/7/11/36. Fyra riktade relationer med mamma, bonusmamma och tränare. Daterad anteckning skapad, rättad och raderad; originaltext och originaldatum bevarades vid rättelsen. En enfärgad fiktiv testbild laddades upp och hämtades som JPEG. Familjen öppnades via en ny separat HTTP-begäran utan session. /healthz gav 200.
Ny deploy dep-dbbo4utg1s2s739kf9s0 är live. Efter publiceringen fanns samtliga fyra personer, fyra relationer och fotot kvar. Startsida och JavaScript kontrollerades: ingen API-nyckel finns i dessa klientsvar.

## Kvar
1. Databas och PUBLIC_ORIGIN är konfigurerade.
2. OpenAI-nyckeln är konfigurerad som serverhemlighet. Återge den inte.
3. Verifiera modellåtkomst och bevisad övre bildkostnad samt säker valutaomräkning. AI_PRICING_VERIFIED är false tills detta är löst; gissa inte IMAGE_CALL_MAX_ORE.
4. Nuvarande Render-verktyg kan inte välja miljö vid skapandet. Tjänsten har ännu inget verifierat environmentId. Flytta ENDAST Godnatt till evm-dajv47uq1p3s739lohng i projekt prj-dajv47uq1p3s739lohn0 via stödd funktion.
5. Render-tjänsten har autoDeploy=yes, trigger=commit. render.yaml anger önskat checksPass men MCP-skapandet kan inte sätta det fältet. Ändra till After CI Checks Pass via stödd funktion. Tills dess: kör CI på ändringsgren och för bara godkänd kod till main.
6. Datalagring och återöppning är testade via API. Redeploy är verifierad. Riktig AI-bok, telefon/iPad och hemskärmsinstallation återstår.

## Skyddade projekt
invoice-simulator och VASS-todo-list samt samtliga tidigare repon och tjänster har inte ändrats.

## Molnfortsättning
Arbetet utförs i en hanterad Linux-molncontainer. Antons dator behövs inte. Koden finns nu i GitHub och tjänsten i Render. Utveckling fortsätter när en chattkörning är aktiv; ingen obegränsad obevakad utvecklingsprocess har skapats.

## Tre levererade AI-testböcker
Fiktiv familj: TEST – Tre godnattsböcker (fiktiva), id a2479196-6ed6-4ff0-be6b-df151ef68aa2.
- Milo, 1,5 år: Milo räknar till tre. 2 sidor, 8 ord per sida. https://godnatt.onrender.com/book/4f7e0650-a328-43a7-8eca-3b0f3368b067
- Nova, 7 år: Nova och de pirriga kullerbyttorna. 3 sidor, 54/58/52 ord. https://godnatt.onrender.com/book/aefadba3-0453-4fce-82cd-18c1bd99fd84
- Alex, 11 år: Stigen under stjärnorna. 4 sidor, 91/99/94/94 ord. https://godnatt.onrender.com/book/0216d0b0-a99a-449e-88a1-30b13da526a5
Samtliga sidor har riktig AI-bild och text. Alla nio bilder hämtades och verifierades som JPEG. Första bilden i varje bok granskades visuellt.
De tre första textförsöken misslyckades eftersom AI gav karaktärsbeskrivningen i objektformat. Kostnad 4 öre. Felet är rättat genom strikt JSON-schema med character_bible som sträng. Nya godkända försök ovan ersätter inte eller raderar debiteringshistoriken.
Ny kodcommit: 9be1dbafe0a103c1a248f5e0f152e63cf0377def. GitHub CI är godkänd med 20 tester.
Ompublicering dep-dbbobabncjis739dcvq0 är live. Efter denna publicering öppnades alla tre böcker på nytt via oberoende HTTP-anrop: status ready, exakt 2/3/4 sidor och fungerande första bild i varje bok. Böcker och bilder är beständiga efter ny publicering.
