# 004: Node.js 24 voor GitHub Actions

**Date:** 2026-10-30  
**Status:** Active  
**Author:** Aanvrager

## Problem Statement

De pipeline meldt dat meerdere gebruikte GitHub Actions nog Node.js 20 declareren, terwijl de runner ze geforceerd met Node.js 24 uitvoert. Dat kan blijven werken, maar de workflow vertrouwt dan op een runtime-overgang die de gekozen action-versie niet zelf vastlegt. De waarschuwing verdwijnt niet door alleen de applicatietests te laten slagen.

De gewenste uitkomst is een workflow waarvan alle directe en indirecte JavaScript-actions Node.js 24 gebruiken, zonder de bestaande schemageneratie, artifact-herstel of Pages-publicatie te veranderen. Dit betreft de runtime van actions; Python 3.11 en de Python-applicatie hoeven hiervoor niet te worden opgewaardeerd. Node.js installeren met een extra setup-stap verandert de runtime van JavaScript-actions niet.

Dit document is een ideatie met gecontroleerde migratiekandidaten, geen reeds toegepaste pipelinewijziging. De gekoppelde upstream-metadata is op 30-10-2026 bekeken; major-tags en branches kunnen later veranderen.

## Prior Art

- **Huidige workflow:** `.github/workflows/driving_schedule.yml` gebruikt checkout v4, configure-pages v5, setup-python v5, deploy-pages v4, upload-artifact v4 en twee downloadstappen met dawidd6/action-download-artifact v3. De actions zijn onderdeel van de bestaande werkwijze, maar veroorzaken volgens de aangeleverde runnerwaarschuwing de runtime-melding.
- **GitHub-migratieadvies:** GitHub adviseert gebruikers action-versies te kiezen die zelf Node.js 24 gebruiken. De aankondiging noemt 16 juni 2026 als begin van de standaardovergang en 23 september 2026 als verwijderdatum van Node.js 20. Dit zijn aangekondigde data, geen bewijs dat deze specifieke workflow al succesvol op Node.js 24 is getest.
- **Runtime forceren:** `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` kan een migratie helpen testen, maar vernieuwt geen action-code of metadata. De aangeleverde melding laat juist zien dat de runner de actions al forceert. Terugschakelen naar de onveilige oude runtime is geen oplossing.
- **Nieuwere action-versies:** De onderzochte metadata bevat concrete Node.js 24-versies voor vijf directe action-repositories. Een hoger major-nummer is op zichzelf onvoldoende: upload-artifact v5 declareert nog Node.js 20.
- **Indirecte afhankelijkheden:** upload-pages-artifact v3 is een composite action en roept upload-artifact v4 aan. Ook de onderzochte v4 verwijst nog naar upload-artifact v4.6.2. Alleen de expliciet genoemde actions vervangen laat deze indirecte Node.js 20-afhankelijkheid dus bestaan.
- **Downloaden uit eerdere runs:** De huidige downloadactie zoekt een eerdere workflowrun op. De huidige master-branch declareert Node.js 24; de onderzochte release v11 declareert nog Node.js 20. De branch bewijst dat ondersteuning bestaat, maar niet welke stabiele release daarvoor geschikt is.

## Proposed Approach

Pas uitsluitend de action-afhankelijkheden en strikt noodzakelijke compatibiliteitsaanpassingen aan. Inventariseer ook de actions die door composite actions worden aangeroepen. Kies gecontroleerde releases of commit-SHA's, niet blind de eerstvolgende major en niet een bewegende master-branch.

### Gecontroleerde Migratiekandidaten

| Huidige verwijzing | Kandidaat | Gecontroleerde eigenschap |
| --- | --- | --- |
| actions/checkout@v4 | actions/checkout@v5 | Metadata declareert node24. |
| actions/setup-python@v5 | actions/setup-python@v6 | Metadata declareert node24; python-version blijft een beschikbare input. |
| actions/configure-pages@v5 | actions/configure-pages@v6 | Metadata declareert node24. |
| actions/deploy-pages@v4 | actions/deploy-pages@v5 | Metadata declareert node24; page_url blijft een output. |
| actions/upload-artifact@v4, drie stappen | actions/upload-artifact@v6 | Metadata declareert node24; name, path en retention-days blijven inputs. |
| dawidd6/action-download-artifact@v3, twee stappen | Nog te kiezen Node.js 24-release of gecontroleerde commit | Master ondersteunt node24; v11 is geen geschikte vervanger. |
| actions/upload-pages-artifact@v3 | Nog te kiezen transitief Node.js 24-compatibele variant | De onderzochte v4 bevat nog een verwijzing naar upload-artifact v4.6.2. |

De kandidaten zijn aantoonbaar geschikte runtimes, niet automatisch de nieuwste releases. Release notes en de volledige gebruikte inputs moeten bij implementatie nog op breaking changes worden beoordeeld.

### Artifact-Herstel Behouden

Behoud voor beide downloadstappen de bestaande artifactnamen, het uitpakpad `docs/`, de workflowselectie en het gedrag wanneer nog geen artifact bestaat. Hieronder vallen de Markdown-schema's met JSON-wijzigingsrapporten en de Google Maps place-ID-cache. Behoud ook de bestaande bewaartermijnen van uploads.

