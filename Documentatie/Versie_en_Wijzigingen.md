# Versie 3 - publicatie op GitHub

Datum: 15 november 2026. Inhoudelijke broncommit: `524d081a445dd57762e14eeb1e7142bbb9a3ba53`.

## Binnengehaald

- Andrews wijzigingen uit AN-Laptop-ver en docs/VierKlassenModel.md, inclusief zijn AI-gebruik en de verwijzing naar zijn oorspronkelijke training.
- Jorres afronding, import-/testherstel en geregistreerde menselijke goedkeuring van alle huidige 80 labels.
- De bestaande YOLO26- en trackinguitkomsten blijven als bronrapportages herkenbaar; de ruwe lokale experimentmappen zijn nog niet meegecommit.

## Aangepast

Rapport, notebook, slides, GenAI-verantwoording en requirementscontrole zijn bijgewerkt. Het rapport onderscheidt Andrews oorspronkelijke extrapolatietracker van de gedeelde ByteTrack-integratie en noemt de juiste YOLOv8x-trainingsinstellingen uit het bronnotebook. De 80-labelreview staat niet langer als open taak vermeld.

De actuele documenten staan nu in de Git-repository onder Documentatie, met directe links naar de primaire bijdragen. De publicatie voegt documentatie toe; overige lokale appwijzigingen, omgevingen en grote ZIP-bestanden worden niet automatisch meegestuurd.

## Controles en versies

De opgehaalde CPU-controle van Jorre rapporteert 537 passed, 1 skipped en 4 subtests passed. Deze publicatieronde heeft na lokale samenvoeging 75 gerichte tests uitgevoerd, die slagen. Het notebook is uitgevoerd en PDF/PPTX zijn op weergave en bestandsintegriteit gecontroleerd. Geen nieuwe modeltraining of volledige echte video-evaluatie.

GitHub main en het afzonderlijke GitHub-final-pakket hebben eigen startprocedures. De GitHub-final-README beschrijft de eenvoudige schoolroute. De uitgebreidere lokale final-kopie is geen ongemerkt meegepubliceerde nieuwe release. De bestanden in Versiebewijs leggen de broncommit, reviewverklaring en checksums vast.

De eerdere versies en lokale ZIP zijn ontwikkelhistorie. Voor een nieuwe indiening moet het team één pakket van de gekozen code-/modelversie bouwen.
