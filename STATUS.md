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
Appen svarar över HTTPS. /api/status rapporterar database=true, ai=false.
Start, manifest och service worker svarar HTTP 200. Familjer, personer, relationer, foto och livslinje är verifierade via den publika API:n. Bokskapande är fortfarande spärrat tills bildkostnadens övre gräns är verifierad.

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
AI_PRICING_VERIFIED=false gäller fortsatt. Budgetrad: 50 000 öre gräns, 0 öre använt/reserverat.
USD_SEK_CEILING=15 är förberedd men AI är avstängd tills samtliga kostnadsförutsättningar är verifierade.

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
