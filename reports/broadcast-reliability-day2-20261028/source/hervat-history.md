# Broadcastbetrouwbaarheid — hervatpunt 28 oktober 2026

## Opdracht en grenzen
Volledige broadcastketen verbeteren in circa drie lokale werkdagen. Bestaande labels, geen menselijke review, geen officiële test/challengebeelden. Dag 1/2/3 zijn werkfasen. Meld steeds de actieve fase.
Gebruiker vraagt limietbewaking: controleer gebruik voor langere proeven en fasewissels; Nieuwste instructie: pas afronden rond 5–10% resterend, afhankelijk van zwaarte en benodigde afrondtijd. Bij 10% geen nieuwe zware proef starten; lopende proeven veilig afronden/checkpointen met voldoende reserve vóór 5%. Gebruik nooit resetcredits zonder expliciete toestemming.

## Dag 1 uitgevoerd
- Nieuwe evaluatieparameter confidence (standaard 0,25), resultaten per wedstrijd en expliciete referentie-/splitstatus.
- Script: scripts/measure_broadcast_baseline.py. Resultaten: reports/broadcast-reliability-day1-20261028/summary.json.
- 4.284 beeldhashes gecontroleerd; 3.936 training en 348 validatie. Geen wedstrijd- of identieke beeldhashoverlap binnen deze manifesten. Geen uitspraak over alle historische trainingsbronnen.
- 341 bruikbare referentieframes; 7 zonder referentie apart gemeld.
- Confidence 0,10: precision 90,44%, recall 92,24%, correct team/alle spelers 83,79%.
- Confidence 0,25: precision 92,07%, recall 91,04%, correct team/alle spelers 82,87%. Eerdere baseline gereproduceerd.
- Appbeleid: detectie vanaf 0,10; tonen/tellen vanaf 0,25 OF gekoppeld track. Kale 0,10-score is dus geen exacte runtimescore.
- Wedstrijd 3 is zwakste: precision 88,71%, recall 90,15%, gezamenlijke teamscore 77,19% op 0,25.
- chain-diagnostics.json: bestaande demo 150 frames, 112 geldige kalibraties, 29 tijdelijke tracks, 20 met meetintervallen. Geen positie-/afstandsnauwkeurigheid gemeten.
- 24 gerichte tests slagen; Ruff en diffcontrole slagen op eerste evaluatiewijzigingen.
- Metingen liepen tijdens formattering van evaluatiecode; alleen opmaak gewijzigd, gebruikte hashes staan in frozen-inputs.json. Bewaar beide baselines; niet overschrijven.

## Dag 1 nog open
Tracking-IDF1 en ID-wissels niet gemeten. Validatieframes zijn gesampled; controleer tijdcontinuiteit voor tracking. Automatische kalibratie versus providerreferentie nog niet op dezelfde beelden gemeten. Geen geschikte onaangeroerde eindset vastgesteld.

## Dag 2 gestart
Eén echte contexttraining met nonplayer_weight=6 (default blijft 3); bestaande V8-featurecache en gecontroleerde providerlabels. Output artifacts/broadcast-reliability-day2/official-context-weight6. Lees metrics.json/role_context.pt; als ontbreken controleer lopend proces voordat herstarten. Trainfunctie weigert bestaande outputmap.
Training en evaluatie op confidence 0,25 afgerond. Kandidaat AFGEWEZEN: precision 92,14% versus 92,07%; recall 90,90% versus 91,04%; gezamenlijke teamfractie 82,77% versus 82,87%. Keeperteam 17 versus 16 correct. Beslissing: reports/broadcast-reliability-day2-20261028/official-context-decision.json. Geen tweede werkpunt nodig na falen primaire acceptatie. Standaardmodel behouden. Volledige regressie op dat moment: 424 tests en 4 subtests geslaagd.