Voorkeur: kies een gepubliceerde, gecontroleerde Node.js 24-versie van de bestaande downloadactie. Als alleen een geschikte upstream-commit beschikbaar is, beoordeel die commit en pin de exacte SHA in plaats van master. Een overstap naar de officiele downloadactie is een alternatief, maar vereist ook het bepalen van de juiste vorige run-ID; die actie is dus geen gegarandeerde drop-in vervanger.

### Pages Zonder Verborgen Oude Runtime

Voorkeur: gebruik een release van de Pages-uploadactie waarvan ook alle geneste JavaScript-actions Node.js 24 gebruiken. Controleer dit bij implementatie opnieuw.

Als zo'n versie ontbreekt, kan op de bestaande Ubuntu-runner het Pages-archief expliciet worden gemaakt en met upload-artifact v6 worden geupload. Dat alternatief moet het Pages-archiefcontract, de artifactnaam `github-pages` en de uitsluiting van ongewenste bestanden behouden. Een willekeurige upload van de map `site/` is niet zonder meer hetzelfde als de bestaande Pages-uploadactie. Kies dit alternatief pas na een gerichte compatibiliteitscontrole.

### Bewijs En Onzekerheden

- **Proven:** De lokale workflow bevat de genoemde directe verwijzingen en de Pages-uploadactie. De gecontroleerde action.yml-bestanden verklaren de runtimes en geneste afhankelijkheden in de tabel. De officiele GitHub-aankondiging adviseert het bijwerken van action-versies naar Node.js 24.
- **Likely:** De vijf gecontroleerde directe upgrades zijn beperkt van omvang, omdat de gebruikte basisinputs in de onderzochte metadata beschikbaar blijven. Dit vervangt geen uitvoeringstest en controle van release notes.
- **Aspirational:** De complete workflow is na vervanging waarschuwingvrij en functioneel gelijkwaardig. Dat is pas aangetoond na controle van de nog te kiezen download- en Pages-uploadverwijzingen en een geslaagde GitHub Actions-run.

### Verificatie En Afbakening

1. Controleer YAML en action-inputs statisch, bijvoorbeeld met actionlint, en loop alle directe en geneste action-verwijzingen na. Een lokale testset kan een runner-runtimewaarschuwing niet bewijzen of uitsluiten.
2. Voer de bestaande Python-testset uit om onbedoelde projectwijzigingen uit te sluiten. Wijzig hiervoor geen Python-versie, businesslogica of berichtinhoud.
3. Test artifact-upload en herstel met bestaande artifacts en met een lege voorgeschiedenis. Controleer dat JSON-wijzigingsrapporten en de place-ID-cache behouden blijven.
4. Controleer Pages-upload, deployment en de bestaande page_url-output. Behoud triggers, artifactnamen, bewaartermijnen en de bestaande machtigingen; voeg alleen aantoonbaar noodzakelijke minimale rechten toe.
5. Gebruik voor de eerste uitvoering een testrepository of gecontroleerde testbestemmingen. Een handmatige run van de bestaande workflow kan publiceren en e-mails versturen; start die niet ongecontroleerd als migratietest.
6. Accepteer de migratie pas wanneer de run geslaagd is, de Node.js 20-waarschuwing niet meer verschijnt en de functionele controles slagen. Verberg waarschuwingen niet als vervanging voor de migratie.

## Next Steps

1. Kies en verifieer de ontbrekende download- en Pages-uploadverwijzingen, inclusief hun transitieve runtimes en release notes.
2. Werk deze migratie desgewenst met `/feature-spec` uit tot korte stories voor directe upgrades, artifact-herstel en Pages-publicatie, met bovenstaande controles als acceptatiecriteria.
3. Pas daarna de workflow in een gerichte wijziging aan en voer de gecontroleerde migratietest uit.

## Sources

- [GitHub: deprecation of Node 20 on GitHub Actions runners](https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/)
- [Checkout v5 metadata](https://raw.githubusercontent.com/actions/checkout/v5/action.yml)
- [Setup Python v6 metadata](https://raw.githubusercontent.com/actions/setup-python/v6/action.yml)
- [Configure Pages v6 metadata](https://raw.githubusercontent.com/actions/configure-pages/v6/action.yml)
- [Deploy Pages v5 metadata](https://raw.githubusercontent.com/actions/deploy-pages/v5/action.yml)
- [Upload Artifact v5 metadata](https://raw.githubusercontent.com/actions/upload-artifact/v5/action.yml)
- [Upload Artifact v6 metadata](https://raw.githubusercontent.com/actions/upload-artifact/v6/action.yml)
- [Download Artifact master metadata](https://raw.githubusercontent.com/dawidd6/action-download-artifact/master/action.yml)
- [Download Artifact v11 metadata](https://raw.githubusercontent.com/dawidd6/action-download-artifact/v11/action.yml)
- [Download Artifact usage and run selection](https://raw.githubusercontent.com/dawidd6/action-download-artifact/master/README.md)
- [Upload Pages Artifact v3 metadata](https://raw.githubusercontent.com/actions/upload-pages-artifact/v3/action.yml)
- [Upload Pages Artifact v4 metadata](https://raw.githubusercontent.com/actions/upload-pages-artifact/v4/action.yml)
