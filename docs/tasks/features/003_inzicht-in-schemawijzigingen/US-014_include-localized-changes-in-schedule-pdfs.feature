Feature: Include Localized Changes In Schedule PDFs
  As a team contact
  I want the PDF to include a change report in the document language
  So that the explanation stays available when the PDF is forwarded or printed

  Scenario Outline: Include the report after the complete schedule in the document language
    Given a current schedule for "EHV HS1" with a valid comparison report
      And its report contains one changed collection time and one removed match
    When the "<language>" PDF is generated
    Then the complete schedule table and its travel costs remain present
      And the change report starts on a new page after the schedule table
      And its heading is "<heading>"
      And its entries are written in "<language>"
      And it identifies "EHV HS1" and the baseline and current versions
      And it shows the old and new collection times
      And it labels the removed match "<removed>"

    Examples:
      | language | heading                       | removed                    |
      | Dutch    | Wijzigingen in het rijschema   | Vervallen uit het schema   |
      | English  | Driving schedule changes      | Removed from the schedule  |

  Scenario: Paginate a long change report without losing entries
    Given a valid report with 60 distinct entries including long match descriptions and location names
    When both localized PDFs are generated and their pages are rendered
    Then each PDF contains all 60 entries in the specified order
      And each report spans multiple pages
      And no report text is clipped or overlaps other text
      And the complete schedule table remains readable

  Scenario Outline: Show a localized notice instead of inventing a historical comparison
    Given a schedule with report state "<state>"
    When the Dutch and English PDFs are generated
    Then the Dutch PDF contains "<Dutch notice>"
      And the English PDF contains "<English notice>"
      And neither PDF invents added or removed matches
      And both PDFs contain the complete current schedule

    Examples:
      | state                                  | Dutch notice                                                          | English notice                                                   |
      | no previous version                    | Geen vorige versie beschikbaar; wijzigingen konden niet worden bepaald | No previous version available; changes could not be determined    |
      | unreadable previous version            | Vorige versie onleesbaar; wijzigingen konden niet worden bepaald       | Previous version unreadable; changes could not be determined      |
      | unchanged legacy version without report| Wijzigingsoverzicht niet beschikbaar                                   | Change report unavailable                                        |