## Nog uit te voeren
- Officials-contextkandidaat is gescoord en afgewezen; volgende ontwikkelstap is een afzonderlijke temporele rolproef binnen shot/track. Gebruik geen gesamplede losse validatieframes alsof het opeenvolgende frames zijn.
- Keeperkoppeling alleen met voldoende herhaald positie-/teambewijs; onbekend behouden bij twijfel.
- Tracking en automatische projectie met geschikte bestaande referenties beoordelen, of ontbrekende referenties expliciet melden.
- Dag 3 acceptatie: precision en correct-teamfractie omhoog; recall maximaal 1 procentpunt omlaag; per wedstrijd maximaal 2 punten gezamenlijke score omlaag; extra runtime maximaal 20%. Keeperfouten mogen niet toenemen. Trackingwijzigingen alleen met betere IDF1 en niet meer ID-wissels.
- Relevante volledige regressiecheck; kandidaat alleen publiceren als criteria slagen, anders baseline behouden. Bal blijft buiten scope.

## Veilig hervatten
Werkmap C:/Messi10. Eerst git status --short en dit document lezen. Behoud alle artifacts/data/cache/runs. Geen git reset of terugdraaien van bestaande wijzigingen.
Gebruik $env:PYTHONPATH='src;.' en .venv/Scripts/python.exe.
Tests: .venv/Scripts/python.exe -m pytest tests/test_broadcast_baseline.py tests/test_broadcast_players.py -q
Alle training/metingen blijven ontwikkeling; human_review_completed en independent_final_test blijven false.

## Tijdcontinuïteit en afsluitcontrole
Validatieclips bevatten telkens 125 bronframes tussen gelabelde beelden (290 intervallen). Dit is geen aaneengesloten trackingreferentie. Meet IDF1 niet alsof dit native opeenvolgende frames zijn. Zoek bestaande aaneengesloten gelabelde trainingsclips voor een expliciete ontwikkelmeting; open geen val/test-archieven.
Alle gestarte baseline-evaluaties, kandidaattraining, kandidaatevaluatie en tests zijn klaar. Geen door deze taak gestarte achtergrondtraining of evaluatie overgebleven. Dag 2 is niet voltooid; volgende stap blijft de temporele rolproef en geschikte trackingreferentie. Geen kandidaat geselecteerd. Standaardmodel behouden.

## Vervolg op 28 oktober — actieve Dag 2
- 900 DENSE beelden klaargezet: data/broadcast-temporal-v1/manifest.json, fingerprint ea385c3d88ab47b48113c294098f7a7fdea2ec4182da30f3d88fd1461b97bed8. Zes clips (eerste per bestaande wedstrijd), eerste 150 aaneengesloten volledig gelabelde frames. Train: SNGS-060/097/151; val: SNGS-021/039/078. Bestaande providerlabels, dezelfde ontwikkelwedstrijden; geen onafhankelijke eindtest.
- Voorbereiding: scripts/prepare_temporal_broadcast.py; afgerond. Beelden uitsluitend uit bestaande SoccerNet train/valid bronnen. Dit verbod op officiële eindtests omvat NIET de reeds gebruikte SoccerNet-validatie; open geen SportsMOT-val/test of challengebeelden.
- Inferentierun: artifacts/broadcast-reliability-day2/temporal-native-v1. Baseline plus temporele officialproef (3 van 5 aanwijzingen, conservatieve aangrenzende boxassociatie). Script scripts/evaluate_temporal_broadcast.py. Per clip atomisch opgeslagen JSON; controleer complete.json voor afronding.
- Terwijl inferentie liep is keeper_teams.py toegevoegd. Inferentie zelf ongewijzigd; bronverzameling-hash kan per clip verschillen. Gebruik voor latere scorevarianten --score-only op de bewaarde outputs en exacte inputcontrole, niet opnieuw infereren vanwege irrelevante bronhashverschillen.
- Volgende scoreactie na afronding: .venv/Scripts/python.exe scripts/evaluate_temporal_broadcast.py --output artifacts/broadcast-reliability-day2/temporal-native-v1 --score-only --score-output artifacts/broadcast-reliability-day2/temporal-native-v1/keeper-comparison
- Keeperproef is afzonderlijk en gecombineerd opgenomen: halve seconde steun van minstens drie toegewezen spelers nabij hetzelfde doel; voorsprong minstens twee stemmen; onbekend bij onvoldoende steun, ID-reset of framegat. Niet standaard aangesloten.
- IDF1 gebruikt globale toewijzing van alle mogelijke IoU>=0,5 identiteitsparen, volgens TrackEval Identity; ID-wissels gebruiken framegewijze toewijzing met continuïteitsvoorkeur. Geen ignore/crowd-benchmarkclaim. Alleen geldige veldspelers inclusief keepers, met expliciete provider-ID’s.
- scripts/evaluate_temporal_field.py --prepare-only draait: zes lossless FFV1-video’s, pixel voor pixel gecontroleerd tegen dezelfde JPEG-decodering. Wacht op afronding.
- Daarna, na detectorinferentie (zelfde GPU, niet tegelijk): .venv/Scripts/python.exe scripts/evaluate_temporal_field.py. Meet automatische veldkalibratie + CameraCalibration op dezelfde beelden tegen provider-grondposities. Output artifacts/broadcast-reliability-day2/field-native-v1. Geen menselijke veldnauwkeurigheid/afstandsnauwkeurigheid claimen.
- Nieuwe tests: tests/test_temporal_reliability.py (ID-fragmentatie, globale identiteitstoewijzing, overlap, resets, beschermde keepers/spelers, keepersteun). Gerichte suite in uitvoering; laatste volledige suite was vóór deze toevoegingen.
- Nog niet aan Dag 3 begonnen; niets activeren voor acceptatie en eindcontrole.

