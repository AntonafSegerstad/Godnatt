# Kontrollerade officiella källor
Kontrollerade 2026-10-20. Kontoplan och modellåtkomst är fortfarande inte verifierade.

- https://developers.openai.com/api/docs/models/gpt-6-luna — textmodell, input 0.10 USD/M token, output 0.50 USD/M token.
- https://developers.openai.com/api/docs/models/gpt-image-2.5-flare — textinput 5 USD/M token, bildinput 8 USD/M token, bildoutput 30 USD/M token. Stöd för text, bildreferenser och low-kvalitet. Källan fastställer inte säkert tokenmaximum för vår bildbeställning.
- https://developers.openai.com/api/docs/guides/image-generation — Images API för generering och redigering med fotoreferenser.
- https://render.com/docs/free — tillfälligt filsystem, gratis Postgres löper ut efter 30 dagar, webbtjänst sover efter inaktivitet. Inkluderade driftskvoter delas inom kontot. Gratis compute garanterar inte att kontots övriga kvoter aldrig kan ge tilläggsavgifter.
- https://neon.com/pricing — hämtad sida anger Free: 1 GB PostgreSQL, 100 CU-timmar per projekt och månad; ingen tidsgräns. Den faktiska kontoplanen måste verifieras innan skapande. Vi använder PostgreSQL för både metadata och begränsade bildbytes.
