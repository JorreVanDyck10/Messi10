# Documentatie bewerken

Deze map bevat de bewerkbare bronnen voor het rapport, notebook en de presentatie.

## Rapport en notebook

bouw_documentatie.py leest Rapport_Sports_Vision.md en het bronbewijs. Het genereert het PDF-rapport en voert het inspectienotebook uit, zonder modeltraining. Gebruik Python met reportlab, pypdf, pandas, matplotlib, PyYAML, nbformat en IPython. De PDF gebruikt Windows-Calibri. De scriptlocatie bepaalt de documentatiemap; final wordt naast Documentatie gevonden. Historische logs en beelden staan onder Trainingsbewijs.

## Presentatie

presentatie.mjs bewaart de oorspronkelijke bouw en versie-2-bewerking. presentatie_publicatie.mjs actualiseert de bestaande versie-2-deck naar publicatieversie 3 met behoud van zestien slides. Gebruik de Codex-presentatieruntime en updatePublication(presentation) op een ingelezen versie-2-kopie. Bewaar de bestaande grafiek inclusief haar oorspronkelijke ingebedde werkmap. Exporteer en controleer tabellen, grafiek, tekst en sprekersnotities. Bij verdere versies werk je op een kopie van de actuele presentatie.

## Historische ZIP-receptuur

Archief/maak_zip_v2.py is uitsluitend ontwikkelhistorie voor de eerdere tweemappen-snapshot. Die receptuur en de oude bronpaden zijn geen actuele GitHub-release. Gebruik hem niet ongemerkt voor de definitieve indiening. Het team bouwt vóór upload één nieuw pakket van de gekozen actuele code-, model- en datasetversie, met PDF, presentatie en trainings-/uitvoercode. Grote ZIP-bestanden en virtuele omgevingen worden niet in deze documentatiemap gecommit.