## Verdere Dag 2-resultaten (actueel)
- Dense baseline op val: precision 96,68%, recall 95,02%, gezamenlijke teamfractie 91,18%, IDF1 93,95%, 9 ID-wissels. Dit zijn drie korte startvensters met providergeometrie, andere/eenvoudigere beelden dan de brede 341-framevalidatie. Geen claim van modelverbetering tegenover eerdere scores.
- Temporele officialproef: geen verandering op val; op train één FP minder. Niet activeren.
- Eerste keeperproef had geen effect omdat hist-v2 geen keeperhoofd uitvoert. keeper-evidence-v1 gebruikte eveneens een hist-checkpoint: geen echte neurale keeperclassificatie. Bewaard als mislukte/no-op proef; niet als bewijs gebruiken.
- Werkelijke keeperclassifier: artifacts/broadcast-pitch-v1/teams/kit_embedding.pt (broadcast-kit-v1); script scripts/collect_keeper_evidence.py; keeper-evidence-v2 bevat echte softmaxscores, bronhashes en per-detectie-ID. Classifier alleen presteert slecht op ongeziene shirtkleuren, niet ongefilterd activeren.
- Keeper-neural-comparison: nieuwe scores met q>=0,9 en diepe doelpositie als extra aanwijzing, daarna herhaalde nabije teamsteun. Op train 12 extra correcte keeperteamlabels; op val 6 extra correcte keeperlabels maar netto gezamenlijke teamscore gelijk door andere fouten. Geen bewezen algemene verbetering; baseline behouden.
- Foutanalyse op brede341-set: 107 on-pitch-referees, 270 onvoldoende-overlap/lokalisatie-of-onbekend, 7 zonder nabije referentie, 5 buitenveldspelers, 5 buitenveldofficials, 4 met overlappende spelerreferentie. Providerdiagnostiek, geen menselijke foutclassificatie.
- Boxfusie-screening uitsluitend dense TRAIN: specialistgewicht 0,75 geeft hoogste AP50:95 (72,19% versus 71,39% op 0,5) met bewaarde bronboxen. Geen nieuwe rol-/NMS-/teammeting in deze screening. Nieuwe profielvariant artifacts/broadcast-reliability-day2/box-fusion075/profile.json bevroren. Volgende echte proef: brede341 evaluatie op dit profiel, dezelfde confidence0,25. Alleen activeren als alle acceptatiecriteria slagen.
- Veldvideo’s moesten MP4 zijn; FFV1-AVI blijft bewaard, geconverteerd naar RGB-lossless H264 MP4 en ALLE gedecodeerde pixels identiek gecontroleerd. Geen app-invoerregels veranderd.
- Automatische veldmeting loopt via scripts/evaluate_temporal_field.py. Eerste vier clips klaar; hervatten gebruikt bestaande netwerkbundels en projection-metrics.json. Transform-invoer gecorrigeerd naar numpy-array; geen netwerkhertraining nodig.
- scripts/evaluate_temporal_broadcast.py ondersteunt nu --geometry automatic en --profile PROFIEL. Voor auto-route nieuwe inferentiemap gebruiken: oude providerroute heeft al providerafhankelijke rolbeslissingen en mag niet als nieuwe automatische modelmeting worden hergebruikt. Auto-route gebruikt dezelfde beelden en bewaarde automatische states.json.
- Volgende GPU-volgorde: veldmeting afronden; box-fusion075 echte brede341 evaluatie; daarna dense automatische baseline (en zo nodig kandidaat). Geen gelijktijdige GPU-taken.

