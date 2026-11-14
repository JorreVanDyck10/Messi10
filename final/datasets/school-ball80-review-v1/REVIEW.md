# Menselijke labelreview: 80 balbeelden

Registratie: 14 november 2026, op basis van expliciete gebruikersbevestiging.

## Uitkomst en herkomst

Het projectteam heeft de huidige 80 beelden gecontroleerd en alle behouden labels akkoord bevonden. Twijfelgevallen vielen buiten deze selectie. De selectie blijft 48 trainingsbeelden en 32 validatiebeelden; geen beeld, labelbox of split is tijdens deze registratie gewijzigd.

De oorspronkelijke annotator blijft Codex (AI), met providerlabels als voorstelbron. De gebruiker bevestigt de menselijke teamreview; Codex registreert deze verklaring en beweert niet zelf de menselijke bespreking te hebben bijgewoond. Namen van individuele reviewers en de oorspronkelijke uitvoeringsdatum zijn niet opgegeven. De tijdstempels in het manifest zijn registratietijden.

## Annotatieregels van de AI-ondersteunde voorbereiding

- De klasse is `ball`: ook zichtbare reserveballen horen bij deze taak; het model bepaalt hiermee niet welke bal in het spel is.
- Gebruik een strakke box rond de zichtbare bal. Beoordeel kleine kandidaten vergroot en in de context van het volledige beeld; schoenen, shirts en veldlijnen zijn geen bal.
- Houd rekening met zichtbare bewegingswaas en gedeeltelijke bedekking. Verzin geen positie voor een volledig verborgen of niet lokaliseerbare bal.
- Behandel een twijfelachtig beeld niet automatisch als negatief. Een negatief label vereist controle dat er werkelijk geen doelobject zichtbaar is.
- Houd de wedstrijdgroepen van training en validatie gescheiden; uitsneden uit hetzelfde bronbeeld behouden hun split.

Dit beschrijft de vastgelegde annotatieafspraken, geen aanvullend individueel reviewlog.

## Hoe onderlinge verschillen zijn afgehandeld

Volgens de gebruiker zijn twijfelgevallen uitgesloten en zijn de overige labels gezamenlijk vastgelegd. De gebruiker heeft aanvullend bevestigd dat de uitgesloten gevallen buiten de huidige 80 beelden vielen en dat alle huidige 80 labels akkoord zijn.

Een bruikbare formulering voor het verslag:

> We werkten met AI-ondersteunde annotatievoorstellen en gezamenlijke labelafspraken. Tijdens onze controle hebben we twijfelgevallen buiten de definitieve selectie gehouden. Voor de behouden beelden hebben we de labels samen vastgesteld en goedgekeurd. De definitieve reviewselectie bevat 80 beelden: 48 voor training en 32 voor validatie.

Er zijn geen aantallen meningsverschillen, specifieke correcties, individuele stemmen of reviewer-identiteiten gereconstrueerd. De 80 opgeslagen labelbestanden zijn gelijk aan de oorspronkelijk geleverde labels; goedkeuring betekent hier dat het team deze labels aanvaardt.

## Grenzen

Deze verklaring geldt uitsluitend voor deze 80-beeldenselectie. Andere datasets en historische trainingsruns worden hiermee niet automatisch menselijk goedgekeurd. De selectie blijft ontwikkeldata en wordt geen onafhankelijke eindtest. Deze registratie voert geen nieuwe training uit en verandert geen mAP-scores.
