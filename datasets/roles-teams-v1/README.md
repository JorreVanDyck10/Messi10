# Rol- en teamuitsneden v1.1

Dit is een classificatiedataset met geselecteerde persoonsuitsneden, geen volledig geannoteerde YOLO-detectiedataset. De bestaande TeamTrack-YOLO-labels blijven behouden.

- `manifest.json` bindt 1.417 originele crops aan beelden, boxen, groepen, subset, rol, team en beeldhash: 1.045 training, 372 validatie. Extra augmentaties bestaan alleen tijdens training.
- 48 beelden verwijzen naar bestaande TeamTrack-train/valbeelden. Elf externe foto’s en negen oorspronkelijke videoframes staan daadwerkelijk onder `sources`. De actuele speler-/rolselectie is 80 unieke bronbeelden inclusief twaalf ongebruikte testbeelden. Met de afzonderlijke historische balexperimenten zijn cumulatief 122 verschillende bronbeelden onderzocht; die zijn niet één dataset van 80 beelden.
- `photo-crops.json` bevat genormaliseerde foto-uitsneden. `source-provenance.json` en [ATTRIBUTION.md](ATTRIBUTION.md) bevatten auteurs, licenties, URL’s, geleverde varianten, afmetingen en hashes.
- `original-proposals.json` bewaart automatische voorstellen. `original-labels.json` bevat de door AI geselecteerde rol-/teamlabels. Sommige voorstellen betreffen dezelfde persoon; aantallen zijn cropobservaties, geen unieke mensen.
- `review` bevat context, voorstellen en definitieve controlebladen. De status blijft `provisional_ai_visual`; menselijke review is niet verricht.

TeamTrack Team A: witte veldspelers en rode doelman, bron-ID’s 0..10. Team B: blauwe veldspelers en gele doelman, bron-ID’s 11..21. In de oorspronkelijke video zijn claret/lichtblauw en oranje doelman Team A; donker/goud en groene doelman Team B. Dit zijn visuele toewijzingen, geen geverifieerde clubnamen. `person` betekent dat geen betrouwbaarder specifiek rollabel is toegekend.

Alle crops uit een foto of samenhangende videogroep blijven samen. Train en val delen geen bronbeelden of groepen. Uitsneden zijn onderling afhankelijk; zij vormen geen onafhankelijke wedstrijden of unieke mensen. Bronvideo’s, bestaande TeamTrack-splits en oorspronkelijke afmetingen blijven behouden.

Herhaal de geselecteerde training met `scripts/Train-RollenTeams.ps1`. Gebruik `git lfs pull` voor exacte bronbytes. Wijzigingen vragen een nieuwe datasetversie en evaluatie. Zie [de echte resultaten en beperkingen](../../docs/Resultaten_Rollen_en_Teams.md).
