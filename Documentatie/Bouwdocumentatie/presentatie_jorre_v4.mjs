// Gerichte wijzigingen in Jorres originele twaalf-slidepresentatie.
// Bron: ../Bronnen/Jorre_Presentatie_20261114.pptx. Importeren met @oai/artifact-tool.
export async function updateJorreDeck(p) {
  const snapshot=await p.inspect({kind:'textbox,table',include:'id,name,text'});
  const records=typeof snapshot==='string'?JSON.parse(snapshot).records:snapshot.records;
  function replace(oldText,newText){
    const r=records.find(x=>x.kind==='textbox'&&x.text===oldText);
    if(!r)throw new Error('Ontbrekend tekstanker: '+oldText);
    p.resolve(r.id).text=newText;
  }
  replace('Andrew, Milan, Raoul en Jorre   /   14 november 2026','Andrew, Milan Wouters, Raoul en Jorre   /   15 november 2026');
  replace('537 tests en 4 subtests geslaagd','537 tests en 4 subtests geslaagd; 1 GPU-test overgeslagen');
  replace('1 GPU-test overgeslagen op deze CPU-laptop',"Milan Wouters: video's gezocht en ondersteund gelabeld");
  replace('Codex hielp met code, curatie, diagnose en documenten','Codex hielp met code, curatie, training en documentatie');
  replace('Het team bevestigt de controle van de 80 labels','AI/provider-voorstellen; het team keurde alle 80 labels goed');
  replace('De studenten verdedigen de gemaakte keuzes zelf','Andrew: AI bij code en debugging; eigen keuzes verdedigen');
  const table=records.find(x=>x.kind==='table'&&x.text.includes('40 epochs, invoer 1536'));
  if(!table)throw new Error('Modeltabel ontbreekt');
  p.resolve(table.id).cells.set(1,2,'Limiet 40 epochs, invoer 1536');
  p.slides.items[0].speakerNotes.text+='\nVersie 4, 15 november: gebaseerd op Jorres uploadbranch 8e29c3ff. Milan Wouters is de gebruiker van de persoonlijke verklaring. De overige teamnamen zijn overgenomen uit Jorres oorspronkelijke deck.';
  p.slides.items[4].speakerNotes.text+='\n40 is de ingestelde epochlimiet van het spelerscheckpoint; dit bewijst geen 40 voltooide epochs. Andrews oorspronkelijke train.ipynb vermeldt wel 50 voltooide epochs. De runnaam met 640 verandert imgsz 1280 niet.';
  p.slides.items[6].speakerNotes.text+='\nBron van deze klasse-AP: oorspronkelijke Andrew_Prototype/check_mAP.ipynb, 38 beelden en 905 instanties. Gemiddeld mAP@50 0.8852951351456926 en mAP@50:95 0.6674041467873353. De checkpointmetadata bewaart voor de laatste maat 0.66698; dit zijn afzonderlijke opgeslagen metingen. Geen nieuwe evaluatie tijdens deze documentatieronde.';
  p.slides.items[10].speakerNotes.text=`Milan Wouters verklaart zelf voetbalvideo's te hebben gezocht en geselecteerd en aan ondersteund labelen en controleren te hebben gewerkt. De oorspronkelijke provider- en Codex-voorstellen blijven vermeld; er is geen individueel correctielog voor alle boxen. Het team bevestigt alle huidige 80 labels. Milan gebruikte Codex voor code en interface, annotatiegereedschap, datasetcuratie, trainings- en evaluatieopdrachten, foutdiagnose, installatie, integratie, mergeconflicten, uitleg en documentatie. Voorbeelden en grenzen staan in AI_Usage_Milan_Wouters.md. Andrew beschrijft AI bij structuur, eerste codeonderdelen en debugging in VierKlassenModel.md hoofdstuk 16. Jorres uploadpakket is eveneens met Codex-ondersteuning gemaakt. De historische CPU-controle meldt 537 geslaagde tests, vier subtests en een overgeslagen GPU-test; dit is geen nieuwe controle. Het team blijft verantwoordelijk voor inhoud, eigen verdediging en de aparte GenAI-policy. Bronnen: docs/ai_usage.md, docs/GenAI_Disclosure.md, docs/VierKlassenModel.md, reports/release-20261114/checks.json, persoonlijke gebruikersverklaring.`;
  p.slides.items[11].speakerNotes.text+='\nOpen opleverpunten: exacte koppeling van de definitieve 80-labelselectie aan concrete training en beide AP-maten; geaccepteerde statische MVP-clip met eigen puntparen en controles; aparte GenAI-policy en individuele verdediging. De automatische demonstratie van 75 frames is wel meegeleverd. YOLO26 is onderzocht, maar de gedocumenteerde vergelijking behoudt YOLO11s.';
  return {slides:p.slides.items.length,source:'Jorre uploadbranch 8e29c3ff',version:4};
}
