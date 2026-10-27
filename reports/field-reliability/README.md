# Veldherkenning: technische vergelijking, 26 oktober 2026

**Beslissing: kandidaat niet standaard activeren.** Menselijke beoordeling is
nog open; de huidige uitvoering toont geen bewezen verbetering van correcte
dekking of projectienauwkeurigheid.

| Bron | Frames | V2 intern geldig | V3 intern geldig | Langste uitval V2 / V3 |
|---|---:|---:|---:|---:|
| Broadcast | 1.239 | 251 (20,26%) | 149 (12,03%) | 16,64 / 16,64 s |
| PANORIS, vaste brede camera | 150 | 0 | 0 | 6,00 / 6,00 s |

V3 wijst 94 directe broadcastschattingen af omdat ze niet overeenkomen met
voldoende betrouwbare gemeten camerabeweging. Acht directe schattingen krijgen
een positieve temporele bevestiging; 22 frames worden via camerabeweging
overbrugd. Het aantal intern geldige frames is geen menselijke accuracymeting.
De vaste camera heeft op alle frames onvoldoende herkende veldpunten.

De gemeten kalibratie plus herprojectie kostte voor broadcast 10,45 s (V2) en
16,63 s (V3); voor PANORIS 0,76 s en 0,83 s. Dit is exclusief nieuwe detector-
of veldnetwerkinference en exclusief de gezamenlijke vergelijkingvideo.
De PANORIS-veldwaarnemingen zijn eenmalig met de bestaande PnLCalib-release
berekend; de eigenlijke vergelijking gebruikt diezelfde opgeslagen uitvoer.

Voor ieder videotype zijn dertig beoordelingsframes en tien ontwikkelframes
vastgelegd. De oorspronkelijke beelden en contactbladen staan lokaal onder
`artifacts/field-reliability-20261026/{broadcast,fixed}/review-frames`.
Scenario-indeling en veldreferenties zijn niet als menselijke labels ingevuld.
Beide bronnen waren eerder ontwikkelvideo's, dus geen onafhankelijke eindtest.

- `comparison.json`: werkelijke technische metrics, runtime en activeringsbeslissing.
- `handoff-examples.json`: echte modeluitvoer bij herkenning, uitval en herstel;
  uitdrukkelijk geen referentiewaarheid.
- `software-validation.json`: 244 geslaagde tests en vier subtests, lintcontrole,
  formatteringscontrole en controle van de videolengtes en oorspronkelijke wijzigingen.
- `artifacts/field-reliability-20261026/{broadcast,fixed}/comparison.mp4`: lokale
  gesynchroniseerde vergelijking met dezelfde opgeslagen detecties.
- `artifacts/field-reliability-20261026/provenance-check.json`: behoud van de
  oude cameraklasse, runtime en gecontroleerde releasegewichten.

De nieuwe profielversie blijft expliciet selecteerbaar voor onderzoek. De
standaard blijft versie 2. Zie `docs/Veldherkenning_Betrouwbaarheid.md` voor het
contract, CLI-gebruik, herhaling en de menselijke beoordeling.
