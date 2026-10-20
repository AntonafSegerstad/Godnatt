# Godnatt
PWA för personliga godnattsagor. Python/FastAPI, PostgreSQL och vanlig HTML/CSS/JavaScript. Familjens namn visas i familjevalet. En fyrsiffrig PIN krävs för att läsa och ändra familjens innehåll. PIN kontrolleras på servern, lagras saltad med scrypt och ger en säker HttpOnly-session i 12 timmar. Fem felaktiga försök ger fem minuters spärr. Befintliga familjer väljer sin första kod via en separat engångslänk.

## Drift
Avsedd miljö: Render-projekt prj-dajv47uq1p3s739lohn0, miljö evm-dajv47uq1p3s739lohng. Lägg endast till en NY tjänst. Ändra inte andra projekt eller tjänster. render.yaml anger en gratis Python-webbtjänst. Ingen Render-databas eller disk skapas.

En separat kostnadsfri Neon-databas har skapats; se STATUS.md. Använd den direkta anslutningen (inte -pooler-host), eftersom bokarbetarens advisory lock kräver stabil session. Sätt DATABASE_URL i Render som serverhemlighet. Data, foton och bilder lagras i PostgreSQL (bytea), aldrig på Render-disken. Appen stoppar nya bilder vid 400 MiB; marginal för tabeller och index inom Neons verifierade 1 GB gratisgräns. Databasen har även kvot för beräkning. Kontrollera alltid kontots faktiska gratisplan innan skapande. Använd inte betald uppgradering. Render Free kan sova och vara långsam vid första öppningen.

Sätt OPENAI_API_KEY som hemlighet i Render, aldrig i kod, klient eller chatt. Sätt PUBLIC_ORIGIN till tjänstens publika HTTPS-origin. Koppla rätt GitHub-repo till den nya Render-tjänsten. Välj automatisk publicering efter godkända CI-kontroller, inte före dem. render.yaml använder checksPass: nya versioner ska publiceras först när GitHub CI är godkänd.

Start: pip install -r requirements.txt, därefter python -m uvicorn app:app --host 0.0.0.0 --port 8000. Inga användardata ingår i repot.

## AI och hård budget: viktigt kvarstående villkor
AI är avsiktligt avstängd som standard. Tre riktiga testböcker har skapats efter Antons uttryckliga godkännande. Se STATUS.md för länkar och verifiering. Innan aktivering krävs verifierad kontoåtkomst till båda modellerna, en dokumenterad övre kostnadsgräns för varje begränsat bildanrop (högst åtta referenser i 512 px, högst 16 000 UTF-8-byte prompt, en 1024×1024 low-bild), samt en säker USD/SEK-gräns inklusive eventuella avgifter och skatt.

Officiella tokenpriser har kontrollerats, men de hämtade källorna fastställer inte en garanterad maxkostnad per Flare-bild. IMAGE_CALL_MAX_ORE får därför INTE sättas till en gissad normal kostnad. AI_PRICING_VERIFIED ska vara false tills detta är löst. En efterkontroll av faktisk kostnad kan aldrig ersätta en riktig förhandsgräns.

Delad budgetrad låses före varje API-anrop. Gränsen är högst 50 000 öre, gemensam för alla familjer, alla instanser och alla försök. Reservationen är varaktig. Vid timeout, saknad usage eller krasch ligger hela beloppet kvar. Inga automatiska API-återförsök görs. Textinput begränsas och textoutput har explicit tokenstopp. Modeller och priser kan ändras på servern, men kräver ny verifiering. Missad kostnadsgräns stänger ytterligare generering genom limit_ore=0 och kräver manuell granskning.

Budgeten omfattar endast anrop som går via denna app och denna databas. Dela inte samma OpenAI-projektnyckel med andra program inom POC-budgeten.

## Funktioner
- Familjer och personer med ålder, kön och foton.
- Flera riktade relationer mellan verkliga person-id:n.
- Automatisk sparning av daterad personkontext, ursprungstext, rättelser och radering.
- Bokbeställning lagrar en egen daterad kontextkopia. AI:s sagohändelser skriver aldrig till livslinjen.
- Exakt sidantal valideras före bildanrop. Klar-status sätts först när alla sidor och bilder är sparade.
- Advisory lock hindrar dubbelarbete. Vid omstart hanteras köade jobb; avbrutna pågående jobb markeras som misslyckade utan att gissningsvis upprepa betalda anrop.
- Bokläsare med länkar, pilar och svep. PWA-manifest, service worker, ikoner och offlinebesked.
- Extern beständig databas gör böcker åtkomliga från andra enheter utan konton.

## Begränsningar
- Ingen bakgrundstjänst har satts i drift före verifierad publicering.
- En kostnadsfri Render-instans kan avbryta jobb. Boken blir då misslyckad, aldrig falskt klar. Ny beställning är ett nytt debiterbart försök.
- Visuell likhet mellan AI-sidor kan inte garanteras av kod; samma fotoreferenser och karaktärsbeskrivning används varje gång.
- Sparade böckers kontextkopior bevarar historiken vid senare rättelser i livslinjen.
- Borttagning av person tar bort personens relationer och livslinje. Redan skapade böcker bevaras. Fotobytes sparas även när de används av en befintlig bok.
- Ingen verklig mobilinstallation, publicering eller riktig AI-kvalitet kan markeras verifierad utan anslutningar.

## Test
Kör med en separat testdatabas: TEST_DATABASE_URL=... python -m pytest -q. Testerna rensar endast en egen unik schema per körning. CI kör PostgreSQL 17. Inga riktiga barnuppgifter, foton eller AI-anrop används.

## Godkänt testläge
2026-10-20 godkände Anton att öppna generering för test. AI_TEST_MODE=true kan öppna generering utan att AI_PRICING_VERIFIED felaktigt sätts till true. Samma delade budgetbokföring, atomiska reservationer, inga automatiska återförsök och lås gäller. Testreservationen på 50 kr per bild är mycket försiktig jämfört med den publicerade kostnadskalkylatorn men är inte en garanterad leverantörsgräns. Därför är strikt verifiering av högsta bildkostnad fortfarande en begränsning. Använd explicit 1024x1024 och low, aldrig auto. Börja med tre korta böcker med fiktiva personer och utan personfoton.
