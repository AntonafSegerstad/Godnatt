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
Appskalet svarar över HTTPS. /api/status rapporterar database=false, ai=false.
Start, manifest och service worker svarar HTTP 200. Appen kan INTE spara familjer eller skapa böcker innan serverkonfigurationen är klar.

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

## Säkerhetsblockering
Försök att skapa Render-tjänsten med DATABASE_URL avvisades av automatisk säkerhetsgranskning. Skälet var att användaren inte uttryckligen godkänt överföringen av databasnyckeln från Neon till Render. Tjänsten skapades därefter UTAN databasnyckel, vilket var den säkrare oberoende åtgärden.
Överför inte databasnyckeln förrän Anton särskilt godkänt att Godnatts Neon-nyckel får läggas som DATABASE_URL i Godnatts Render-tjänst. Skicka inte hemligheter via chatten, repo eller loggar. Ingen sådan nyckel har överförts till Render.

## Kvar
1. Efter uttryckligt godkännande: sätt DATABASE_URL i just tjänsten srv-dbbo020u01pc73edte3g. Bevara övriga variabler. Sätt PUBLIC_ORIGIN=https://godnatt.onrender.com.
2. Anton lägger OPENAI_API_KEY säkert i samma tjänst. Nyckeln ska aldrig skrivas i chatten.
3. Verifiera modellåtkomst och bevisad övre bildkostnad samt säker valutaomräkning. AI_PRICING_VERIFIED är false tills detta är löst; gissa inte IMAGE_CALL_MAX_ORE.
4. Nuvarande Render-verktyg kan inte välja miljö vid skapandet. Tjänsten har ännu inget verifierat environmentId. Flytta ENDAST Godnatt till evm-dajv47uq1p3s739lohng i projekt prj-dajv47uq1p3s739lohn0 via stödd funktion.
5. Render-tjänsten har autoDeploy=yes, trigger=commit. render.yaml anger önskat checksPass men MCP-skapandet kan inte sätta det fältet. Ändra till After CI Checks Pass via stödd funktion. Tills dess: kör CI på ändringsgren och för bara godkänd kod till main.
6. Kontrollera datalagring i publicerad app, riktig AI-bok, återöppning, omstart/redeploy, telefon/iPad och hemskärmsinstallation.

## Skyddade projekt
invoice-simulator och VASS-todo-list samt samtliga tidigare repon och tjänster har inte ändrats.

## Molnfortsättning
Arbetet utförs i en hanterad Linux-molncontainer. Antons dator behövs inte. Koden finns nu i GitHub och tjänsten i Render. Utveckling fortsätter när en chattkörning är aktiv; ingen obegränsad obevakad utvecklingsprocess har skapats.
