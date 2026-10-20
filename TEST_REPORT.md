# Testresultat 2026-10-20
18 godkända tester, 0 misslyckade. JavaScript-syntax och Python-kompilering godkända.

Miljö: molncontainer, Python 3.12, PGlite via PostgreSQL-protokoll. AI-nätanrop är utbytta mot tydligt fiktiva testsvar. Testpersoner och testbilder är fiktiva. Ingen testdatabas eller testdata ingår i leveranspaketet.

Godkända:
1. Familj, person, ålder och redigering.
2. Flera riktade relationer, olika personer, avvisar relation mellan familjer.
3. Daterade minnen, rättelse, originaltext och originaldatum, radering.
4. Foto uppladdat och hämtat från databas, ogiltig bild avvisad, fotoreferens borttagen.
5. AI spärras utan säker konfiguration.
6. Sidantal och ursprungskontroll för webbanrop.
7. Tolv samtidiga reservationsförsök kan inte passera databasens budgetrad i testmiljön.
8. Samma debiteringsoperation kan inte startas två gånger. Okänd kostnad ligger reserverad.
9. Avbrutet bokjobb markeras misslyckat; reservationen ligger kvar.
10. Bok och bilder kan öppnas från en andra API-klient efter återinitiering av schema; personradering bevarar bok.
11. Ofärdiga böcker lämnar inte ut sidor som färdig bok.
12. Textunderlag skiljer på 1,5, 7 och 11 år.
13. PWA-manifest, ikoner och responsiva brytpunkter finns.
14. Simulerat AI-flöde: exakt två kompletta sidor; ingen skrivning till livslinjen; ingen omkörning av klar bok.
15. Fel sidantal stoppar bildanrop.
16. Timeout gör ett enda anrop och behåller reservationen.
17. Bruten kostnadsförutsättning spärrar nya reservationer.

Inte verifierat:
- Native PostgreSQL/Neon med flera riktiga backend-processer. PGlite använder en enda PostgreSQL-session med multiplexer.
- Faktisk OpenAI-åtkomst, bildlikhet, API-kompatibilitet på kontot och säkert maximipris per bild.
- Mobil/iPad-rendering och installation på hemskärm.
- Publik HTTPS, GitHub CI, Render-publicering, omstart och redeploy mot extern databas.
- Obevakad fortsatt utveckling utan en aktiv chattkörning.

En biblioteksvarning om framtida ändring i Starlettes testklient visas. Den påverkarde inte testerna.

Render YAML har även validerats mot Render JSON Schema. Neon Free-projekt och tabeller skapade. Direkt testanslutning från containern misslyckades vid DNS-upplösning; inga native integrationstester kunde därför köras. Återstående körs i GitHub CI eller från Render efter publicering.

18. Servern avvisar Neon transaction-pooler för att skydda sessionslås under bokskapande.

## Verifiering i GitHub och Render
2026-10-20: GitHub Actions körde samma 18 tester mot riktig PostgreSQL 17, samtliga godkända. Körning 39442979880. JavaScript-kontroll godkänd. Render-deploy dep-dbbo02gu01pc73edtk2g är live. HTTP 200 för startsida, manifest, service worker och /api/status. Databas och AI är ännu inte anslutna till tjänsten; publicerade verksamhetsflöden återstår.

## Efter säker serverkonfiguration
Anton har godkänt Neon till Render och serverhemligheterna är placerade i Godnatts egen tjänst. Publika tester godkända för familj, fyra personer, fyra riktade relationer, daterad rättelse med bevarat original, radering, fotouppladdning och återöppning utan session. OpenAI-modellernas läsendpoints svarade 200. Ingen betald AI-generering har genomförts. Budgeten står på 0/500 kr och AI förblir avstängd tills bildkostnadstaket kan verifieras.

## Riktigt AI-test
Tre kompletta böcker med 2/3/4 sidor för fiktiva barn 1,5/7/11 år. Alla nio illustrationer och sidtexter sparade. Exakt sidantal och bildhämtning verifierade. Visuell kontroll av första bilden i varje bok: enkel pekboksbild, mjuk gymnastiksaga respektive mörkare scoutäventyr. Rättningen av ett verkligt AI-formatfel verifierades genom nya böcker. Budgeträkning totalt 1,09 kr inklusive första misslyckade textförsök, inga osäkra reservationer. CI med strikt bokformat och testläge är godkänd med 20 tester. Testläget är uttryckligen godkänt; strikt högsta bildkostnad är fortfarande inte bevisad.

Efter ompublicering dep-dbbobabncjis739dcvq0 verifierades återöppning av alla tre färdiga böcker med exakt sidantal och fungerande bilder. 20 automatiska tester är godkända. Fotolikhet och verklig mobilinstallation har inte testats; dessa tre böcker använder fiktiva personer utan fotoreferenser.

## UI update, 2026-10-20

- GitHub Actions run 39450632655: 22 tests passed on PostgreSQL, plus JavaScript syntax check.
- Family deletion rejects active book jobs, removes family content and unused linked images, retains charge records and committed budget, and preserves other families.
- General information is one saved profile record per person; edits retain original text and date. Existing event context remains available separately.
- Reader fills the available viewport with a top-right close button, safe-area spacing, portrait/landscape layout and paging. Node-based rendering and page-turn smoke check passed. Physical mobile/browser layout has not been visually tested.
- Render deployment dep-dbbomumk1f9s73c59oeg is live at commit 5ce8a9e43761b5cfae74110ac7ba3863e307056a.
