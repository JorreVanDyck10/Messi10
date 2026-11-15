# Andrew: vierklassendetector

Het door de gebruiker aangeleverde `best.pt` is 136.786.938 bytes en heeft SHA-256
`78a847ecd67f78566e666a54aabca6141e7e63495fb76783e17b3a859d90fee9`.
De klassen zijn `ball`, `goalkeeper`, `player` en `referee`. In de gezamenlijke
pipeline blijft een keeper een speler met `player_kind=goalkeeper`.

`configs/models-andrew.json` maakt de gewichten apart selecteerbaar in de app.
**Modellen trainen → Train andrew-model (4 klassen)** traint dit model met zijn
oorspronkelijke vierklassendata. **Alles trainen** bevat deze taak ook. De nieuwe
kandidaat staat apart van de andere detector-, rol-, shirt-, context- en veldkandidaten;
export/import behoudt die scheiding. Er wordt geen notebook uitgevoerd.

De originele bijdrage komt uit `AndrewNoeyens-patch-1`, commit
`811798c78836201fbf262ac0f3ecc03f5aa3e245`, en blijft staan in `Andrew_Prototype`.
De dataset heeft 612 trainingsbeelden, 38 validatiebeelden en 13 testbeelden.
De testbeelden gaan niet naar training. De bronframefamilies zijn gescheiden;
volledige wedstrijdscheiding en onafhankelijke modelnauwkeurigheid zijn nog
niet bevestigd. Het profiel wordt daarom niet automatisch standaard.

De gezamenlijke app gebruikt zijn bestaande tracking, zonder de afzonderlijke
extrapolatiecode uit `model_deployment.ipynb`. Zie `provenance.json`, de
[trainingshandleiding](../../docs/Trainen_op_Andere_Laptop.md) en de technische
[inferentiecontrole](../../reports/portable-training-20261105/andrew-inference.json).