## Laatste besluiten — Dag 2, vervolg
- Boxfusie0,75 op brede341: precision92,29%, recall91,24%, gezamenlijke teamfractie82,99%; keepers19correct/37wrong versus16/38. MAAR denseprovider-val: IDF1 daalt93,95 naar92,69 en gezamenlijke teamscore91,18 naar90,68. Niet standaard activeren. Eigen automatische variant is ook afgerond: precision96,44%, recall72,44%, gezamenlijke teamscore69,58%, veld-IDF1 80,46. Complete runs fusion075-provider-native-v1 en fusion075-automatic-native-v1.
- Baseline automatische denseval: precision96,52%, recall72,45%, gezamenlijke teamfractie69,43%, veld-IDF1 79,71%,16 veld-ID-wissels. Image-IDF1 (ook zonder veldpositie)90,38%,22 ID-wissels. Rapporteer beeld- en veldtracking afzonderlijk. Aanvullend rapport: image-and-field-tracking-comparison.json.
- Canonical rank-guard direct-refit (configs/field-rank-guard.json) geeft+51 validatieframes op dense900; op alle gemeenschappelijke providerpunten exact dezelfde fouten. Toch AFGEWEZEN als standaard: historische80 providerlijnframes bij een releasecache +1 onjuiste trainkalibratie en+2 onjuiste valkalibraties. Bronbestanden field-rank-guard-historical80.json en field-rank-guard-comparison.json. Niet promoten vanwege alleen hogere dekking.
- Strengere extra-controlpuntvariant (SUPPORTED_RANK_SETTINGS) reduceert dit, maar nog+1 onjuiste valkalibratie; ook niet promoten. field-supported-rank-historical80.json.
- Nieuwe veel voorzichtigere beleidsproef: MOTION_RANK_SETTINGS / configs/field-motion-rank.json. Als nominale semantische fit mathematisch onvoldoende is maar andere punten de geometrie wel zouden kunnen bepalen, wordt GEEN nieuwe homografie gefit. Status insufficient_fit_geometry laat bestaande CameraCalibration alleen via zijn bestaande optische-flow-, semantische-, lijn- en leeftijdscontroles overbruggen. Originele geometrie-/oriëntatiefouten blijven geblokkeerd. Oude defaults blijven ongewijzigd.
- Eerste motion-rank-v1 meting had geen effect doordat nieuwe status aanvankelijk in invalid_observation werd omgezet. Dit is nu gecorrigeerd met gerichte test op echt berekende optische flow en verstrijken van twee seconden. V1-resultaten zijn bewaard als mislukte proef, niet gebruiken voor acceptatie.
- Actieve CPU-meting: scripts/evaluate_temporal_field.py --motion-rank, uitvoer field-motion-rank-v2; wacht op 6 projectie-metricsbestanden. Daarna pas nieuwe GPU-inferentie met --geometry automatic --field-root artifacts/broadcast-reliability-day2/field-motion-rank-v2 --output artifacts/broadcast-reliability-day2/motion-rank-automatic-native-v1.
- Historische80 directescores met MOTION_RANK_SETTINGS veranderen niet (geen nieuwe onjuiste directe kalibraties); opnieuw bevestigen na bronstabilisatie. Nieuwe tests/test_temporal_reliability.py:8tests geslaagd, inclusief echte optische-flowbrug, geen start zonderanker en afbreken na2sec. Vorige gecombineerde veldsuite42tests geslaagd vóór laatste motionstatuswijziging; volledige suite nog opnieuw draaien bij Dag3.
- rank-guard-automatic-native-v1 (onveilige refitvariant) is afgerond en bewaard, maar blijft experimenteel; niet verwarren met de nieuwe motion-rank-automatic-native-v1.
- Alle netwerkgewichten en standaard models-broadcast.json zijn tot nu toe behouden. Alleen experimentele configuraties toegevoegd. Geen menselijke review of eindtest goedgekeurd.

