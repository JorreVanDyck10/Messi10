# Afzonderlijke YOLO26-spelersgewichten

Importeer het werkelijk gefinetunede voetbalcheckpoint met
`scripts/Import-Yolo26.ps1 -Weights "C:/pad/naar/best.pt"`.
De import maakt een eigen kopie onder de SHA-256 van het bestand en bewaart
herkomst in `provenance.json`. Het YOLO11-gewicht wordt niet vervangen.

Er is nog geen gefinetuned YOLO26-checkpoint in deze map geleverd. Het algemene
COCO-model is geen vervanging voor het gerapporteerde spelersmodel van Raoul.
Gebruik Git LFS om de echte geïmporteerde `.pt` later met het team te delen.
