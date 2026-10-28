# Sports Vision: interface en gelopen afstanden

De app combineert de nieuwste gedeelde data, balprofielen, gedeeltelijke veldkalibratie en schoolmodus met de broadcastspelers, teams en cameracompensatie. Modelprofielen blijven afzonderlijk beschikbaar; de nieuwe balgewichten worden niet automatisch standaard.

## Starten

Vanuit de projectmap:

```powershell
git pull --ff-only origin main
git lfs pull
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Voor de geselecteerde gezamenlijke modellen en de lokale veldruntime blijft `scripts/Start-Gezamenlijk.ps1` beschikbaar. Die start vereist de bestaande lokale modelselectie en veldomgeving. Voor de eenvoudige schoolworkflow gebruik je `scripts/Start-School.ps1`; de schoolmodus behoudt handmatige kalibratie en verwerking zonder tracking of teamherkenning.

## Gebruik

- **Nieuwe analyse:** upload een MP4. Automatische analyse blijft standaard aan; schakel die uit voor handmatige kalibratie. Modelprofielen en trackingopties staan onder geavanceerde instellingen.
- **Opgeslagen analyses:** open een voltooid resultaat zonder nieuwe detectie of veldherkenning. Na een teamcorrectie volgt het keuzemenu de nieuwe uitvoer; de oorspronkelijke analyse blijft selecteerbaar.
- **Veldcontrole:** controleer automatische veldanalyses per bronframe met de bestaande reviewfuncties.
- **Overzicht:** de samengestelde video houdt bronbeeld en tactical map op dezelfde tijdlijn. De samenvatting toont clipduur, bronresolutie en bij automatische analyse bruikbare veldkalibratie.
- **Spelers en afstanden:** filter tijdelijke ID’s op team en vergelijk maximaal vijf ID’s op de grafiek. De tabel toont geschatte meters, gemeten tijd en meetdekking. Teamtotalen gelden voor de volledige clip.
- **Teams:** de bestaande telling, bronframeweergave en expliciet ingediende correcties blijven beschikbaar.
- **Details en downloads:** technische verwerkingstijden en oorspronkelijke uitvoerbestanden. Trainingsstatus staat in de zijbalk onder technische status.

Bestaande `?run=VOLLEDIGE_RUN_ID`-links blijven werken. De navigatie kan vanuit een directe link ook terug naar een nieuwe analyse.

## Wat de meters betekenen

Methodeversie: `observed_median3_step02_v1`. De berekening gebruikt uitsluitend opgeslagen, actuele detecties met de rol `player`, een tijdelijke tracking-ID en een geldige veldpositie. Dezelfde regels voor geldige veldposities als bij de spelertelling gelden.

Genormaliseerde coördinaten worden omgerekend met de veldlengte en veldbreedte. Vastgelegde afmetingen uit het kalibratierecord worden hergebruikt. Anders geldt de zichtbare aanname **105 × 68 m**. Je kunt de afmetingen per analyse aanpassen; deze keuze blijft bewaard tijdens de browsersessie. Nieuwe handmatige kalibraties bewaren hun gebruikte afmetingen in het kalibratierecord.

Ontbrekende detecties, ongeldige kalibratie, dubbele ID’s in hetzelfde frame en ontbrekende frames onderbreken een segment. Een trackingreset begint een nieuwe shotnamespace, ook als een aangeleverd bestand een ID hergebruikt. Verschillende tijdelijke ID’s worden nooit samengevoegd tot een persoon.

Een ruwe verplaatsing boven de technische grens van standaard **12 m/s** onderbreekt het segment vóór filtering. Deze instelbare grens is geen onafhankelijk gevalideerde classificatie. Binnen ieder segment krijgen de binnenste posities een gecentreerd mediaanfilter van drie frames; de eindpunten blijven behouden. Afstanden worden in stappen van minimaal 0,2 seconde opgeteld, inclusief een kortere resterende eindstap. Ook na filtering wordt de spronggrens gecontroleerd.

**Meetdekking** is de geaccepteerde meettijd voor een tijdelijke ID gedeeld door de volledige clipduur. Nul meter met geldige meettijd betekent waargenomen stilstand. Zonder meetintervallen verschijnt **Niet beschikbaar**. Gaten worden niet aangevuld en meters worden niet naar een volledige wedstrijd geëxtrapoleerd. Detectie-, tracking- en kalibratiefouten kunnen de schatting beïnvloeden; onafhankelijke afstandsnauwkeurigheid is niet gemeten.

Teamtotalen sommeren geaccepteerde intervallen. Alleen wanneer alle observaties binnen het interval dezelfde teamindeling hebben, telt dat interval bij dat team; overige intervallen vallen onder onbekend. Een track met wisselende teamindeling verschijnt als onbekend/wisselend in de tabel en grafiek.

De CSV-download bevat numerieke afstand, meettijd, meetdekking, tijdelijke ID, shot, team en de gebruikte instellingen en methodeversie. Een tweede CSV bevat afzonderlijke meetintervallen. De oorspronkelijke runbestanden blijven behouden. De cache houdt rekening met framegegevenshash, veldafmetingen, meetinstellingen, clipduur en methodeversie.

## Controle op 28 oktober 2026

- **422 tests en 4 subtests geslaagd**, inclusief bekende verplaatsingen, stilstand, meetgaten, trackingresets, rollen, ongeldige sprongen en alternatieve veldafmetingen.
- Streamlit AppTest controleert afstandsinstellingen, filters, downloads, opgeslagen analyses, directe links, teamcorrecties, uploadanalyse en schoolmodus.
- De bestaande Ruff-codecontrole en formatteringscontrole slagen. De formatteringsachterstand uit de samengevoegde branches is afzonderlijk bijgewerkt: bij 45 bestanden zijn de Python-syntaxbomen voor en na formattering gelijk gecontroleerd. Historische rapporten, gegevens en gewichten zijn niet geformatteerd.
- Een bestaande echte broadcastanalyse is geopend met gesynchroniseerde video, minimap, teams en afstanden. Dit is een technische controle, geen onafhankelijke nauwkeurigheidsmeting.
- De browsercontrole gebruikt 1440 × 900 en 390 × 844. Resultaattabs laden hun inhoud alleen wanneer geopend. Tabellen schuiven binnen hun eigen weergave; de mobiele pagina zelf blijft binnen de schermbreedte.

Lokale controlebeelden staan onder `.cache/sports-vision-overview.png` en `.cache/sports-vision-mobile.png`; deze lokale bestanden worden niet naar GitHub gestuurd.
