# Acceptatie op de echte ontwikkelclip

Deze checklist is bewust nog niet als uitgevoerd gemarkeerd. Synthetische engineeringtests vervangen geen gezamenlijke voetbalacceptatie of test op een tweede laptop.

## MVP-review door beide personen

- [ ] Bron, gebruik, cliphash en ontwikkel-/testrol zijn vastgelegd.
- [ ] Vier hoeken en twee onafhankelijke controlepunten zijn werkelijk zichtbaar.
- [ ] Begin, midden en einde tonen dezelfde camerageometrie.
- [ ] Puntvolgorde, veldoriëntatie en controlefouten zijn gezamenlijk beoordeeld.
- [ ] Echte modelgewichten, klassennamen, coördinaten en inference-instellingen zijn bevestigd.
- [ ] Hetzelfde frame heeft hetzelfde moment op beeld en minimap.
- [ ] Geen detecties betekent geen actuele veldpunten; projectiefouten worden niet verborgen.
- [ ] Personen, spelers en scheidsrechters worden semantisch correct benoemd.
- [ ] De H.264-video speelt af en bron-/uitvoerframeaantal stemmen overeen.
- [ ] Runtime, sampled proces-RAM en indien beschikbaar GPU-allocatie zijn beoordeeld.
- [ ] Tweede teamlid start de toepassing vanuit een nieuwe eigen omgeving.
- [ ] Reviewer accepteert uitsluitend de beoordeelde run met `accept-mvp`.

## Tracking en trajecten

- [ ] Player-klassen bestaan daadwerkelijk; confidence behoudt de lage kandidaten.
- [ ] De geaccepteerde MVP gebruikt dezelfde video, modellen, kalibratie, code en dependencies.
- [ ] Normale beweging, kruising en tijdelijk verdwijnen hebben handmatige referentie-ID's.
- [ ] Beide personen controleren de referenties en zichtbaarheid per frame.
- [ ] Video en minimap tonen dezelfde actuele ID.
- [ ] Gaten blijven zichtbaar en voorspellingen worden niet als waarnemingen getekend.
- [ ] ID-wissels, overnames, onderbrekingen, missen en onterechte tracks zijn gerapporteerd.
- [ ] Eventuele parametervergelijking gebruikt dezelfde opgeslagen detecties.
- [ ] De volledige MVP-controle blijft slagen.

## Foutencatalogus per incident

Bewaar fout-ID, videohash, bronframe/tijdstip, detectie-ID, box, grondcontactpunt, veldpositie, systeem-ID en eventueel referentie-ID. Voeg beeldmateriaal, foutcategorie, hypothese, experiment en reviewer toe. Scheid detectiefouten van projectie-/kalibratiefouten en identiteitsfouten.

## Verdediging

Beiden kunnen het volledige gegevenspad uitleggen, inclusief de planaire aanname, het delen door de homogene component, verschil tussen detectorconfidence en IoU, twee ByteTrack-matchingsstappen, onafhankelijke evaluatie en de grenzen van hun claims. mAP komt uit echte runs van persoon 1; een visueel mooie demonstratie vervangt die evaluatie niet.
