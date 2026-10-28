# 001: Wekelijkse aankondiging van de komende wedstrijd

**Date:** 2026-10-28
**Status:** Active
**Author:** Aanvrager

## Problem Statement

Teamcontacten krijgen met de huidige automatisering een e-mail met PDF-rijschema's wanneer de gegenereerde schema-inhoud verandert. Dat is niet hetzelfde als iedere week een korte, tijdige aankondiging van de komende wedstrijd: een ongewijzigd schema triggert geen bericht. De relevante wedstrijd- en reisinformatie is al beschikbaar, maar wordt nog niet als Telegram-aankondiging verstuurd.

De gewenste aankondiging is bedoeld voor de ingestelde teamcontacten en bevat wedstrijdgegevens, rijschema en praktische informatie. Als werkhypothese wordt het bericht op maandag verstuurd over de eerstvolgende wedstrijd. Nog te bepalen is of dat altijd de eerstvolgende wedstrijd is of alleen een wedstrijd binnen de komende zeven dagen.

## Prior Art

- **Bestaande wekelijkse planning:** GitHub Actions draait iedere maandag om 06:00 UTC. Het script haalt wedstrijden uit de Sportlink-agenda en genereert Nederlandstalige rijschema's met datum, tegenstander, verzameltijd, start- en eindtijd, locatie, kosten, afstand en reistijd. Dit werkt al voor de huidige PDF-workflow.
- **E-mail met PDF:** Per team is een e-mailadres configureerbaar. De workflow verstuurt de PDF alleen wanneer wijzigingen worden gedetecteerd. Dit biedt de volledige planning, maar voldoet niet aan een vaste wekelijkse aankondiging en is geen Telegram-bericht.
- **Telegram:** Er is nog geen botintegratie of configuratie van Telegram-chatbestemmingen. De Telegram Bot API is de voorgestelde verzendroute; voor normaal laag volume kan deze rechtstreeks worden gebruikt, maar actuele limieten en voorwaarden moeten worden gecontroleerd. Een gebruiker moet de bot eerst starten voor een privébericht; voor een teamgroep moet de bot aan die groep worden toegevoegd.
- **Inhoudelijke grens:** De kalender en rijschema's bevatten reistijden en verzameltijden, maar geen toegewezen chauffeurs. Namen van chauffeurs kunnen dus niet betrouwbaar worden aangekondigd zonder een aanvullende gegevensbron.

## Proposed Approach

Maak een afzonderlijke wekelijkse notificatiestap die wedstrijden in de komende zeven dagen per team uit de bestaande Sportlink-kalender selecteert en een Telegram-bericht aan de geconfigureerde teamchats verstuurt. Laat deze stap onafhankelijk zijn van de wijzigingsdetectie voor PDF's, zodat ook bij een ongewijzigd rijschema het wekelijkse bericht kan worden verzonden.

Houd het eerste bericht bij controleerbare gegevens: team en tegenstander, datum en aanvangstijd, locatie, verzameltijd, reistijd, afstand en reiskosten. Vermeld geen chauffeur zolang die niet uit een betrouwbare bron komt. Configureer per team een of meer Telegram-chat-ID's en bewaar de bot-token als geheim; e-mailadressen zijn geen Telegram-bestemming.

- **Proven:** De geplande workflow draait iedere maandag. De Sportlink-verwerking levert wedstrijdgegevens en de gegenereerde schema's bevatten verzameltijd, locatie, kosten, afstand en reistijd. De huidige e-mailstap is gekoppeld aan wijzigingen, niet aan de wekelijkse planning.
- **Likely:** De bestaande kalenderverwerking kan de eerstvolgende wedstrijd selecteren en de aankondiging samenstellen zonder de PDF-generatie te veranderen. Een losse notificatiestap verkleint de kans dat PDF-wijzigingslogica de wekelijkse verzending onderdrukt.
- **Aspirational:** De teamcontacten gebruiken Telegram en willen de bot in een groepschat toelaten of de bot privé starten. Beschikbaarheid, rate limits en foutafhandeling van de Telegram Bot API moeten worden gecontroleerd. Telegram-botberichten zijn niet end-to-end versleuteld; berichten blijven daarom beperkt tot wedstrijd- en reisinformatie zonder gevoelige persoonsgegevens.

## Next Steps

1. Kies per team tussen een Telegram-groep of een of meer privéchats en leg vast wie de bot start of aan de groep toevoegt.
2. Controleer de actuele Telegram Bot API-limieten en bepaal de bot-token- en chat-ID-configuratie.
3. Bevestig het lokale verzendtijdstip; de huidige workflow draait om 06:00 UTC en verschuift lokaal met zomer- en wintertijd.
4. Stem de berichttekst en het gedrag bij afgelaste, gewijzigde of ontbrekende wedstrijden af met de teamcontacten.
5. Werk dit uit in een feature-specificatie met tests voor wedstrijdselectie, wekelijkse verzending zonder PDF-wijzigingen en foutafhandeling.
