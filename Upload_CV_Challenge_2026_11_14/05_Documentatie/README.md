# Definitieve documentatie — versie 5

15 november 2026. Team: Andrew, Milan Wouters, Raoul en Jorre.

- [Definitief rapport](../01_Rapport/Sports_Vision_Rapport.pdf) en [bewerkbare tekst](../01_Rapport/Sports_Vision_Rapport.md)
- [Jorres bijgewerkte presentatie](../02_Presentatie/Sports_Vision_Presentatie.pptx), twaalf bewerkbare slides
- [AI-gebruik Milan](AI_Usage_Milan_Wouters.md), [Jorre](AI_Usage_Jorre_Van_Dyck.md) en [Raoul](AI_Usage_Raoul.md)
- [Andrews eigen verklaring](../03_Code/docs/VierKlassenModel.md#16-gebruik-van-ai-tijdens-de-ontwikkeling)
- [Gezamenlijk GenAI-gebruik](GenAI_en_Eigenaarschap.md) en [bijdragen](Bijdragen_Andrew_en_Jorre.md)
- [Requirementscontrole](Requirementscontrole.md) en [wijzigingen](Versie_en_Wijzigingen.md)
- [Aangetoonde koppeling van de 80 beelden aan baltraining](Koppeling_80_Beelden_en_Baltraining.md)
- [Uitgevoerd overzichtsnotebook](../03_Code/Training_en_Evaluatie.ipynb), [bal-v2-training en audit](../03_Code/Bal_v2_Training_en_Labelkoppeling.ipynb) en [oorspronkelijke Andrew-training](../03_Code/Andrew_Prototype/train.ipynb)

Bronregistraties staan in Versiebewijs, trainingslogs en foutvoorbeelden in Trainingsbewijs en de oorspronkelijke opdracht in Bronnen. De originele Jorre-presentatie blijft bronmateriaal; de definitieve presentatie staat in 02_Presentatie.

De code en het inferentieprofiel volgen Jorres uploadpakket. Versie 5 voegt oorspronkelijke bal-v2-trainingsdata, gewichten, een audit en een uitgevoerd inspectie-/hertrainnotebook toe. De huidige app blijft Andrews balmodel gebruiken. Standaard start geen van de nieuwe notebookcellen training. Er is geen nieuwe nauwkeurigheidsmeting uitgevoerd.

Alle vereiste bestandstypen zijn aanwezig. Inhoudelijk blijven een heldere vaste-camera-MVP-demonstratie, de aparte GenAI-policy en de individuele verdediging aandachtspunten. De verbinding van alle 80 reviewbeelden met de grotere historische baltraining is nu aangetoond; de scores gelden voor de volledige historische validatie. CONTROLE.json bewaart Jorres oorspronkelijke controles; CONTROLE_DOCUMENTATIE.json beschrijft versie 5.
