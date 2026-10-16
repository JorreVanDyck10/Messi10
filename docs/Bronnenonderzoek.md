# Uitgevoerd bronnenonderzoek

Onderzoek uitgevoerd op 16 oktober 2026. Er zijn geen fictieve bronbeoordelingen of toegangsgoedkeuringen ingevuld.

| Bron | Gevonden kenmerken | Werkelijk onderzoek / besluit |
|---|---|---|
| [Alfheim, Simula](https://datasets.simula.no/alfheim/) | Video's van vaste camera-arrays, ruwe H.264-segmenten; niet-commercieel onderzoeksgebruik volgens de aanbieder | Drie korte segmenten van camera 1 bekeken. Sterk gebogen veldlijnen zichtbaar. Geen directe MVP-keuze zonder rectificatie en geometriecontrole. Alleen technische screening uitgevoerd. |
| [SoccerTrack v2](https://atomscott.github.io/SoccerTrack-v2/) en [datasetpagina](https://huggingface.co/datasets/atomscott/soccertrack-v2) | Panoramische voetbalvideo's van een vaste opstelling. De canonieke download vraagt instemming met toegangsvoorwaarden | Als mogelijke onderzoeksbron geregistreerd; geen accountinstemming of volledige datasetdownload uitgevoerd. |
| [PANORIS-video, door de gebruiker gekozen](https://www.youtube.com/watch?v=HBTFZwMdcCw) | Volledig veld in een panorama, 3840 × 960, ongeveer 141 seconden | Volledig gedownload op expliciet verzoek. Metadata, checksum en bronidentiteit bewaard; de gebruiker vroeg opname in GitHub. Gezamenlijke geometriecontrole blijft open. |

De PANORIS-bron is de huidige projectinvoer. Het kiezen van deze bron en het delen in GitHub zijn echte gebruikersinstructies. Definitieve labelregels, onafhankelijke splitbeoordeling en inhoudelijke projectacceptatie zijn afzonderlijke controles.

De MP4 behoudt de oorspronkelijke videopixels en bevat VP9-video plus AAC-audio. Git LFS voorkomt opname van het grote bestand als gewone Git-blob. De ruwe, uitgebreide downloader-metadata met tijdelijke downloadlinks blijft buiten Git; het publieke bronrecord bevat alleen noodzakelijke herkomstgegevens.
