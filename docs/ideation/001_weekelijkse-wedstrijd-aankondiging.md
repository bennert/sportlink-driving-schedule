# 001: Wekelijkse aankondiging van de komende wedstrijd

**Date:** 2026-10-28
**Status:** Active
**Author:** Aanvrager

## Problem Statement

Teamcontacten krijgen met de huidige automatisering een e-mail met PDF-rijschema's wanneer de gegenereerde schema-inhoud verandert. Dat is niet hetzelfde als iedere week een korte, tijdige aankondiging van de komende wedstrijd: een ongewijzigd schema triggert geen bericht. De relevante wedstrijd- en reisinformatie is al beschikbaar, maar wordt nog niet als WhatsApp-aankondiging verstuurd.

De gewenste aankondiging is bedoeld voor de ingestelde teamcontacten en bevat wedstrijdgegevens, rijschema en praktische informatie. Als werkhypothese wordt het bericht op maandag verstuurd over de eerstvolgende wedstrijd. Nog te bepalen is of dat altijd de eerstvolgende wedstrijd is of alleen een wedstrijd binnen de komende zeven dagen.

## Prior Art

- **Bestaande wekelijkse planning:** GitHub Actions draait iedere maandag om 06:00 UTC. Het script haalt wedstrijden uit de Sportlink-agenda en genereert Nederlandstalige rijschema's met datum, tegenstander, verzameltijd, start- en eindtijd, locatie, kosten, afstand en reistijd. Dit werkt al voor de huidige PDF-workflow.
- **E-mail met PDF:** Per team is een e-mailadres configureerbaar. De workflow verstuurt de PDF alleen wanneer wijzigingen worden gedetecteerd. Dit biedt de volledige planning, maar voldoet niet aan een vaste wekelijkse aankondiging en is geen WhatsApp-bericht.
- **WhatsApp:** Er is geen WhatsApp-integratie of configuratie voor telefoonnummers aanwezig. Een ondersteunde verzendmethode, zoals de WhatsApp Business Platform API of een provider, moet nog worden gekozen en gevalideerd.
- **Inhoudelijke grens:** De kalender en rijschema's bevatten reistijden en verzameltijden, maar geen toegewezen chauffeurs. Namen van chauffeurs kunnen dus niet betrouwbaar worden aangekondigd zonder een aanvullende gegevensbron.

## Proposed Approach

Maak een afzonderlijke wekelijkse notificatiestap die de eerstvolgende wedstrijd per team uit de bestaande Sportlink-kalender selecteert en een WhatsApp-bericht aan de geconfigureerde teamcontacten verstuurt. Laat deze stap onafhankelijk zijn van de wijzigingsdetectie voor PDF's, zodat ook bij een ongewijzigd rijschema het wekelijkse bericht kan worden verzonden.

Houd het eerste bericht bij controleerbare gegevens: team en tegenstander, datum en aanvangstijd, locatie, verzameltijd en relevante reisgegevens die al in het rijschema staan. Vermeld geen chauffeur zolang die niet uit een betrouwbare bron komt. Gebruik aparte ontvangersconfiguratie voor WhatsApp; e-mailadressen zijn niet bruikbaar als WhatsApp-bestemming.

- **Proven:** De geplande workflow draait iedere maandag. De Sportlink-verwerking levert wedstrijdgegevens en de gegenereerde schema's bevatten verzameltijd, locatie, kosten, afstand en reistijd. De huidige e-mailstap is gekoppeld aan wijzigingen, niet aan de wekelijkse planning.
- **Likely:** De bestaande kalenderverwerking kan de eerstvolgende wedstrijd selecteren en de aankondiging samenstellen zonder de PDF-generatie te veranderen. Een losse notificatiestap verkleint de kans dat PDF-wijzigingslogica de wekelijkse verzending onderdrukt.
- **Aspirational:** Een WhatsApp-provider kan berichten betrouwbaar en volgens de actuele WhatsApp-regels verzenden voor de gekozen ontvangers. Kosten, templategoedkeuring, opt-in, limieten en storingsafhandeling zijn nog niet onderzocht. Ook is nog niet bewezen dat de teamcontacten WhatsApp-berichten op deze manier willen ontvangen.

## Next Steps

1. Kies een WhatsApp-verzendmethode en controleer kosten, opt-in-vereisten, berichtsjablonen en configuratie van telefoonnummers.
2. Leg vast of het bericht de eerstvolgende wedstrijd bevat of alleen een wedstrijd binnen de komende zeven dagen, en op welk lokaal tijdstip het wordt verzonden.
3. Stem de berichttekst en het gedrag bij afgelaste, gewijzigde of ontbrekende wedstrijden af met de teamcontacten.
4. Werk dit uit in een feature-specificatie met tests voor wedstrijdselectie, wekelijkse verzending zonder PDF-wijzigingen en foutafhandeling.
