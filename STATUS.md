# Leveransstatus
Datum: 2026-10-20.

## Miljö
Bygget har körts i en hanterad Linux-miljö i molnet, i /workspace/scratch. Antons dator används inte. Scratch är tillfälligt; leveranspaketet är sparat separat. Ingen löpande obevakad byggtjänst har skapats. Nytt arbete kräver en aktiv chattkörning tills en annan molnprocess konfigurerats.

## Byggt
PWA-klient, server, PostgreSQL-schema, fotolagring, relationer, datum och ursprung i livslinjen, bokbeställning, AI-adapter, budgetbokföring, läsare, fel- och omstartshantering, Render-konfiguration och GitHub CI. Lokal Git-historik i molnet. GitHub-repot AntonafSegerstad/Godnatt har skapats och verifierats.

## Konton
GitHub verifierat med eget läsanrop: AntonafSegerstad (id 208667649).
Render verifierat med egna läsanrop: My Workspace, tea-dajv1feq1p3s739let4g. Miljö evm-dajv47uq1p3s739lohng innehåller invoice-simulator och VASS-todo-list. Inga befintliga resurser har ändrats.
GitHub-repot AntonafSegerstad/Godnatt är nu skapat av Anton och verifierat skrivbart. Första README-commit: 682a07cbb60ad1e15668e14f197327601d558321. Källkod förs över i nästa commit.
Render-anslutningen stöder nya Free-webbtjänster, men dess skapandeverktyg saknar val av environmentId. Placeringen i användarens befintliga miljö måste lösas med stödd Blueprint- eller Dashboard-funktion innan den markeras klar.
Neon är nu verifierat anslutet. Ett nytt separat Godnatt-projekt på kontots verifierade Free-plan har skapats i Frankfurt. Projekt spring-glitter-25968553, branch br-polished-grass-baynrq60 (production), databas godnatt. Compute är begränsad till 0,25 CU och logisk lagringskvot till 512 MiB. Schema och budgetrad är skapade. Inga riktiga personuppgifter eller böcker finns där. OpenAI-servernyckel är inte konfigurerad.

## Testgränser
Testning sker med PGlite (PostgreSQL i WebAssembly) och PostgreSQL-protokoll, inte med en fristående produktionsserver. Det ger databas- och API-testning men bevisar inte verklig flerprocesslåsning i Neon. GitHub CI är förberett för PostgreSQL 17 och måste köras efter anslutning.
AI-svar i tester är simulerade. Inga riktiga bilder eller API-böcker har genererats. Mobil- och iPad-CSS är skriven; ingen visuell webbläsarkontroll eller hemskärmsinstallation har utförts. Ingen verklig Render-omstart eller ny publicering har testats. En andra API-klient och återinitiering av schemat testas i testsviten.

## Blockerat
1. GitHub-repot är skapat. För över koden och kör CI.
2. Neon-databasen är skapad och klar för serverkoppling. Hämta direkt anslutning säkert via Neon-verktygen vid konfiguration. Använd inte poolerad anslutning till arbetaren: dess advisory locks kräver en stabil PostgreSQL-session.
3. Skapa endast en ny Free-webbtjänst i Render och placera den i prj-dajv47uq1p3s739lohn0 / evm-dajv47uq1p3s739lohng. GitHub och Render är redan anslutna.
4. Säker OpenAI-nyckel i Render, modellåtkomst och bevisad maximal bildkostnad före AI-aktivering.
5. Publicera över HTTPS och verifiera riktiga flöden, mobilinstallation, varaktighet efter deploy och en riktig AI-bok inom budget.

## Kostnad
0 kr AI-kostnad under bygget. Inga betalda driftplaner har beställts. AI förblir avstängd tills förhandsgränsen är verifierad. En godtycklig prisgissning räcker inte för att bevisa ett verkligt stopp på 500 kr.

## Fortsätt
Packa upp källpaketet och öppna STATUS.md och README.md. Koden finns på huvudgrenen main i medföljande Git-bundle. För över till det nya GitHub-repot efter säker anslutning. Behåll samtliga andra projekt och data.

## Senaste verifiering
Render YAML är godkänd mot aktuell publicerad JSON Schema. 18 tester godkända i PGlite. Försök att köra samma tester mot Neon stoppades av DNS-begränsning i molncontainern innan databaskoppling. Ingen native testkörning är därför godkänd ännu. Neon-tabellerna har skapats via den verifierade anslutningen.
