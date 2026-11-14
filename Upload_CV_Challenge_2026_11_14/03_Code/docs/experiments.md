# Experimentlog

Dit log bevat geen verzonnen voetbalmetrics. De implementatiecontrole en werkelijk gemeten uitvoer staan in `docs/validation.md` en lokale runmanifesten.

Gebruik voor ieder echt experiment:

- experiment-ID, uitvoerder en reviewer;
- vraag, hypothese en referentierun;
- precies gewijzigde instelling;
- video-/dataset-/splitversie, gewichtshashes en codeversie;
- volledige configuratie en hardware;
- echte resultaten en verbeterde/verslechterde voorbeelden;
- onzekerheid, conclusie en volgende beslissing.

Voor gezamenlijke spelers-/trackingexperimenten moeten persoon 1 en persoon 2
dezelfde ontwikkelclip en modeloverdracht nog bevestigen. Het afzonderlijke
veldexperiment hieronder gebruikt de door de gebruiker aangeleverde ontwikkelclip.

## Broadcast-veldherkenning — 16 oktober 2026

Vraag: veroorzaakt de verplichte controle met twee lijnen de volledige uitval,
en kunnen onafhankelijke modelcontroles plus beperkte camerabeweging meer
bruikbare kalibraties opleveren zonder gewichten of pixelgrenzen te wijzigen?

De echte oude baseline heeft 0/1.239 bruikbare frames. Op dezelfde nieuw
opgeslagen netwerkuitvoer geeft aangepaste geometrie 228 frames, confidence 0,25
277 frames en de gekozen strengere confidence met camerabeweging 252 frames.
De confidencekeuze gebruikt uitsluitend de tien vooraf geselecteerde
ontwikkelframes: beide instellingen leveren daar 2/10 op, dus 0,3434 blijft.
De dertig beoordelingsframes komen uit andere tijdgroepen en hebben nog geen
menselijke referenties. De cijfers hierboven meten interne consistentie;
menselijke projectiefout en de 90%-doelstelling blijven open.

Het veldmodel is niet opnieuw getraind; persoon 1 en zijn model blijven buiten
de wijziging. De kandidaat blijft experimenteel door lange uitval. De uiteindelijke
controle voegt lijntegenspraak aan de bewegingsvalidatie toe en verwijdert vier
frames uit de eerste technische kandidaat van 256 frames. Eerdere lokale
runmanifesten blijven bewaard.

Zie [de methode, beslissing en reproduceerprocedure](Broadcast_Veldexperiment.md)
en `reports/broadcast-field-experiment.json` voor exacte bron-/gewichtshashes,
instellingen, software, uitvalintervallen, controlefouten en tijdmetingen.
