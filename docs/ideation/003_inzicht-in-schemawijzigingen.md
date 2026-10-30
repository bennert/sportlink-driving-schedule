# 003: Inzicht in schemawijzigingen bij een nieuwe PDF

**Date:** 2026-10-30  
**Status:** Active  
**Author:** Aanvrager

## Problem Statement

Als een team een nieuwe PDF ontvangt, is niet direct duidelijk wat er in het rijschema veranderd is. De ontvanger moet de vorige en nieuwe versie zelf vergelijken. Dat maakt het gemakkelijk om een gewijzigde verzameltijd, aanvangstijd of locatie te missen.

De behoefte is inzicht in inhoudelijke schemawijzigingen, niet in verschillen tussen PDF-bestanden. Reiskosten en het kilometertarief mogen geen wijzigingsmelding veroorzaken en horen niet in het wijzigingsoverzicht.

Dit document verkent een oplossing; het implementeert nog geen nieuwe functionaliteit. Als uitgangspunt geldt dat teamcontacten de wijzigingen bij de PDF in de e-mail willen zien. Of de samenvatting ook in de PDF zelf moet staan, is nog een productkeuze.

## Prior Art

- **Bestaande wijzigingsdetectie:** `create_driving_schedule.py` vergelijkt de vorige en nieuwe Markdown na normalisatie met `strip_travel_metrics`. Daarmee is er al een beslismoment voor relevante wijzigingen. De uitkomst is alleen een ja/nee; er ontstaat nog geen overzicht per wedstrijd.
- **Technische diff:** `print_content_diff` schrijft een unified diff naar de workflowlog. Dit helpt een beheerder bij onderzoek, maar toont volledige Markdown-regels en ook kostenverschillen wanneer een andere wijziging de vergelijking triggert. Teamcontacten krijgen deze uitleg niet mee.
- **E-mail met PDF's:** `send_team_emails.py` verstuurt de Nederlandstalige en Engelstalige PDF met een algemene melding. Het kanaal bestaat al, maar de e-mail vertelt niet wat er is gewijzigd.
- **Vorige versie als artifact:** De workflow probeert eerdere Markdown-bestanden terug te halen. Dat biedt een vergelijkingsbasis, maar de download mag mislukken en artifacts hebben een beperkte bewaartermijn. Aanwezigheid van een eerdere, daadwerkelijk bezorgde versie is dus niet gegarandeerd.
- **Visuele PDF-vergelijking:** Een vergelijking van gerenderde pagina's kan ook opmaakverschillen zichtbaar maken. Voor dit probleem voegt dat complexiteit en ruis toe; gestructureerde wedstrijdgegevens zijn een geschiktere basis voor begrijpelijke meldingen.

## Proposed Approach

Maak per team een gestructureerd wijzigingsoverzicht tijdens het vergelijken van de oude en nieuwe schema-inhoud, voordat oude bestanden worden verwijderd. Gebruik ditzelfde overzicht voor een korte uitleg in de e-mail en in de GitHub Actions-run summary. Behoud de volledige PDF als actuele bron.

### MVP

1. **Vergelijk inhoud, niet PDF-bytes.** Hergebruik dezelfde normalisatieregels als de bestaande wijzigingscheck. Negeer reiskosten, kilometertarief en de al uitgesloten technische routegegevens en kaart-URL-wijzigingen. Een gewijzigde locatienaam blijft wel relevant.
2. **Maak wijzigingen concreet.** Onderscheid toegevoegde wedstrijden, verwijderde wedstrijden en aangepaste velden. Toon bij aanpassingen de oude en nieuwe datum, wedstrijdomschrijving, verzameltijd, starttijd, eindtijd of locatie. Toon ook relevante instellingen, zoals een gewijzigde basislocatie of warming-uptijd.
3. **Koppel wedstrijden voorzichtig.** Onderzoek of Sportlink een stabiele wedstrijdidentificatie levert en hoe die samen met de vorige versie bewaard kan worden. De huidige Markdown bevat daarvoor geen expliciete identificatie. Als een koppeling niet betrouwbaar is, meld dan verwijderd en toegevoegd in plaats van een onzekere tijd- of datumwijziging te presenteren als feit.
4. **Bewaar het resultaat tot verzending.** Schrijf een klein, gestructureerd bestand per team dat de e-mailstap kan lezen. Maak het beschikbaar zonder te vertrouwen op al verwijderde oude Markdown of op het parsen van console-uitvoer. De precieze bestandsvorm volgt in de feature-specificatie.
5. **Leg uit bij de PDF.** Zet de samenvatting boven de verwijzing naar de bijlagen. Render dezelfde gegevens in de workflow-samenvatting voor de beheerder. Gebruik bij lange lijsten een expliciet aantal overige wijzigingen en een volledig, toegankelijk overzicht; kap niet stilzwijgend af.
6. **Wees eerlijk over de vergelijkingsbasis.** Zonder vorige versie: meld 'Geen vorige versie beschikbaar; wijzigingen konden niet worden bepaald'. Alleen wanneer een eerste publicatie aantoonbaar is, mag de tekst 'Eerste schema' luiden. Vergelijk in het MVP met de vorige beschikbare schemaversie, niet met een onbewezen laatst ontvangen e-mail.

