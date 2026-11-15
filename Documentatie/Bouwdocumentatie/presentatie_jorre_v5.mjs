// Gebruik dezelfde originele Jorre-presentatie en behoud alle twaalf slides.
import {updateJorreDeck} from './presentatie_jorre_v4.mjs';
export async function updateJorreDeckV5(p) {
  await updateJorreDeck(p);
  const result=await p.inspect({kind:'textbox',include:'id,name,text'});
  const records=typeof result==='string'?JSON.parse(result).records:result.records;
  const replace=(before,after)=>{
    const r=records.find(x=>x.kind==='textbox'&&x.text===before);
    if(!r)throw new Error('Tekstanker ontbreekt: '+before);
    p.resolve(r.id).text=after;
  };
  replace('Technische kwaliteit en GenAI','GenAI en eigen verantwoordelijkheid');
  replace('537 tests en 4 subtests geslaagd; 1 GPU-test overgeslagen','Milan: videokeuze en labelwerk; AI voor code en onderzoek');
  replace("Milan Wouters: video's gezocht en ondersteund gelabeld",'Andrew: AI voor structuur, eerste code en debugging');
  replace('Codex hielp met code, curatie, training en documentatie','Jorre: AI voor presentatie, eerste model en programmeren');
  replace('AI/provider-voorstellen; het team keurde alle 80 labels goed','Raoul: AI voor leidraad, ideeën en vergelijking van opties');
  replace('Andrew: AI bij code en debugging; eigen keuzes verdedigen','Teamreview: 80 labels akkoord; AI/provider-herkomst vermeld');
  replace('De AI/provider-herkomst blijft vermeld.','80 bronbeelden via 174 crops gekoppeld aan historische baltraining');
  p.slides.items[3].speakerNotes.text+='\nNieuwe audit: alle 80 goedgekeurde bronbeelden zijn een ongewijzigde subset van het historische corpus van 132 beelden. Beeld- en labelhashes, splits en 174 positieve croptransformaties komen overeen. De datasetfingerprint verbindt de crops met het v2-experiment. Geen nieuwe training op exact 80 beelden; de historische AP geldt voor de volledige validatie van 73 beelden en niet voor het huidige Andrew-model. Bron: Koppeling_80_Beelden_en_Baltraining.md en Trainingsbewijs/labelset_training_koppeling.json.';
  p.slides.items[0].speakerNotes.text=p.slides.items[0].speakerNotes.text.replace('Versie 4','Versie 5')+'\nVersie 5 voegt Jorres en Raouls persoonlijke AI-gebruik toe op basis van de beschrijving van Milan Wouters.';
  p.slides.items[10].speakerNotes.text=`Milan Wouters verklaart zelf video's te hebben gezocht en geselecteerd en ondersteund te hebben gelabeld en gecontroleerd. Codex hielp met code, interface, curatie, trainings- en evaluatieopdrachten, diagnose, installatie, integratie en documenten. Andrew beschrijft AI voor documentstructuur, eerste code en debugging, met eigen controle volgens zijn verklaring. Volgens Milans nieuwe beschrijving gebruikte Jorre AI om de PowerPoint te verbeteren, bij een eerste modelopzet om de data te verkennen en controleren en bij algemeen programmeren. Volgens diezelfde beschrijving gebruikte Raoul AI als leidraad, voor ideeën, vergelijking van opties en duidelijke uitleg van hun verschillen en voor- en nadelen. Jorres en Raouls beschrijvingen zijn aangeleverd door Milan; er is geen nieuwe persoonlijke goedkeuring of promptgeschiedenis verzonnen. De AI/provider-voorstellen voor labels blijven vermeld. Het team bevestigt de huidige 80 labels. De historische CPU-controle meldt 537 geslaagde tests, vier subtests en één overgeslagen GPU-test. Dat is geen nieuwe controle van deze documentatieronde. Iedereen moet zijn eigen keuzes zonder AI kunnen verdedigen; de aparte GenAI-policy blijft te controleren. Bronnen: AI_Usage_Milan_Wouters.md, AI_Usage_Jorre_Van_Dyck.md, AI_Usage_Raoul.md, docs/VierKlassenModel.md hoofdstuk 16, docs/ai_usage.md, docs/GenAI_Disclosure.md, reports/release-20261114/checks.json.`;
  p.slides.items[11].speakerNotes.text='De koppeling tussen de 80 reviewbeelden en de grotere historische v2-training is inmiddels gecontroleerd via hashes, splits, 174 positieve crops, datasetfingerprint en gewichten. Dit is geen nieuwe exact-80-run. Nog te onderbouwen: heldere vaste-camera-MVP-scope en geometrische juistheid, aparte GenAI-policy en individuele verdediging. De automatische demonstratie bevat 75 frames en heeft op 73 een projectie; beschikbaarheid bewijst geen positiejuistheid. YOLO26 is onderzocht; de gedocumenteerde vergelijking behoudt YOLO11s. Extra functies moeten volgens de opdracht ook succesvol worden verdedigd om boven 85% te kunnen scoren. Bronnen: opdracht p. 4, Requirementscontrole.md, Koppeling_80_Beelden_en_Baltraining.md.';
  return {slides:p.slides.items.length,source:'Jorre uploadbranch 8e29c3ff',version:5};
}
