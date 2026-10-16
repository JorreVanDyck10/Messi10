# GenAI-gebruik en eigenaarschap

## Werkelijk gebruikte opdracht

Datum: 2026-10-16. Tool: Codex in de desktopapp; exact model niet onafhankelijk vastgelegd.

De gebruiker vroeg eerst: **"wees uitgebreid en concreet"**, met het werkpakket `02_Persoon_2_Pipeline_Minimap_Tracking.md`. Daarna koos de gebruiker via vragen voor een technisch stappenplan, lerend technisch niveau, Streamlit met één video, nog te selecteren videobron, echte spelerklassen als einddoel, afbakening op persoon 2 en een volledig zichtbaar veld.

De implementatieopdracht begon letterlijk met **"PLEASE IMPLEMENT THIS PLAN:"**, gevolgd door het volledige eerder besproken technische stappenplan. Dat verzoek omvatte de pipeline, kalibratie, interface, tracking, tests, documentatie en overdracht. Het volledige plan en de prompt staan in de oorspronkelijke chat; dit bestand is een samenvatting en geen achteraf verzonnen prompttranscript.

## Omvang van AI-hulp

De nieuwe Python-modules, Streamlit-interface, configuraties, tests en documentatieteksten in deze eerste versie zijn door Codex opgesteld. Er is geen reeds bestaande applicatiecode als eigen werk van het team gepresenteerd. De oorspronkelijke workspace bevatte alleen een Git-repository zonder commits.

Technische API-aannames zijn gecontroleerd tegen de geïnstalleerde Streamlit-skill/referenties, de werkelijke Ultralytics-trackerbroncode, officiële documentatie en lokale tests. Detectie-, geometrie- en trackingcontroles zijn afzonderlijk uitgevoerd. De actuele aantallen en resultaten worden vastgelegd in `validation.md`.

## Nog door het team uit te voeren

Het team moet de code reviewen en zelfstandig kunnen uitleggen, echte beelden en spelergewichten kiezen, brongebruik bevestigen, annotaties en splits beoordelen, echte metrics produceren en onafhankelijke eindclaims onderbouwen. De AI heeft geen menselijke review, tweede-laptopcontrole, handmatige voetbaltrackingreferenties of mondelinge verdediging gesimuleerd.

Bewaar volgende echte prompts op het moment van gebruik, met doel, overgenomen/verworpen suggesties, eigen wijzigingen en controles. De uiteindelijke disclosure kan pas drie tot vijf representatieve prompts bevatten zodra die werkelijk bestaan.

## Integratiehulp

De gebruiker vroeg op 16 oktober 2026 letterlijk: **"fix de merge conflicts"**. Codex heeft de conflicten tussen `codex/pipeline-minimap` en de bijgewerkte `main` onderzocht, beide README-werkpakketten samengevoegd, ignore-regels gecombineerd en de afzonderlijke trainings-/pipeline-dependencies behouden. De gezamenlijke testsuite, lint en formaatcontrole zijn uitgevoerd; het resultaat staat in `validation.md`. Deze technische controle is geen vervanging voor menselijke inhoudelijke review.

## Eerste echte minimapproef

De gebruiker koos daarna **"Echte minimapproef"** en vroeg opnieuw letterlijk **"PLEASE IMPLEMENT THIS PLAN:"**, gevolgd door het plan voor de PANORIS-bron, frames 0–149, geometriecontrole en een trackingvrije minimapvideo op 1920. Codex heeft de echte bronhash geverifieerd, het fragment voorbereid, punten visueel op oorspronkelijke resolutie ingeschat, controles gemeten en de volledige detector-/videoketen uitgevoerd. De puntkeuze, code en verslagen zijn AI-ondersteund. Er zijn geen menselijke reviewer, labelgoedkeuring, spelerklassen of formele foutmetrics verzonnen. Het technische reviewrecord blijft ongoedgekeurd voor menselijke MVP-acceptatie. Zie `PANORIS_Pilot.md` en de bijbehorende echte rapporten voor controles en beperkingen.

## Klikbare kalibratiepunten

De gebruiker meldde de fout **"Kalibratiepunten moeten eindige getallen bevatten"** en vroeg daarna letterlijk **"ik moet de hoeken enz zelf in vullen ma kan da nie gwn da ik kan selecteren gewoon?"**. Vervolgens vroeg hij **"zet ook bij hoeken linksboven rechtsboven enz zoda het duidelijk is"**. Codex heeft een Streamlit-v2-klikcomponent gemaakt met zoom, oorspronkelijke beeldcoördinaten, automatisch volgend ontbrekend punt, correcties via selectie en tabel, en Nederlandse plaatsnamen met een schema. Lege of niet-eindige waarden blokkeren de berekening met een concrete aanwijzing. Bestaande PANORIS-punten kunnen uitsluitend bij passende video-identiteit als suggestie worden geladen. Er is geen kalibratie automatisch goedgekeurd. De klik-/reviewflow is met AppTest gecontroleerd en de frontend is op de lokale PANORIS-clip bekeken en bediend; dit is geen menselijke geometrieacceptatie.

Na **"nu krijg ik dit Onafhankelijke controle faalt: fouten [13.54, 59.74] pixels."** heeft Codex de actuele browserpuntentabel gelezen, de afwijkingen onafhankelijk nagerekend en de oorspronkelijke puntkeuze voor diagnose bewaard. De interface kreeg benoemde controlefouten, grenswaarden en visuele foutlijnen. De kwaliteitsgrenzen zijn behouden. De reeds bestaande pilotpunten zijn vervolgens als suggestie geladen; de numerieke controle slaagde in de browser. Reviewer, brongebruik en menselijke goedkeuring zijn niet door de AI ingevuld.

## Voorbereiden op echte spelertracking

De gebruiker vroeg **"ik wil spelertracking toevoegen, er gaat iemand binnenkort veel gelabelde data in de github zette"** en koos daarna expliciet **"Eerst echte spelerklassen, daarna spelertracking"**. Codex heeft de bestaande ByteTrack-implementatie gecontroleerd en een registratiecommando voor getrainde spelersgewichten, een modelkeuze in de frontend en een concrete overdrachtshandleiding toegevoegd. De bestaande semantische en menselijke MVP-controles zijn behouden. De geregistreerde modelmetadata is in tests gesimuleerd; er zijn geen nieuwe echte spelersgewichten, annotaties, training of evaluatie verzonnen. Een werkelijke poging om de COCO-baseline als spelersmodel te registreren is terecht afgewezen.

De gebruiker vroeg daarna **"zeg ff wa moe tpersoon 1 nu nog inorde brengen en push en pull daarna alles"**. Codex heeft de overdracht aangevuld met een concrete checklist en de actuele GitHub-wijzigingen geïnspecteerd. De extra TeamTrack-video's worden onderscheiden van de nog aan te leveren label- en modeloverdracht. De lokale pipelinewijzigingen en rapporten worden gecommit en gesynchroniseerd met de taakbranch; grote lokaal gegenereerde runs en gewichten blijven volgens de projectafspraken buiten gewone Git-commits.