### Voorbeeld Voor Een Teamcontact

```text
Wijzigingen in het rijschema voor EHV HS1

- 1 november, EHV HS1 - Tegenstander: verzamelen van 10:00 naar 10:15.
- 8 november, Tegenstander - EHV HS1: locatie van Hal A naar Hal B.
- Toegevoegd: 15 november, EHV HS1 - Tegenstander, aanvang 11:00.
- Vervallen uit het schema: 22 november, Tegenstander - EHV HS1.

Het actuele rijschema staat in de bijgevoegde PDF's.
```

'Vervallen uit het schema' betekent niet automatisch dat een wedstrijd is afgelast. Een verdwenen regel kan ook door de reikwijdte van de agenda of de brongegevens komen.

### Bewijs En Onzekerheden

- **Proven:** Oude en nieuwe Markdown zijn beschikbaar op het moment van de vergelijking. De code heeft al een genormaliseerde wijzigingscheck, een technische diff en een afzonderlijke e-mailstap. De huidige normalisatie sluit kosten en kilometertarieven uit.
- **Likely:** Een beknopt overzicht met oude en nieuwe waarden maakt de reden voor een nieuwe PDF sneller duidelijk dan een handmatige vergelijking. Gestructureerde gegevens laten dezelfde inhoud in e-mail en workflow-samenvatting gebruiken zonder twee onafhankelijke vergelijkingen.
- **Aspirational:** Wedstrijden blijven over datum-, naam- en locatiewijzigingen heen betrouwbaar herkenbaar. Dit vereist onderzoek naar bronidentificatie en opslag daarvan; het is nog niet aangetoond.
- **Aspirational:** Het overzicht kan later precies aansluiten bij de laatst succesvol bezorgde versie per team. Daarvoor is extra verzendstatus nodig; de huidige artifact-versie bewijst geen succesvolle bezorging.

### Alternatieven En Afbakening

- **Alleen de technische diff meesturen:** Weinig bouwwerk, maar te veel Markdown-ruis en onvoldoende uitleg voor teamcontacten. Niet aanbevolen als eindoplossing.
- **Markeringen in de PDF:** Wijzigingen zijn ook bij doorsturen zichtbaar. Dit vraagt extra ontwerp voor leesbaarheid, zwart-witafdrukken en verdwenen wedstrijden. Bewaar dit als vervolgstap als e-mailuitleg onvoldoende blijkt.
- **Telegram uitbreiden:** Kan nuttig zijn, maar de bestaande wekelijkse aankondiging heeft een ander ritme dan PDF-wijzigingen. Niet meenemen in het MVP zonder expliciete keuze.
- **Geen wijziging van de bestaande kostenuitsluiting:** Kosten blijven zichtbaar in de schema's, maar veroorzaken geen melding. Technische opmaakwijzigingen mogen niet als gewijzigde wedstrijd worden omschreven.

## Next Steps

1. Bevestig of e-mail plus workflow-samenvatting voldoende is, of dat de uitleg ook in de PDF moet staan. Stem ook de taal van de samenvatting af op de ontvangers.
2. Onderzoek stabiele wedstrijdidentificatie in Sportlink en kies een conservatieve terugval wanneer de vorige versie die informatie nog niet bevat.
3. Werk het MVP uit met `/feature-spec`, inclusief scenario's voor toegevoegde en verdwenen wedstrijden, gewijzigde tijden en locaties, relevante instellingen, ontbrekende vorige versies, dubbele wedstrijden en onzekere koppelingen.
4. Neem regressiescenario's op waarin alleen kosten, kilometertarief of kaart-URL veranderen: geen inhoudelijke wijzigingsmelding. Controleer ook een combinatie van een echte wijziging en gewijzigde kosten: alleen de echte wijziging verschijnt in het overzicht.
5. Valideer een voorbeeldmail met een teamcontact voordat PDF-markeringen, Telegram-uitbreiding of een bezorgingshistorie worden toegevoegd.
