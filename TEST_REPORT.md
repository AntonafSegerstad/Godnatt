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