## Actief na laatste voortgang — nog Dag 2
- Limiet bij vorige controle64% vijf-uursverbruik,16%weekverbruik. Gebruiker wil pas afronden rond5–10% resterend. Blijf nuttig werk doen, controleer gebruik bij grote stappen; geen resetcredits gebruiken.
- Voorzichtige MOTION_RANK_SETTINGS statusafhandeling is gerepareerd: insufficient_fit_geometry staat nu in toegelaten redenen, zodat bestaande camerabrug kan werken. field-motion-rank-v2 is afgerond: oude geldige frames behouden, SNGS-07884→86 geldig, SNGS-039102 blijft102. Andere vier150/150. Geen nieuwe homografie door deze regel, alleen begrensde camerabrug vanaf eerder anker.
- Eigen lange clip: scripts/evaluate_motion_rank_clip.py; artifacts/broadcast-reliability-day2/user-clip-motion-rank-v1/summary.json:251→255 geldig op1239frames;4gewonnen,0verloren. Geen menselijke grondreferentie, dus geen nauwkeurigheidsclaim voor deze clip.
- Op historische80frames veranderen directe correct/wrong-scores met motion-rank niet. De direct-refit RANK_GUARD en extra-controlpunt SUPPORTED_RANK varianten blijven afgewezen; nooit standaard activeren.
- Nieuwe volledige regressie:432tests en4subtests geslaagd in115,19s. Dit was na toevoeging van alle huidige acht temporele tests. Bij echte nieuwe bronwijzigingen opnieuw relevante tests en uiteindelijke fullsuite.
- GPU-ketenmeting motion-rank-automatic-native-v1 loopt/was bij laatste controle op5van6clips. Lees complete.json en baseline-metrics.json voor afronding. Belangrijk: nieuwe scorecode bevat ook image_tracking en samenvatting image_IDF1/image_ID_switches, naast veldafhankelijke IDF1.
- Aanvullende nuttige training-only associatieproef gestart: scripts/tune_tracking_association.py; artifacts/broadcast-reliability-day2/tracker-association-v1. Bevroren detecties/beelden/rollen/geometrie uit temporal-native-v1. Alleen match_thresh0,7/0,85/0,9 vergeleken metbaseline0,8; alle andere trackerinstellingen behouden. Voorwaarde trainingIDF1+min0,002, geen extraID-wissels en geen dalingbeeld-IDF1. Daarna precies één gekozen drempel op valproviderroute EN automatische route controleren. Als geen trainingskandidaat slaagt: niet opvalzoeken.
- Geen productiestandaard gewijzigd. Mogelijke afronding Dag3: definitieve acceptatie per onderdeel, runtimecheck, echte videointegratie/CSV/minimap, bronkwaliteit, beknopt voor/na-verslag en schone hervatinstructies.
