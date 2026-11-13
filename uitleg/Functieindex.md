# Functieindex bij de studiegids

Gemaakt op 13 november 2026. Dit is een bronindex, geen nieuwe uitvoering van modellen of tests. De korte uitleg hoort bij de bredere hoofdstukken in Studiegids.md. Broncommentaren zijn letterlijk uit de code overgenomen en kunnen Engels zijn.

Elke definitie vermeldt bestand, regels, argumenten, aangeroepen functies en technische kenmerken. Die kenmerken zijn uit de syntax afgeleid: een if-statement bewijst bijvoorbeeld geen inhoudelijk correcte validatie. Ga voor de precieze werking naar de gekoppelde bron.

Definities van externe bibliotheken zijn niet gekopieerd. Het bestand waar een functie staat bepaalt haar context; twee functies met dezelfde naam kunnen iets anders doen.

## persoon1/__init__.py

Ondersteunende module of pakketstart. Lees de definities hieronder voor de precieze scope.

Bron: [persoon1/__init__.py](../persoon1/__init__.py).

Broncommentaar: Reproducible data, detection and evaluation tools for Sports Vision.
Geen eigen top-level functies of classes. Dit bestand bevat pakketinitialisatie, constanten of direct uitgevoerde scriptcode.

## persoon1/__main__.py

Ondersteunende module of pakketstart. Lees de definities hieronder voor de precieze scope.

Bron: [persoon1/__main__.py](../persoon1/__main__.py). Lokale wijzigingen of nog niet gecommit bij het samenstellen. Deze bron is niet door het publiceren van de uitleg automatisch meegecommit.

### parser

Vindplaats: [persoon1/__main__.py regel 9](../persoon1/__main__.py#L9), tot regel 75.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `argparse.ArgumentParser`, `p.add_argument`, `root.add_subparsers`, `sub.add_parser`.
Technische leespunten: return.

### execute

Vindplaats: [persoon1/__main__.py regel 78](../persoon1/__main__.py#L78), tot regel 146.
Argumenten: `(args)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `ValueError`, `canonical_hash`, `environment`, `evaluate_run`, `extract`, `inspect_video`, `json.dumps`, `len`, `now`, `predict_manifest`, `prepare_sources`, `print`, `read_json`, `require_approval`, `run.get`, `serve`, `sha256` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

### main

Vindplaats: [persoon1/__main__.py regel 149](../persoon1/__main__.py#L149), tot regel 157.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `execute`, `json.dumps`, `parser`, `parser().parse_args`, `print`.
Technische leespunten: return, foutafhandeling, voorwaardelijke vertakking.

## persoon1/annotation.py

Bewaart annotaties en biedt de lokale annotatiebediening aan.

Bron: [persoon1/annotation.py](../persoon1/annotation.py).

Broncommentaar: Small localhost-only box editor with separate automatic suggestions and reviews.

### save_annotation

Vindplaats: [persoon1/annotation.py regel 51](../persoon1/annotation.py#L51), tot regel 101.
Argumenten: `(manifest, payload)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `'\n'.join`, `ValueError`, `all`, `author.casefold`, `dataset_path`, `dict`, `frame.get`, `frame.get('annotator', '').strip`, `frame.pop`, `frame.update`, `history.open`, `isinstance`, `json.dumps`, `label_path.exists`, `label_path.parent.mkdir`, `label_path.read_text`, `label_path.write_text`, `len` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

Broncommentaar: Approval records human assertions; this is not identity authentication.

### serve

Vindplaats: [persoon1/annotation.py regel 104](../persoon1/annotation.py#L104), tot regel 165.
Argumenten: `(manifest, proposals, split, port)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `HTML.replace`, `HTML.replace('__TOKEN__', token).encode`, `HTTPServer`, `HTTPServer(('127.0.0.1', port), Handler).serve_forever`, `Path`, `Path(manifest).resolve`, `Path(proposals).resolve`, `ValueError`, `any`, `dataset_path`, `int`, `isinstance`, `json.dumps`, `json.dumps(body, ensure_ascii=False).encode`, `json.loads`, `label.is_file`, `len`, `load_manifest` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

### serve.Handler

Vindplaats: [persoon1/annotation.py regel 110](../persoon1/annotation.py#L110), tot regel 161.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: BaseHTTPRequestHandler.

### serve.Handler.respond

Vindplaats: [persoon1/annotation.py regel 111](../persoon1/annotation.py#L111), tot regel 119.
Argumenten: `(self, body, content='application/json', status=200)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `isinstance`, `json.dumps`, `json.dumps(body, ensure_ascii=False).encode`, `len`, `self.end_headers`, `self.send_header`, `self.send_response`, `self.wfile.write`, `str`.
Technische leespunten: voorwaardelijke vertakking.

### serve.Handler.do_GET

Vindplaats: [persoon1/annotation.py regel 121](../persoon1/annotation.py#L121), tot regel 145.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `dataset_path`, `label.is_file`, `len`, `load_manifest`, `mimetypes.guess_type`, `next`, `path.read_bytes`, `read_labels`, `records.append`, `self.path.startswith`, `self.respond`, `str`, `suggestion.is_file`, `unquote`.
Technische leespunten: return, foutafhandeling, lus, voorwaardelijke vertakking.

### serve.Handler.do_POST

Vindplaats: [persoon1/annotation.py regel 147](../persoon1/annotation.py#L147), tot regel 161.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `ValueError`, `any`, `int`, `json.loads`, `load_manifest`, `payload.get`, `save_annotation`, `self.headers.get`, `self.respond`, `self.rfile.read`, `str`.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, voorwaardelijke vertakking.

## persoon1/appearance_evaluation.py

Evalueert de volledige aanvullende rolpipeline op gelabelde frames.

Bron: [persoon1/appearance_evaluation.py](../persoon1/appearance_evaluation.py).

Broncommentaar: Evaluate the actual two-stage detector, keeping photo crops distinct from detection AP.

### run

Vindplaats: [persoon1/appearance_evaluation.py regel 21](../persoon1/appearance_evaluation.py#L21), tot regel 193.
Argumenten: `(output, model_manifest_path=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `''.join`, `(DATA / 'manifest.json').read_text`, `(ROOT / 'datasets/teamtrack-players-v2/manifest.json').read_text`, `(output / 'detections.jsonl').write_text`, `Counter`, `FrameRecord`, `Path`, `UltralyticsDetector`, `baseline.detect`, `copy.deepcopy`, `coverage.append`, `cv2.imread`, `cv2.imwrite`, `detector.detect`, `detector.set_video_identity`, `dict`, `enumerate`, `evaluate` en andere aanroepen.
Technische leespunten: lus, voorwaardelijke vertakking.

## persoon1/appearance_video_probe.py

Voert een beperkte echte videoproef met rolherkenning uit.

Bron: [persoon1/appearance_video_probe.py](../persoon1/appearance_video_probe.py).

Broncommentaar: Real development video inference without pretending a field calibration is available.

### run

Vindplaats: [persoon1/appearance_video_probe.py regel 20](../persoon1/appearance_video_probe.py#L20), tot regel 69.
Argumenten: `(video_path, output, frames=30, model_manifest_path=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `''.join`, `(output / 'detections.jsonl').write_text`, `Counter`, `FrameRecord`, `Path`, `UltralyticsDetector`, `capture.read`, `capture.release`, `cv2.VideoCapture`, `cv2.imwrite`, `detector.detect`, `detector.set_video_identity`, `dict`, `inspect_video`, `json.dumps`, `len`, `load_model_manifest`, `min` en andere aanroepen.
Technische leespunten: lus, voorwaardelijke vertakking.

## persoon1/core.py

Controleert datasets, labels, groepssplits, reviewstatus en bestandsidentiteit.

Bron: [persoon1/core.py](../persoon1/core.py).

Broncommentaar: Dataset provenance and review gates. Heavy ML dependencies are loaded lazily.

### now

Vindplaats: [persoon1/core.py regel 17](../persoon1/core.py#L17), tot regel 18.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `datetime.now`, `datetime.now(timezone.utc).isoformat`.
Technische leespunten: return.

### read_json

Vindplaats: [persoon1/core.py regel 21](../persoon1/core.py#L21), tot regel 22.
Argumenten: `(path)`. Retourtypehint: `niet opgegeven`.
Leest gestructureerde JSON-gegevens.
Lees verder bij aanroepen: `Path`, `Path(path).read_text`, `json.loads`.
Technische leespunten: return.

### write_json

Vindplaats: [persoon1/core.py regel 25](../persoon1/core.py#L25), tot regel 28.
Argumenten: `(path, value)`. Retourtypehint: `niet opgegeven`.
Schrijft JSON-gegevens; de module bepaalt de precieze schrijfwaarborgen.
Lees verder bij aanroepen: `Path`, `json.dumps`, `path.parent.mkdir`, `path.write_text`.

### sha256

Vindplaats: [persoon1/core.py regel 31](../persoon1/core.py#L31), tot regel 36.
Argumenten: `(path)`. Retourtypehint: `niet opgegeven`.
Berekent een SHA-256-identiteit van de exacte bestandsbytes.
Lees verder bij aanroepen: `Path`, `Path(path).open`, `h.hexdigest`, `h.update`, `hashlib.sha256`, `iter`, `stream.read`.
Technische leespunten: return, with-context, lus.

### canonical_hash

Vindplaats: [persoon1/core.py regel 39](../persoon1/core.py#L39), tot regel 40.
Argumenten: `(value)`. Retourtypehint: `niet opgegeven`.
Maakt een herhaalbare hash van gestructureerde gegevens.
Lees verder bij aanroepen: `hashlib.sha256`, `hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest`, `json.dumps`, `json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode`.
Technische leespunten: return.

### environment

Vindplaats: [persoon1/core.py regel 43](../persoon1/core.py#L43), tot regel 74.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `Path(__file__).resolve`, `bool`, `code_root.glob`, `now`, `p.relative_to`, `platform.platform`, `sha256`, `sorted`, `str`, `subprocess.check_output`, `subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True, stderr=subprocess.DEVNULL).strip`, `subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total,memory.free,driver_version', '--format=csv,noheader'], text=True, stderr=subprocess.STDOUT, timeout=15).strip`, `torch.cuda.get_device_name`, `torch.cuda.get_device_properties`, `torch.cuda.is_available`, `version`.
Technische leespunten: return, foutafhandeling, lus, voorwaardelijke vertakking.

### load_manifest

Vindplaats: [persoon1/core.py regel 77](../persoon1/core.py#L77), tot regel 93.
Argumenten: `(path)`. Retourtypehint: `niet opgegeven`.
Leest de datasetbeschrijving samen met de bijbehorende basislocatie.
Lees verder bij aanroepen: `Path`, `Path(path).resolve`, `ValueError`, `any`, `data.get`, `frame.get`, `isinstance`, `len`, `n.strip`, `read_json`, `set`.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

### dataset_path

Vindplaats: [persoon1/core.py regel 96](../persoon1/core.py#L96), tot regel 102.
Argumenten: `(root, relative)`. Retourtypehint: `niet opgegeven`.
Resolveert datasetbestanden met de toegelaten padgrenzen.
Lees verder bij aanroepen: `(root / relative).resolve`, `ValueError`, `isinstance`, `path.is_relative_to`, `root.resolve`.
Technische leespunten: return, expliciete foutmelding, voorwaardelijke vertakking.

### read_labels

Vindplaats: [persoon1/core.py regel 105](../persoon1/core.py#L105), tot regel 123.
Argumenten: `(path, class_count)`. Retourtypehint: `niet opgegeven`.
Leest en controleert de YOLO-labelregels.
Lees verder bij aanroepen: `Path`, `Path(path).read_text`, `Path(path).read_text(encoding='utf-8-sig').splitlines`, `ValueError`, `all`, `enumerate`, `int`, `labels.append`, `len`, `line.split`, `line.strip`, `map`.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

### label_pixels

Vindplaats: [persoon1/core.py regel 126](../persoon1/core.py#L126), tot regel 128.
Argumenten: `(label, width, height)`. Retourtypehint: `niet opgegeven`.
Zet genormaliseerde labelcoördinaten om naar oorspronkelijke beeldpixels.
Technische leespunten: return.

### validate_dataset

Vindplaats: [persoon1/core.py regel 131](../persoon1/core.py#L131), tot regel 223.
Argumenten: `(manifest_path, require_review=False, min_frames=40, max_frames=80)`. Retourtypehint: `niet opgegeven`.
Controleert datasetstructuur, bestanden, labels en groepsgrenzen.
Lees verder bij aanroepen: `'/'.join`, `(dhash ^ other_hash).bit_count`, `Counter`, `Image.open`, `ImageOps.grayscale`, `ImageOps.grayscale(image).resize`, `ImageOps.grayscale(image).resize((9, 8)).getdata`, `ValueError`, `abs`, `author.casefold`, `canonical_hash`, `data.get`, `dataset_path`, `defaultdict`, `dict`, `enumerate`, `errors.append`, `f.get` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

Broncommentaar: Return errors instead of silently treating absent labels as negative samples.

### require_approval

Vindplaats: [persoon1/core.py regel 226](../persoon1/core.py#L226), tot regel 239.
Argumenten: `(manifest_path, approval_path)`. Retourtypehint: `niet opgegeven`.
Vereist een passende echte menselijke datasetgoedkeuring.
Lees verder bij aanroepen: `'; '.join`, `ValueError`, `any`, `approval.get`, `isinstance`, `len`, `r.strip`, `read_json`, `reviewers[0].strip`, `reviewers[0].strip().casefold`, `reviewers[1].strip`, `reviewers[1].strip().casefold`, `validate_dataset`.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

### require_experiment_data

Vindplaats: [persoon1/core.py regel 242](../persoon1/core.py#L242), tot regel 263.
Argumenten: `(manifest_path, approval_path, provisional_ai=False)`. Retourtypehint: `niet opgegeven`.
Laat alleen de expliciet gekozen en passende reviewroute toe.
Lees verder bij aanroepen: `'; '.join`, `ValueError`, `attestation.get`, `data.get`, `dataset_path`, `frame.get`, `load_manifest`, `read_json`, `require_approval`, `sha256`, `validate_dataset`.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

Broncommentaar: Keep provisional AI experiments explicit and separate from team approval.

## persoon1/error_review.py

Verbindt concrete foutgevallen met beelden en evaluatierecords.

Bron: [persoon1/error_review.py](../persoon1/error_review.py).

Broncommentaar: Produce source-resolution context for selected development FP/FN records.

### main

Vindplaats: [persoon1/error_review.py regel 8](../persoon1/error_review.py#L8), tot regel 52.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Image.new`, `Image.open`, `Image.open(dataset_path(images, frame['image'])).convert`, `ImageDraw.Draw`, `ImageDraw.Draw(sheet).text`, `Path`, `crop.resize`, `dataset_path`, `draw.rectangle`, `enumerate`, `error.get`, `image.crop`, `int`, `label_pixels`, `len`, `load_manifest`, `max`, `min` en andere aanroepen.
Technische leespunten: return, lus.

### main.area

Vindplaats: [persoon1/error_review.py regel 18](../persoon1/error_review.py#L18), tot regel 20.
Argumenten: `(error)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `error.get`.
Technische leespunten: return.

## persoon1/metrics.py

Berekent IoU, eenmalige boxmatches, AP op 101 recallpunten en TP/FP/FN.

Bron: [persoon1/metrics.py](../persoon1/metrics.py).

Broncommentaar: Explicit 101-recall-point AP for fully labelled boxes without ignore/crowd regions.  Both reference and fine-tuned predictions use the same implementation. This is not advertised as the complete COCO benchmark (area ranges/crowd handling are absent).

### iou

Vindplaats: [persoon1/metrics.py regel 10](../persoon1/metrics.py#L10), tot regel 15.
Argumenten: `(a, b)`. Retourtypehint: `niet opgegeven`.
Rekent overlapoppervlakte gedeeld door gezamenlijke boxoppervlakte.
Lees verder bij aanroepen: `max`, `min`.
Technische leespunten: return.

### match_class

Vindplaats: [persoon1/metrics.py regel 18](../persoon1/metrics.py#L18), tot regel 32.
Argumenten: `(ground_truth, predictions, class_id, threshold)`. Retourtypehint: `niet opgegeven`.
Matcht voorspellingen in confidencevolgorde aan nog niet gebruikte referentieboxen.
Lees verder bij aanroepen: `enumerate`, `flags.append`, `ground_truth.items`, `gt.get`, `gt.values`, `iou`, `map`, `max`, `predictions.items`, `set`, `sorted`, `sum`, `used.add`.
Technische leespunten: return, lus, voorwaardelijke vertakking.

### ap101

Vindplaats: [persoon1/metrics.py regel 35](../persoon1/metrics.py#L35), tot regel 43.
Argumenten: `(total, flags)`. Retourtypehint: `niet opgegeven`.
Middelt de geïnterpoleerde precisie op 101 recallniveaus.
Lees verder bij aanroepen: `curve.append`, `enumerate`, `max`, `range`, `sum`.
Technische leespunten: return, lus, voorwaardelijke vertakking.

### evaluate

Vindplaats: [persoon1/metrics.py regel 46](../persoon1/metrics.py#L46), tot regel 84.
Argumenten: `(ground_truth, predictions, names, confidence=0.25, match_iou=0.5)`. Retourtypehint: `niet opgegeven`.
Controleert de meetinvoer en berekent AP, werkpuntmetingen en foutrecords.
Lees verder bij aanroepen: `ValueError`, `all`, `ap101`, `aps.append`, `enumerate`, `errors.append`, `gt.items`, `len`, `match_class`, `math.isfinite`, `per_class.append`, `predictions.items`, `predictions.values`, `range`, `set`, `sum`, `type`.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

## persoon1/modeling.py

Bouwt YOLO-data, start training, voert inference uit en laat resultaten evalueren.

Bron: [persoon1/modeling.py](../persoon1/modeling.py).

Broncommentaar: Inference, training and auditable evaluation. No fake labels or review approvals.

### yolo

Vindplaats: [persoon1/modeling.py regel 17](../persoon1/modeling.py#L17), tot regel 25.
Argumenten: `(weights)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(Path(os.environ['YOLO_CONFIG_DIR']) / 'Ultralytics').mkdir`, `Path`, `Path('.cache/matplotlib').resolve`, `Path('.cache/ultralytics').resolve`, `Path('data').resolve`, `Path('models').resolve`, `Path('runs').resolve`, `Path(os.environ['MPLCONFIGDIR']).mkdir`, `YOLO`, `os.environ.setdefault`, `settings.update`, `str`.
Technische leespunten: return.

### fresh_output

Vindplaats: [persoon1/modeling.py regel 28](../persoon1/modeling.py#L28), tot regel 31.
Argumenten: `(path)`. Retourtypehint: `niet opgegeven`.
Vereist een nieuwe uitvoerlocatie om bestaand bewijs niet te overschrijven.
Lees verder bij aanroepen: `Path`, `Path(path).resolve`, `path.mkdir`.
Technische leespunten: return.

### class_mapping

Vindplaats: [persoon1/modeling.py regel 34](../persoon1/modeling.py#L34), tot regel 45.
Argumenten: `(model, path, names)`. Retourtypehint: `niet opgegeven`.
Verbindt werkelijke modelklassen met expliciete doelklassen.
Lees verder bij aanroepen: `ValueError`, `mapping.items`, `names.index`, `next`, `raw.items`, `raw.values`, `read_json`.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

Broncommentaar: Mapping is by verified model class name, never by assumed integer IDs.

### assert_final_access

Vindplaats: [persoon1/modeling.py regel 48](../persoon1/modeling.py#L48), tot regel 55.
Argumenten: `(manifest, approvals, weights, config, freeze_path)`. Retourtypehint: `niet opgegeven`.
Bewaakt de voorwaarden voordat gereserveerde eindtestdata gebruikt wordt.
Lees verder bij aanroepen: `ValueError`, `any`, `canonical_hash`, `freeze.get`, `identity.items`, `read_json`, `require_approval`, `sha256`.
Technische leespunten: return, expliciete foutmelding, voorwaardelijke vertakking.

### predict_manifest

Vindplaats: [persoon1/modeling.py regel 58](../persoon1/modeling.py#L58), tot regel 128.
Argumenten: `(manifest, weights, mapping_path, out, split='val', imgsz=640, device='0', confidence=0.001, freeze=None, approvals=None)`. Retourtypehint: `niet opgegeven`.
Voert het model op de geselecteerde subset uit en bewaart voorspellingen.
Lees verder bij aanroepen: `'\n'.join`, `(out / 'detections.jsonl').open`, `(proposals / f"{frame['frame_id']}.txt").write_text`, `Image.fromarray`, `Image.fromarray(result.plot()[:, :, ::-1]).save`, `Path`, `Path(model.ckpt_path).resolve`, `ValueError`, `access.exists`, `access.open`, `access.read_text`, `access.read_text(encoding='utf-8').splitlines`, `any`, `assert_final_access`, `box.cls.item`, `box.conf.item`, `box.xyxy[0].tolist`, `canonical_hash` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

### build_yolo_dataset

Vindplaats: [persoon1/modeling.py regel 131](../persoon1/modeling.py#L131), tot regel 151.
Argumenten: `(manifest, approvals, output, provisional_ai=False)`. Retourtypehint: `niet opgegeven`.
Maakt een YOLO-train/validatiestructuur vanuit het gecontroleerde manifest.
Lees verder bij aanroepen: `(output / 'data.yaml').write_text`, `(output / sub / split).mkdir`, `Path`, `ValueError`, `any`, `dataset_path`, `dict`, `enumerate`, `fresh_output`, `load_manifest`, `require_experiment_data`, `shutil.copy2`, `str`, `yaml.safe_dump`.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

### train

Vindplaats: [persoon1/modeling.py regel 154](../persoon1/modeling.py#L154), tot regel 208.
Argumenten: `(manifest, approvals, config_path, weights, output, device='0', smoke=False, provisional_ai=False)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(output / f'train-batch-{batch}.log').open`, `LOGGER.addHandler`, `LOGGER.removeHandler`, `RuntimeError`, `ValueError`, `attempts.append`, `best.is_file`, `build_yolo_dataset`, `config.get`, `config.update`, `contextlib.redirect_stderr`, `contextlib.redirect_stdout`, `environment`, `fresh_output`, `gc.collect`, `logging.StreamHandler`, `model.train`, `now` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

Broncommentaar: Only retry CUDA OOM at batches 4, 2, 1, each from fresh pretrained weights.

### evaluate_run

Vindplaats: [persoon1/modeling.py regel 211](../persoon1/modeling.py#L211), tot regel 261.
Argumenten: `(manifest, prediction_dir, output, work_conf=0.25, freeze=None, approvals=None, provisional_ai=False)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `'\n'.join`, `(output / 'per-class.csv').open`, `(output / 'report.md').write_text`, `(prediction_dir / 'detections.jsonl').read_text`, `(prediction_dir / 'detections.jsonl').read_text(encoding='utf-8').splitlines`, `Path`, `ValueError`, `assert_final_access`, `canonical_hash`, `csv.DictWriter`, `data.get`, `dataset_path`, `evaluate`, `frame.get`, `fresh_output`, `json.loads`, `label_pixels`, `len` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

## persoon1/participant_baseline.py

Vergelijkt lokalisatie zonder COCO-person ten onrechte speler te noemen.

Bron: [persoon1/participant_baseline.py](../persoon1/participant_baseline.py).

Broncommentaar: Compare localization of the annotated participants without inventing COCO roles.

### compare

Vindplaats: [persoon1/participant_baseline.py regel 13](../persoon1/participant_baseline.py#L13), tot regel 57.
Argumenten: `(manifest, attestation, baseline_weights, candidate_predictions, output, device='0')`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(candidate_predictions / 'detections.jsonl').read_text`, `(candidate_predictions / 'detections.jsonl').read_text().splitlines`, `(output / 'baseline-predictions.jsonl').open`, `Path`, `ValueError`, `b.conf.item`, `b.xyxy[0].tolist`, `dataset_path`, `evaluate`, `float`, `fresh_output`, `json.dumps`, `json.loads`, `label_pixels`, `len`, `list`, `load_manifest`, `map` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

## persoon1/preprocessing_audit.py

Onderzoekt hoeveel kleine trainingsboxen na de echte voorbewerking overblijven.

Bron: [persoon1/preprocessing_audit.py](../persoon1/preprocessing_audit.py).

Broncommentaar: Count labels surviving the installed YOLO training transforms on real train images.

### main

Vindplaats: [persoon1/preprocessing_audit.py regel 10](../persoon1/preprocessing_audit.py#L10), tot regel 35.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Counter`, `LOGGER.setLevel`, `Path`, `Path('.cache/ultralytics').resolve`, `Path('runs/EXP-P003-teamtrack-players/dataset/images/train').resolve`, `YOLODataset`, `dict`, `enumerate`, `get_cfg`, `int`, `labels['cls'].reshape`, `now`, `original.update`, `os.environ.setdefault`, `print`, `read_json`, `retained.update`, `sample['cls'].reshape` en andere aanroepen.
Technische leespunten: lus.

## persoon1/project_dataset.py

Bouwt de oorspronkelijke gerichte projectdataset vanuit de bronselectie.

Bron: [persoon1/project_dataset.py](../persoon1/project_dataset.py).

Broncommentaar: Rebuild the disclosed, provisional ball dataset from the exact LFS source video.

### prepare

Vindplaats: [persoon1/project_dataset.py regel 9](../persoon1/project_dataset.py#L9), tot regel 67.
Argumenten: `(video, selection, output)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(output / 'labels' / f'{fid}.txt').write_text`, `(output / sub).mkdir`, `ImageDraw.Draw`, `ImageDraw.Draw(crop).rectangle`, `Path`, `ValueError`, `abs`, `av.open`, `container.decode`, `crop.save`, `enumerate`, `float`, `frames.append`, `image.crop`, `image.crop((x - 32, y - 32, x + 64, y + 64)).resize`, `image.save`, `len`, `now` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

## persoon1/review_sheets.py

Maakt visuele controlebladen voor beelden en annotaties.

Bron: [persoon1/review_sheets.py](../persoon1/review_sheets.py).

Broncommentaar: Reproducible full-frame and individual-box sheets, without altering labels.

### create_sheets

Vindplaats: [persoon1/review_sheets.py regel 11](../persoon1/review_sheets.py#L11), tot regel 58.
Argumenten: `(manifest, output)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Image.new`, `Image.open`, `Image.open(dataset_path(root, frame['image'])).convert`, `ImageDraw.Draw`, `ImageDraw.Draw(crops).text`, `ImageDraw.Draw(full).text`, `ImageDraw.Draw(official).rectangle`, `ImageDraw.Draw(officials).text`, `Path`, `crop.thumbnail`, `crops.paste`, `crops.save`, `dataset_path`, `draw.rectangle`, `draw.text`, `enumerate`, `full.paste`, `full.save` en andere aanroepen.
Technische leespunten: return, lus, voorwaardelijke vertakking.

## persoon1/role_training.py

Bouwt rolcrops, leert CNN-/kleurclassificatiekoppen en bewaart rol-/teammetingen.

Bron: [persoon1/role_training.py](../persoon1/role_training.py).

Broncommentaar: Reproducible supervised appearance heads; no reserved test frames are opened.

### save

Vindplaats: [persoon1/role_training.py regel 22](../persoon1/role_training.py#L22), tot regel 24.
Argumenten: `(path, value)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `json.dumps`, `path.parent.mkdir`, `path.write_text`.

### build

Vindplaats: [persoon1/role_training.py regel 27](../persoon1/role_training.py#L27), tot regel 127.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(DATA / 'photo-crops.json').read_text`, `(DATA / 'review-history.jsonl').exists`, `(DATA / 'source-provenance.json').read_text`, `(base / 'manifest.json').read_text`, `(base / 'role-annotations.json').read_text`, `Counter`, `ValueError`, `annotations[source['id']].items`, `cv2.imread`, `dict`, `enumerate`, `existing.is_file`, `existing.read_text`, `int`, `json.loads`, `json.loads(existing.read_text(encoding='utf-8')).get`, `np.loadtxt`, `original_labels.is_file` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

### scores

Vindplaats: [persoon1/role_training.py regel 130](../persoon1/role_training.py#L130), tot regel 157.
Argumenten: `(target, predicted, names)`. Retourtypehint: `niet opgegeven`.
Berekent de verwarringsmatrix en classificatiemetingen per rol en gemiddeld.
Lees verder bij aanroepen: `confusion.tolist`, `confusion[:, i].sum`, `confusion[i].sum`, `enumerate`, `float`, `int`, `len`, `np.mean`, `np.zeros`, `per.append`, `sum`, `zip`.
Technische leespunten: return, lus.

### load_training_manifest

Vindplaats: [persoon1/role_training.py regel 160](../persoon1/role_training.py#L160), tot regel 195.
Argumenten: `(path)`. Retourtypehint: `niet opgegeven`.
Controleert bronbeelden, cropidentiteiten en splits van extra roltraining.
Lees verder bij aanroepen: `(path.parent / row['image']).resolve`, `Path`, `Path(path).resolve`, `ValueError`, `cv2.imread`, `data.get`, `groups.setdefault`, `identifiers.add`, `image.is_relative_to`, `images.setdefault`, `json.loads`, `len`, `np.isfinite`, `np.isfinite(row['bbox']).all`, `path.read_text`, `row.get`, `set`, `sha256_file` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

Broncommentaar: Explicit extension data must preserve its own train/val groups and source bytes.

### supervised_team_videos

Vindplaats: [persoon1/role_training.py regel 198](../persoon1/role_training.py#L198), tot regel 201.
Argumenten: `(rows, base)`. Retourtypehint: `niet opgegeven`.
Verzamelt alleen de bronidentiteiten met toegelaten teamsupervisie.
Lees verder bij aanroepen: `r.get`, `sorted`.
Technische leespunten: return.

### train

Vindplaats: [persoon1/role_training.py regel 204](../persoon1/role_training.py#L204), tot regel 463.
Argumenten: `(output, fine_tune=False, encoder_checkpoint=None, manifest_path=None, fine_tune_blocks=3)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(ROOT / 'datasets/teamtrack-players-v2/manifest.json').read_text`, `Path`, `Path(manifest_path).resolve`, `ROLE_NAMES.index`, `TEAM_NAMES.index`, `ValueError`, `backbone`, `backbone(pretrained=not bool(encoder_checkpoint)).eval`, `backbone(pretrained=not bool(encoder_checkpoint)).eval().to`, `block.parameters`, `bool`, `build`, `chosen.cpu`, `colours.append`, `copy.deepcopy`, `criterion`, `crop_tensor`, `current.append` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

## persoon1/teamtrack_dataset.py

Zet de geselecteerde TeamTrack-bronnen en rollen om naar onze dataset.

Bron: [persoon1/teamtrack_dataset.py](../persoon1/teamtrack_dataset.py).

Broncommentaar: Build explicit player/referee labels from source MOT boxes and reviewed role boxes.

### build

Vindplaats: [persoon1/teamtrack_dataset.py regel 8](../persoon1/teamtrack_dataset.py#L8), tot regel 114.
Argumenten: `(root='datasets/teamtrack-players-v2')`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `'\n'.join`, `(root / 'data.yaml').write_text`, `(root / 'review-history.jsonl').exists`, `(root / label).parent.mkdir`, `(root / label).write_text`, `Image.new`, `Image.open`, `ImageDraw.Draw`, `ImageDraw.Draw(crop).rectangle`, `Path`, `ValueError`, `any`, `boxes.extend`, `create_sheets`, `crop.resize`, `draw.text`, `enumerate`, `existing.exists` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

## persoon1/technical_check.py

Controleert de technische omgeving en gerichte modelproeven.

Bron: [persoon1/technical_check.py](../persoon1/technical_check.py).

Broncommentaar: One-epoch GPU software check on generated rectangles, never project results.

### main

Vindplaats: [persoon1/technical_check.py regel 12](../persoon1/technical_check.py#L12), tot regel 70.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(root / 'dataset' / part / split).mkdir`, `(root / 'dataset/labels' / split / f'{index}.txt').write_text`, `(root / f'batch-{batch}.log').open`, `Image.new`, `ImageDraw.Draw`, `ImageDraw.Draw(image).rectangle`, `LOGGER.addHandler`, `LOGGER.removeHandler`, `Path`, `RuntimeError`, `checkpoint.is_file`, `config.update`, `contextlib.redirect_stderr`, `contextlib.redirect_stdout`, `data.write_text`, `environment`, `gc.collect`, `image.save` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

## persoon1/video.py

Controleert of voorbereidt video, tijdstempels en framegegevens; de map bepaalt welke route.

Bron: [persoon1/video.py](../persoon1/video.py). Lokale wijzigingen of nog niet gecommit bij het samenstellen. Deze bron is niet door het publiceren van de uitleg automatisch meegecommit.

Broncommentaar: Decode using actual presentation timestamps, including variable frame rate.

### split_videos

Vindplaats: [persoon1/video.py regel 10](../persoon1/video.py#L10), tot regel 74.
Argumenten: `(source_dir, output_dir, seconds=20)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `Path(output_dir).resolve`, `Path(source_dir).resolve`, `ValueError`, `abs`, `av.open`, `clip.relative_to`, `clip.relative_to(output_dir).as_posix`, `enumerate`, `float`, `frames`, `imageio_ffmpeg.get_ffmpeg_exe`, `len`, `manifest['sources'].append`, `math.isfinite`, `now`, `output_dir.exists`, `output_dir.is_relative_to` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

Broncommentaar: Re-encode at source resolution with keyframes on segment boundaries.  Audio is omitted: these are computer vision inputs. Keep the final short segment, verify decoded frame coverage, and retain source provenance.

### frames

Vindplaats: [persoon1/video.py regel 77](../persoon1/video.py#L77), tot regel 94.
Argumenten: `(path, as_image=True)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `ValueError`, `av.open`, `container.decode`, `enumerate`, `float`, `frame.to_image`, `str`.
Technische leespunten: yield of generator, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

### inspect_video

Vindplaats: [persoon1/video.py regel 97](../persoon1/video.py#L97), tot regel 116.
Argumenten: `(path, output)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `Path(path).resolve`, `ValueError`, `av.open`, `frames`, `intervals.add`, `now`, `record.update`, `round`, `set`, `sha256`, `sorted`, `str`, `write_json`.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

### extract

Vindplaats: [persoon1/video.py regel 119](../persoon1/video.py#L119), tot regel 164.
Argumenten: `(path, plan_path, output_dir)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(output_dir / 'images').mkdir`, `Path`, `Path(output_dir).resolve`, `Path(path).resolve`, `ValueError`, `decoded.to_image`, `frames`, `groups.add`, `image.save`, `len`, `max`, `output_dir.exists`, `output_dir.mkdir`, `plan.get`, `read_json`, `selected.append`, `set`, `sha256` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

Broncommentaar: Execute explicit source windows, preserving groups and held-out membership.

### prepare_sources

Vindplaats: [persoon1/video.py regel 167](../persoon1/video.py#L167), tot regel 201.
Argumenten: `(plan_path, output_dir)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(prefix / frame['image']).as_posix`, `(prefix / frame['label']).as_posix`, `Path`, `Path(os.path.relpath(video, output_dir)).as_posix`, `Path(output_dir).resolve`, `Path(plan_path).resolve`, `Path(spec['video']).resolve`, `ValueError`, `combined['frames'].append`, `combined['videos'].append`, `extract`, `len`, `os.path.relpath`, `output_dir.exists`, `output_dir.mkdir`, `plan.get`, `print`, `read_json` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

Broncommentaar: Combine fixed source plans without changing their held-out membership.

## scripts/broadcast_field_experiment.py

Voert de ontwikkelvergelijking voor Broadcast-veldherkenning uit.

Bron: [scripts/broadcast_field_experiment.py](../scripts/broadcast_field_experiment.py).

Broncommentaar: Frozen, reproducible ablations on the user's development clip; no invented human references.

### summarize

Vindplaats: [scripts/broadcast_field_experiment.py regel 28](../scripts/broadcast_field_experiment.py#L28), tot regel 47.
Argumenten: `(states, fps, development_indices)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Counter`, `dict`, `failure_intervals`, `float`, `len`, `max`, `np.median`, `s.get`, `s.get('quality', {}).get`, `sum`.
Technische leespunten: return.

### main

Vindplaats: [scripts/broadcast_field_experiment.py regel 50](../scripts/broadcast_field_experiment.py#L50), tot regel 256.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `''.join`, `(output / 'camera_motion.jsonl').write_text`, `(output / 'experiment.json').is_file`, `(output / f'{name}.jsonl').write_text`, `(result.directory / 'framegegevens.jsonl').read_text`, `(result.directory / 'framegegevens.jsonl').read_text().splitlines`, `AutomaticCalibration`, `CameraCalibration`, `Path`, `Path(bundle.observations_path).read_text`, `Path(bundle.observations_path).read_text().splitlines`, `PipelineError`, `VideoWriter`, `argparse.ArgumentParser`, `bundle.frames`, `bundle.manifest.get`, `bundle.validate_for`, `camera.update` en andere aanroepen.
Technische leespunten: expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

## scripts/build_role_extension.py

Bouwt het afzonderlijke v2-manifest voor de extra rolcrops.

Bron: [scripts/build_role_extension.py](../scripts/build_role_extension.py).

Broncommentaar: Versioned AI crop corrections after explicit visual inspection; no synthetic human review.

### main

Vindplaats: [scripts/build_role_extension.py regel 15](../scripts/build_role_extension.py#L15), tot regel 208.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Counter`, `Path`, `Path(os.path.relpath(image, output)).as_posix`, `Path(os.path.relpath(old_root / original['image'], output)).as_posix`, `ValueError`, `add`, `decisions.append`, `dict`, `item.get`, `load_training_manifest`, `original['image'].startswith`, `os.path.relpath`, `output.exists`, `output.mkdir`, `print`, `r.get`, `read_json`, `rows.append` en andere aanroepen.
Technische leespunten: expliciete foutmelding, lus, voorwaardelijke vertakking.

### main.add

Vindplaats: [scripts/build_role_extension.py regel 121](../scripts/build_role_extension.py#L121), tot regel 148.
Argumenten: `(item, image, group, split, role, origin)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `Path(os.path.relpath(image, output)).as_posix`, `decisions.append`, `item.get`, `os.path.relpath`, `rows.append`, `sha256_file`.

## scripts/collect_development_candidates.py

Verzamelt kandidaatbeelden; voorstellen zijn nog geen gereviewde labels.

Bron: [scripts/collect_development_candidates.py](../scripts/collect_development_candidates.py).

Broncommentaar: Collect unlabelled, model-assisted candidates from existing TRAIN groups only.

### main

Vindplaats: [scripts/collect_development_candidates.py regel 18](../scripts/collect_development_candidates.py#L18), tot regel 162.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(output / 'images').mkdir`, `Counter`, `OSError`, `UltralyticsDetector`, `ValueError`, `abs`, `argparse.ArgumentParser`, `args.output.resolve`, `asdict`, `capture.read`, `capture.release`, `capture.set`, `cv2.VideoCapture`, `cv2.imwrite`, `cv2.pointPolygonTest`, `cv2.putText`, `cv2.resize`, `detector.detect` en andere aanroepen.
Technische leespunten: expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

## scripts/evaluate_role_extension.py

Vergelijkt aanvullende roltrainingen en bewaart uitgesplitste resultaten.

Bron: [scripts/evaluate_role_extension.py](../scripts/evaluate_role_extension.py).

Broncommentaar: Compare two real classifiers on identical conditional crops, never report this as detection AP.

### infer

Vindplaats: [scripts/evaluate_role_extension.py regel 18](../scripts/evaluate_role_extension.py#L18), tot regel 48.
Argumenten: `(weights, root, rows)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `AppearanceClassifier`, `Detection`, `classifier.classify`, `cv2.imread`, `defaultdict`, `grouped.items`, `grouped[row['image']].append`, `objects[0].get`, `sha256_file`, `str`, `zip`.
Technische leespunten: return, lus.

### summarize

Vindplaats: [scripts/evaluate_role_extension.py regel 51](../scripts/evaluate_role_extension.py#L51), tot regel 65.
Argumenten: `(rows, predictions)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `ROLE_NAMES.index`, `len`, `np.array`, `r.get`, `scores`, `sum`.
Technische leespunten: return.

### main

Vindplaats: [scripts/evaluate_role_extension.py regel 68](../scripts/evaluate_role_extension.py#L68), tot regel 123.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `argparse.ArgumentParser`, `args.output.mkdir`, `groups.items`, `infer`, `load_training_manifest`, `p.add_argument`, `p.parse_args`, `predictions.items`, `print`, `r.get`, `report['subsets'].items`, `sha256_file`, `subset.items`, `summarize`, `write_json`.

## scripts/evaluate_video_teams.py

Vergelijkt kleurteamindeling op vastgelegde referentiecrops.

Bron: [scripts/evaluate_video_teams.py](../scripts/evaluate_video_teams.py).

Broncommentaar: Development-only colour clustering benchmark on fixed, visually reviewed crops.  Ground-truth roles/boxes isolate kit assignment from detection errors. Every video starts cold; labels are used for scoring only, never for fitting the clusters.

### run

Vindplaats: [scripts/evaluate_video_teams.py regel 22](../scripts/evaluate_video_teams.py#L22), tot regel 134.
Argumenten: `(output, implementation=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(ROOT / 'src/football_pipeline/teams.py').resolve`, `(manifest.parent / image).resolve`, `Counter`, `Detection`, `Path`, `ValueError`, `bool`, `cv2.imread`, `dict`, `groups.items`, `groups.setdefault`, `groups.setdefault(item['video'], {}).setdefault`, `groups.setdefault(item['video'], {}).setdefault(item['image'], []).append`, `images.items`, `implementation.resolve`, `importlib.util.module_from_spec`, `importlib.util.spec_from_file_location`, `json.dumps` en andere aanroepen.
Technische leespunten: expliciete foutmelding, lus, voorwaardelijke vertakking.

## scripts/export_football_annotations.py

Exporteert annotatievoorstellen naar de lokale voetbalworkflow.

Bron: [scripts/export_football_annotations.py](../scripts/export_football_annotations.py). Lokale wijzigingen of nog niet gecommit bij het samenstellen. Deze bron is niet door het publiceren van de uitleg automatisch meegecommit.

Broncommentaar: Export portable automatic proposals and their actual annotation status.  Run from the repository root: python -m scripts.export_football_annotations

### main

Vindplaats: [scripts/export_football_annotations.py regel 14](../scripts/export_football_annotations.py#L14), tot regel 103.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `'\n'.join`, `(review_dir / f"{frame['frame_id']}.txt").write_text`, `(run / 'detections.jsonl').read_text`, `(run / 'detections.jsonl').read_text(encoding='utf-8').splitlines`, `(run / 'run.json').as_posix`, `Counter`, `Path`, `Path('reports/football78-frame-index.csv').open`, `ValueError`, `clip_manifest.as_posix`, `clip_manifest.exists`, `counts.update`, `csv.DictWriter`, `dict`, `enumerate`, `frames.append`, `json.dumps`, `json.loads` en andere aanroepen.
Technische leespunten: expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

## scripts/fetch_role_photos.py

Haalt vastgelegde bronfoto’s met bronmetadata op.

Bron: [scripts/fetch_role_photos.py](../scripts/fetch_role_photos.py).

Broncommentaar: Download explicitly selected Commons sources with their attribution metadata.

### main

Vindplaats: [scripts/fetch_role_photos.py regel 14](../scripts/fetch_role_photos.py#L14), tot regel 89.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(root / 'configs/role-photo-sources.json').read_text`, `(target.parent / 'source-provenance.json').write_text`, `Path`, `Path(__file__).resolve`, `Path(source['title']).suffix.lower`, `ValueError`, `hashlib.sha256`, `hashlib.sha256(response.content).hexdigest`, `image.raise_for_status`, `info.get`, `info.get('thumburl', info['url']).split`, `iter`, `json.dumps`, `json.loads`, `next`, `path.is_file`, `path.relative_to`, `path.relative_to(target.parent).as_posix` en andere aanroepen.
Technische leespunten: expliciete foutmelding, lus, voorwaardelijke vertakking.

## scripts/field_calibration_diagnostic.py

Onderzoekt veldwaarnemingen en afwijzingen voor diagnose.

Bron: [scripts/field_calibration_diagnostic.py](../scripts/field_calibration_diagnostic.py).

Broncommentaar: Exercise real field weights with artificial camera motion of the upstream example image.  This is an engineering diagnostic, never real video accuracy or an independent football benchmark.

### main

Vindplaats: [scripts/field_calibration_diagnostic.py regel 22](../scripts/field_calibration_diagnostic.py#L22), tot regel 107.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(result.directory / 'framegegevens.jsonl').read_text`, `(result.directory / 'framegegevens.jsonl').read_text().splitlines`, `Path`, `ValueError`, `VideoWriter`, `all`, `argparse.ArgumentParser`, `args.output.mkdir`, `cv2.getRotationMatrix2D`, `cv2.imread`, `cv2.putText`, `cv2.warpAffine`, `inspect_video`, `json.dumps`, `json.loads`, `next`, `np.sin`, `parser.add_argument` en andere aanroepen.
Technische leespunten: expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

## scripts/field_calibration_pilot.py

Maakt een beperkte echte veldmodelproef met bewaarde instellingen.

Bron: [scripts/field_calibration_pilot.py](../scripts/field_calibration_pilot.py).

Broncommentaar: Download an attributed development clip, freeze a review selection, and run real field inference.  This creates no human labels or approvals. The selected frames remain an unfinished review template.

### main

Vindplaats: [scripts/field_calibration_pilot.py regel 44](../scripts/field_calibration_pilot.py#L44), tot regel 172.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `ValueError`, `argparse.ArgumentParser`, `asdict`, `cv2.imwrite`, `datetime.now`, `datetime.now(UTC).isoformat`, `directory.mkdir`, `find_tool`, `hashlib.file_digest`, `hashlib.file_digest(stream, 'sha1').hexdigest`, `images.mkdir`, `inspect_video`, `json.dumps`, `np.linspace`, `np.linspace(0, video.frame_count - 1, 30, dtype=int).tolist`, `original.is_file`, `original.open`, `original.with_suffix` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

## scripts/field_calibration_worker.py

Voert de externe punt-/lijnnetwerken in de aparte Pythonomgeving uit.

Bron: [scripts/field_calibration_worker.py](../scripts/field_calibration_worker.py).

Broncommentaar: PnLCalib network adapter. Execute with .tools/pnlcalib-env, never the player-training venv.  Upstream networks and heatmap extraction are imported from the pinned external GPL-2.0 checkout. This adapter uses ground keypoints plus independent line-network consistency, not PnL 3D refinement.

### main

Vindplaats: [scripts/field_calibration_worker.py regel 33](../scripts/field_calibration_worker.py#L33), tot regel 215.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(repository / 'config' / config).open`, `Counter`, `Path`, `ValueError`, `adapter_sources.items`, `any`, `argparse.ArgumentParser`, `args.output.mkdir`, `args.runtime.read_text`, `args.source.strip`, `args.usage.strip`, `capture.get`, `capture.read`, `capture.release`, `constructor`, `coords_to_dict`, `cv2.VideoCapture`, `cv2.cvtColor` en andere aanroepen.
Technische leespunten: expliciete foutmelding, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

## scripts/football48_ball_experiment.py

Vergelijkt pretrained sports ball met echte ballen-fine-tuning op Football48.

Bron: [scripts/football48_ball_experiment.py](../scripts/football48_ball_experiment.py).

Broncommentaar: Reproducible, provisional ball fine-tuning on the delivered football48 crops.  This development-only route has no independent test split and never grants team review. The older persoon1 final-test/review gates remain unchanged.

### truth_and_identity

Vindplaats: [scripts/football48_ball_experiment.py regel 30](../scripts/football48_ball_experiment.py#L30), tot regel 83.
Argumenten: `(source)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `balls.append`, `cv2.imread`, `digest_json`, `groups.setdefault`, `int`, `label.read_text`, `label.read_text().splitlines`, `len`, `line.split`, `map`, `np.isfinite`, `np.isfinite([x, y, width, height]).all`, `np.max`, `np.max(sizes, 0).tolist`, `np.median`, `np.median(sizes, 0).tolist`, `np.min`, `np.min(sizes, 0).tolist` en andere aanroepen.
Technische leespunten: return, lus, voorwaardelijke vertakking.

### measure

Vindplaats: [scripts/football48_ball_experiment.py regel 86](../scripts/football48_ball_experiment.py#L86), tot regel 150.
Argumenten: `(weights, source_class, manifest, truth, source, output, imgsz, device)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(output / 'detections.jsonl').open`, `ValueError`, `box.tolist`, `cv2.imread`, `cv2.imwrite`, `cv2.rectangle`, `evaluate`, `float`, `gc.collect`, `json.dumps`, `len`, `map`, `metrics.pop`, `metrics.update`, `model.names.items`, `model.predict`, `output.mkdir`, `result.boxes.conf.cpu` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

### main

Vindplaats: [scripts/football48_ball_experiment.py regel 153](../scripts/football48_ball_experiment.py#L153), tot regel 262.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(dataset / 'data.yaml').write_text`, `(run / f'train-batch-{batch}.log').open`, `LOGGER.addHandler`, `LOGGER.removeHandler`, `RuntimeError`, `argparse.ArgumentParser`, `args.candidate_weights.resolve`, `args.run.resolve`, `attempts.append`, `best.is_file`, `code_identity`, `contextlib.redirect_stderr`, `contextlib.redirect_stdout`, `create`, `dataset.as_posix`, `datetime.now`, `datetime.now(UTC).isoformat`, `dependencies` en andere aanroepen.
Technische leespunten: expliciete foutmelding, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

## scripts/panoris_pilot.py

Bereidt de statische pilot voor en controleert projectie en technische uitvoer.

Bron: [scripts/panoris_pilot.py](../scripts/panoris_pilot.py).

Broncommentaar: Reproduce the dev-00 pilot; never convert agent measurements into human approvals.

### prepare

Vindplaats: [scripts/panoris_pilot.py regel 22](../scripts/panoris_pilot.py#L22), tot regel 122.
Argumenten: `(output: Path, points_config: dict)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `PipelineError`, `asdict`, `clip.exists`, `clip.is_file`, `cv2.imwrite`, `find_tool`, `inspect_video`, `inspection_path.is_file`, `next`, `output.mkdir`, `points_config.get`, `provenance_path.is_file`, `read_frame`, `read_json`, `read_json(inspection_path).get`, `sha256_file`, `source.stat`, `source.with_suffix` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

### assess_geometry

Vindplaats: [scripts/panoris_pilot.py regel 125](../scripts/panoris_pilot.py#L125), tot regel 247.
Argumenten: `(video, config: dict, output: Path)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `PipelineError`, `all`, `anchors.issubset`, `asdict`, `bool`, `calibration_preview`, `create_calibration`, `cv2.cvtColor`, `cv2.drawMarker`, `cv2.imwrite`, `cv2.line`, `cv2.matchTemplate`, `cv2.minMaxLoc`, `float`, `frame_errors.append`, `len`, `list`, `max` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

### summarize

Vindplaats: [scripts/panoris_pilot.py regel 250](../scripts/panoris_pilot.py#L250), tot regel 304.
Argumenten: `(result, geometry: dict, output: Path)`. Retourtypehint: `dict`.
Lees verder bij aanroepen: `(result.directory / 'framegegevens.jsonl').open`, `Counter`, `PipelineError`, `dict`, `len`, `list`, `map`, `max`, `min`, `per_frame.append`, `range`, `read_json`, `str`, `sum`, `validate_completed`, `write_json`.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

### main

Vindplaats: [scripts/panoris_pilot.py regel 307](../scripts/panoris_pilot.py#L307), tot regel 348.
Argumenten: `(argv=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `argparse.ArgumentParser`, `args.output.resolve`, `assess_geometry`, `code_identity`, `parser.add_argument`, `parser.parse_args`, `prepare`, `print`, `process_video`, `read_json`, `sha256_file`, `summarize`, `write_json`.
Technische leespunten: return, foutafhandeling, voorwaardelijke vertakking.

## scripts/run_field_training.py

Stuurt voorbereiding, training en vergelijking aan met aparte logbestanden.

Bron: [scripts/run_field_training.py](../scripts/run_field_training.py).

Broncommentaar: Run both networks and then compare, keeping durable status and subprocess logs.

### main

Vindplaats: [scripts/run_field_training.py regel 18](../scripts/run_field_training.py#L18), tot regel 120.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(output / (phase + '.log')).open`, `SystemExit`, `argparse.ArgumentParser`, `args.dataset.resolve`, `args.output.resolve`, `args.runtime.resolve`, `args.video.resolve`, `commands.insert`, `datetime.now`, `datetime.now(UTC).isoformat`, `json.dumps`, `log.flush`, `log.write`, `os.getpid`, `output.mkdir`, `parser.add_argument`, `parser.parse_args`, `pending.append` en andere aanroepen.
Technische leespunten: expliciete foutmelding, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

## scripts/setup_field_model.py

Installeert de geïsoleerde PnLCalib-runtime en gecontroleerde releasegewichten.

Bron: [scripts/setup_field_model.py](../scripts/setup_field_model.py).

Broncommentaar: Install only the isolated field-model runtime and official release weights.

### checksum

Vindplaats: [scripts/setup_field_model.py regel 19](../scripts/setup_field_model.py#L19), tot regel 21.
Argumenten: `(path)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `Path(path).open`, `hashlib.file_digest`, `hashlib.file_digest(stream, 'sha256').hexdigest`.
Technische leespunten: return, with-context.

### run

Vindplaats: [scripts/setup_field_model.py regel 24](../scripts/setup_field_model.py#L24), tot regel 25.
Argumenten: `(arguments, **kwargs)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `str`, `subprocess.check_output`, `subprocess.check_output([str(a) for a in arguments], text=True, **kwargs).strip`.
Technische leespunten: return.

### main

Vindplaats: [scripts/setup_field_model.py regel 28](../scripts/setup_field_model.py#L28), tot regel 91.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(environment / 'installed-requirements.txt').write_text`, `ValueError`, `argparse.ArgumentParser`, `args.output.parent.mkdir`, `args.output.write_text`, `checksum`, `json.dumps`, `output.write`, `p.is_file`, `p.relative_to`, `parser.add_argument`, `parser.error`, `parser.parse_args`, `path.is_file`, `path.with_suffix`, `print`, `python.is_file`, `repository.exists` en andere aanroepen.
Technische leespunten: expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

## scripts/setup_field_training.py

Bereidt de afzonderlijke veldtrainingsomgeving voor.

Bron: [scripts/setup_field_training.py](../scripts/setup_field_training.py).

Broncommentaar: Extend the pinned inference runtime read-only in an isolated Windows training venv.

### main

Vindplaats: [scripts/setup_field_training.py regel 12](../scripts/setup_field_training.py#L12), tot regel 40.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(ROOT / '.tools/field-runtime.json').read_text`, `(environment / 'installed-requirements.txt').write_text`, `(site / 'field_runtime_bootstrap.py').write_text`, `Path`, `json.loads`, `packages.resolve`, `print`, `project_path.write_text`, `python.exists`, `str`, `subprocess.check_output`, `subprocess.run`.
Technische leespunten: foutafhandeling, voorwaardelijke vertakking.

## scripts/smoke_model.py

Doet een kleine technische modelcontrole, geen onafhankelijke prestatiemeting.

Bron: [scripts/smoke_model.py](../scripts/smoke_model.py).

Broncommentaar: Exercise actual YOLO inference on a local reference image; this is not a detection evaluation.
Geen eigen top-level functies of classes. Dit bestand bevat pakketinitialisatie, constanten of direct uitgevoerde scriptcode.

## scripts/verify_player_pipeline.py

Controleert contracten en echte pipeline-uitvoer op spelers en rollen.

Bron: [scripts/verify_player_pipeline.py](../scripts/verify_player_pipeline.py).

Broncommentaar: Run real player inference, field projection and video encoding, then audit the result.

### verify_records

Vindplaats: [scripts/verify_player_pipeline.py regel 23](../scripts/verify_player_pipeline.py#L23), tot regel 154.
Argumenten: `(directory: Path, manifest: dict)`. Retourtypehint: `dict`.
Lees verder bij aanroepen: `((uv >= 0) & (uv <= 1)).all`, `(directory / 'framegegevens.jsonl').read_text`, `(directory / 'framegegevens.jsonl').read_text(encoding='utf-8').splitlines`, `Counter`, `Detection.from_dict`, `FrameRecord`, `available_roles`, `detection.get`, `dict`, `float`, `inspect_video`, `int`, `json.loads`, `known_counts.append`, `known_person_counts.append`, `len`, `manifest['models'].get`, `math.isclose` en andere aanroepen.
Technische leespunten: return, lus, voorwaardelijke vertakking.

### main

Vindplaats: [scripts/verify_player_pipeline.py regel 157](../scripts/verify_player_pipeline.py#L157), tot regel 223.
Argumenten: `()`. Retourtypehint: `None`.
Lees verder bij aanroepen: `(result.directory / 'calibration.json').read_text`, `SystemExit`, `argparse.ArgumentParser`, `args.models.resolve`, `args.report.parent.mkdir`, `args.report.resolve`, `available_roles`, `datetime.now`, `datetime.now(UTC).isoformat`, `field.add_argument`, `json.loads`, `load_automatic_calibration`, `manifest.get`, `manifest['models'].get`, `parser.add_argument`, `parser.add_mutually_exclusive_group`, `parser.parse_args`, `print` en andere aanroepen.
Technische leespunten: expliciete foutmelding, foutafhandeling.

## src/football_pipeline/__init__.py

Ondersteunende module of pakketstart. Lees de definities hieronder voor de precieze scope.

Bron: [src/football_pipeline/__init__.py](../src/football_pipeline/__init__.py).

Broncommentaar: Video processing without a dependency on the Streamlit UI.
Geen eigen top-level functies of classes. Dit bestand bevat pakketinitialisatie, constanten of direct uitgevoerde scriptcode.

## src/football_pipeline/__main__.py

Ondersteunende module of pakketstart. Lees de definities hieronder voor de precieze scope.

Bron: [src/football_pipeline/__main__.py](../src/football_pipeline/__main__.py).
Geen eigen top-level functies of classes. Dit bestand bevat pakketinitialisatie, constanten of direct uitgevoerde scriptcode.

## src/football_pipeline/appearance.py

Maakt persoonscrops, CNN- en kleurfeatures en voorspelt aanvullende rollen en teams.

Bron: [src/football_pipeline/appearance.py](../src/football_pipeline/appearance.py).

Broncommentaar: Supervised crop roles and match-specific team appearance, independent of pitch position.

### crop_tensor

Vindplaats: [src/football_pipeline/appearance.py regel 16](../src/football_pipeline/appearance.py#L16), tot regel 30.
Argumenten: `(frame, box)`. Retourtypehint: `niet opgegeven`.
Knipt een persoonsgebied uit en maakt de genormaliseerde RGB-tensor voor de classifier.
Lees verder bij aanroepen: `PipelineError`, `cv2.cvtColor`, `cv2.resize`, `int`, `max`, `min`, `np.ceil`, `rgb.copy`, `torch.from_numpy`, `torch.from_numpy(rgb.copy()).permute`, `torch.from_numpy(rgb.copy()).permute(2, 0, 1).float`, `torch.tensor`.
Technische leespunten: return, expliciete foutmelding, voorwaardelijke vertakking.

### jersey_feature

Vindplaats: [src/football_pipeline/appearance.py regel 33](../src/football_pipeline/appearance.py#L33), tot regel 57.
Argumenten: `(frame, box, *, remove_turf=False)`. Retourtypehint: `niet opgegeven`.
Berekent 32 histogramkenmerken van een centraal shirtgebied.
Lees verder bij aanroepen: `cv2.cvtColor`, `cv2.resize`, `hsv.reshape`, `int`, `keep.any`, `max`, `np.concatenate`, `np.concatenate([v / max(1, v.sum()) for v in hist]).astype`, `np.histogram`, `np.zeros`, `v.sum`.
Technische leespunten: return, voorwaardelijke vertakking.

Broncommentaar: Central upper torso colour; no pitch-coordinate or person-location features.

### backbone

Vindplaats: [src/football_pipeline/appearance.py regel 60](../src/football_pipeline/appearance.py#L60), tot regel 65.
Argumenten: `(pretrained=False)`. Retourtypehint: `niet opgegeven`.
Bouwt de MobileNetV3 Small-feature-extractor zonder oorspronkelijke classificatiekop.
Lees verder bij aanroepen: `mobilenet_v3_small`, `torch.nn.Flatten`, `torch.nn.Sequential`.
Technische leespunten: return.

### AppearanceClassifier

Vindplaats: [src/football_pipeline/appearance.py regel 68](../src/football_pipeline/appearance.py#L68), tot regel 138.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### AppearanceClassifier.__init__

Vindplaats: [src/football_pipeline/appearance.py regel 69](../src/football_pipeline/appearance.py#L69), tot regel 96.
Argumenten: `(self, spec)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `PipelineError`, `VideoTeams`, `backbone`, `backbone().to`, `backbone().to(self.device).eval`, `float`, `len`, `path.is_file`, `self.backbone.load_state_dict`, `self.device.isdigit`, `self.role_head.load_state_dict`, `self.team_head.load_state_dict`, `set`, `sha256_file`, `spec.get`, `state.get`, `state['mean'].to` en andere aanroepen.
Technische leespunten: expliciete foutmelding, voorwaardelijke vertakking.

### AppearanceClassifier.classify

Vindplaats: [src/football_pipeline/appearance.py regel 98](../src/football_pipeline/appearance.py#L98), tot regel 138.
Argumenten: `(self, frame, detections, video_hash)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `crop_tensor`, `features.clone`, `float`, `int`, `jersey_feature`, `len`, `np.stack`, `range`, `role.argmax`, `role.max`, `self.backbone`, `self.role_head`, `self.role_head(role_features).softmax`, `self.role_head(role_features).softmax(1).cpu`, `self.role_head(role_features).softmax(1).cpu().numpy`, `self.team_head`, `self.team_head(features).softmax`, `self.team_head(features).softmax(1).cpu` en andere aanroepen.
Technische leespunten: with-context, lus, voorwaardelijke vertakking.

## src/football_pipeline/automatic_calibration.py

Leest automatische veldwaarnemingen, schat geometrie en projecteert geldige grondpunten.

Bron: [src/football_pipeline/automatic_calibration.py](../src/football_pipeline/automatic_calibration.py).

Broncommentaar: Content-addressed per-frame calibration; network inference lives in a separate process.

### transform

Vindplaats: [src/football_pipeline/automatic_calibration.py regel 21](../src/football_pipeline/automatic_calibration.py#L21), tot regel 30.
Argumenten: `(points, matrix)`. Retourtypehint: `niet opgegeven`.
Voert een projectieve punttransformatie inclusief homogene deling uit.
Lees verder bij aanroepen: `(denominator < 0).all`, `(denominator > 0).all`, `(np.abs(denominator) < 1e-10).any`, `ValueError`, `len`, `np.abs`, `np.asarray`, `np.column_stack`, `np.isfinite`, `np.isfinite(homogeneous).all`, `np.ones`.
Technische leespunten: return, expliciete foutmelding, voorwaardelijke vertakking.

### estimate_frame

Vindplaats: [src/football_pipeline/automatic_calibration.py regel 33](../src/football_pipeline/automatic_calibration.py#L33), tot regel 151.
Argumenten: `(observation: dict, image_size)`. Retourtypehint: `dict`.
Lees verder bij aanroepen: `(coordinates < 0).any`, `(coordinates[:, 0] >= width).any`, `(coordinates[:, 1] >= height).any`, `(denominators < -1e-10).all`, `(denominators > 1e-10).all`, `ValueError`, `cv2.contourArea`, `cv2.convexHull`, `cv2.convexHull(xy[inliers].astype(np.float32)).reshape`, `cv2.findHomography`, `cv2.setRNGSeed`, `distance.tolist`, `errors.max`, `float`, `inliers.mean`, `inliers.sum`, `int`, `len` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

Broncommentaar: Recompute from semantic observations, never trust a saved matrix or confidence claim.  Line consistency is a cross-model check, NOT independent human ground truth. No previous-frame state or extrapolation is used, including after cuts.

### AutomaticCalibration

Vindplaats: [src/football_pipeline/automatic_calibration.py regel 155](../src/football_pipeline/automatic_calibration.py#L155), tot regel 273.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### AutomaticCalibration.settings

Vindplaats: [src/football_pipeline/automatic_calibration.py regel 161](../src/football_pipeline/automatic_calibration.py#L161), tot regel 173.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `PipelineError`, `any`, `self.manifest.get`, `validate_settings`.
Technische leespunten: return, expliciete foutmelding, voorwaardelijke vertakking.

### AutomaticCalibration.identity

Vindplaats: [src/football_pipeline/automatic_calibration.py regel 176](../src/football_pipeline/automatic_calibration.py#L176), tot regel 184.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `Path(__file__).with_name`, `digest_json`, `sha256_file`.
Technische leespunten: return, voorwaardelijke vertakking.

### AutomaticCalibration.validate_for

Vindplaats: [src/football_pipeline/automatic_calibration.py regel 186](../src/football_pipeline/automatic_calibration.py#L186), tot regel 230.
Argumenten: `(self, video: VideoMetadata, approved=True)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `PipelineError`, `any`, `isinstance`, `list`, `m.get`, `m[k].strip`, `models.values`, `re.fullmatch`, `set`, `sha256_file`, `spec.get`, `str`, `upstream.get`.
Technische leespunten: expliciete foutmelding, voorwaardelijke vertakking.

### AutomaticCalibration.frames

Vindplaats: [src/football_pipeline/automatic_calibration.py regel 232](../src/football_pipeline/automatic_calibration.py#L232), tot regel 273.
Argumenten: `(self, video)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `Path(self.observations_path).open`, `PipelineError`, `ValueError`, `abs`, `estimate_checked`, `estimate_frame`, `float`, `json.loads`, `list`, `max`, `min`, `np.asarray`, `np.isfinite`, `np.isfinite(raw).all`, `range`, `raw.min`, `set` en andere aanroepen.
Technische leespunten: yield of generator, expliciete foutmelding, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

### load_automatic_calibration

Vindplaats: [src/football_pipeline/automatic_calibration.py regel 276](../src/football_pipeline/automatic_calibration.py#L276), tot regel 279.
Argumenten: `(path)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `AutomaticCalibration`, `Path`, `Path(path).resolve`, `path.with_name`, `read_json`, `str`.
Technische leespunten: return.

### project_automatic

Vindplaats: [src/football_pipeline/automatic_calibration.py regel 282](../src/football_pipeline/automatic_calibration.py#L282), tot regel 302.
Argumenten: `(detection: Detection, state: dict, image_size)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(uv < 0).any`, `(uv > 1).any`, `np.asarray`, `transform`, `uv.tolist`, `valid_box`.
Technische leespunten: return, foutafhandeling, voorwaardelijke vertakking.

### prepare_automatic_calibration

Vindplaats: [src/football_pipeline/automatic_calibration.py regel 305](../src/football_pipeline/automatic_calibration.py#L305), tot regel 405.
Argumenten: `(video_path, runtime_path, output_root, *, source, usage, progress=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(candidate / 'automatic_calibration.json').is_file`, `Path`, `Path(__file__).with_name`, `Path(output_root).resolve`, `Path(runtime_path).resolve`, `Path(video_path).resolve`, `PipelineError`, `bundle.validate_for`, `candidate.is_dir`, `destination.exists`, `destination.mkdir`, `digest_json`, `existing.validate_for`, `inspect_video`, `int`, `load_automatic_calibration`, `log_path.open`, `log_path.read_bytes` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

Broncommentaar: Run the isolated worker with an argument array; only publish completed bundles.

## src/football_pipeline/calibration_evaluation.py

Vergelijkt automatische veldprojectie met expliciet gereviewde menselijke referenties.

Bron: [src/football_pipeline/calibration_evaluation.py](../src/football_pipeline/calibration_evaluation.py).

Broncommentaar: Evaluate automatic projection against explicitly reviewed, held-out human landmarks.

### evaluate_calibration

Vindplaats: [src/football_pipeline/calibration_evaluation.py regel 15](../src/football_pipeline/calibration_evaluation.py#L15), tot regel 141.
Argumenten: `(run_directory, reference_path)`. Retourtypehint: `niet opgegeven`.
Vergelijkt de run met onafhankelijk gereviewde menselijke veldpunten.
Lees verder bij aanroepen: `(directory / 'framegegevens.jsonl').open`, `(pixels < 0).any`, `(pixels[:, 0] >= width).any`, `(pixels[:, 1] >= height).any`, `(uv < 0).any`, `(uv > 1).any`, `Path`, `PipelineError`, `ValueError`, `any`, `bool`, `distances.max`, `distances.tolist`, `enumerate`, `errors.extend`, `f.get`, `float`, `isinstance` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

## src/football_pipeline/calibration_input.py

Geeft kalibratiepunten herkenbare namen en levert alleen passende pilotsuggesties.

Bron: [src/football_pipeline/calibration_input.py](../src/football_pipeline/calibration_input.py).

Broncommentaar: Known coordinate suggestions, never an automatic calibration approval.

### point_label

Vindplaats: [src/football_pipeline/calibration_input.py regel 10](../src/football_pipeline/calibration_input.py#L10), tot regel 23.
Argumenten: `(point: dict)`. Retourtypehint: `str`.
Lees verder bij aanroepen: `labels.get`, `point.get`.
Technische leespunten: return.

Broncommentaar: Friendly labels for the orientation used by the manual selection workflow.

### panoris_point_suggestion

Vindplaats: [src/football_pipeline/calibration_input.py regel 26](../src/football_pipeline/calibration_input.py#L26), tot regel 45.
Argumenten: `(video: VideoMetadata, root: Path=ROOT)`. Retourtypehint: `list[dict] | None`.
Lees verder bij aanroepen: `deepcopy`, `hashes.add`, `list`, `provenance_path.is_file`, `read_json`.
Technische leespunten: return, foutafhandeling, voorwaardelijke vertakking.

## src/football_pipeline/cli.py

Verbindt commandoregelargumenten met de pipelinehandelingen.

Bron: [src/football_pipeline/cli.py](../src/football_pipeline/cli.py).

### main

Vindplaats: [src/football_pipeline/cli.py regel 16](../src/football_pipeline/cli.py#L16), tot regel 217.
Argumenten: `(argv=None)`. Retourtypehint: `int`.
Lees verder bij aanroepen: `Calibration`, `Path`, `Path(bundle.observations_path).with_name`, `PipelineError`, `SyntheticDetector`, `accept.add_argument`, `accept_mvp`, `argparse.ArgumentParser`, `args.points.read_text`, `asdict`, `attempt_download_asset`, `calibrate.add_argument`, `calibration.validate_for`, `calibration_source.add_argument`, `create_calibration`, `demo.add_argument`, `dependencies`, `evaluate_calibration` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, voorwaardelijke vertakking.

## src/football_pipeline/contracts.py

Definieert gegevensstructuren, JSON-invoer en uitvoer en hashes.

Bron: [src/football_pipeline/contracts.py](../src/football_pipeline/contracts.py).

### PipelineError

Vindplaats: [src/football_pipeline/contracts.py regel 10](../src/football_pipeline/contracts.py#L10), tot regel 11.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: ValueError.

Broncommentaar: An actionable input, model or processing failure.

### sha256_file

Vindplaats: [src/football_pipeline/contracts.py regel 14](../src/football_pipeline/contracts.py#L14), tot regel 19.
Argumenten: `(path: str | Path)`. Retourtypehint: `str`.
Berekent een SHA-256-identiteit van de exacte bestandsbytes.
Lees verder bij aanroepen: `Path`, `Path(path).open`, `digest.hexdigest`, `digest.update`, `hashlib.sha256`, `iter`, `stream.read`.
Technische leespunten: return, with-context, lus.

### digest_json

Vindplaats: [src/football_pipeline/contracts.py regel 22](../src/football_pipeline/contracts.py#L22), tot regel 23.
Argumenten: `(value: Any)`. Retourtypehint: `str`.
Berekent een identiteit van genormaliseerd geserialiseerde gegevens.
Lees verder bij aanroepen: `hashlib.sha256`, `hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest`, `json.dumps`, `json.dumps(value, sort_keys=True, allow_nan=False).encode`.
Technische leespunten: return.

### read_json

Vindplaats: [src/football_pipeline/contracts.py regel 26](../src/football_pipeline/contracts.py#L26), tot regel 33.
Argumenten: `(path: str | Path)`. Retourtypehint: `dict`.
Leest gestructureerde JSON-gegevens.
Lees verder bij aanroepen: `Path`, `Path(path).read_text`, `PipelineError`, `isinstance`, `json.loads`.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, voorwaardelijke vertakking.

### write_json

Vindplaats: [src/football_pipeline/contracts.py regel 36](../src/football_pipeline/contracts.py#L36), tot regel 40.
Argumenten: `(path: str | Path, value: Any)`. Retourtypehint: `None`.
Schrijft JSON-gegevens; de module bepaalt de precieze schrijfwaarborgen.
Lees verder bij aanroepen: `Path`, `json.dumps`, `path.with_suffix`, `temporary.replace`, `temporary.write_text`.

### VideoMetadata

Vindplaats: [src/football_pipeline/contracts.py regel 44](../src/football_pipeline/contracts.py#L44), tot regel 61.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### VideoMetadata.fps

Vindplaats: [src/football_pipeline/contracts.py regel 56](../src/football_pipeline/contracts.py#L56), tot regel 57.
Argumenten: `(self)`. Retourtypehint: `float`.
Technische leespunten: return.

### VideoMetadata.size

Vindplaats: [src/football_pipeline/contracts.py regel 60](../src/football_pipeline/contracts.py#L60), tot regel 61.
Argumenten: `(self)`. Retourtypehint: `tuple[int, int]`.
Technische leespunten: return.

### Detection

Vindplaats: [src/football_pipeline/contracts.py regel 65](../src/football_pipeline/contracts.py#L65), tot regel 88.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### Detection.from_dict

Vindplaats: [src/football_pipeline/contracts.py regel 85](../src/football_pipeline/contracts.py#L85), tot regel 88.
Argumenten: `(cls, value: dict)`. Retourtypehint: `Detection`.
Lees verder bij aanroepen: `cls`, `value.items`.
Technische leespunten: return.

### FrameRecord

Vindplaats: [src/football_pipeline/contracts.py regel 92](../src/football_pipeline/contracts.py#L92), tot regel 110.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### FrameRecord.to_dict

Vindplaats: [src/football_pipeline/contracts.py regel 100](../src/football_pipeline/contracts.py#L100), tot regel 110.
Argumenten: `(self)`. Retourtypehint: `dict`.
Lees verder bij aanroepen: `asdict`, `count_exclusion_reason`, `counted_as_player`, `player_summary`, `result.pop`, `zip`.
Technische leespunten: return, lus, voorwaardelijke vertakking.

### RunResult

Vindplaats: [src/football_pipeline/contracts.py regel 114](../src/football_pipeline/contracts.py#L114), tot regel 121.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### RunResult.video_path

Vindplaats: [src/football_pipeline/contracts.py regel 120](../src/football_pipeline/contracts.py#L120), tot regel 121.
Argumenten: `(self)`. Retourtypehint: `Path`.
Technische leespunten: return.

## src/football_pipeline/demo.py

Maakt synthetische demonstratiegegevens voor softwarecontrole, geen voetbalbenchmark.

Bron: [src/football_pipeline/demo.py](../src/football_pipeline/demo.py).

Broncommentaar: Synthetic fixtures are engineering checks, never evidence of football model quality.

### default_points

Vindplaats: [src/football_pipeline/demo.py regel 16](../src/football_pipeline/demo.py#L16), tot regel 28.
Argumenten: `(width: int, height: int)`. Retourtypehint: `list[dict]`.
Technische leespunten: return.

### SyntheticDetector

Vindplaats: [src/football_pipeline/demo.py regel 31](../src/football_pipeline/demo.py#L31), tot regel 39.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### SyntheticDetector.detect

Vindplaats: [src/football_pipeline/demo.py regel 35](../src/football_pipeline/demo.py#L35), tot regel 39.
Argumenten: `(self, frame, frame_index)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Detection`.
Technische leespunten: return, voorwaardelijke vertakking.

### generate_demo

Vindplaats: [src/football_pipeline/demo.py regel 42](../src/football_pipeline/demo.py#L42), tot regel 98.
Argumenten: `(directory: Path)`. Retourtypehint: `dict`.
Lees verder bij aanroepen: `(directory / 'synthetic.identity').write_text`, `SyntheticDetector`, `VideoWriter`, `asdict`, `create_calibration`, `cv2.line`, `cv2.putText`, `cv2.rectangle`, `default_points`, `detector.detect`, `digest_json`, `directory.mkdir`, `inspect_video`, `map`, `np.full`, `range`, `tuple`, `write_json` en andere aanroepen.
Technische leespunten: return, foutafhandeling, lus, voorwaardelijke vertakking.

## src/football_pipeline/detection.py

Controleert profielen, voert YOLO uit en combineert waar nodig persoonsvoorstellen.

Bron: [src/football_pipeline/detection.py](../src/football_pipeline/detection.py).

### load_model_manifest

Vindplaats: [src/football_pipeline/detection.py regel 11](../src/football_pipeline/detection.py#L11), tot regel 86.
Argumenten: `(path: str | Path)`. Retourtypehint: `dict`.
Leest het profiel en weigert ontbrekende of veranderde gewichten en onjuiste klassemapping.
Lees verder bij aanroepen: `(path.parent / spec['weights']).resolve`, `Path`, `Path(path).resolve`, `PipelineError`, `any`, `expected[k].lower`, `float`, `identifiers.add`, `int`, `isinstance`, `manifest.get`, `mapping.items`, `mapping.values`, `math.isfinite`, `name.strip`, `read_json`, `set`, `sha256_file` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

### available_roles

Vindplaats: [src/football_pipeline/detection.py regel 89](../src/football_pipeline/detection.py#L89), tot regel 92.
Argumenten: `(manifest)`. Retourtypehint: `niet opgegeven`.
Verzamelt welke semantische rollen het gekozen profiel echt kan leveren.
Lees verder bij aanroepen: `manifest.get`, `manifest.get('appearance', {}).get`, `roles.update`, `spec['class_mapping'].values`.
Technische leespunten: return.

### merge_person_proposals

Vindplaats: [src/football_pipeline/detection.py regel 95](../src/football_pipeline/detection.py#L95), tot regel 139.
Argumenten: `(detections, overlap=0.5)`. Retourtypehint: `niet opgegeven`.
Selecteert één waarneming voor bepaalde dubbele persoonsvoorstellen.
Lees verder bij aanroepen: `abs`, `enumerate`, `kept.append`, `max`, `min`, `sorted`.
Technische leespunten: return, lus, voorwaardelijke vertakking.

Broncommentaar: One human observation per overlapping proposal; keep non-human detections intact.

### validate_detection_devices

Vindplaats: [src/football_pipeline/detection.py regel 142](../src/football_pipeline/detection.py#L142), tot regel 161.
Argumenten: `(manifest: dict)`. Retourtypehint: `None`.
Controleert of de gevraagde rekenapparaten bruikbaar zijn.
Lees verder bij aanroepen: `PipelineError`, `any`, `device.replace`, `device.replace(',', '').isdigit`, `device.split`, `device.startswith`, `int`, `manifest.get`, `spec.get`, `str`, `str(spec.get('device', 'cpu')).lower`, `str(spec.get('device', 'cpu')).lower().strip`, `torch.cuda.device_count`, `torch.cuda.is_available`.
Technische leespunten: expliciete foutmelding, lus, voorwaardelijke vertakking.

Broncommentaar: Fail before expensive field inference when a requested CUDA device is unavailable.

### UltralyticsDetector

Vindplaats: [src/football_pipeline/detection.py regel 164](../src/football_pipeline/detection.py#L164), tot regel 250.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### UltralyticsDetector.__init__

Vindplaats: [src/football_pipeline/detection.py regel 165](../src/football_pipeline/detection.py#L165), tot regel 192.
Argumenten: `(self, manifest: dict)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(Path(os.environ['YOLO_CONFIG_DIR']) / 'Ultralytics').mkdir`, `AppearanceClassifier`, `Path`, `Path(__file__).resolve`, `Path(os.environ['MPLCONFIGDIR']).mkdir`, `PipelineError`, `YOLO`, `int`, `manifest.get`, `model.names.get`, `os.environ.setdefault`, `self.models.append`, `spec['expected_names'].items`, `str`, `validate_detection_devices`.
Technische leespunten: expliciete foutmelding, lus, voorwaardelijke vertakking.

### UltralyticsDetector.set_video_identity

Vindplaats: [src/football_pipeline/detection.py regel 194](../src/football_pipeline/detection.py#L194), tot regel 199.
Argumenten: `(self, video_hash)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `VideoTeams`.
Technische leespunten: voorwaardelijke vertakking.

### UltralyticsDetector.detect

Vindplaats: [src/football_pipeline/detection.py regel 201](../src/football_pipeline/detection.py#L201), tot regel 250.
Argumenten: `(self, frame, frame_index: int)`. Retourtypehint: `list[Detection]`.
Lees verder bij aanroepen: `Detection`, `PipelineError`, `box.astype`, `box.astype(float).copy`, `box.tolist`, `detections.append`, `float`, `inputs.extend`, `int`, `len`, `max`, `merge_person_proposals`, `model.predict`, `range`, `result.boxes.cls.cpu`, `result.boxes.cls.cpu().numpy`, `result.boxes.conf.cpu`, `result.boxes.conf.cpu().numpy` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

## src/football_pipeline/evaluation.py

Meet trackinggedrag tegen referenties en houdt de scope van de beoordeling bij.

Bron: [src/football_pipeline/evaluation.py](../src/football_pipeline/evaluation.py).

### iou_matrix

Vindplaats: [src/football_pipeline/evaluation.py regel 13](../src/football_pipeline/evaluation.py#L13), tot regel 21.
Argumenten: `(predicted: list, references: list)`. Retourtypehint: `np.ndarray`.
Lees verder bij aanroepen: `(p[:, 2:] - p[:, :2]).prod`, `(r[:, 2:] - r[:, :2]).prod`, `len`, `np.asarray`, `np.divide`, `np.empty`, `np.maximum`, `np.maximum(0, intersection_max - intersection_min).prod`, `np.minimum`, `np.zeros_like`.
Technische leespunten: return, voorwaardelijke vertakking.

### evaluate_frames

Vindplaats: [src/football_pipeline/evaluation.py regel 24](../src/football_pipeline/evaluation.py#L24), tot regel 122.
Argumenten: `(predictions: list[dict], references: list[dict])`. Retourtypehint: `dict`.
Lees verder bij aanroepen: `(values[2:] <= values[:2]).any`, `(values[:2] < 0).any`, `PipelineError`, `any`, `check_box`, `d.get`, `events.append`, `iou_matrix`, `isinstance`, `known_matched.add`, `len`, `linear_sum_assignment`, `list`, `matched_predictions.add`, `matched_references.add`, `np.asarray`, `np.isfinite`, `np.isfinite(values).all` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

Broncommentaar: Project-specific counts, not standardized MOT/IDF1 metrics.

### evaluate_frames.check_box

Vindplaats: [src/football_pipeline/evaluation.py regel 29](../src/football_pipeline/evaluation.py#L29), tot regel 42.
Argumenten: `(box)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(values[2:] <= values[:2]).any`, `(values[:2] < 0).any`, `PipelineError`, `isinstance`, `np.asarray`, `np.isfinite`, `np.isfinite(values).all`.
Technische leespunten: expliciete foutmelding, foutafhandeling, voorwaardelijke vertakking.

### evaluate_run

Vindplaats: [src/football_pipeline/evaluation.py regel 125](../src/football_pipeline/evaluation.py#L125), tot regel 147.
Argumenten: `(run_directory: Path, reference_path: Path)`. Retourtypehint: `dict`.
Lees verder bij aanroepen: `(run_directory / 'framegegevens.jsonl').open`, `PipelineError`, `evaluate_frames`, `isinstance`, `manifest.get`, `map`, `read_json`, `reference.get`, `report.update`, `str`, `validate_completed`.
Technische leespunten: return, expliciete foutmelding, with-context, voorwaardelijke vertakking.

## src/football_pipeline/field_data.py

Verzamelt en selecteert velddata binnen opslag- en splitsafspraken.

Bron: [src/football_pipeline/field_data.py](../src/football_pipeline/field_data.py).

Broncommentaar: Bounded, resumable field-training corpus; downloaded highlights are never ground truth.

### CorpusBudget

Vindplaats: [src/football_pipeline/field_data.py regel 32](../src/football_pipeline/field_data.py#L32), tot regel 65.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### CorpusBudget.__init__

Vindplaats: [src/football_pipeline/field_data.py regel 33](../src/football_pipeline/field_data.py#L33), tot regel 36.
Argumenten: `(self, root, limit=20 * GIB)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `Path(root).resolve`, `self.root.mkdir`.

### CorpusBudget.used

Vindplaats: [src/football_pipeline/field_data.py regel 38](../src/football_pipeline/field_data.py#L38), tot regel 41.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `p.is_file`, `p.stat`, `self.root.rglob`, `sum`.
Technische leespunten: return, voorwaardelijke vertakking.

### CorpusBudget.start_tracking

Vindplaats: [src/football_pipeline/field_data.py regel 43](../src/football_pipeline/field_data.py#L43), tot regel 45.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `self.used`.

### CorpusBudget.account

Vindplaats: [src/football_pipeline/field_data.py regel 47](../src/football_pipeline/field_data.py#L47), tot regel 49.
Argumenten: `(self, change)`. Retourtypehint: `niet opgegeven`.
Technische leespunten: voorwaardelijke vertakking.

### CorpusBudget.require

Vindplaats: [src/football_pipeline/field_data.py regel 51](../src/football_pipeline/field_data.py#L51), tot regel 55.
Argumenten: `(self, additional)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `ValueError`, `self.used`, `shutil.disk_usage`.
Technische leespunten: expliciete foutmelding, voorwaardelijke vertakking.

### CorpusBudget.write_json

Vindplaats: [src/football_pipeline/field_data.py regel 57](../src/football_pipeline/field_data.py#L57), tot regel 65.
Argumenten: `(self, path, value)`. Retourtypehint: `niet opgegeven`.
Schrijft JSON-gegevens; de module bepaalt de precieze schrijfwaarborgen.
Lees verder bij aanroepen: `Path`, `Path(path).exists`, `Path(path).resolve`, `Path(path).resolve().is_relative_to`, `Path(path).stat`, `ValueError`, `content.replace`, `content.replace('\n', os.linesep).encode`, `json.dumps`, `len`, `self.account`, `self.require`, `write_json`.
Technische leespunten: expliciete foutmelding, voorwaardelijke vertakking.

### download

Vindplaats: [src/football_pipeline/field_data.py regel 68](../src/football_pipeline/field_data.py#L68), tot regel 131.
Argumenten: `(url, destination, budget, expected_size=None, expected_sha256=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `ValueError`, `budget.account`, `budget.require`, `budget.write_json`, `destination.exists`, `destination.parent.mkdir`, `destination.with_suffix`, `info.update`, `int`, `json.loads`, `len`, `max`, `old.get`, `old.update`, `partial.exists`, `partial.open`, `partial.replace` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, with-context, voorwaardelijke vertakking.

Broncommentaar: Resume only the same URL/ETag, verify completed content before skipping it.

### extract_archive

Vindplaats: [src/football_pipeline/field_data.py regel 134](../src/football_pipeline/field_data.py#L134), tot regel 179.
Argumenten: `(archive, output, budget)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(output / m.filename).exists`, `(output / m.filename).stat`, `(output / member.filename).resolve`, `(output / p).is_file`, `Path`, `Path(output).resolve`, `ValueError`, `all`, `budget.account`, `budget.require`, `budget.write_json`, `bundle.infolist`, `bundle.read`, `hashlib.sha256`, `hashlib.sha256(data).hexdigest`, `json.loads`, `len`, `m.is_dir` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

Broncommentaar: Verify ZIP CRCs and reject traversal; retain archives for verified resumption.

### collect_dataset

Vindplaats: [src/football_pipeline/field_data.py regel 182](../src/football_pipeline/field_data.py#L182), tot regel 217.
Argumenten: `(root, budget, splits=('train', 'valid'))`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(root / 'dataset-inventory.json').exists`, `(root / 'dataset-inventory.json').read_text`, `budget.write_json`, `download`, `extract_archive`, `json.load`, `json.loads`, `next`, `print`, `range`, `spec.get`, `spec.get('lfs', {}).get`, `str`, `str(exc).lower`, `urllib.request.urlopen`.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

### match_split

Vindplaats: [src/football_pipeline/field_data.py regel 220](../src/football_pipeline/field_data.py#L220), tot regel 222.
Argumenten: `(match_id)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `hashlib.sha256`, `hashlib.sha256(match_id.encode()).hexdigest`, `int`, `match_id.encode`.
Technische leespunten: return.

### identify_match

Vindplaats: [src/football_pipeline/field_data.py regel 225](../src/football_pipeline/field_data.py#L225), tot regel 232.
Argumenten: `(title)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `re.search`, `re.sub`, `re.sub('[^a-z0-9]+', '-', title).strip`, `title.lower`, `title.lower().replace`, `title.lower().replace('–', '-').replace`.
Technische leespunten: return, voorwaardelijke vertakking.

Broncommentaar: Conservative candidate ID. A title alone never certifies training eligibility.

### discover_highlights

Vindplaats: [src/football_pipeline/field_data.py regel 235](../src/football_pipeline/field_data.py#L235), tot regel 289.
Argumenten: `(root, per_channel=25, budget=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `budget.write_json if budget else write_json`, `client.extract_info`, `destination.exists`, `destination.read_text`, `entry.get`, `identify_match`, `inventory['searches'].append`, `inventory['videos'].append`, `json.loads`, `known.add`, `len`, `list`, `match_split`, `result.get`, `str`, `title.lower`, `yt_dlp.YoutubeDL`.
Technische leespunten: return, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

### collect_highlights

Vindplaats: [src/football_pipeline/field_data.py regel 292](../src/football_pipeline/field_data.py#L292), tot regel 377.
Argumenten: `(root, budget, ffmpeg, count=30)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `CHANNELS.index`, `ValueError`, `[x['id'] for x in inventory['videos'] if x['channel_source'] == v['channel_source']].index`, `budget.require`, `budget.start_tracking`, `budget.used`, `budget.write_json`, `client.extract_info`, `file.exists`, `file.relative_to`, `file.stat`, `inventory.update`, `item.get`, `item.update`, `json.loads`, `matches.add`, `metadata.get`, `path.read_text` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

### collect_highlights.hook

Vindplaats: [src/football_pipeline/field_data.py regel 321](../src/football_pipeline/field_data.py#L321), tot regel 324.
Argumenten: `(progress)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `ValueError`, `progress.get`.
Technische leespunten: expliciete foutmelding, voorwaardelijke vertakking.

### frame_signature

Vindplaats: [src/football_pipeline/field_data.py regel 380](../src/football_pipeline/field_data.py#L380), tot regel 384.
Argumenten: `(image)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(small[:, 1:] > small[:, :-1]).flatten`, `cv2.cvtColor`, `cv2.resize`.
Technische leespunten: return.

### near_duplicate

Vindplaats: [src/football_pipeline/field_data.py regel 387](../src/football_pipeline/field_data.py#L387), tot regel 390.
Argumenten: `(signature, previous, maximum=5)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `any`, `np.count_nonzero`.
Technische leespunten: return.

### sampled_frames

Vindplaats: [src/football_pipeline/field_data.py regel 393](../src/football_pipeline/field_data.py#L393), tot regel 449.
Argumenten: `(video, fps, size, ffmpeg)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `ValueError`, `error_log.read`, `error_log.read().decode`, `error_log.seek`, `int`, `len`, `max`, `np.ceil`, `np.frombuffer`, `np.frombuffer(data, np.uint8).reshape`, `print`, `process.poll`, `process.stdout.close`, `process.stdout.read`, `process.terminate`, `process.wait`, `str`, `subprocess.Popen` en andere aanroepen.
Technische leespunten: return, yield of generator, expliciete foutmelding, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

Broncommentaar: Decode at most five analysis frames/s; selected source frame indices remain exact for CFR video.

### prepare_frames

Vindplaats: [src/football_pipeline/field_data.py regel 452](../src/football_pipeline/field_data.py#L452), tot regel 559.
Argumenten: `(root, budget, maximum_per_video=180, ffmpeg=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(output / f['image']).exists`, `(root / 'highlight-inventory.json').read_text`, `ValueError`, `all`, `budget.account`, `budget.require`, `budget.write_json`, `cap.get`, `cap.release`, `cv2.VideoCapture`, `cv2.calcHist`, `cv2.compareHist`, `cv2.cvtColor`, `cv2.imencode`, `cv2.inRange`, `cv2.inRange(hsv, (25, 40, 30), (95, 255, 255)).mean`, `cv2.normalize`, `cv2.resize` en andere aanroepen.
Technische leespunten: expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

### main

Vindplaats: [src/football_pipeline/field_data.py regel 562](../src/football_pipeline/field_data.py#L562), tot regel 593.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `CorpusBudget`, `FileLock`, `argparse.ArgumentParser`, `args.ffmpeg.is_file`, `args.root.resolve`, `budget.start_tracking`, `budget.used`, `collect_dataset`, `collect_highlights`, `discover_highlights`, `int`, `json.dumps`, `parser.add_argument`, `parser.error`, `parser.parse_args`, `prepare_frames`, `print`, `str`.
Technische leespunten: return, with-context, voorwaardelijke vertakking.

## src/football_pipeline/field_layout.py

Bewaart de namen en genormaliseerde locaties van veldmarkeringen.

Bron: [src/football_pipeline/field_layout.py](../src/football_pipeline/field_layout.py).

Broncommentaar: PnLCalib's semantic IDs on its assumed 105 x 68 template (not measured pitch dimensions).
Geen eigen top-level functies of classes. Dit bestand bevat pakketinitialisatie, constanten of direct uitgevoerde scriptcode.

## src/football_pipeline/field_learning.py

Levert veldtraining, heatmapverlies, voorstellen en vergelijkingen in de aparte runtime.

Bron: [src/football_pipeline/field_learning.py](../src/football_pipeline/field_learning.py).

Broncommentaar: Single-GPU PnLCalib fine-tuning, proposals and measured comparisons.  Run with .tools/field-training-env/Scripts/python.exe; upstream stays unmodified.

### timestamp

Vindplaats: [src/football_pipeline/field_learning.py regel 28](../src/football_pipeline/field_learning.py#L28), tot regel 29.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `datetime.now`, `datetime.now(UTC).isoformat`.
Technische leespunten: return.

### validate_labels

Vindplaats: [src/football_pipeline/field_learning.py regel 32](../src/football_pipeline/field_learning.py#L32), tot regel 49.
Argumenten: `(data)`. Retourtypehint: `niet opgegeven`.
Controleert eindige genormaliseerde veldlabels en toegestane afronding.
Lees verder bij aanroepen: `ValueError`, `all`, `copy.deepcopy`, `isinstance`, `math.isfinite`, `max`, `min`, `normalized.items`, `point.get`, `type`.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

### dataset_index

Vindplaats: [src/football_pipeline/field_learning.py regel 52](../src/football_pipeline/field_learning.py#L52), tot regel 125.
Argumenten: `(root, limits=None, splits=('train', 'valid'))`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(limits or {}).get`, `Path`, `Path(root).resolve`, `ValueError`, `digest_json`, `enumerate`, `excluded.append`, `image.with_suffix`, `info.get`, `info_path.parent.glob`, `int`, `len`, `list`, `match_splits.values`, `normalized.items`, `np.linspace`, `read_json`, `root.rglob` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

Broncommentaar: Explicit index bypasses upstream Windows basename and missing match_info bugs.

### upstream_runtime

Vindplaats: [src/football_pipeline/field_learning.py regel 128](../src/football_pipeline/field_learning.py#L128), tot regel 142.
Argumenten: `(path)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `ValueError`, `read_json`, `runtime['source_sha256'].items`, `sha256_file`, `str`, `subprocess.check_output`, `subprocess.check_output(['git', '-C', str(repository), 'rev-parse', 'HEAD'], text=True).strip`, `sys.path.insert`, `validate_runtime_models`.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

### load_model

Vindplaats: [src/football_pipeline/field_learning.py regel 145](../src/football_pipeline/field_learning.py#L145), tot regel 156.
Argumenten: `(runtime, role, device)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `constructor`, `model.load_state_dict`, `model.to`, `read_yaml`, `torch.load`.
Technische leespunten: return.

### read_yaml

Vindplaats: [src/football_pipeline/field_learning.py regel 159](../src/football_pipeline/field_learning.py#L159), tot regel 162.
Argumenten: `(path)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `Path(path).read_text`, `yaml.safe_load`.
Technische leespunten: return.

### masked_heatmap_loss

Vindplaats: [src/football_pipeline/field_learning.py regel 165](../src/football_pipeline/field_learning.py#L165), tot regel 169.
Argumenten: `(output, target, mask)`. Retourtypehint: `niet opgegeven`.
Berekeningsstap voor heatmapverlies met een supervisiemasker.
Lees verder bij aanroepen: `(error * weight).sum`, `(output.float() - target.float()).square`, `(weight.sum() * output.shape[-1] * output.shape[-2]).clamp_min`, `mask.to`, `output.float`, `target.float`, `weight.sum`.
Technische leespunten: return.

Broncommentaar: Mask per-channel squared errors before reduction, normalized by valid pixels.

### FieldDataset

Vindplaats: [src/football_pipeline/field_learning.py regel 172](../src/football_pipeline/field_learning.py#L172), tot regel 203.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### FieldDataset.__init__

Vindplaats: [src/football_pipeline/field_learning.py regel 173](../src/football_pipeline/field_learning.py#L173), tot regel 174.
Argumenten: `(self, rows, role, augment=False)`. Retourtypehint: `niet opgegeven`.

### FieldDataset.__len__

Vindplaats: [src/football_pipeline/field_learning.py regel 176](../src/football_pipeline/field_learning.py#L176), tot regel 177.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `len`.
Technische leespunten: return.

### FieldDataset.__getitem__

Vindplaats: [src/football_pipeline/field_learning.py regel 179](../src/football_pipeline/field_learning.py#L179), tot regel 203.
Argumenten: `(self, index)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Image.open`, `KeypointsDB`, `KeypointsDB(data, image).get_tensor_w_mask`, `LineKeypointsDB`, `LineKeypointsDB(data, image).get_tensor`, `RandomHorizontalFlip`, `RandomHorizontalFlip(0.5)`, `copy.deepcopy`, `data.pop`, `random.uniform`, `read_json`, `source.convert`, `source.convert('RGB').resize`, `tf.adjust_brightness`, `tf.to_tensor`, `torch.from_numpy`, `torch.from_numpy(mask).float`, `torch.from_numpy(target).float` en andere aanroepen.
Technische leespunten: return, with-context, voorwaardelijke vertakking.

### atomic_torch_save

Vindplaats: [src/football_pipeline/field_learning.py regel 206](../src/football_pipeline/field_learning.py#L206), tot regel 211.
Argumenten: `(value, path)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `path.with_suffix`, `temporary.replace`, `torch.save`.

### publish_epoch_checkpoint

Vindplaats: [src/football_pipeline/field_learning.py regel 214](../src/football_pipeline/field_learning.py#L214), tot regel 226.
Argumenten: `(report_path, report, role, record, state, checkpoint)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `atomic_torch_save`, `checkpoint.resolve`, `copy.deepcopy`, `sha256_file`, `str`, `timestamp`, `write_json`.
Technische leespunten: return.

Broncommentaar: Publish a fresh checkpoint, then its pointer; a crash preserves the previous committed epoch.

### run_epoch

Vindplaats: [src/football_pipeline/field_learning.py regel 229](../src/football_pipeline/field_learning.py#L229), tot regel 272.
Argumenten: `(model, loader, device, optimizer=None, scaler=None, max_steps=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `ValueError`, `enumerate`, `float`, `image.to`, `json.dumps`, `loss.detach`, `mask.to`, `masked_heatmap_loss`, `model`, `model.parameters`, `model.train`, `optimizer.zero_grad`, `print`, `scaler.scale`, `scaler.scale(loss).backward`, `scaler.step`, `scaler.unscale_`, `scaler.update` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

### _train

Vindplaats: [src/football_pipeline/field_learning.py regel 275](../src/football_pipeline/field_learning.py#L275), tot regel 475.
Argumenten: `(args)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(args.output / f'{role}-best-{epoch + 1:03d}.pt').resolve`, `DataLoader`, `FieldDataset`, `Path`, `Path(saved.get('path', args.output / (role + '-best.pt'))).resolve`, `ValueError`, `all`, `any`, `args.output.mkdir`, `args.output.resolve`, `atomic_torch_save`, `best_path.resolve`, `checkpoint.resolve`, `dataset_index`, `digest_json`, `float`, `history.append`, `importlib.metadata.version` en andere aanroepen.
Technische leespunten: expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

### train

Vindplaats: [src/football_pipeline/field_learning.py regel 478](../src/football_pipeline/field_learning.py#L478), tot regel 483.
Argumenten: `(args)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `FileLock`, `_train`, `args.output.mkdir`, `str`.
Technische leespunten: with-context.

### make_runtime

Vindplaats: [src/football_pipeline/field_learning.py regel 486](../src/football_pipeline/field_learning.py#L486), tot regel 510.
Argumenten: `(base_path, output)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(output / 'training-report.json').resolve`, `ValueError`, `read_json`, `sha256_file`, `str`, `validate_runtime_models`, `write_json`.
Technische leespunten: expliciete foutmelding, lus, voorwaardelijke vertakking.

### image_observation

Vindplaats: [src/football_pipeline/field_learning.py regel 513](../src/football_pipeline/field_learning.py#L513), tot regel 562.
Argumenten: `(models, image, device, *, amp=False)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `coords_to_dict`, `cv2.cvtColor`, `float`, `get_keypoints_from_heatmap_batch_maxpool`, `get_keypoints_from_heatmap_batch_maxpool_l`, `kp.items`, `ln.items`, `max`, `min`, `models[0]`, `models[1]`, `tensor[None].to`, `tf.resize`, `tf.to_tensor`, `torch.autocast`, `torch.inference_mode`.
Technische leespunten: return, with-context.

### _propose

Vindplaats: [src/football_pipeline/field_learning.py regel 565](../src/football_pipeline/field_learning.py#L565), tot regel 606.
Argumenten: `(args)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(args.root / 'frames').glob`, `CorpusBudget`, `Path`, `ValueError`, `budget.require`, `budget.start_tracking`, `budget.write_json`, `cv2.imread`, `digest_json`, `image_observation`, `json.dumps`, `json.dumps(result).encode`, `len`, `load_model`, `load_model(runtime, r, 'cuda:0').eval`, `output.mkdir`, `print`, `read_json` en andere aanroepen.
Technische leespunten: expliciete foutmelding, lus, voorwaardelijke vertakking.

### propose

Vindplaats: [src/football_pipeline/field_learning.py regel 609](../src/football_pipeline/field_learning.py#L609), tot regel 613.
Argumenten: `(args)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `FileLock`, `_propose`, `str`.
Technische leespunten: with-context.

### reprojection_metrics

Vindplaats: [src/football_pipeline/field_learning.py regel 616](../src/football_pipeline/field_learning.py#L616), tot regel 649.
Argumenten: `(observation, labels, settings)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `SoccerPitch`, `abs`, `bool`, `errors.append`, `estimate_checked`, `float`, `labels.items`, `len`, `max`, `np.array`, `np.asarray`, `np.hypot`, `np.linalg.inv`, `np.linalg.norm`, `transform`.
Technische leespunten: return, foutafhandeling, lus, voorwaardelijke vertakking.

### _compare

Vindplaats: [src/football_pipeline/field_learning.py regel 652](../src/football_pipeline/field_learning.py#L652), tot regel 772.
Argumenten: `(args)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `'\n'.join`, `(args.output / 'report.md').write_text`, `CameraCalibration`, `Path`, `Path(bundle.observations_path).open`, `ValueError`, `any`, `args.output.mkdir`, `cap.read`, `cap.release`, `cv2.VideoCapture`, `cv2.imread`, `dataset_index`, `estimate_checked`, `estimator.update`, `float`, `image_observation`, `inspect_video` en andere aanroepen.
Technische leespunten: expliciete foutmelding, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

### compare

Vindplaats: [src/football_pipeline/field_learning.py regel 775](../src/football_pipeline/field_learning.py#L775), tot regel 780.
Argumenten: `(args)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `FileLock`, `_compare`, `args.output.mkdir`, `str`.
Technische leespunten: with-context.

### main

Vindplaats: [src/football_pipeline/field_learning.py regel 783](../src/football_pipeline/field_learning.py#L783), tot regel 813.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `any`, `argparse.ArgumentParser`, `args.output.mkdir`, `compare`, `dataset_index`, `json.dumps`, `len`, `parser.add_argument`, `parser.error`, `parser.parse_args`, `print`, `propose`, `train`, `write_json`.
Technische leespunten: voorwaardelijke vertakking.

## src/football_pipeline/field_model_spec.py

Legt de toegelaten externe bron en gewichten vast en controleert hun identiteit.

Bron: [src/football_pipeline/field_model_spec.py](../src/football_pipeline/field_model_spec.py).

Broncommentaar: Pinned model provenance; dependency-free so the setup can bootstrap a clean machine.

### validate_runtime_models

Vindplaats: [src/football_pipeline/field_model_spec.py regel 17](../src/football_pipeline/field_model_spec.py#L17), tot regel 61.
Argumenten: `(runtime)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `Path(model['path']).resolve`, `Path(path).open`, `Path(runtime[key]).resolve`, `RELEASE_WEIGHTS.items`, `ValueError`, `checksum`, `hashlib.file_digest`, `hashlib.file_digest(stream, 'sha256').hexdigest`, `json.loads`, `model.get`, `re.fullmatch`, `report.get`, `report.get('models', {}).get`, `report_path.read_text`, `runtime.get`, `saved.get`, `set` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, with-context, lus, voorwaardelijke vertakking.

Broncommentaar: Accept pinned releases or traceable local fine-tunes, always verifying actual bytes.

### validate_runtime_models.checksum

Vindplaats: [src/football_pipeline/field_model_spec.py regel 24](../src/football_pipeline/field_model_spec.py#L24), tot regel 26.
Argumenten: `(path)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `Path(path).open`, `hashlib.file_digest`, `hashlib.file_digest(stream, 'sha256').hexdigest`.
Technische leespunten: return, with-context.

## src/football_pipeline/field_motion.py

Controleert veldgeometrie en volgt tijdelijk een schatting met gemeten camerabeweging.

Bron: [src/football_pipeline/field_motion.py](../src/football_pipeline/field_motion.py).

Broncommentaar: Checked planar keypoints and bounded, measured camera-motion propagation.  Model hold-outs are a self-consistency check, never human accuracy evidence. The field network, player detector and manual/static-camera workflow stay separate.

### validate_settings

Vindplaats: [src/football_pipeline/field_motion.py regel 37](../src/football_pipeline/field_motion.py#L37), tot regel 59.
Argumenten: `(settings)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `DEFAULT_SETTINGS.items`, `PipelineError`, `dict`, `np.isfinite`, `set`, `type`.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

### _spread

Vindplaats: [src/football_pipeline/field_motion.py regel 62](../src/football_pipeline/field_motion.py#L62), tot regel 63.
Argumenten: `(xy, size, minimum)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `cv2.contourArea`, `cv2.convexHull`, `np.asarray`, `np.prod`.
Technische leespunten: return.

### checked_matrix

Vindplaats: [src/football_pipeline/field_motion.py regel 66](../src/football_pipeline/field_motion.py#L66), tot regel 77.
Argumenten: `(inverse, xy, uv)`. Retourtypehint: `niet opgegeven`.
Weigert ongeldige, onstabiele of verkeerd georiënteerde matrices.
Lees verder bij aanroepen: `ValueError`, `np.column_stack`, `np.isfinite`, `np.isfinite(inverse).all`, `np.linalg.cond`, `np.linalg.det`, `np.linalg.inv`, `np.linalg.norm`, `np.mean`, `transform`.
Technische leespunten: return, expliciete foutmelding, voorwaardelijke vertakking.

Broncommentaar: Return image -> field only for finite, oriented, nondegenerate visible support.

### line_checks

Vindplaats: [src/football_pipeline/field_motion.py regel 80](../src/football_pipeline/field_motion.py#L80), tot regel 92.
Argumenten: `(lines, inverse)`. Retourtypehint: `niet opgegeven`.
Vergelijkt de schatting met beschikbare lijnwaarnemingen.
Lees verder bij aanroepen: `(np.abs(vector[0] * delta[:, 1] - vector[1] * delta[:, 0]) / length).tolist`, `errors.extend`, `identifiers.append`, `np.abs`, `np.asarray`, `np.linalg.norm`, `transform`.
Technische leespunten: return, lus, voorwaardelijke vertakking.

### estimate_checked

Vindplaats: [src/football_pipeline/field_motion.py regel 95](../src/football_pipeline/field_motion.py#L95), tot regel 210.
Argumenten: `(observation, image_size, settings=None)`. Retourtypehint: `niet opgegeven`.
Schat automatische veldgeometrie met aparte kwaliteitscontroles.
Lees verder bij aanroepen: `(xy < 0).any`, `(xy[:, 0] >= width).any`, `(xy[:, 1] >= height).any`, `ValueError`, `_spread`, `abs`, `checked_matrix`, `cv2.findHomography`, `cv2.setRNGSeed`, `errors.tolist`, `float`, `inliers.mean`, `inliers.sum`, `int`, `len`, `line_checks`, `mask.ravel`, `mask.ravel().astype` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

### CameraCalibration

Vindplaats: [src/football_pipeline/field_motion.py regel 213](../src/football_pipeline/field_motion.py#L213), tot regel 391.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

Broncommentaar: One sequential stream; reference age is never refreshed by a propagated result.

### CameraCalibration.__init__

Vindplaats: [src/football_pipeline/field_motion.py regel 216](../src/football_pipeline/field_motion.py#L216), tot regel 223.
Argumenten: `(self, fps, settings=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `validate_settings`.

### CameraCalibration.update

Vindplaats: [src/football_pipeline/field_motion.py regel 225](../src/football_pipeline/field_motion.py#L225), tot regel 391.
Argumenten: `(self, frame, direct, index)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(b >= 0).all`, `(uv <= 1).all`, `(uv >= 0).all`, `ValueError`, `_spread`, `backward.ravel`, `backward.ravel().astype`, `checked_matrix`, `cv2.absdiff`, `cv2.calcHist`, `cv2.calcOpticalFlowPyrLK`, `cv2.compareHist`, `cv2.cvtColor`, `cv2.findHomography`, `cv2.goodFeaturesToTrack`, `cv2.inRange`, `cv2.morphologyEx`, `cv2.normalize` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, with-context, voorwaardelijke vertakking.

### status_label

Vindplaats: [src/football_pipeline/field_motion.py regel 394](../src/football_pipeline/field_motion.py#L394), tot regel 397.
Argumenten: `(state)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `state.get`.
Technische leespunten: return, voorwaardelijke vertakking.

## src/football_pipeline/field_review.py

Bewaart echte reviewgegevens en onderzoekt uitvalperiodes.

Bron: [src/football_pipeline/field_review.py](../src/football_pipeline/field_review.py).

Broncommentaar: Separate human reference documents. These are never read by calibration inference.

### failure_intervals

Vindplaats: [src/football_pipeline/field_review.py regel 14](../src/football_pipeline/field_review.py#L14), tot regel 25.
Argumenten: `(records)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `enumerate`, `intervals.append`, `len`, `row.get`, `row.get('calibration', {}).get`.
Technische leespunten: return, lus, voorwaardelijke vertakking.

### save_review

Vindplaats: [src/football_pipeline/field_review.py regel 28](../src/football_pipeline/field_review.py#L28), tot regel 86.
Argumenten: `(path, template, *, index, points, calibratable, reviewer, confirmed=False)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(values < 0).any`, `(values >= template['image_size']).any`, `Path`, `Path(path).is_file`, `Path(path).parent.mkdir`, `PipelineError`, `cleaned.append`, `datetime.now`, `datetime.now(UTC).isoformat`, `document.get`, `document.update`, `float`, `len`, `np.array`, `np.isfinite`, `np.isfinite(values).all`, `p.get`, `read_json` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

Broncommentaar: Only an explicit user save can add a human assessment; incomplete sets stay unapproved.

### finalize_review

Vindplaats: [src/football_pipeline/field_review.py regel 89](../src/football_pipeline/field_review.py#L89), tot regel 99.
Argumenten: `(path, *, confirmed=False)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `PipelineError`, `all`, `datetime.now`, `datetime.now(UTC).isoformat`, `document.update`, `f.get`, `read_json`, `sorted`, `write_json`.
Technische leespunten: return, expliciete foutmelding, voorwaardelijke vertakking.

## src/football_pipeline/field_review_ui.py

Toont bronframes en overlays voor handmatige veldbeoordeling.

Bron: [src/football_pipeline/field_review_ui.py](../src/football_pipeline/field_review_ui.py).

Broncommentaar: Frame-synchronous visual inspection shared by fresh processing and saved runs.

### review_records

Vindplaats: [src/football_pipeline/field_review_ui.py regel 25](../src/football_pipeline/field_review_ui.py#L25), tot regel 31.
Argumenten: `(directory, manifest_mtime, records_mtime)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(Path(directory) / 'framegegevens.jsonl').read_text`, `(Path(directory) / 'framegegevens.jsonl').read_text(encoding='utf-8').splitlines`, `Path`, `json.loads`, `st.cache_data`, `validate_completed`.
Technische leespunten: return.

### source_frame

Vindplaats: [src/football_pipeline/field_review_ui.py regel 35](../src/football_pipeline/field_review_ui.py#L35), tot regel 39.
Argumenten: `(path, video_hash, index)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `PipelineError`, `inspect_video`, `read_frame`, `st.cache_data`.
Technische leespunten: return, expliciete foutmelding, voorwaardelijke vertakking.

### visual_review

Vindplaats: [src/football_pipeline/field_review_ui.py regel 42](../src/football_pipeline/field_review_ui.py#L42), tot regel 277.
Argumenten: `(directory)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(directory / 'framegegevens.jsonl').stat`, `(directory / 'runmanifest.json').stat`, `(existing or {}).get`, `Detection.from_dict`, `FrameRecord`, `LINES_UV.values`, `POINTS_UV.items`, `Path`, `any`, `apply_point_click`, `cv2.circle`, `cv2.cvtColor`, `cv2.line`, `cv2.putText`, `datetime.now`, `datetime.now(UTC).isoformat`, `enumerate`, `evaluate_calibration` en andere aanroepen.
Technische leespunten: return, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

### visual_review.clicked

Vindplaats: [src/football_pipeline/field_review_ui.py regel 198](../src/football_pipeline/field_review_ui.py#L198), tot regel 209.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `apply_point_click`, `str`.
Technische leespunten: foutafhandeling.

## src/football_pipeline/geometry.py

Berekent en controleert handmatige homography en projecteert voetpunten.

Bron: [src/football_pipeline/geometry.py](../src/football_pipeline/geometry.py).

### CalibrationControlError

Vindplaats: [src/football_pipeline/geometry.py regel 13](../src/football_pipeline/geometry.py#L13), tot regel 32.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: PipelineError.

Broncommentaar: Rejected calibration with independent checks available for visual diagnosis.

### CalibrationControlError.__init__

Vindplaats: [src/football_pipeline/geometry.py regel 16](../src/football_pipeline/geometry.py#L16), tot regel 32.
Argumenten: `(self, checks, projected, errors, diagonal)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `errors.round`, `errors.round(2).tolist`, `float`, `max`, `np.median`, `super`, `super().__init__`, `xy.tolist`, `zip`.

### point_coordinate_issues

Vindplaats: [src/football_pipeline/geometry.py regel 35](../src/football_pipeline/geometry.py#L35), tot regel 50.
Argumenten: `(points: list[dict])`. Retourtypehint: `list[str]`.
Geeft aan welke puntvelden ontbreken of ongeldige getallen bevatten.
Lees verder bij aanroepen: `', '.join`, `enumerate`, `float`, `invalid.append`, `isinstance`, `issues.append`, `np.isfinite`, `point.get`.
Technische leespunten: return, foutafhandeling, lus, voorwaardelijke vertakking.

Broncommentaar: Name missing/non-finite cells without silently replacing them with zero.

### Calibration

Vindplaats: [src/football_pipeline/geometry.py regel 54](../src/football_pipeline/geometry.py#L54), tot regel 106.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### Calibration.identity

Vindplaats: [src/football_pipeline/geometry.py regel 66](../src/football_pipeline/geometry.py#L66), tot regel 67.
Argumenten: `(self)`. Retourtypehint: `str`.
Lees verder bij aanroepen: `asdict`, `digest_json`.
Technische leespunten: return.

### Calibration.polygon

Vindplaats: [src/football_pipeline/geometry.py regel 70](../src/football_pipeline/geometry.py#L70), tot regel 71.
Argumenten: `(self)`. Retourtypehint: `np.ndarray`.
Lees verder bij aanroepen: `np.array`.
Technische leespunten: return.

### Calibration.validate_for

Vindplaats: [src/football_pipeline/geometry.py regel 73](../src/football_pipeline/geometry.py#L73), tot regel 106.
Argumenten: `(self, video: VideoMetadata, approved: bool=True)`. Retourtypehint: `None`.
Lees verder bij aanroepen: `PipelineError`, `create_calibration`, `isinstance`, `len`, `np.allclose`, `np.shape`, `self.review.get`, `str`, `str(self.review.get('reviewer', '')).strip`, `str(self.review.get('source', '')).strip`, `str(self.review.get('usage', '')).strip`, `tuple`.
Technische leespunten: expliciete foutmelding, voorwaardelijke vertakking.

### create_calibration

Vindplaats: [src/football_pipeline/geometry.py regel 109](../src/football_pipeline/geometry.py#L109), tot regel 172.
Argumenten: `(video: VideoMetadata, points: list[dict], reference_frame: int=0)`. Retourtypehint: `Calibration`.
Past een homography op de fitpunten en meet afwijkingen op controlepunten.
Lees verder bij aanroepen: `'; '.join`, `(all_uv < 0).any`, `(all_uv > 1).any`, `(all_xy < 0).any`, `(all_xy[:, 0] >= video.width).any`, `(all_xy[:, 1] >= video.height).any`, `Calibration`, `CalibrationControlError`, `PipelineError`, `check_uv.reshape`, `cv2.contourArea`, `cv2.findHomography`, `cv2.isContourConvex`, `cv2.perspectiveTransform`, `cv2.perspectiveTransform(check_uv.reshape(-1, 1, 2), inverse).reshape`, `errors.tolist`, `isinstance`, `len` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, voorwaardelijke vertakking.

### valid_box

Vindplaats: [src/football_pipeline/geometry.py regel 175](../src/football_pipeline/geometry.py#L175), tot regel 181.
Argumenten: `(detection: Detection, image_size: tuple[int, int])`. Retourtypehint: `bool`.
Controleert boxgeometrie, beeldgrenzen en geldige confidencewaarden.
Lees verder bij aanroepen: `bool`, `np.asarray`, `np.isfinite`, `np.isfinite(box).all`.
Technische leespunten: return, voorwaardelijke vertakking.

### project_detection

Vindplaats: [src/football_pipeline/geometry.py regel 184](../src/football_pipeline/geometry.py#L184), tot regel 207.
Argumenten: `(detection: Detection, calibration: Calibration)`. Retourtypehint: `None`.
Projecteert het onderste midden van de box of bewaart waarom dat niet mag.
Lees verder bij aanroepen: `(uv < -1e-09).any`, `(uv > 1 + 1e-09).any`, `abs`, `cv2.pointPolygonTest`, `np.asarray`, `np.isfinite`, `np.isfinite(transformed).all`, `np.isfinite(uv).all`, `tuple`, `uv.tolist`, `valid_box`.
Technische leespunten: return, voorwaardelijke vertakking.

## src/football_pipeline/model_handoff.py

Registreert modelgewichten met klassen, instellingen en evaluatieverwijzing.

Bron: [src/football_pipeline/model_handoff.py](../src/football_pipeline/model_handoff.py).

Broncommentaar: Register an explicitly mapped player model without changing baseline semantics.

### available_model_profiles

Vindplaats: [src/football_pipeline/model_handoff.py regel 11](../src/football_pipeline/model_handoff.py#L11), tot regel 24.
Argumenten: `(default: Path, directory: Path)`. Retourtypehint: `dict[Path, str]`.
Zoekt modelprofielen voor de interface, met de standaard als eerste.
Lees verder bij aanroepen: `default.resolve`, `dict.fromkeys`, `directory.glob`, `manifest.get`, `p.resolve`, `read_json`, `sorted`, `str`.
Technische leespunten: return, foutafhandeling, lus, voorwaardelijke vertakking.

### register_player_model

Vindplaats: [src/football_pipeline/model_handoff.py regel 27](../src/football_pipeline/model_handoff.py#L27), tot regel 100.
Argumenten: `(weights: Path, mapping_path: Path, output: Path, *, model_id='players_v1', imgsz=1920, confidence=0.1, iou=0.7, device='cpu', evaluation_record: Path | None=None)`. Retourtypehint: `dict`.
Maakt een traceerbaar profiel voor echte spelersgewichten.
Lees verder bij aanroepen: `Path`, `Path(os.path.relpath(evaluation_record, output.parent)).as_posix`, `Path(os.path.relpath(weights, output.parent)).as_posix`, `PipelineError`, `YOLO`, `evaluation_record.is_file`, `evaluation_record.resolve`, `load_model_manifest`, `mapping.values`, `model.names.items`, `os.path.relpath`, `output.exists`, `output.open`, `output.parent.mkdir`, `output.resolve`, `read_json`, `set`, `set(mapping).issubset` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, with-context, voorwaardelijke vertakking.

## src/football_pipeline/participants.py

Houdt rol, veldligging, zichtbaarheid en spelertelling gescheiden.

Bron: [src/football_pipeline/participants.py](../src/football_pipeline/participants.py).

Broncommentaar: Keep model roles separate from geometric field membership.  Being on grass never turns a generic person, steward or official into a player. These rules filter predictions; they cannot repair an incorrect model class.

### player_exclusion_reason

Vindplaats: [src/football_pipeline/participants.py regel 29](../src/football_pipeline/participants.py#L29), tot regel 32.
Argumenten: `(detection: Detection, image_size: tuple[int, int])`. Retourtypehint: `str | None`.
Wijst een waarneming af als de rol of veldpositie geen geldige player is.
Lees verder bij aanroepen: `field_exclusion_reason`.
Technische leespunten: return, voorwaardelijke vertakking.

### field_exclusion_reason

Vindplaats: [src/football_pipeline/participants.py regel 35](../src/football_pipeline/participants.py#L35), tot regel 45.
Argumenten: `(detection: Detection, image_size: tuple[int, int])`. Retourtypehint: `str | None`.
Controleert box en huidige veldpositie onafhankelijk van de rol.
Lees verder bij aanroepen: `(position < -1e-09).any`, `(position > 1 + 1e-09).any`, `np.asarray`, `np.isfinite`, `np.isfinite(position).all`, `valid_box`.
Technische leespunten: return, voorwaardelijke vertakking.

### visible_detection

Vindplaats: [src/football_pipeline/participants.py regel 48](../src/football_pipeline/participants.py#L48), tot regel 49.
Argumenten: `(detection: Detection, confidence: float=DISPLAY_CONFIDENCE)`. Retourtypehint: `bool`.
Laat de weergavedrempel of een actuele gekoppelde track gelden.
Technische leespunten: return.

### field_available

Vindplaats: [src/football_pipeline/participants.py regel 52](../src/football_pipeline/participants.py#L52), tot regel 54.
Argumenten: `(record: FrameRecord)`. Retourtypehint: `bool`.
Bepaalt of voor dit frame bruikbare veldgeometrie beschikbaar is.
Lees verder bij aanroepen: `record.calibration.get`.
Technische leespunten: return.

### count_exclusion_reason

Vindplaats: [src/football_pipeline/participants.py regel 57](../src/football_pipeline/participants.py#L57), tot regel 69.
Argumenten: `(record: FrameRecord, detection: Detection, confidence=DISPLAY_CONFIDENCE)`. Retourtypehint: `str | None`.
Geeft de concrete reden waarom een detectie niet meetelt.
Lees verder bij aanroepen: `field_available`, `player_exclusion_reason`, `visible_detection`.
Technische leespunten: return, voorwaardelijke vertakking.

### counted_as_player

Vindplaats: [src/football_pipeline/participants.py regel 72](../src/football_pipeline/participants.py#L72), tot regel 73.
Argumenten: `(record: FrameRecord, detection: Detection, confidence=DISPLAY_CONFIDENCE)`. Retourtypehint: `bool`.
Levert waar op als er geen uitsluitreden voor de spelertelling is.
Lees verder bij aanroepen: `count_exclusion_reason`.
Technische leespunten: return.

### player_summary

Vindplaats: [src/football_pipeline/participants.py regel 76](../src/football_pipeline/participants.py#L76), tot regel 112.
Argumenten: `(record: FrameRecord, confidence=DISPLAY_CONFIDENCE)`. Retourtypehint: `dict`.
Verzamelt zichtbare spelers, geldige veldtellingen, andere rollen en teamtotalen.
Lees verder bij aanroepen: `Counter`, `counted_as_player`, `dict`, `field_available`, `field_exclusion_reason`, `len`, `player_exclusion_reason`, `reasons.items`, `sum`, `valid_box`, `visible_detection`.
Technische leespunten: return.

## src/football_pipeline/pipeline.py

Orkestreert invoercontrole, verwerking per frame, uitvoer en acceptatie.

Bron: [src/football_pipeline/pipeline.py](../src/football_pipeline/pipeline.py).

### code_identity

Vindplaats: [src/football_pipeline/pipeline.py regel 30](../src/football_pipeline/pipeline.py#L30), tot regel 40.
Argumenten: `()`. Retourtypehint: `dict`.
Maakt hashes van de eigen pipelinecode en leest waar mogelijk de commit.
Lees verder bij aanroepen: `(ROOT / 'src' / 'football_pipeline').glob`, `digest_json`, `p.is_file`, `p.relative_to`, `sha256_file`, `sorted`, `str`, `subprocess.check_output`, `subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip`.
Technische leespunten: return, foutafhandeling.

### dependencies

Vindplaats: [src/football_pipeline/pipeline.py regel 43](../src/football_pipeline/pipeline.py#L43), tot regel 45.
Argumenten: `()`. Retourtypehint: `dict`.
Bewaart de werkelijk geïnstalleerde versies van relevante pakketten.
Lees verder bij aanroepen: `importlib.metadata.version`.
Technische leespunten: return.

### processing_lock

Vindplaats: [src/football_pipeline/pipeline.py regel 49](../src/football_pipeline/pipeline.py#L49), tot regel 85.
Argumenten: `(root: Path)`. Retourtypehint: `niet opgegeven`.
Voorkomt conflicterende verwerking in dezelfde uitvoerlocatie.
Lees verder bij aanroepen: `(root / '.processing.lock').open`, `PipelineError`, `fcntl.flock`, `lock.close`, `lock.fileno`, `lock.flush`, `lock.seek`, `lock.tell`, `lock.write`, `msvcrt.locking`, `root.mkdir`.
Technische leespunten: yield of generator, expliciete foutmelding, foutafhandeling, voorwaardelijke vertakking.

### validate_completed

Vindplaats: [src/football_pipeline/pipeline.py regel 88](../src/football_pipeline/pipeline.py#L88), tot regel 104.
Argumenten: `(directory: Path)`. Retourtypehint: `dict`.
Controleert dat de opgeslagen run als voltooid en bruikbaar geldt.
Lees verder bij aanroepen: `Path`, `Path(name).is_absolute`, `PipelineError`, `artifacts.items`, `manifest.get`, `path.is_file`, `read_json`, `required.add`, `required.issubset`, `sha256_file`.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

### accept_mvp

Vindplaats: [src/football_pipeline/pipeline.py regel 107](../src/football_pipeline/pipeline.py#L107), tot regel 130.
Argumenten: `(directory: Path, reviewer: str, confirmed: bool)`. Retourtypehint: `Path`.
Registreert de expliciete review van een daarvoor geschikte echte MVP-run.
Lees verder bij aanroepen: `PipelineError`, `datetime.now`, `datetime.now(UTC).isoformat`, `directory.resolve`, `manifest.get`, `reviewer.strip`, `str`, `validate_completed`, `write_json`.
Technische leespunten: return, expliciete foutmelding, voorwaardelijke vertakking.

### check_mvp_acceptance

Vindplaats: [src/football_pipeline/pipeline.py regel 133](../src/football_pipeline/pipeline.py#L133), tot regel 160.
Argumenten: `(path: Path | None, video_hash: str, calibration: Calibration | AutomaticCalibration, model_manifest: dict, code: dict, versions: dict)`. Retourtypehint: `dict`.
Controleert dat een bestaand reviewrecord bij de huidige trackingvoorwaarden hoort.
Lees verder bij aanroepen: `Path`, `PipelineError`, `acceptance.get`, `manifest.get`, `read_json`, `str`, `str(acceptance.get('reviewer', '')).strip`, `validate_completed`.
Technische leespunten: return, expliciete foutmelding, voorwaardelijke vertakking.

### process_video

Vindplaats: [src/football_pipeline/pipeline.py regel 163](../src/football_pipeline/pipeline.py#L163), tot regel 491.
Argumenten: `(video_path: str | Path, calibration: Calibration | AutomaticCalibration | None, model_manifest_path: str | Path, output_root: str | Path, *, tracker_config_path: str | Path | None=None, mvp_acceptance_path: str | Path | None=None, progress: Callable | None=None, field_progress: Callable | None=None, detector=None, replay_run: str | Path | None=None, technical_pilot: bool=False, field_runtime_path: str | Path | None=None, field_source: str='', field_usage: str='', field_settings: dict | None=None, recalibrate_replay: bool=False)`. Retourtypehint: `RunResult`.
Voert de complete verwerking van bronvideo tot gecontroleerde uitvoer uit.
Lees verder bij aanroepen: `(Path(replay_run) / 'framegegevens.jsonl').open`, `(directory / 'controlebeelden').mkdir`, `(directory / 'framegegevens.jsonl').open`, `(directory / 'video.partial.mp4').replace`, `(replay_manifest or {}).get`, `(replay_manifest or {}).get('artifacts', {}).get`, `AutomaticCalibration`, `ByteTrackAdapter`, `CameraCalibration`, `Counter`, `FrameRecord`, `Path`, `Path(output_root).resolve`, `PipelineError`, `RunResult`, `Trajectories`, `UltralyticsDetector`, `VideoWriter` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, with-context, lus, voorwaardelijke vertakking.

Broncommentaar: Process sequentially; injected detectors are explicitly marked as non-model evidence.

## src/football_pipeline/point_picker.py

Zet klikken in de kalibratiecomponent om naar de juiste puntgegevens.

Bron: [src/football_pipeline/point_picker.py](../src/football_pipeline/point_picker.py).

Broncommentaar: Responsive image point selection using Streamlit's inline component API.

### apply_point_click

Vindplaats: [src/football_pipeline/point_picker.py regel 14](../src/football_pipeline/point_picker.py#L14), tot regel 29.
Argumenten: `(points, event, *, context, selected, width, height)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `PipelineError`, `any`, `deepcopy`, `event.get`, `isinstance`, `len`, `math.isfinite`, `round`, `type`, `updated[index].update`.
Technische leespunten: return, expliciete foutmelding, voorwaardelijke vertakking.

Broncommentaar: Validate a browser event before changing original-image coordinates.

### _register_picker

Vindplaats: [src/football_pipeline/point_picker.py regel 129](../src/football_pipeline/point_picker.py#L129), tot regel 147.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `st.components.v2.component`.
Technische leespunten: return.

### point_picker

Vindplaats: [src/football_pipeline/point_picker.py regel 150](../src/football_pipeline/point_picker.py#L150), tot regel 167.
Argumenten: `(frame, points, selected, *, context, key, on_clicked_change, diagnostics=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `PipelineError`, `_register_picker`, `_register_picker()`, `base64.b64encode`, `base64.b64encode(encoded).decode`, `cv2.imencode`, `point_label`.
Technische leespunten: return, expliciete foutmelding, voorwaardelijke vertakking.

## src/football_pipeline/render.py

Tekent detecties, kalibratieoverlays, minimap en optionele waargenomen trajecten.

Bron: [src/football_pipeline/render.py](../src/football_pipeline/render.py).

### detection_color

Vindplaats: [src/football_pipeline/render.py regel 37](../src/football_pipeline/render.py#L37), tot regel 40.
Argumenten: `(detection)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `COLORS.get`, `TEAM_COLORS.get`.
Technische leespunten: return, voorwaardelijke vertakking.

### label

Vindplaats: [src/football_pipeline/render.py regel 43](../src/football_pipeline/render.py#L43), tot regel 44.
Argumenten: `(image, text, point, color=(235, 240, 235), scale=0.6)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `cv2.putText`.

### field_pixel

Vindplaats: [src/football_pipeline/render.py regel 47](../src/football_pipeline/render.py#L47), tot regel 48.
Argumenten: `(position)`. Retourtypehint: `niet opgegeven`.
Zet genormaliseerde veldcoördinaten om naar minimappixels.
Lees verder bij aanroepen: `round`.
Technische leespunten: return.

### render_frame

Vindplaats: [src/football_pipeline/render.py regel 51](../src/football_pipeline/render.py#L51), tot regel 185.
Argumenten: `(frame: np.ndarray, record: FrameRecord, histories: Trajectories | None=None, display_confidence: float=DISPLAY_CONFIDENCE, technical_pilot: bool=False, recognized_points: bool=True, tracked_points: bool=True)`. Retourtypehint: `np.ndarray`.
Tekent één gecombineerd bronbeeld en minimapbeeld.
Lees verder bij aanroepen: `LABELS.get`, `any`, `automatic_preview`, `cv2.circle`, `cv2.line`, `cv2.rectangle`, `cv2.resize`, `detection_color`, `enumerate`, `field_pixel`, `histories.segments`, `label`, `legend.append`, `legend.extend`, `len`, `max`, `min`, `np.full` en andere aanroepen.
Technische leespunten: return, lus, voorwaardelijke vertakking.

### automatic_preview

Vindplaats: [src/football_pipeline/render.py regel 188](../src/football_pipeline/render.py#L188), tot regel 217.
Argumenten: `(frame: np.ndarray, state: dict, *, recognized_points=True, tracked_points=True)`. Retourtypehint: `np.ndarray`.
Lees verder bij aanroepen: `LINES_UV.values`, `cv2.circle`, `cv2.clipLine`, `cv2.line`, `frame.copy`, `label`, `map`, `max`, `np.abs`, `np.abs(projected).max`, `np.asarray`, `np.isfinite`, `np.isfinite(projected).all`, `np.linalg.inv`, `round`, `state.get`, `status_label`, `str` en andere aanroepen.
Technische leespunten: return, foutafhandeling, lus, voorwaardelijke vertakking.

Broncommentaar: Draw only visible portions; virtual offscreen corners are never fabricated observations.

### calibration_preview

Vindplaats: [src/football_pipeline/render.py regel 220](../src/football_pipeline/render.py#L220), tot regel 239.
Argumenten: `(frame: np.ndarray, points: list[dict], grid: bool=True)`. Retourtypehint: `np.ndarray`.
Lees verder bij aanroepen: `cv2.circle`, `cv2.line`, `frame.copy`, `int`, `label`, `max`, `range`, `round`, `str`.
Technische leespunten: return, foutafhandeling, lus, voorwaardelijke vertakking.

## src/football_pipeline/replay.py

Leest opgeslagen detecties opnieuw met controle op frame en video.

Bron: [src/football_pipeline/replay.py](../src/football_pipeline/replay.py).

### replay_detections

Vindplaats: [src/football_pipeline/replay.py regel 8](../src/football_pipeline/replay.py#L8), tot regel 24.
Argumenten: `(stream, frame_index: int, video: VideoMetadata)`. Retourtypehint: `list[Detection]`.
Leest opgeslagen detecties met controle op bronframe en video.
Lees verder bij aanroepen: `Detection.from_dict`, `PipelineError`, `abs`, `json.loads`, `list`, `stream.readline`.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

## src/football_pipeline/teams.py

Maakt shirtkleurfeatures en verzamelt twee videolokale kleurclusters.

Bron: [src/football_pipeline/teams.py](../src/football_pipeline/teams.py).

Broncommentaar: Per-video kit-colour clustering; new videos never inherit another match's team identities.

### kit_feature

Vindplaats: [src/football_pipeline/teams.py regel 9](../src/football_pipeline/teams.py#L9), tot regel 32.
Argumenten: `(frame, box)`. Retourtypehint: `niet opgegeven`.
Berekent kleurkenmerken voor de afzonderlijke clustering met verzadigingsweging.
Lees verder bij aanroepen: `(~green).any`, `cv2.cvtColor`, `cv2.cvtColor(cv2.resize(crop, (16, 24)), cv2.COLOR_BGR2HSV).reshape`, `cv2.cvtColor(cv2.resize(crop, (16, 24)), cv2.COLOR_BGR2HSV).reshape(-1, 3).astype`, `cv2.resize`, `green.mean`, `int`, `len`, `max`, `np.concatenate`, `np.concatenate([hue, sat, 0.6 * value]).astype`, `np.histogram`.
Technische leespunten: return, voorwaardelijke vertakking.

Broncommentaar: Saturation-weighted torso histograms; grey hue cannot dominate a kit.  A predominantly green torso is retained; mixed green background is filtered. Numbers/stripes remain a distribution instead of becoming a median shirt colour. This is separate from the trained role classifier's input format.

### VideoTeams

Vindplaats: [src/football_pipeline/teams.py regel 35](../src/football_pipeline/teams.py#L35), tot regel 124.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### VideoTeams.__init__

Vindplaats: [src/football_pipeline/teams.py regel 36](../src/football_pipeline/teams.py#L36), tot regel 40.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.

### VideoTeams.update

Vindplaats: [src/football_pipeline/teams.py regel 42](../src/football_pipeline/teams.py#L42), tot regel 109.
Argumenten: `(self, frame, detections)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(labels == i).any`, `any`, `distances.argmin`, `float`, `int`, `kit_feature`, `len`, `max`, `min`, `np.allclose`, `np.arange`, `np.asarray`, `np.bincount`, `np.linalg.norm`, `np.linalg.norm(centers - self.centers, axis=1).sum`, `np.linalg.norm(centers[::-1] - self.centers, axis=1).sum`, `np.linalg.norm(values - centers[labels], axis=1).sum`, `np.quantile` en andere aanroepen.
Technische leespunten: return, lus, voorwaardelijke vertakking.

### VideoTeams.info

Vindplaats: [src/football_pipeline/teams.py regel 112](../src/football_pipeline/teams.py#L112), tot regel 124.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `len`, `self.centers.tolist`.
Technische leespunten: return.

## src/football_pipeline/tracking.py

Verbindt ByteTrack met onze detectie-indexen en beheert waargenomen trajecten.

Bron: [src/football_pipeline/tracking.py](../src/football_pipeline/tracking.py).

### load_tracker_config

Vindplaats: [src/football_pipeline/tracking.py regel 15](../src/football_pipeline/tracking.py#L15), tot regel 31.
Argumenten: `(path: str | Path)`. Retourtypehint: `dict`.
Lees verder bij aanroepen: `Path`, `Path(path).read_text`, `PipelineError`, `isinstance`, `np.isfinite`, `yaml.safe_load`.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

### ByteTrackAdapter

Vindplaats: [src/football_pipeline/tracking.py regel 34](../src/football_pipeline/tracking.py#L34), tot regel 89.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### ByteTrackAdapter.__init__

Vindplaats: [src/football_pipeline/tracking.py regel 35](../src/football_pipeline/tracking.py#L35), tot regel 66.
Argumenten: `(self, config: dict, fps: float)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `PipelineError`, `SimpleNamespace`, `getattr`, `int`, `len`, `super`, `super().init_track`, `tracker_class`, `version`, `zip`.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

### ByteTrackAdapter.__init__.SourceIndexedTracker

Vindplaats: [src/football_pipeline/tracking.py regel 38](../src/football_pipeline/tracking.py#L38), tot regel 48.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: BYTETracker.

### ByteTrackAdapter.__init__.SourceIndexedTracker.init_track

Vindplaats: [src/football_pipeline/tracking.py regel 39](../src/football_pipeline/tracking.py#L39), tot regel 48.
Argumenten: `(self, results, features=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `PipelineError`, `int`, `len`, `super`, `super().init_track`, `zip`.
Technische leespunten: return, expliciete foutmelding, lus, voorwaardelijke vertakking.

### ByteTrackAdapter.update

Vindplaats: [src/football_pipeline/tracking.py regel 68](../src/football_pipeline/tracking.py#L68), tot regel 89.
Argumenten: `(self, detections: list[Detection], frame_index: int, image_size: tuple[int, int])`. Retourtypehint: `None`.
Lees verder bij aanroepen: `Boxes`, `PipelineError`, `_IndexedBoxes`, `int`, `len`, `np.array`, `np.array([[*d.bbox_xyxy, d.confidence, 0] for d in players], dtype=np.float32).reshape`, `player_exclusion_reason`, `seen.add`, `self.tracker.update`, `set`.
Technische leespunten: expliciete foutmelding, lus, voorwaardelijke vertakking.

### _IndexedBoxes

Vindplaats: [src/football_pipeline/tracking.py regel 92](../src/football_pipeline/tracking.py#L92), tot regel 106.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

Broncommentaar: Carry source indices when ByteTrack slices high/low confidence subsets.

### _IndexedBoxes.__init__

Vindplaats: [src/football_pipeline/tracking.py regel 95](../src/football_pipeline/tracking.py#L95), tot regel 97.
Argumenten: `(self, boxes, indices=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `len`, `np.arange`.

### _IndexedBoxes.__len__

Vindplaats: [src/football_pipeline/tracking.py regel 99](../src/football_pipeline/tracking.py#L99), tot regel 100.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `len`.
Technische leespunten: return.

### _IndexedBoxes.__getitem__

Vindplaats: [src/football_pipeline/tracking.py regel 102](../src/football_pipeline/tracking.py#L102), tot regel 103.
Argumenten: `(self, item)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `_IndexedBoxes`.
Technische leespunten: return.

### _IndexedBoxes.__getattr__

Vindplaats: [src/football_pipeline/tracking.py regel 105](../src/football_pipeline/tracking.py#L105), tot regel 106.
Argumenten: `(self, name)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `getattr`.
Technische leespunten: return.

### Trajectories

Vindplaats: [src/football_pipeline/tracking.py regel 109](../src/football_pipeline/tracking.py#L109), tot regel 129.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### Trajectories.__init__

Vindplaats: [src/football_pipeline/tracking.py regel 110](../src/football_pipeline/tracking.py#L110), tot regel 112.
Argumenten: `(self, fps: float, seconds: float=5.0)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `max`, `round`.

### Trajectories.update

Vindplaats: [src/football_pipeline/tracking.py regel 114](../src/football_pipeline/tracking.py#L114), tot regel 125.
Argumenten: `(self, detections: list[Detection], frame_index: int)`. Retourtypehint: `None`.
Lees verder bij aanroepen: `deque`, `list`, `self.points.setdefault`, `self.points.setdefault(detection.track_id, deque()).append`, `self.points[key].popleft`.
Technische leespunten: lus, voorwaardelijke vertakking.

### Trajectories.segments

Vindplaats: [src/football_pipeline/tracking.py regel 127](../src/football_pipeline/tracking.py#L127), tot regel 129.
Argumenten: `(self, track_id: int)`. Retourtypehint: `list[tuple]`.
Lees verder bij aanroepen: `list`, `self.points.get`, `zip`.
Technische leespunten: return.

## src/football_pipeline/video.py

Controleert of voorbereidt video, tijdstempels en framegegevens; de map bepaalt welke route.

Bron: [src/football_pipeline/video.py](../src/football_pipeline/video.py).

### find_tool

Vindplaats: [src/football_pipeline/video.py regel 19](../src/football_pipeline/video.py#L19), tot regel 29.
Argumenten: `(name: str)`. Retourtypehint: `str`.
Lees verder bij aanroepen: `(ROOT / '.tools').glob`, `Path`, `Path(explicit).is_file`, `PipelineError`, `name.upper`, `os.environ.get`, `shutil.which`, `sorted`, `str`.
Technische leespunten: return, expliciete foutmelding, voorwaardelijke vertakking.

### probe_json

Vindplaats: [src/football_pipeline/video.py regel 32](../src/football_pipeline/video.py#L32), tot regel 48.
Argumenten: `(path: Path, *, frames: bool=False)`. Retourtypehint: `dict`.
Lees verder bij aanroepen: `PipelineError`, `find_tool`, `json.loads`, `result.stderr.strip`, `str`, `subprocess.run`.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, voorwaardelijke vertakking.

### inspect_video

Vindplaats: [src/football_pipeline/video.py regel 51](../src/football_pipeline/video.py#L51), tot regel 97.
Argumenten: `(path: str | Path)`. Retourtypehint: `VideoMetadata`.
Lees verder bij aanroepen: `Fraction`, `Path`, `Path(path).resolve`, `PipelineError`, `VideoMetadata`, `abs`, `float`, `int`, `len`, `max`, `path.is_file`, `path.suffix.lower`, `payload.get`, `probe_json`, `sha256_file`, `str`, `stream.get`, `stream.get('tags', {}).get` en andere aanroepen.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, lus, voorwaardelijke vertakking.

### read_frame

Vindplaats: [src/football_pipeline/video.py regel 100](../src/football_pipeline/video.py#L100), tot regel 111.
Argumenten: `(video: VideoMetadata, frame_index: int)`. Retourtypehint: `np.ndarray`.
Lees verder bij aanroepen: `PipelineError`, `cap.read`, `cap.release`, `cap.set`, `cv2.VideoCapture`.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, voorwaardelijke vertakking.

### tool_versions

Vindplaats: [src/football_pipeline/video.py regel 114](../src/football_pipeline/video.py#L114), tot regel 118.
Argumenten: `()`. Retourtypehint: `dict`.
Lees verder bij aanroepen: `find_tool`, `subprocess.check_output`, `subprocess.check_output([find_tool(name), '-version'], text=True).splitlines`.
Technische leespunten: return.

### VideoWriter

Vindplaats: [src/football_pipeline/video.py regel 121](../src/football_pipeline/video.py#L121), tot regel 198.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

Broncommentaar: Stream BGR frames to FFmpeg; stderr goes to disk to avoid pipe deadlocks.

### VideoWriter.__init__

Vindplaats: [src/football_pipeline/video.py regel 124](../src/football_pipeline/video.py#L124), tot regel 163.
Argumenten: `(self, path: Path, width: int, height: int, fps_num: int, fps_den: int)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `PipelineError`, `find_tool`, `self.error_log.close`, `str`, `subprocess.Popen`, `tempfile.TemporaryFile`.
Technische leespunten: expliciete foutmelding, foutafhandeling.

### VideoWriter.write

Vindplaats: [src/football_pipeline/video.py regel 165](../src/football_pipeline/video.py#L165), tot regel 174.
Argumenten: `(self, frame: np.ndarray)`. Retourtypehint: `None`.
Lees verder bij aanroepen: `PipelineError`, `np.ascontiguousarray`, `np.ascontiguousarray(frame).tobytes`, `self.process.stdin.write`.
Technische leespunten: expliciete foutmelding, foutafhandeling, voorwaardelijke vertakking.

### VideoWriter.close

Vindplaats: [src/football_pipeline/video.py regel 176](../src/football_pipeline/video.py#L176), tot regel 198.
Argumenten: `(self, abort: bool=False)`. Retourtypehint: `None`.
Lees verder bij aanroepen: `PipelineError`, `self.error_log.close`, `self.error_log.read`, `self.error_log.read().decode`, `self.error_log.seek`, `self.path.is_file`, `self.path.stat`, `self.process.kill`, `self.process.stdin.close`, `self.process.wait`.
Technische leespunten: return, expliciete foutmelding, foutafhandeling, voorwaardelijke vertakking.

## streamlit_app.py

Bedient upload, modelkeuze, veldpunten, review, verwerking en videoweergave.

Bron: [streamlit_app.py](../streamlit_app.py).

Broncommentaar: Run with: python -m streamlit run streamlit_app.py

### cached_video_metadata

Vindplaats: [streamlit_app.py regel 75](../streamlit_app.py#L75), tot regel 77.
Argumenten: `(path: str, file_hash: str)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `inspect_video`, `st.cache_data`.
Technische leespunten: return.

### cached_frame

Vindplaats: [streamlit_app.py regel 81](../streamlit_app.py#L81), tot regel 82.
Argumenten: `(video, index)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `read_frame`, `st.cache_data`.
Technische leespunten: return.

### save_clicked_point

Vindplaats: [streamlit_app.py regel 292](../streamlit_app.py#L292), tot regel 331.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `apply_point_click`, `digest_json`, `enumerate`, `point.get`, `st.session_state.pop`, `str`.
Technische leespunten: return, foutafhandeling, lus, voorwaardelijke vertakking.

### show_progress

Vindplaats: [streamlit_app.py regel 583](../streamlit_app.py#L583), tot regel 587.
Argumenten: `(count, total, elapsed)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `progress_bar.progress`.

### show_field_progress

Vindplaats: [streamlit_app.py regel 589](../streamlit_app.py#L589), tot regel 592.
Argumenten: `(count, total, elapsed)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `progress_bar.progress`.

## tests/conftest.py

Ondersteunende module of pakketstart. Lees de definities hieronder voor de precieze scope.

Bron: [tests/conftest.py](../tests/conftest.py).

### video_metadata

Vindplaats: [tests/conftest.py regel 9](../tests/conftest.py#L9), tot regel 10.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `VideoMetadata`.
Technische leespunten: return.

### calibration

Vindplaats: [tests/conftest.py regel 14](../tests/conftest.py#L14), tot regel 27.
Argumenten: `(video_metadata)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `create_calibration`, `default_points`.
Technische leespunten: return, lus.

### demo_fixture

Vindplaats: [tests/conftest.py regel 31](../tests/conftest.py#L31), tot regel 32.
Argumenten: `(tmp_path_factory)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `generate_demo`, `pytest.fixture`, `tmp_path_factory.mktemp`.
Technische leespunten: return.

### model_manifest

Vindplaats: [tests/conftest.py regel 36](../tests/conftest.py#L36), tot regel 58.
Argumenten: `(tmp_path)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `str`, `weights.write_bytes`, `write_json`.
Technische leespunten: return.

## tests/test_app.py

Testmodule voor app

Bron: [tests/test_app.py](../tests/test_app.py).

### test_app_initial_screen_and_rerun

Vindplaats: [tests/test_app.py regel 10](../tests/test_app.py#L10), tot regel 16.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval app initial screen and rerun. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `AppTest.from_file`, `AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=20).run`, `app.run`, `str`.

### test_preloaded_calibration_processes_once_on_explicit_click

Vindplaats: [tests/test_app.py regel 19](../tests/test_app.py#L19), tot regel 74.
Argumenten: `(demo_fixture, tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval preloaded calibration processes once on explicit click. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `AppTest.from_file`, `AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=30).run`, `Mock`, `SimpleNamespace`, `SyntheticDetector`, `alternate.resolve`, `app.button`, `app.button(key='process').click`, `app.button(key='process').click().run`, `app.checkbox`, `app.checkbox(key='tracking').check`, `app.checkbox(key='tracking').check().run`, `app.run`, `app.selectbox`, `app.selectbox(key='model_profile').select_index`, `app.selectbox(key='model_profile').select_index(1).run`, `asdict`, `demo_fixture['models'].resolve` en andere aanroepen.
Technische leespunten: return.

### test_preloaded_calibration_processes_once_on_explicit_click.upload

Vindplaats: [tests/test_app.py regel 52](../tests/test_app.py#L52), tot regel 53.
Argumenten: `(label, **kwargs)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `{'video_upload': video_upload, 'calibration_upload': calibration_upload}.get`.
Technische leespunten: return.

### test_point_table_calculation_review_and_invalidation

Vindplaats: [tests/test_app.py regel 77](../tests/test_app.py#L77), tot regel 109.
Argumenten: `(demo_fixture, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval point table calculation review and invalidation. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `AppTest.from_file`, `AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=20).run`, `Mock`, `SimpleNamespace`, `app.button`, `app.button(key='calculate').click`, `app.button(key='calculate').click().run`, `app.checkbox`, `app.checkbox(key='confirm_static_camera').check`, `app.run`, `app.text_input[0].set_value`, `app.text_input[1].set_value`, `app.text_input[2].set_value`, `deepcopy`, `demo_fixture['video'].read_bytes`, `monkeypatch.setattr`, `monkeypatch.setenv`, `next` en andere aanroepen.

### test_image_click_workflow_advances_persists_and_invalidates_draft

Vindplaats: [tests/test_app.py regel 112](../tests/test_app.py#L112), tot regel 159.
Argumenten: `(demo_fixture, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval image click workflow advances persists and invalidates draft. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `AppTest.from_file`, `AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=20).run`, `SimpleNamespace`, `app.button`, `app.button(key='browser_click').click`, `app.button(key='browser_click').click().run`, `app.button(key='calculate').click`, `app.button(key='calculate').click().run`, `app.run`, `app.selectbox[0].select_index`, `app.selectbox[0].select_index(0).run`, `demo_fixture['video'].read_bytes`, `inspect_video`, `monkeypatch.setattr`, `on_clicked_change`, `range`, `st.button`, `str`.
Technische leespunten: lus.

### test_image_click_workflow_advances_persists_and_invalidates_draft.simulate_browser

Vindplaats: [tests/test_app.py regel 121](../tests/test_app.py#L121), tot regel 133.
Argumenten: `(frame, points, selected, *, context, key, on_clicked_change, diagnostics=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `SimpleNamespace`, `on_clicked_change`, `st.button`.

### test_image_click_workflow_advances_persists_and_invalidates_draft.simulate_browser.click

Vindplaats: [tests/test_app.py regel 122](../tests/test_app.py#L122), tot regel 131.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `SimpleNamespace`, `on_clicked_change`.

### test_failed_calibration_shows_named_errors_and_persists_until_correction

Vindplaats: [tests/test_app.py regel 162](../tests/test_app.py#L162), tot regel 188.
Argumenten: `(demo_fixture, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval failed calibration shows named errors and persists until correction. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `AppTest.from_file`, `AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=20).run`, `SimpleNamespace`, `app.button`, `app.button(key='calculate').click`, `app.button(key='calculate').click().run`, `app.run`, `deepcopy`, `demo_fixture['video'].read_bytes`, `monkeypatch.setattr`, `pd.DataFrame`, `str`.

## tests/test_app_player_runtime.py

Testmodule voor app player runtime

Bron: [tests/test_app_player_runtime.py](../tests/test_app_player_runtime.py).

### test_player_app_checks_runtime_and_preserves_automatic_tracking_limit

Vindplaats: [tests/test_app_player_runtime.py regel 11](../tests/test_app_player_runtime.py#L11), tot regel 46.
Argumenten: `(demo_fixture, model_manifest, tmp_path, monkeypatch, cuda_available, role)`. Retourtypehint: `niet opgegeven`.
Controleert het geval player app checks runtime and preserves automatic tracking limit. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `AppTest.from_file`, `AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=30).run`, `any`, `app.button`, `app.checkbox`, `app.file_uploader`, `app.file_uploader(key='video_upload').set_value`, `app.file_uploader(key='video_upload').set_value(('synthetic-runtime-check.mp4', demo_fixture['video'].read_bytes(), 'video/mp4')).run`, `app.get`, `app.get('button_group')[0].set_value`, `app.get('button_group')[0].set_value('Automatische veldkalibratie').run`, `app.text_input`, `app.text_input(key='field_source').set_value`, `app.text_input(key='field_usage').set_value`, `app.text_input(key='field_usage').set_value('Synthetic software test').run`, `demo_fixture['video'].read_bytes`, `monkeypatch.setattr`, `monkeypatch.setenv` en andere aanroepen.
Technische leespunten: voorwaardelijke vertakking.

## tests/test_appearance.py

Testmodule voor appearance

Bron: [tests/test_appearance.py](../tests/test_appearance.py).

### fixed_classifier

Vindplaats: [tests/test_appearance.py regel 17](../tests/test_appearance.py#L17), tot regel 50.
Argumenten: `(tmp_path, role)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `ROLE_NAMES.index`, `backbone`, `encoder.state_dict`, `len`, `role_head.bias.zero_`, `role_head.state_dict`, `role_head.weight.zero_`, `sha256_file`, `str`, `team_head.bias.copy_`, `team_head.state_dict`, `team_head.weight.zero_`, `torch.nn.Linear`, `torch.no_grad`, `torch.ones`, `torch.save`, `torch.tensor`, `torch.zeros`.
Technische leespunten: return, with-context, voorwaardelijke vertakking.

### person

Vindplaats: [tests/test_appearance.py regel 53](../tests/test_appearance.py#L53), tot regel 54.
Argumenten: `(role='player', box=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Detection`.
Technische leespunten: return.

### test_trained_role_can_override_player_without_using_field_location

Vindplaats: [tests/test_appearance.py regel 57](../tests/test_appearance.py#L57), tot regel 68.
Argumenten: `(tmp_path, calibration)`. Retourtypehint: `niet opgegeven`.
Controleert het geval trained role can override player without using field location. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `AppearanceClassifier`, `FrameRecord`, `ROLE_NAMES.index`, `fixed_classifier`, `model.classify`, `np.zeros`, `person`, `player_summary`, `project_detection`.

### test_uncertain_role_abstains_and_new_video_does_not_inherit_supervised_team

Vindplaats: [tests/test_appearance.py regel 71](../tests/test_appearance.py#L71), tot regel 83.
Argumenten: `(tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval uncertain role abstains and new video does not inherit supervised team. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `AppearanceClassifier`, `fixed_classifier`, `model.classify`, `np.zeros`, `person`, `uncertain.classify`.

### test_person_proposals_are_merged_without_losing_ball_or_source_identity

Vindplaats: [tests/test_appearance.py regel 86](../tests/test_appearance.py#L86), tot regel 96.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval person proposals are merged without losing ball or source identity. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `merge_person_proposals`, `person`.

### test_contained_upper_body_uses_strong_full_body_proposal_and_real_feet

Vindplaats: [tests/test_appearance.py regel 99](../tests/test_appearance.py#L99), tot regel 113.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval contained upper body uses strong full body proposal and real feet. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `merge_person_proposals`, `person`.

### test_containment_does_not_merge_distinct_overlapping_people

Vindplaats: [tests/test_appearance.py regel 116](../tests/test_appearance.py#L116), tot regel 128.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval containment does not merge distinct overlapping people. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `len`, `merge_person_proposals`, `person`.

### test_kit_features_suppress_grey_hue_noise_and_keep_green_clothing

Vindplaats: [tests/test_appearance.py regel 131](../tests/test_appearance.py#L131), tot regel 139.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval kit features suppress grey hue noise and keep green clothing. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `green[:16].sum`, `grey[:16].any`, `kit_feature`, `np.full`.

### test_refining_video_clusters_keeps_team_names_stable

Vindplaats: [tests/test_appearance.py regel 142](../tests/test_appearance.py#L142), tot regel 160.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval refining video clusters keeps team names stable. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `VideoTeams`, `len`, `list`, `model.update`, `np.zeros`, `person`, `players.append`, `range`, `reversed`.
Technische leespunten: lus.

### test_manifest_pins_appearance_weights_and_capabilities

Vindplaats: [tests/test_appearance.py regel 163](../tests/test_appearance.py#L163), tot regel 173.
Argumenten: `(model_manifest, tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval manifest pins appearance weights and capabilities. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `available_roles`, `fixed_classifier`, `load_model_manifest`, `pytest.raises`, `write_json`.
Technische leespunten: with-context.

### test_new_video_colour_clusters_wait_for_two_kits_and_keep_other_roles_out

Vindplaats: [tests/test_appearance.py regel 176](../tests/test_appearance.py#L176), tot regel 201.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval new video colour clusters wait for two kits and keep other roles out. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `VideoTeams`, `all`, `any`, `len`, `model.update`, `np.zeros`, `one_kit.update`, `person`, `players.append`, `range`.
Technische leespunten: lus.

### test_team_counts_and_replay_preserve_appearance_but_recompute_geometry

Vindplaats: [tests/test_appearance.py regel 204](../tests/test_appearance.py#L204), tot regel 217.
Argumenten: `(calibration, video_metadata)`. Retourtypehint: `niet opgegeven`.
Controleert het geval team counts and replay preserve appearance but recompute geometry. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `FrameRecord`, `all`, `io.StringIO`, `json.dumps`, `person`, `project_detection`, `record.to_dict`, `replay_detections`, `zip`.
Technische leespunten: lus.

### test_tiled_proposals_restore_source_coordinates_and_reject_cut_person_boxes

Vindplaats: [tests/test_appearance.py regel 220](../tests/test_appearance.py#L220), tot regel 264.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval tiled proposals restore source coordinates and reject cut person boxes. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `Proposals`, `SimpleNamespace`, `detector.detect`, `len`, `np.zeros`, `object.__new__`, `torch.tensor`, `torch.tensor(boxes, dtype=torch.float32).reshape`.
Technische leespunten: return.

### test_tiled_proposals_restore_source_coordinates_and_reject_cut_person_boxes.Proposals

Vindplaats: [tests/test_appearance.py regel 225](../tests/test_appearance.py#L225), tot regel 242.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### test_tiled_proposals_restore_source_coordinates_and_reject_cut_person_boxes.Proposals.predict

Vindplaats: [tests/test_appearance.py regel 228](../tests/test_appearance.py#L228), tot regel 242.
Argumenten: `(self, pixels, **kwargs)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `SimpleNamespace`, `len`, `torch.tensor`, `torch.tensor(boxes, dtype=torch.float32).reshape`.
Technische leespunten: return.

### test_changing_video_identity_resets_only_video_local_team_calibration

Vindplaats: [tests/test_appearance.py regel 267](../tests/test_appearance.py#L267), tot regel 282.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval changing video identity resets only video local team calibration. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `SimpleNamespace`, `VideoTeams`, `detector.set_video_identity`, `np.zeros`, `object.__new__`.

### test_role_dataset_builder_never_overwrites_recorded_human_review

Vindplaats: [tests/test_appearance.py regel 285](../tests/test_appearance.py#L285), tot regel 294.
Argumenten: `(tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval role dataset builder never overwrites recorded human review. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `monkeypatch.setattr`, `path.read_text`, `path.write_text`, `pytest.raises`, `role_training.build`.
Technische leespunten: with-context.

## tests/test_automatic_calibration.py

Testmodule voor automatic calibration

Bron: [tests/test_automatic_calibration.py](../tests/test_automatic_calibration.py).

### observation

Vindplaats: [tests/test_automatic_calibration.py regel 29](../tests/test_automatic_calibration.py#L29), tot regel 49.
Argumenten: `(index=0, inverse=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(transform(LINES_UV[i], inverse) < [640, 360]).all`, `(transform(LINES_UV[i], inverse) >= 0).all`, `float`, `np.asarray`, `transform`, `transform(LINES_UV[i], inverse).tolist`, `zip`.
Technische leespunten: return.

### bundle_for

Vindplaats: [tests/test_automatic_calibration.py regel 52](../tests/test_automatic_calibration.py#L52), tot regel 78.
Argumenten: `(video, directory, rows=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `''.join`, `AutomaticCalibration`, `directory.mkdir`, `json.dumps`, `list`, `observation`, `path.write_text`, `range`, `sha256_file`, `str`, `write_json`.
Technische leespunten: return.

### test_pan_zoom_and_missing_corners_use_current_frame_transform

Vindplaats: [tests/test_automatic_calibration.py regel 81](../tests/test_automatic_calibration.py#L81), tot regel 94.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval pan zoom and missing corners use current frame transform. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `Detection`, `estimate_frame`, `np.array`, `observation`, `project_automatic`, `pytest.approx`, `transform`.
Technische leespunten: lus.

### test_unreliable_frames_have_no_matrix

Vindplaats: [tests/test_automatic_calibration.py regel 109](../tests/test_automatic_calibration.py#L109), tot regel 128.
Argumenten: `(condition, expected)`. Retourtypehint: `niet opgegeven`.
Controleert het geval unreliable frames have no matrix. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `estimate_frame`, `float`, `observation`, `pytest.mark.parametrize`, `row['points'].append`.
Technische leespunten: lus, voorwaardelijke vertakking.

### test_above_ground_points_never_enter_fit

Vindplaats: [tests/test_automatic_calibration.py regel 131](../tests/test_automatic_calibration.py#L131), tot regel 134.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval above ground points never enter fit. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `estimate_frame`, `observation`, `row['points'].extend`.

### test_automatic_projection_rejects_truncated_outside_and_invalid_boxes

Vindplaats: [tests/test_automatic_calibration.py regel 145](../tests/test_automatic_calibration.py#L145), tot regel 150.
Argumenten: `(box, expected)`. Retourtypehint: `niet opgegeven`.
Controleert het geval automatic projection rejects truncated outside and invalid boxes. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `Detection`, `estimate_frame`, `float`, `observation`, `project_automatic`, `pytest.mark.parametrize`.

### test_full_pipeline_loss_recovery_artifacts_cache_and_frame_identity

Vindplaats: [tests/test_automatic_calibration.py regel 153](../tests/test_automatic_calibration.py#L153), tot regel 191.
Argumenten: `(demo_fixture, tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval full pipeline loss recovery artifacts cache and frame identity. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(result.directory / 'framegegevens.jsonl').read_text`, `(result.directory / 'framegegevens.jsonl').read_text().splitlines`, `SyntheticDetector`, `bundle_for`, `inspect_video`, `json.loads`, `load_automatic_calibration`, `observation`, `portable.validate_for`, `process_video`, `pytest.raises`, `range`, `validate_completed`.
Technische leespunten: with-context, lus.

### test_bundle_rejects_different_video_and_corrupt_observations

Vindplaats: [tests/test_automatic_calibration.py regel 194](../tests/test_automatic_calibration.py#L194), tot regel 204.
Argumenten: `(demo_fixture, tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval bundle rejects different video and corrupt observations. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `Path`, `Path(bundle.observations_path).write_text`, `bundle.validate_for`, `bundle_for`, `deepcopy`, `inspect_video`, `other.validate_for`, `pytest.raises`.
Technische leespunten: with-context.

### test_timeline_errors_fail_even_if_bundle_hash_is_updated

Vindplaats: [tests/test_automatic_calibration.py regel 208](../tests/test_automatic_calibration.py#L208), tot regel 222.
Argumenten: `(demo_fixture, tmp_path, condition)`. Retourtypehint: `niet opgegeven`.
Controleert het geval timeline errors fail even if bundle hash is updated. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `bundle.frames`, `bundle.validate_for`, `bundle_for`, `inspect_video`, `list`, `observation`, `pytest.mark.parametrize`, `pytest.raises`, `range`, `rows.append`, `rows.pop`.
Technische leespunten: with-context, voorwaardelijke vertakking.

### test_automatic_replay_requires_same_calibration_and_recomputes_positions

Vindplaats: [tests/test_automatic_calibration.py regel 225](../tests/test_automatic_calibration.py#L225), tot regel 250.
Argumenten: `(demo_fixture, tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval automatic replay requires same calibration and recomputes positions. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(original.directory / 'framegegevens.jsonl').read_bytes`, `(replayed.directory / 'framegegevens.jsonl').read_bytes`, `SyntheticDetector`, `bundle_for`, `inspect_video`, `monkeypatch.setattr`, `process_video`, `pytest.raises`.
Technische leespunten: with-context.

### test_automatic_ui_processes_only_on_click_and_invalidates_when_switching

Vindplaats: [tests/test_automatic_calibration.py regel 253](../tests/test_automatic_calibration.py#L253), tot regel 299.
Argumenten: `(demo_fixture, tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval automatic ui processes only on click and invalidates when switching. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `AppTest.from_file`, `AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=30).run`, `Mock`, `SimpleNamespace`, `SyntheticDetector`, `app.button`, `app.button(key='process').click`, `app.button(key='process').click().run`, `app.checkbox`, `app.run`, `app.segmented_control`, `app.segmented_control(key='calibration_mode').set_value`, `app.segmented_control(key='calibration_mode').set_value('Automatische veldkalibratie').run`, `app.segmented_control(key='calibration_mode').set_value('Handmatig').run`, `app.text_input`, `app.text_input(key='field_source').set_value`, `app.text_input(key='field_source').set_value('changed source').run`, `app.text_input(key='field_usage').set_value` en andere aanroepen.

### test_independent_evaluation_reports_coverage_and_rejects_unreviewed_labels

Vindplaats: [tests/test_automatic_calibration.py regel 302](../tests/test_automatic_calibration.py#L302), tot regel 347.
Argumenten: `(tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval independent evaluation reports coverage and rejects unreviewed labels. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `''.join`, `(directory / 'framegegevens.jsonl').write_text`, `calibration_evaluation.evaluate_calibration`, `directory.mkdir`, `enumerate`, `estimate_frame`, `json.dumps`, `list`, `monkeypatch.setattr`, `observation`, `pytest.approx`, `pytest.raises`, `range`, `write_json`.
Technische leespunten: with-context.

## tests/test_field_motion.py

Testmodule voor field motion

Bron: [tests/test_field_motion.py](../tests/test_field_motion.py).

### test_points_are_checked_without_mandatory_lines_and_controls_are_not_refitted

Vindplaats: [tests/test_field_motion.py regel 19](../tests/test_field_motion.py#L19), tot regel 33.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval points are checked without mandatory lines and controls are not refitted. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `deepcopy`, `estimate_checked`, `len`, `next`, `observation`, `set`, `set(quality['control_ids']).isdisjoint`.

### test_exact_four_point_fit_needs_additional_nonparallel_line_controls

Vindplaats: [tests/test_field_motion.py regel 36](../tests/test_field_motion.py#L36), tot regel 49.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval exact four point fit needs additional nonparallel line controls. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `estimate_checked`, `np.array`, `observation`, `row['lines'].append`, `transform`, `transform(LINES_UV[17], inverse).tolist`, `transform(LINES_UV[i], inverse).tolist`.

### texture

Vindplaats: [tests/test_field_motion.py regel 52](../tests/test_field_motion.py#L52), tot regel 56.
Argumenten: `(seed=4)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `cv2.GaussianBlur`, `np.random.default_rng`, `np.stack`, `rng.integers`.
Technische leespunten: return.

### unknown

Vindplaats: [tests/test_field_motion.py regel 59](../tests/test_field_motion.py#L59), tot regel 60.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `estimate_checked`.
Technische leespunten: return.

### test_actual_optical_flow_measures_pan_zoom_and_expires_without_refreshing_anchor

Vindplaats: [tests/test_field_motion.py regel 63](../tests/test_field_motion.py#L63), tot regel 89.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval actual optical flow measures pan zoom and expires without refreshing anchor. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `CameraCalibration`, `camera.update`, `cv2.warpPerspective`, `estimate_checked`, `np.array`, `observation`, `pytest.approx`, `range`, `texture`, `transform`, `unknown`.
Technische leespunten: lus.

### test_motion_failure_resets_then_direct_recognition_recovers

Vindplaats: [tests/test_field_motion.py regel 93](../tests/test_field_motion.py#L93), tot regel 116.
Argumenten: `(failure)`. Retourtypehint: `niet opgegeven`.
Controleert het geval motion failure resets then direct recognition recovers. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `CameraCalibration`, `camera.update`, `cv2.GaussianBlur`, `deepcopy`, `estimate_checked`, `np.full_like`, `observation`, `pytest.mark.parametrize`, `texture`, `unknown`.
Technische leespunten: lus, voorwaardelijke vertakking.

### test_confidence_is_a_separate_profile_and_old_identity_is_preserved

Vindplaats: [tests/test_field_motion.py regel 119](../tests/test_field_motion.py#L119), tot regel 137.
Argumenten: `(demo_fixture, tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval confidence is a separate profile and old identity is preserved. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `AutomaticCalibration`, `bundle_for`, `filtered.validate_for`, `inspect_video`, `invalid.validate_for`, `len`, `pytest.raises`.
Technische leespunten: with-context.

### test_confidence_comparison_filters_the_same_raw_observations

Vindplaats: [tests/test_field_motion.py regel 140](../tests/test_field_motion.py#L140), tot regel 148.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval confidence comparison filters the same raw observations. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `deepcopy`, `estimate_checked`, `observation`, `point.update`.
Technische leespunten: lus.

### test_full_score_bundles_validate_completeness_before_comparisons

Vindplaats: [tests/test_field_motion.py regel 152](../tests/test_field_motion.py#L152), tot regel 188.
Argumenten: `(demo_fixture, tmp_path, fault)`. Retourtypehint: `niet opgegeven`.
Controleert het geval full score bundles validate completeness before comparisons. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `''.join`, `Path`, `all`, `bundle.frames`, `bundle.manifest.update`, `bundle.validate_for`, `bundle_for`, `inspect_video`, `json.dumps`, `list`, `observation`, `path.write_text`, `pytest.mark.parametrize`, `pytest.raises`, `range`, `row['lines'].extend`, `row['points'].extend`, `rows[0]['lines'].pop` en andere aanroepen.
Technische leespunten: with-context, lus, voorwaardelijke vertakking.

### test_motion_also_checks_available_lines_and_resets_across_missing_indices

Vindplaats: [tests/test_field_motion.py regel 191](../tests/test_field_motion.py#L191), tot regel 203.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval motion also checks available lines and resets across missing indices. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `CameraCalibration`, `camera.update`, `deepcopy`, `estimate_checked`, `observation`, `texture`, `unknown`.
Technische leespunten: lus.

### test_motion_rejects_fewer_than_twenty_or_low_ratio_inliers

Vindplaats: [tests/test_field_motion.py regel 207](../tests/test_field_motion.py#L207), tot regel 220.
Argumenten: `(monkeypatch, inliers)`. Retourtypehint: `niet opgegeven`.
Controleert het geval motion rejects fewer than twenty or low ratio inliers. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `CameraCalibration`, `camera.update`, `estimate_checked`, `len`, `monkeypatch.setattr`, `np.eye`, `np.zeros`, `observation`, `pytest.mark.parametrize`, `texture`, `unknown`.
Technische leespunten: return.

### test_motion_rejects_fewer_than_twenty_or_low_ratio_inliers.bad_consensus

Vindplaats: [tests/test_field_motion.py regel 212](../tests/test_field_motion.py#L212), tot regel 215.
Argumenten: `(a, b, *args)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `len`, `np.eye`, `np.zeros`.
Technische leespunten: return.

### test_recalibration_reuses_detections_but_recomputes_current_geometry

Vindplaats: [tests/test_field_motion.py regel 223](../tests/test_field_motion.py#L223), tot regel 259.
Argumenten: `(demo_fixture, tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval recalibration reuses detections but recomputes current geometry. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(replayed.directory / 'framegegevens.jsonl').read_bytes`, `(result.directory / 'framegegevens.jsonl').read_bytes`, `(result.directory / 'framegegevens.jsonl').read_text`, `(result.directory / 'framegegevens.jsonl').read_text().splitlines`, `AutomaticCalibration`, `SyntheticDetector`, `bundle_for`, `inspect_video`, `json.loads`, `monkeypatch.setattr`, `process_video`, `pytest.raises`, `validate_completed`.
Technische leespunten: with-context.

### test_human_references_require_explicit_input_and_completion_is_separate

Vindplaats: [tests/test_field_motion.py regel 262](../tests/test_field_motion.py#L262), tot regel 290.
Argumenten: `(tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval human references require explicit input and completion is separate. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `finalize_review`, `pytest.raises`, `read_json`, `save_review`.
Technische leespunten: with-context.

### test_failed_intervals_include_first_last_and_empty

Vindplaats: [tests/test_field_motion.py regel 293](../tests/test_field_motion.py#L293), tot regel 298.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval failed intervals include first last and empty. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `failure_intervals`.

### test_new_ui_saved_run_uses_same_frame_and_point_toggles

Vindplaats: [tests/test_field_motion.py regel 301](../tests/test_field_motion.py#L301), tot regel 323.
Argumenten: `(demo_fixture, tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval new ui saved run uses same frame and point toggles. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `AppTest.from_file`, `AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=30).run`, `AutomaticCalibration`, `SyntheticDetector`, `any`, `app.checkbox`, `app.checkbox(key='open_field_review').check`, `app.checkbox(key='open_field_review').check().run`, `app.checkbox(key=f'recognized_{token}').uncheck`, `app.checkbox(key=f'recognized_{token}').uncheck().run`, `app.checkbox(key=f'tracked_{token}').uncheck`, `app.checkbox(key=f'tracked_{token}').uncheck().run`, `app.slider`, `app.slider(key=f'review_frame_{token}').set_value`, `app.slider(key=f'review_frame_{token}').set_value(4).run`, `bundle_for`, `inspect_video`, `monkeypatch.setenv` en andere aanroepen.

### test_ui_human_reference_is_only_saved_after_explicit_input

Vindplaats: [tests/test_field_motion.py regel 326](../tests/test_field_motion.py#L326), tot regel 377.
Argumenten: `(demo_fixture, tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval ui human reference is only saved after explicit input. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(tmp_path / 'configs').mkdir`, `(tmp_path / 'data/field-reviews').exists`, `(tmp_path / 'data/field-reviews').rglob`, `AppTest.from_file`, `AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=30).run`, `AutomaticCalibration`, `SyntheticDetector`, `any`, `app.button`, `app.button(key=f'finalize_{token}_Ontwikkeling').click`, `app.button(key=f'finalize_{token}_Ontwikkeling').click().run`, `app.button(key=f'save_review_{token}').click`, `app.button(key=f'save_review_{token}').click().run`, `app.checkbox`, `app.checkbox(key='open_field_review').check`, `app.checkbox(key='open_field_review').check().run`, `app.checkbox(key=f'confirm_set_{token}_Ontwikkeling').check`, `app.checkbox(key=f'confirm_set_{token}_Ontwikkeling').check().run` en andere aanroepen.

## tests/test_field_training.py

Testmodule voor field training

Bron: [tests/test_field_training.py](../tests/test_field_training.py).

### Response

Vindplaats: [tests/test_field_training.py regel 31](../tests/test_field_training.py#L31), tot regel 35.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: io.BytesIO.

### Response.__init__

Vindplaats: [tests/test_field_training.py regel 32](../tests/test_field_training.py#L32), tot regel 35.
Argumenten: `(self, content, status=200, headers=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `len`, `str`, `super`, `super().__init__`.

### test_download_resumes_and_rehashes_completed_files

Vindplaats: [tests/test_field_training.py regel 38](../tests/test_field_training.py#L38), tot regel 66.
Argumenten: `(tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval download resumes and rehashes completed files. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `CorpusBudget`, `Response`, `budget.start_tracking`, `budget.used`, `download`, `len`, `monkeypatch.setattr`, `p.is_file`, `p.stat`, `pytest.fail`, `pytest.raises`, `sha256_file`, `str`, `sum`, `target.read_bytes`, `target.with_suffix`, `target.with_suffix('.zip.part').write_bytes`, `target.write_bytes` en andere aanroepen.
Technische leespunten: return, with-context.

### test_download_resumes_and_rehashes_completed_files.open_request

Vindplaats: [tests/test_field_training.py regel 46](../tests/test_field_training.py#L46), tot regel 53.
Argumenten: `(request, timeout)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Response`, `len`, `str`.
Technische leespunten: return.

### test_budget_rejects_before_download_writes

Vindplaats: [tests/test_field_training.py regel 69](../tests/test_field_training.py#L69), tot regel 74.
Argumenten: `(tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval budget rejects before download writes. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `CorpusBudget`, `Response`, `download`, `monkeypatch.setattr`, `pytest.raises`, `target.exists`.
Technische leespunten: with-context.

### test_complete_partial_download_publishes_without_request

Vindplaats: [tests/test_field_training.py regel 77](../tests/test_field_training.py#L77), tot regel 84.
Argumenten: `(tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval complete partial download publishes without request. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `CorpusBudget`, `download`, `monkeypatch.setattr`, `partial.write_bytes`, `pytest.fail`, `sha256_file`, `target.read_bytes`, `target.with_suffix`, `write_json`.

### test_exclusive_budget_tracking_accounts_atomic_metadata_and_refuses_overflow

Vindplaats: [tests/test_field_training.py regel 87](../tests/test_field_training.py#L87), tot regel 93.
Argumenten: `(tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval exclusive budget tracking accounts atomic metadata and refuses overflow. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(tmp_path / 'metadata.json').stat`, `CorpusBudget`, `budget.start_tracking`, `budget.used`, `budget.write_json`, `pytest.raises`.
Technische leespunten: with-context.

### test_zip_rejects_traversal_and_changed_extraction

Vindplaats: [tests/test_field_training.py regel 96](../tests/test_field_training.py#L96), tot regel 107.
Argumenten: `(tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval zip rejects traversal and changed extraction. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(tmp_path / 'dataset/train/example.json').write_text`, `CorpusBudget`, `bundle.writestr`, `extract_archive`, `pytest.raises`, `zipfile.ZipFile`.
Technische leespunten: with-context.

### test_mask_removes_invisible_error_and_gradient_before_reduction

Vindplaats: [tests/test_field_training.py regel 110](../tests/test_field_training.py#L110), tot regel 118.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval mask removes invisible error and gradient before reduction. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `loss.backward`, `loss.item`, `masked_heatmap_loss`, `masked_heatmap_loss(prediction, target, torch.zeros_like(mask)).item`, `prediction.grad.flatten`, `prediction.grad.flatten().tolist`, `torch.tensor`, `torch.zeros_like`.

### test_interrupted_checkpoint_publication_preserves_previous_committed_epoch

Vindplaats: [tests/test_field_training.py regel 121](../tests/test_field_training.py#L121), tot regel 149.
Argumenten: `(tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval interrupted checkpoint publication preserves previous committed epoch. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `OSError`, `atomic_torch_save`, `fresh.resolve`, `json.loads`, `monkeypatch.setattr`, `publish_epoch_checkpoint`, `pytest.raises`, `record['history'].append`, `report_path.read_text`, `sha256_file`, `str`, `torch.load`, `torch.tensor`, `write_json`.
Technische leespunten: expliciete foutmelding, with-context.

### test_interrupted_checkpoint_publication_preserves_previous_committed_epoch.fail

Vindplaats: [tests/test_field_training.py regel 129](../tests/test_field_training.py#L129), tot regel 130.
Argumenten: `(*args)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `OSError`.
Technische leespunten: expliciete foutmelding.

### test_invalid_normalized_labels_rejected

Vindplaats: [tests/test_field_training.py regel 153](../tests/test_field_training.py#L153), tot regel 155.
Argumenten: `(coordinate)`. Retourtypehint: `niet opgegeven`.
Controleert het geval invalid normalized labels rejected. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `float`, `pytest.mark.parametrize`, `pytest.raises`, `validate_labels`.
Technische leespunten: with-context.

### test_label_roundoff_is_clamped_without_changing_raw_labels

Vindplaats: [tests/test_field_training.py regel 158](../tests/test_field_training.py#L158), tot regel 163.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval label roundoff is clamped without changing raw labels. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `validate_labels`.

### test_duplicate_and_compilation_selection

Vindplaats: [tests/test_field_training.py regel 166](../tests/test_field_training.py#L166), tot regel 173.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval duplicate and compilation selection. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `frame_signature`, `identify_match`, `image.copy`, `match_split`, `near_duplicate`, `np.random.default_rng`, `np.random.default_rng(42).integers`, `np.random.default_rng(99).integers`.

### test_frame_preparation_spacing_provenance_and_resume

Vindplaats: [tests/test_field_training.py regel 176](../tests/test_field_training.py#L176), tot regel 220.
Argumenten: `(tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval frame preparation spacing provenance and resume. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(tmp_path / 'frames/example/manifest.json').read_text`, `Capture`, `CorpusBudget`, `all`, `json.loads`, `monkeypatch.setattr`, `np.random.default_rng`, `np.repeat`, `prepare_frames`, `pytest.fail`, `range`, `rng.integers`, `sha256_file`, `source.write_bytes`, `write_json`.
Technische leespunten: return, yield of generator, lus.

### test_frame_preparation_spacing_provenance_and_resume.Capture

Vindplaats: [tests/test_field_training.py regel 198](../tests/test_field_training.py#L198), tot regel 205.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### test_frame_preparation_spacing_provenance_and_resume.Capture.get

Vindplaats: [tests/test_field_training.py regel 199](../tests/test_field_training.py#L199), tot regel 202.
Argumenten: `(self, property_id)`. Retourtypehint: `niet opgegeven`.
Technische leespunten: return.

### test_frame_preparation_spacing_provenance_and_resume.Capture.release

Vindplaats: [tests/test_field_training.py regel 204](../tests/test_field_training.py#L204), tot regel 205.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.

### test_frame_preparation_spacing_provenance_and_resume.frames

Vindplaats: [tests/test_field_training.py regel 207](../tests/test_field_training.py#L207), tot regel 211.
Argumenten: `(*args)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `np.random.default_rng`, `np.repeat`, `range`, `rng.integers`.
Technische leespunten: yield of generator, lus.

### make_dataset

Vindplaats: [tests/test_field_training.py regel 223](../tests/test_field_training.py#L223), tot regel 237.
Argumenten: `(tmp_path)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(root / 'main.jpg').write_bytes`, `(root / 'replay.jpg').write_bytes`, `root.mkdir`, `split.encode`, `write_json`.
Technische leespunten: lus.

### test_both_networks_use_same_windows_safe_main_camera_index

Vindplaats: [tests/test_field_training.py regel 240](../tests/test_field_training.py#L240), tot regel 249.
Argumenten: `(tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval both networks use same windows safe main camera index. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(tmp_path / 'valid/main.jpg').write_bytes`, `Path`, `all`, `dataset_index`, `len`, `make_dataset`, `pytest.raises`.
Technische leespunten: with-context.

### test_match_overlap_rejected_even_when_images_differ

Vindplaats: [tests/test_field_training.py regel 252](../tests/test_field_training.py#L252), tot regel 260.
Argumenten: `(tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval match overlap rejected even when images differ. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `dataset_index`, `info['main.jpg'].update`, `json.loads`, `make_dataset`, `path.read_text`, `pytest.raises`, `write_json`.
Technische leespunten: with-context, lus.

### test_finetuned_runtime_requires_matching_completed_report

Vindplaats: [tests/test_field_training.py regel 263](../tests/test_field_training.py#L263), tot regel 290.
Argumenten: `(tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval finetuned runtime requires matching completed report. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `pytest.raises`, `role.encode`, `runtime['models'].values`, `sha256_file`, `str`, `validate_runtime_models`, `weights.write_bytes`, `write_json`.
Technische leespunten: with-context, lus.

## tests/test_geometry.py

Testmodule voor geometry

Bron: [tests/test_geometry.py](../tests/test_geometry.py).

### detection

Vindplaats: [tests/test_geometry.py regel 11](../tests/test_geometry.py#L11), tot regel 12.
Argumenten: `(box)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Detection`.
Technische leespunten: return.

### test_known_perspective_transform_and_independent_checks

Vindplaats: [tests/test_geometry.py regel 15](../tests/test_geometry.py#L15), tot regel 28.
Argumenten: `(video_metadata, calibration)`. Retourtypehint: `niet opgegeven`.
Controleert het geval known perspective transform and independent checks. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(projected[:2] / projected[2]).tolist`, `create_calibration`, `deepcopy`, `detection`, `max`, `np.array`, `project_detection`, `pytest.approx`.
Technische leespunten: lus.

### test_invalid_calibrations_rejected

Vindplaats: [tests/test_geometry.py regel 32](../tests/test_geometry.py#L32), tot regel 47.
Argumenten: `(video_metadata, calibration, mutation)`. Retourtypehint: `niet opgegeven`.
Controleert het geval invalid calibrations rejected. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `create_calibration`, `deepcopy`, `points[4].update`, `pytest.mark.parametrize`, `pytest.raises`.
Technische leespunten: with-context, lus, voorwaardelijke vertakking.

### test_failed_independent_check_exposes_diagnostics_without_moving_click

Vindplaats: [tests/test_geometry.py regel 50](../tests/test_geometry.py#L50), tot regel 63.
Argumenten: `(video_metadata, calibration)`. Retourtypehint: `niet opgegeven`.
Controleert het geval failed independent check exposes diagnostics without moving click. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `create_calibration`, `deepcopy`, `np.hypot`, `pytest.approx`, `pytest.raises`.
Technische leespunten: with-context.

### test_projection_status_and_no_invented_position

Vindplaats: [tests/test_geometry.py regel 76](../tests/test_geometry.py#L76), tot regel 80.
Argumenten: `(calibration, box, status)`. Retourtypehint: `niet opgegeven`.
Controleert het geval projection status and no invented position. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `detection`, `float`, `project_detection`, `pytest.mark.parametrize`.

### test_loaded_matrix_scale_and_review_are_validated

Vindplaats: [tests/test_geometry.py regel 83](../tests/test_geometry.py#L83), tot regel 89.
Argumenten: `(video_metadata, calibration)`. Retourtypehint: `niet opgegeven`.
Controleert het geval loaded matrix scale and review are validated. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `calibration.validate_for`, `pytest.raises`, `replace`.
Technische leespunten: with-context.

### test_display_resize_does_not_change_geometry

Vindplaats: [tests/test_geometry.py regel 92](../tests/test_geometry.py#L92), tot regel 101.
Argumenten: `(calibration)`. Retourtypehint: `niet opgegeven`.
Controleert het geval display resize does not change geometry. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `FrameRecord`, `detection`, `item.field_position.copy`, `np.zeros`, `project_detection`, `render_frame`.

### test_homogeneous_zero_divisor_never_creates_a_position

Vindplaats: [tests/test_geometry.py regel 104](../tests/test_geometry.py#L104), tot regel 109.
Argumenten: `(calibration)`. Retourtypehint: `niet opgegeven`.
Controleert het geval homogeneous zero divisor never creates a position. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `detection`, `project_detection`.

### test_malformed_review_is_an_actionable_error

Vindplaats: [tests/test_geometry.py regel 112](../tests/test_geometry.py#L112), tot regel 115.
Argumenten: `(video_metadata, calibration)`. Retourtypehint: `niet opgegeven`.
Controleert het geval malformed review is an actionable error. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `calibration.validate_for`, `pytest.raises`.
Technische leespunten: with-context.

## tests/test_joint_integration.py

Testmodule voor joint integration

Bron: [tests/test_joint_integration.py](../tests/test_joint_integration.py).

Broncommentaar: Audit actual export contracts; fixtures below are explicitly synthetic software evidence.

### audit_fixture

Vindplaats: [tests/test_joint_integration.py regel 14](../tests/test_joint_integration.py#L14), tot regel 68.
Argumenten: `(tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Detection`, `FrameRecord`, `FrameRecord(0, 0.0, (640, 360), people, {'status': 'valid'}).to_dict`, `FrameRecord(1, 0.04, (640, 360), [unavailable], {'status': 'insufficient_points'}).to_dict`, `FrameRecord(2, 0.08, (640, 360), [], {'status': 'valid'}).to_dict`, `SimpleNamespace`, `deepcopy`, `enumerate`, `monkeypatch.setattr`, `people.append`, `rows.append`.
Technische leespunten: return, lus.

### write_rows

Vindplaats: [tests/test_joint_integration.py regel 71](../tests/test_joint_integration.py#L71), tot regel 75.
Argumenten: `(directory, rows)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `''.join`, `(directory / 'framegegevens.jsonl').write_text`, `json.dumps`.

### test_joint_audit_checks_team_roles_unknown_field_and_empty_frame

Vindplaats: [tests/test_joint_integration.py regel 78](../tests/test_joint_integration.py#L78), tot regel 88.
Argumenten: `(tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval joint audit checks team roles unknown field and empty frame. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `audit_fixture`, `verifier.verify_records`, `write_rows`.

### test_joint_audit_rejects_inconsistent_export

Vindplaats: [tests/test_joint_integration.py regel 92](../tests/test_joint_integration.py#L92), tot regel 106.
Argumenten: `(tmp_path, monkeypatch, damage)`. Retourtypehint: `niet opgegeven`.
Controleert het geval joint audit rejects inconsistent export. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `ROLE_NAMES.index`, `audit_fixture`, `pytest.mark.parametrize`, `pytest.raises`, `rows[0]['detections'][3].update`, `verifier.verify_records`, `write_rows`.
Technische leespunten: with-context, voorwaardelijke vertakking.

### test_joint_app_runs_automatic_field_and_preserves_roles_teams_on_review

Vindplaats: [tests/test_joint_integration.py regel 109](../tests/test_joint_integration.py#L109), tot regel 210.
Argumenten: `(demo_fixture, model_manifest, tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval joint app runs automatic field and preserves roles teams on review. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `AppTest.from_file`, `AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=30).run`, `Detection`, `JointDetector`, `any`, `app.button`, `app.button(key='process').click`, `app.button(key='process').click().run`, `app.checkbox`, `app.checkbox(key='open_field_review').check`, `app.checkbox(key='open_field_review').check().run`, `app.file_uploader`, `app.file_uploader(key='video_upload').set_value`, `app.file_uploader(key='video_upload').set_value(('joint-synthetic.mp4', demo_fixture['video'].read_bytes(), 'video/mp4')).run`, `app.run`, `app.slider`, `app.slider(key=f'review_frame_{token}').set_value`, `app.slider(key=f'review_frame_{token}').set_value(8).run` en andere aanroepen.
Technische leespunten: return, lus, voorwaardelijke vertakking.

### test_joint_app_runs_automatic_field_and_preserves_roles_teams_on_review.prepare

Vindplaats: [tests/test_joint_integration.py regel 144](../tests/test_joint_integration.py#L144), tot regel 146.
Argumenten: `(video_path, runtime_path, output_root, **kwargs)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `calls.append`.
Technische leespunten: return.

### test_joint_app_runs_automatic_field_and_preserves_roles_teams_on_review.JointDetector

Vindplaats: [tests/test_joint_integration.py regel 148](../tests/test_joint_integration.py#L148), tot regel 174.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### test_joint_app_runs_automatic_field_and_preserves_roles_teams_on_review.JointDetector.detect

Vindplaats: [tests/test_joint_integration.py regel 152](../tests/test_joint_integration.py#L152), tot regel 174.
Argumenten: `(self, frame, frame_index)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Detection`, `detections.append`, `enumerate`.
Technische leespunten: return, lus, voorwaardelijke vertakking.

## tests/test_model_handoff.py

Testmodule voor model handoff

Bron: [tests/test_model_handoff.py](../tests/test_model_handoff.py).

### handoff

Vindplaats: [tests/test_model_handoff.py regel 12](../tests/test_model_handoff.py#L12), tot regel 28.
Argumenten: `(tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `SimpleNamespace`, `monkeypatch.setattr`, `weights.parent.mkdir`, `weights.write_bytes`, `write_json`.
Technische leespunten: return.

### test_register_player_model_verifies_names_hashes_and_preserves_previous_version

Vindplaats: [tests/test_model_handoff.py regel 31](../tests/test_model_handoff.py#L31), tot regel 46.
Argumenten: `(handoff)`. Retourtypehint: `niet opgegeven`.
Controleert het geval register player model verifies names hashes and preserves previous version. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `Path`, `Path(manifest['models'][0]['weights']).resolve`, `load_model_manifest`, `output.read_bytes`, `pytest.raises`, `register_player_model`, `sha256_file`, `weights.resolve`, `write_json`.
Technische leespunten: with-context.

### test_invalid_handoff_cannot_create_ready_profile

Vindplaats: [tests/test_model_handoff.py regel 50](../tests/test_model_handoff.py#L50), tot regel 74.
Argumenten: `(handoff, monkeypatch, case)`. Retourtypehint: `niet opgegeven`.
Controleert het geval invalid handoff cannot create ready profile. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `SimpleNamespace`, `monkeypatch.setattr`, `output.exists`, `pytest.mark.parametrize`, `pytest.raises`, `register_player_model`, `write_json`.
Technische leespunten: with-context, voorwaardelijke vertakking.

### test_profile_discovery_adds_registered_model_without_restarting

Vindplaats: [tests/test_model_handoff.py regel 77](../tests/test_model_handoff.py#L77), tot regel 87.
Argumenten: `(handoff)`. Retourtypehint: `niet opgegeven`.
Controleert het geval profile discovery adds registered model without restarting. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `available_model_profiles`, `available_model_profiles(default, output.parent).values`, `default.resolve`, `list`, `output.parent.mkdir`, `output.resolve`, `read_json`, `register_player_model`, `write_json`.

## tests/test_models_and_evaluation.py

Testmodule voor models and evaluation

Bron: [tests/test_models_and_evaluation.py](../tests/test_models_and_evaluation.py).

### test_duplicate_semantic_suppliers_rejected

Vindplaats: [tests/test_models_and_evaluation.py regel 10](../tests/test_models_and_evaluation.py#L10), tot regel 17.
Argumenten: `(model_manifest)`. Retourtypehint: `niet opgegeven`.
Controleert het geval duplicate semantic suppliers rejected. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `deepcopy`, `load_model_manifest`, `manifest['models'].append`, `pytest.raises`, `write_json`.
Technische leespunten: with-context.

### test_person_never_becomes_a_specialized_role

Vindplaats: [tests/test_models_and_evaluation.py regel 21](../tests/test_models_and_evaluation.py#L21), tot regel 27.
Argumenten: `(model_manifest, role)`. Retourtypehint: `niet opgegeven`.
Controleert het geval person never becomes a specialized role. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `load_model_manifest`, `pytest.mark.parametrize`, `pytest.raises`, `write_json`.
Technische leespunten: with-context.

### test_handover_weight_hash_is_verified

Vindplaats: [tests/test_models_and_evaluation.py regel 30](../tests/test_models_and_evaluation.py#L30), tot regel 35.
Argumenten: `(model_manifest)`. Retourtypehint: `niet opgegeven`.
Controleert het geval handover weight hash is verified. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `load_model_manifest`, `pytest.raises`, `write_json`.
Technische leespunten: with-context.

### test_non_object_manifest_is_an_actionable_error

Vindplaats: [tests/test_models_and_evaluation.py regel 38](../tests/test_models_and_evaluation.py#L38), tot regel 42.
Argumenten: `(tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval non object manifest is an actionable error. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `load_model_manifest`, `path.write_text`, `pytest.raises`.
Technische leespunten: with-context.

### test_cuda_profile_explains_cpu_environment_before_inference

Vindplaats: [tests/test_models_and_evaluation.py regel 46](../tests/test_models_and_evaluation.py#L46), tot regel 51.
Argumenten: `(monkeypatch, device)`. Retourtypehint: `niet opgegeven`.
Controleert het geval cuda profile explains cpu environment before inference. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `monkeypatch.setattr`, `pytest.mark.parametrize`, `pytest.raises`, `validate_detection_devices`.
Technische leespunten: with-context.

### test_explicit_cpu_and_available_cuda_devices

Vindplaats: [tests/test_models_and_evaluation.py regel 54](../tests/test_models_and_evaluation.py#L54), tot regel 62.
Argumenten: `(monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval explicit cpu and available cuda devices. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `monkeypatch.setattr`, `pytest.raises`, `validate_detection_devices`.
Technische leespunten: with-context.

### test_evaluation_switches_takeovers_gaps_and_full_occlusion

Vindplaats: [tests/test_models_and_evaluation.py regel 65](../tests/test_models_and_evaluation.py#L65), tot regel 85.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval evaluation switches takeovers gaps and full occlusion. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `enumerate`, `evaluate_frames`, `range`.

### test_evaluation_uses_one_to_one_assignment

Vindplaats: [tests/test_models_and_evaluation.py regel 88](../tests/test_models_and_evaluation.py#L88), tot regel 102.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval evaluation uses one to one assignment. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `evaluate_frames`.

## tests/test_panoris_pilot.py

Testmodule voor panoris pilot

Bron: [tests/test_panoris_pilot.py](../tests/test_panoris_pilot.py).

### pilot_config

Vindplaats: [tests/test_panoris_pilot.py regel 11](../tests/test_panoris_pilot.py#L11), tot regel 20.
Argumenten: `(video_metadata, calibration)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `deepcopy`, `list`.
Technische leespunten: return.

### pitch_frame

Vindplaats: [tests/test_panoris_pilot.py regel 23](../tests/test_panoris_pilot.py#L23), tot regel 27.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `cv2.line`, `cv2.rectangle`, `np.zeros`.
Technische leespunten: return.

### test_static_geometry_passes_without_human_approval

Vindplaats: [tests/test_panoris_pilot.py regel 30](../tests/test_panoris_pilot.py#L30), tot regel 38.
Argumenten: `(video_metadata, calibration, tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval static geometry passes without human approval. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `len`, `monkeypatch.setattr`, `panoris_pilot.assess_geometry`, `pilot_config`, `pitch_frame`.

### test_failed_geometry_is_recorded_without_correcting_points

Vindplaats: [tests/test_panoris_pilot.py regel 41](../tests/test_panoris_pilot.py#L41), tot regel 49.
Argumenten: `(video_metadata, calibration, tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval failed geometry is recorded without correcting points. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(tmp_path / 'calibration-technical.json').exists`, `panoris_pilot.assess_geometry`, `pilot_config`, `pytest.raises`, `read_json`.
Technische leespunten: with-context.

### test_camera_shift_stops_pilot

Vindplaats: [tests/test_panoris_pilot.py regel 52](../tests/test_panoris_pilot.py#L52), tot regel 59.
Argumenten: `(video_metadata, calibration, tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval camera shift stops pilot. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `monkeypatch.setattr`, `np.roll`, `panoris_pilot.assess_geometry`, `pilot_config`, `pitch_frame`, `pytest.raises`, `read_json`.
Technische leespunten: with-context.

## tests/test_participants.py

Testmodule voor participants

Bron: [tests/test_participants.py](../tests/test_participants.py).

### candidate

Vindplaats: [tests/test_participants.py regel 11](../tests/test_participants.py#L11), tot regel 12.
Argumenten: `(role='player', confidence=0.9, box=None)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Detection`.
Technische leespunten: return.

### test_only_players_on_pitch_count_but_other_roles_and_off_pitch_predictions_are_preserved

Vindplaats: [tests/test_participants.py regel 15](../tests/test_participants.py#L15), tot regel 35.
Argumenten: `(calibration)`. Retourtypehint: `niet opgegeven`.
Controleert het geval only players on pitch count but other roles and off pitch predictions are preserved. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `Detection.from_dict`, `FrameRecord`, `FrameRecord(0, 0, (640, 360), roundtrip).to_dict`, `candidate`, `dict.fromkeys`, `frame.to_dict`, `len`, `player_summary`, `project_detection`.
Technische leespunten: lus.

### test_field_loss_is_unknown_not_zero_and_recovery_uses_current_transform

Vindplaats: [tests/test_participants.py regel 38](../tests/test_participants.py#L38), tot regel 53.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval field loss is unknown not zero and recovery uses current transform. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `FrameRecord`, `candidate`, `frame.to_dict`, `player_summary`, `project_automatic`.
Technische leespunten: lus.

### test_claimed_valid_projection_without_valid_position_cannot_count

Vindplaats: [tests/test_participants.py regel 57](../tests/test_participants.py#L57), tot regel 60.
Argumenten: `(position)`. Retourtypehint: `niet opgegeven`.
Controleert het geval claimed valid projection without valid position cannot count. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `FrameRecord`, `candidate`, `float`, `player_exclusion_reason`, `player_summary`, `pytest.mark.parametrize`, `replace`.

### test_truncated_feet_and_invalid_boxes_do_not_count

Vindplaats: [tests/test_participants.py regel 63](../tests/test_participants.py#L63), tot regel 67.
Argumenten: `(calibration)`. Retourtypehint: `niet opgegeven`.
Controleert het geval truncated feet and invalid boxes do not count. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `FrameRecord`, `FrameRecord(0, 0, (640, 360), [detection]).to_dict`, `candidate`, `project_detection`.
Technische leespunten: lus.

### test_generic_person_profile_has_no_available_player_count

Vindplaats: [tests/test_participants.py regel 70](../tests/test_participants.py#L70), tot regel 84.
Argumenten: `(calibration)`. Retourtypehint: `niet opgegeven`.
Controleert het geval generic person profile has no available player count. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `FrameRecord`, `candidate`, `project_detection`, `record.to_dict`.

## tests/test_person1.py

Testmodule voor person1

Bron: [tests/test_person1.py](../tests/test_person1.py).

### TempCase

Vindplaats: [tests/test_person1.py regel 13](../tests/test_person1.py#L13), tot regel 23.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: unittest.TestCase.

### TempCase.setUp

Vindplaats: [tests/test_person1.py regel 14](../tests/test_person1.py#L14), tot regel 18.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Path`, `Path('.cache/tests').resolve`, `Path(self.tmp.name).resolve`, `self.base.mkdir`, `tempfile.TemporaryDirectory`.

### TempCase.tearDown

Vindplaats: [tests/test_person1.py regel 20](../tests/test_person1.py#L20), tot regel 23.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `self.root.is_relative_to`, `self.tmp.cleanup`.

### MetricsTests

Vindplaats: [tests/test_person1.py regel 26](../tests/test_person1.py#L26), tot regel 79.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: unittest.TestCase.

### MetricsTests.setUp

Vindplaats: [tests/test_person1.py regel 27](../tests/test_person1.py#L27), tot regel 30.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.

### MetricsTests.test_perfect_prediction

Vindplaats: [tests/test_person1.py regel 32](../tests/test_person1.py#L32), tot regel 35.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval perfect prediction. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `evaluate`, `self.assertEqual`.

### MetricsTests.test_missing_prediction

Vindplaats: [tests/test_person1.py regel 37](../tests/test_person1.py#L37), tot regel 40.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval missing prediction. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `evaluate`, `self.assertEqual`.

### MetricsTests.test_high_confidence_false_positive_changes_ap

Vindplaats: [tests/test_person1.py regel 42](../tests/test_person1.py#L42), tot regel 45.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval high confidence false positive changes ap. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `evaluate`, `self.assertAlmostEqual`.

### MetricsTests.test_duplicate_is_not_second_true_positive

Vindplaats: [tests/test_person1.py regel 47](../tests/test_person1.py#L47), tot regel 51.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval duplicate is not second true positive. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `evaluate`, `self.assertEqual`.

### MetricsTests.test_stricter_iou_changes_localisation_score

Vindplaats: [tests/test_person1.py regel 53](../tests/test_person1.py#L53), tot regel 57.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval stricter iou changes localisation score. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `evaluate`, `self.assertEqual`, `self.assertLess`.

### MetricsTests.test_workpoint_does_not_truncate_ap_curve

Vindplaats: [tests/test_person1.py regel 59](../tests/test_person1.py#L59), tot regel 62.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval workpoint does not truncate ap curve. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `evaluate`, `self.assertEqual`.

### MetricsTests.test_missing_empty_frame_rejected

Vindplaats: [tests/test_person1.py regel 64](../tests/test_person1.py#L64), tot regel 66.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval missing empty frame rejected. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `evaluate`, `self.assertRaises`.
Technische leespunten: with-context.

### MetricsTests.test_wrong_class_does_not_match

Vindplaats: [tests/test_person1.py regel 68](../tests/test_person1.py#L68), tot regel 71.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval wrong class does not match. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `evaluate`, `self.assertEqual`, `self.assertIsNone`.

### MetricsTests.test_nan_prediction_rejected

Vindplaats: [tests/test_person1.py regel 73](../tests/test_person1.py#L73), tot regel 75.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval nan prediction rejected. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `evaluate`, `float`, `self.assertRaises`.
Technische leespunten: with-context.

### MetricsTests.test_iou_disjoint_and_identical

Vindplaats: [tests/test_person1.py regel 77](../tests/test_person1.py#L77), tot regel 79.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval iou disjoint and identical. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `iou`, `self.assertEqual`.

### DatasetTests

Vindplaats: [tests/test_person1.py regel 82](../tests/test_person1.py#L82), tot regel 225.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: TempCase.

### DatasetTests.setUp

Vindplaats: [tests/test_person1.py regel 83](../tests/test_person1.py#L83), tot regel 97.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `(self.root / f'{i}.txt').write_text`, `Image.frombytes`, `Image.frombytes('RGB', (64, 48), rng.randbytes(64 * 48 * 3)).save`, `enumerate`, `frames.append`, `random.Random`, `rng.randbytes`, `super`, `super().setUp`, `write_json`.
Technische leespunten: lus.

### DatasetTests.check

Vindplaats: [tests/test_person1.py regel 99](../tests/test_person1.py#L99), tot regel 100.
Argumenten: `(self, review=True)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `validate_dataset`.
Technische leespunten: return.

### DatasetTests.update

Vindplaats: [tests/test_person1.py regel 102](../tests/test_person1.py#L102), tot regel 103.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `write_json`.

### DatasetTests.test_valid_fixture

Vindplaats: [tests/test_person1.py regel 105](../tests/test_person1.py#L105), tot regel 106.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval valid fixture. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `self.assertEqual`, `self.check`.

### DatasetTests.test_default_frame_requirement_is_enforced

Vindplaats: [tests/test_person1.py regel 108](../tests/test_person1.py#L108), tot regel 109.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval default frame requirement is enforced. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `any`, `self.assertTrue`, `validate_dataset`.

### DatasetTests.test_cross_subset_group_is_rejected

Vindplaats: [tests/test_person1.py regel 111](../tests/test_person1.py#L111), tot regel 114.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval cross subset group is rejected. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `any`, `self.assertTrue`, `self.check`, `self.update`.

### DatasetTests.test_temporal_leakage_is_rejected

Vindplaats: [tests/test_person1.py regel 116](../tests/test_person1.py#L116), tot regel 119.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval temporal leakage is rejected. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `any`, `self.assertTrue`, `self.check`, `self.update`.

### DatasetTests.test_missing_label_is_not_negative

Vindplaats: [tests/test_person1.py regel 121](../tests/test_person1.py#L121), tot regel 123.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval missing label is not negative. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(self.root / '0.txt').unlink`, `self.assertTrue`, `self.check`.

### DatasetTests.test_empty_label_requires_negative_status

Vindplaats: [tests/test_person1.py regel 125](../tests/test_person1.py#L125), tot regel 127.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval empty label requires negative status. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(self.root / '0.txt').write_text`, `any`, `self.assertTrue`, `self.check`.

### DatasetTests.test_duplicate_pixels_are_rejected

Vindplaats: [tests/test_person1.py regel 129](../tests/test_person1.py#L129), tot regel 131.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval duplicate pixels are rejected. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(self.root / '0.png').read_bytes`, `(self.root / '1.png').write_bytes`, `any`, `self.assertTrue`, `self.check`.

### DatasetTests.test_independent_review_is_required

Vindplaats: [tests/test_person1.py regel 133](../tests/test_person1.py#L133), tot regel 136.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval independent review is required. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `any`, `self.assertTrue`, `self.check`, `self.update`.

### DatasetTests.test_content_change_changes_fingerprint

Vindplaats: [tests/test_person1.py regel 138](../tests/test_person1.py#L138), tot regel 141.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval content change changes fingerprint. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(self.root / '0.txt').write_text`, `self.assertNotEqual`, `self.check`.

### DatasetTests.test_unsafe_paths_rejected

Vindplaats: [tests/test_person1.py regel 143](../tests/test_person1.py#L143), tot regel 149.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval unsafe paths rejected. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `dataset_path`, `self.assertRaises`, `self.check`, `self.update`.
Technische leespunten: with-context.

### DatasetTests.test_invalid_boxes

Vindplaats: [tests/test_person1.py regel 151](../tests/test_person1.py#L151), tot regel 156.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval invalid boxes. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(self.root / 'bad.txt').write_text`, `read_labels`, `self.assertRaises`, `self.subTest`.
Technische leespunten: with-context, lus.

### DatasetTests.test_approval_never_accepts_an_unready_dataset

Vindplaats: [tests/test_person1.py regel 158](../tests/test_person1.py#L158), tot regel 162.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval approval never accepts an unready dataset. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `require_approval`, `self.assertRaises`, `write_json`.
Technische leespunten: with-context.

### DatasetTests.test_annotation_edit_invalidates_old_review

Vindplaats: [tests/test_person1.py regel 164](../tests/test_person1.py#L164), tot regel 169.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval annotation edit invalidates old review. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(self.root / 'review-history.jsonl').is_file`, `save_annotation`, `self.assertEqual`, `self.assertTrue`.

### DatasetTests.test_same_author_cannot_approve

Vindplaats: [tests/test_person1.py regel 171](../tests/test_person1.py#L171), tot regel 173.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval same author cannot approve. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `save_annotation`, `self.assertRaises`.
Technische leespunten: with-context.

### DatasetTests.test_empty_annotation_requires_explicit_confirmation

Vindplaats: [tests/test_person1.py regel 175](../tests/test_person1.py#L175), tot regel 177.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval empty annotation requires explicit confirmation. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `save_annotation`, `self.assertRaises`.
Technische leespunten: with-context.

### DatasetTests.test_approval_preserves_saved_boxes

Vindplaats: [tests/test_person1.py regel 179](../tests/test_person1.py#L179), tot regel 183.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval approval preserves saved boxes. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(self.root / '0.txt').read_text`, `save_annotation`, `self.assertEqual`.

### DatasetTests.provisional_fixture

Vindplaats: [tests/test_person1.py regel 185](../tests/test_person1.py#L185), tot regel 195.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `frame.update`, `self.check`, `self.data.update`, `self.update`, `sha256`, `write_json`.
Technische leespunten: return, lus.

### DatasetTests.test_provisional_labels_do_not_pass_human_review

Vindplaats: [tests/test_person1.py regel 197](../tests/test_person1.py#L197), tot regel 201.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval provisional labels do not pass human review. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `any`, `require_experiment_data`, `self.assertRaises`, `self.assertTrue`, `self.check`, `self.provisional_fixture`.
Technische leespunten: with-context.

### DatasetTests.test_explicit_provisional_route_checks_attestation

Vindplaats: [tests/test_person1.py regel 203](../tests/test_person1.py#L203), tot regel 211.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval explicit provisional route checks attestation. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `patch`, `require_experiment_data`, `self.assertEqual`, `self.assertRaisesRegex`, `self.provisional_fixture`, `write_json`.
Technische leespunten: with-context.

### DatasetTests.test_provisional_route_rejects_changed_evidence

Vindplaats: [tests/test_person1.py regel 213](../tests/test_person1.py#L213), tot regel 217.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval provisional route rejects changed evidence. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(self.root / '0.png').write_bytes`, `require_experiment_data`, `self.assertRaisesRegex`, `self.provisional_fixture`.
Technische leespunten: with-context.

### DatasetTests.test_provisional_final_test_is_forbidden

Vindplaats: [tests/test_person1.py regel 219](../tests/test_person1.py#L219), tot regel 225.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval provisional final test is forbidden. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `evaluate_run`, `predictions.mkdir`, `self.assertRaisesRegex`, `sha256`, `write_json`.
Technische leespunten: with-context.

## tests/test_pipeline.py

Testmodule voor pipeline

Bron: [tests/test_pipeline.py](../tests/test_pipeline.py).

### test_entire_clip_encoding_sync_empty_frames_cache_and_corruption

Vindplaats: [tests/test_pipeline.py regel 11](../tests/test_pipeline.py#L11), tot regel 41.
Argumenten: `(demo_fixture, tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval entire clip encoding sync empty frames cache and corruption. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(result.directory / 'controlebeelden').glob`, `(result.directory / 'framegegevens.jsonl').read_text`, `(result.directory / 'framegegevens.jsonl').read_text().splitlines`, `(result.directory / 'framegegevens.jsonl').write_text`, `SyntheticDetector`, `accept_mvp`, `inspect_video`, `json.loads`, `len`, `list`, `process_video`, `pytest.approx`, `pytest.raises`, `range`, `validate_completed`.
Technische leespunten: with-context.

### test_encoder_failure_never_marked_complete

Vindplaats: [tests/test_pipeline.py regel 44](../tests/test_pipeline.py#L44), tot regel 72.
Argumenten: `(demo_fixture, tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval encoder failure never marked complete. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(manifests[0].parent / 'samengestelde_video.mp4').exists`, `PipelineError`, `SyntheticDetector`, `len`, `list`, `monkeypatch.setattr`, `process_video`, `pytest.raises`, `read_json`, `tmp_path.glob`.
Technische leespunten: expliciete foutmelding, with-context.

### test_encoder_failure_never_marked_complete.BrokenWriter

Vindplaats: [tests/test_pipeline.py regel 47](../tests/test_pipeline.py#L47), tot regel 57.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: geen expliciete basisklasse.

### test_encoder_failure_never_marked_complete.BrokenWriter.__init__

Vindplaats: [tests/test_pipeline.py regel 50](../tests/test_pipeline.py#L50), tot regel 51.
Argumenten: `(self, *args)`. Retourtypehint: `niet opgegeven`.

### test_encoder_failure_never_marked_complete.BrokenWriter.write

Vindplaats: [tests/test_pipeline.py regel 53](../tests/test_pipeline.py#L53), tot regel 54.
Argumenten: `(self, frame)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `PipelineError`.
Technische leespunten: expliciete foutmelding.

### test_encoder_failure_never_marked_complete.BrokenWriter.close

Vindplaats: [tests/test_pipeline.py regel 56](../tests/test_pipeline.py#L56), tot regel 57.
Argumenten: `(self, abort=False)`. Retourtypehint: `niet opgegeven`.

### test_tracking_requires_real_mvp_acceptance

Vindplaats: [tests/test_pipeline.py regel 75](../tests/test_pipeline.py#L75), tot regel 86.
Argumenten: `(demo_fixture, tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval tracking requires real mvp acceptance. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `SyntheticDetector`, `process_video`, `pytest.raises`.
Technische leespunten: with-context.

### test_only_one_processing_job_per_root

Vindplaats: [tests/test_pipeline.py regel 89](../tests/test_pipeline.py#L89), tot regel 92.
Argumenten: `(tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval only one processing job per root. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `processing_lock`, `pytest.raises`.
Technische leespunten: with-context.

### test_unavailable_detector_gpu_fails_before_field_worker

Vindplaats: [tests/test_pipeline.py regel 95](../tests/test_pipeline.py#L95), tot regel 119.
Argumenten: `(demo_fixture, tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval unavailable detector gpu fails before field worker. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `AssertionError`, `load_model_manifest`, `monkeypatch.setattr`, `process_video`, `pytest.raises`, `read_json`, `write_json`.
Technische leespunten: expliciete foutmelding, with-context.

### test_unavailable_detector_gpu_fails_before_field_worker.forbidden_worker

Vindplaats: [tests/test_pipeline.py regel 112](../tests/test_pipeline.py#L112), tot regel 113.
Argumenten: `(*args, **kwargs)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `AssertionError`.
Technische leespunten: expliciete foutmelding.

### test_tracking_pipeline_preserves_empty_frame_without_predicted_position

Vindplaats: [tests/test_pipeline.py regel 122](../tests/test_pipeline.py#L122), tot regel 141.
Argumenten: `(demo_fixture, tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval tracking pipeline preserves empty frame without predicted position. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(result.directory / 'framegegevens.jsonl').read_text`, `(result.directory / 'framegegevens.jsonl').read_text().splitlines`, `SyntheticDetector`, `json.loads`, `monkeypatch.setattr`, `process_video`.

### test_pipeline_projects_before_tracking_and_preserves_nonplayers

Vindplaats: [tests/test_pipeline.py regel 144](../tests/test_pipeline.py#L144), tot regel 180.
Argumenten: `(demo_fixture, tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval pipeline projects before tracking and preserves nonplayers. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(result.directory / 'framegegevens.jsonl').read_text`, `(result.directory / 'framegegevens.jsonl').read_text().splitlines`, `Detection`, `MixedRoles`, `json.loads`, `len`, `monkeypatch.setattr`, `process_video`, `super`, `super().detect`.
Technische leespunten: return, voorwaardelijke vertakking.

### test_pipeline_projects_before_tracking_and_preserves_nonplayers.MixedRoles

Vindplaats: [tests/test_pipeline.py regel 149](../tests/test_pipeline.py#L149), tot regel 159.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: SyntheticDetector.

### test_pipeline_projects_before_tracking_and_preserves_nonplayers.MixedRoles.detect

Vindplaats: [tests/test_pipeline.py regel 150](../tests/test_pipeline.py#L150), tot regel 159.
Argumenten: `(self, frame, frame_index)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Detection`, `super`, `super().detect`.
Technische leespunten: return, voorwaardelijke vertakking.

### test_technical_pilot_never_impersonates_human_review_or_enables_tracking

Vindplaats: [tests/test_pipeline.py regel 183](../tests/test_pipeline.py#L183), tot regel 224.
Argumenten: `(demo_fixture, tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval technical pilot never impersonates human review or enables tracking. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `SyntheticDetector`, `accept_mvp`, `process_video`, `pytest.raises`, `read_json`, `replace`.
Technische leespunten: with-context.

### test_technical_pilot_requires_explicit_technical_evidence

Vindplaats: [tests/test_pipeline.py regel 227](../tests/test_pipeline.py#L227), tot regel 236.
Argumenten: `(demo_fixture, tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval technical pilot requires explicit technical evidence. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `SyntheticDetector`, `process_video`, `pytest.raises`.
Technische leespunten: with-context.

## tests/test_point_picker.py

Testmodule voor point picker

Bron: [tests/test_point_picker.py](../tests/test_point_picker.py).

### test_click_updates_only_selected_point_in_original_pixels

Vindplaats: [tests/test_point_picker.py regel 9](../tests/test_point_picker.py#L9), tot regel 23.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval click updates only selected point in original pixels. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `apply_point_click`, `deepcopy`.

### test_invalid_or_stale_click_cannot_change_points

Vindplaats: [tests/test_point_picker.py regel 41](../tests/test_point_picker.py#L41), tot regel 46.
Argumenten: `(changes)`. Retourtypehint: `niet opgegeven`.
Controleert het geval invalid or stale click cannot change points. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `apply_point_click`, `float`, `pytest.mark.parametrize`, `pytest.raises`.
Technische leespunten: with-context.

### test_missing_coordinates_name_the_point_instead_of_numpy_error

Vindplaats: [tests/test_point_picker.py regel 50](../tests/test_point_picker.py#L50), tot regel 57.
Argumenten: `(demo_fixture, value)`. Retourtypehint: `niet opgegeven`.
Controleert het geval missing coordinates name the point instead of numpy error. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `create_calibration`, `deepcopy`, `float`, `inspect_video`, `pytest.mark.parametrize`, `pytest.raises`.
Technische leespunten: with-context.

## tests/test_role_extension.py

Testmodule voor role extension

Bron: [tests/test_role_extension.py](../tests/test_role_extension.py).

### extension

Vindplaats: [tests/test_role_extension.py regel 12](../tests/test_role_extension.py#L12), tot regel 39.
Argumenten: `(tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `cv2.imwrite`, `enumerate`, `json.dumps`, `monkeypatch.setattr`, `np.full`, `path.write_text`, `rows.append`, `sha256_file`, `str`.
Technische leespunten: return, lus.

### test_extension_loads_without_mutating_existing_labels

Vindplaats: [tests/test_role_extension.py regel 42](../tests/test_role_extension.py#L42), tot regel 46.
Argumenten: `(tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval extension loads without mutating existing labels. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `extension`, `path.read_bytes`, `role_training.load_training_manifest`.

### test_extension_rejects_bad_data_before_training

Vindplaats: [tests/test_role_extension.py regel 59](../tests/test_role_extension.py#L59), tot regel 74.
Argumenten: `(tmp_path, monkeypatch, damage, message)`. Retourtypehint: `niet opgegeven`.
Controleert het geval extension rejects bad data before training. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `extension`, `json.dumps`, `path.write_text`, `pytest.mark.parametrize`, `pytest.raises`, `role_training.load_training_manifest`, `row.update`.
Technische leespunten: with-context, voorwaardelijke vertakking.

### test_role_only_match_never_inherits_an_untrained_supervised_team_head

Vindplaats: [tests/test_role_extension.py regel 77](../tests/test_role_extension.py#L77), tot regel 83.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval role only match never inherits an untrained supervised team head. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `role_training.supervised_team_videos`.

## tests/test_teamtrack_dataset.py

Testmodule voor teamtrack dataset

Bron: [tests/test_teamtrack_dataset.py](../tests/test_teamtrack_dataset.py).

### test_rebuilding_preserves_actual_annotation_edits

Vindplaats: [tests/test_teamtrack_dataset.py regel 8](../tests/test_teamtrack_dataset.py#L8), tot regel 16.
Argumenten: `(tmp_path)`. Retourtypehint: `niet opgegeven`.
Controleert het geval rebuilding preserves actual annotation edits. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(tmp_path / 'manifest.json').write_text`, `build`, `json.dumps`, `pytest.raises`.
Technische leespunten: with-context.

## tests/test_tracking.py

Testmodule voor tracking

Bron: [tests/test_tracking.py](../tests/test_tracking.py).

### item

Vindplaats: [tests/test_tracking.py regel 8](../tests/test_tracking.py#L8), tot regel 18.
Argumenten: `(index, confidence=0.9, semantic='player', x=100)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Detection`.
Technische leespunten: return.

### test_actual_bytetrack_indexes_low_confidence_and_empty_updates

Vindplaats: [tests/test_tracking.py regel 21](../tests/test_tracking.py#L21), tot regel 44.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval actual bytetrack indexes low confidence and empty updates. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `ByteTrackAdapter`, `fresh.update`, `item`, `load_tracker_config`, `pytest.approx`, `tracker.update`.

### test_tracking_excludes_off_field_players_and_all_other_roles_inside_field

Vindplaats: [tests/test_tracking.py regel 47](../tests/test_tracking.py#L47), tot regel 65.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval tracking excludes off field players and all other roles inside field. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `ByteTrackAdapter`, `item`, `load_tracker_config`, `tracker.update`.

### test_observed_trajectories_keep_gaps_and_expire

Vindplaats: [tests/test_tracking.py regel 68](../tests/test_tracking.py#L68), tot regel 76.
Argumenten: `()`. Retourtypehint: `niet opgegeven`.
Controleert het geval observed trajectories keep gaps and expire. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `Trajectories`, `history.segments`, `history.update`, `item`.
Technische leespunten: lus.

## tests/test_video.py

Testmodule voor video

Bron: [tests/test_video.py](../tests/test_video.py).

### payload

Vindplaats: [tests/test_video.py regel 7](../tests/test_video.py#L7), tot regel 13.
Argumenten: `(timestamps)`. Retourtypehint: `niet opgegeven`.
Technische leespunten: return.

### test_variable_framerate_rejected_even_if_nominal_rate_is_25

Vindplaats: [tests/test_video.py regel 16](../tests/test_video.py#L16), tot regel 21.
Argumenten: `(tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval variable framerate rejected even if nominal rate is 25. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `monkeypatch.setattr`, `path.write_bytes`, `payload`, `pytest.raises`, `video.inspect_video`.
Technische leespunten: with-context.

### test_frame_size_change_rejected

Vindplaats: [tests/test_video.py regel 24](../tests/test_video.py#L24), tot regel 31.
Argumenten: `(tmp_path, monkeypatch)`. Retourtypehint: `niet opgegeven`.
Controleert het geval frame size change rejected. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `monkeypatch.setattr`, `path.write_bytes`, `payload`, `pytest.raises`, `video.inspect_video`.
Technische leespunten: with-context.

## tests/test_video_and_mapping.py

Testmodule voor video and mapping

Bron: [tests/test_video_and_mapping.py](../tests/test_video_and_mapping.py). Lokale wijzigingen of nog niet gecommit bij het samenstellen. Deze bron is niet door het publiceren van de uitleg automatisch meegecommit.

### VideoTests

Vindplaats: [tests/test_video_and_mapping.py regel 12](../tests/test_video_and_mapping.py#L12), tot regel 115.
Class die toestand of een vaste gegevensstructuur groepeert. Overerving: TempCase.

### VideoTests.setUp

Vindplaats: [tests/test_video_and_mapping.py regel 13](../tests/test_video_and_mapping.py#L13), tot regel 28.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Lees verder bij aanroepen: `Fraction`, `av.VideoFrame.from_ndarray`, `av.open`, `enumerate`, `np.full`, `out.add_stream`, `out.mux`, `str`, `stream.encode`, `super`, `super().setUp`.
Technische leespunten: with-context, lus.

### VideoTests.test_actual_variable_presentation_times_are_preserved

Vindplaats: [tests/test_video_and_mapping.py regel 30](../tests/test_video_and_mapping.py#L30), tot regel 35.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval actual variable presentation times are preserved. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `frames`, `list`, `self.assertAlmostEqual`, `self.assertEqual`, `zip`.
Technische leespunten: lus.

### VideoTests.test_inspection_records_vfr_intervals

Vindplaats: [tests/test_video_and_mapping.py regel 37](../tests/test_video_and_mapping.py#L37), tot regel 41.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval inspection records vfr intervals. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `inspect_video`, `self.assertEqual`, `self.assertFalse`.

### VideoTests.test_extraction_does_not_renumber_source_frames

Vindplaats: [tests/test_video_and_mapping.py regel 43](../tests/test_video_and_mapping.py#L43), tot regel 50.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval extraction does not renumber source frames. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(self.root / 'dataset/labels').exists`, `all`, `extract`, `read_json`, `self.assertEqual`, `self.assertFalse`, `self.assertTrue`, `write_json`.

### VideoTests.test_extraction_rejects_overlapping_windows

Vindplaats: [tests/test_video_and_mapping.py regel 52](../tests/test_video_and_mapping.py#L52), tot regel 58.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval extraction rejects overlapping windows. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `extract`, `self.assertRaises`, `write_json`.
Technische leespunten: with-context.

### VideoTests.test_mapping_uses_semantics_instead_of_local_ids

Vindplaats: [tests/test_video_and_mapping.py regel 60](../tests/test_video_and_mapping.py#L60), tot regel 64.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval mapping uses semantics instead of local ids. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `SimpleNamespace`, `class_mapping`, `self.assertEqual`, `write_json`.

### VideoTests.test_mapping_rejects_unavailable_model_class

Vindplaats: [tests/test_video_and_mapping.py regel 66](../tests/test_video_and_mapping.py#L66), tot regel 70.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval mapping rejects unavailable model class. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `SimpleNamespace`, `class_mapping`, `self.assertRaises`, `write_json`.
Technische leespunten: with-context.

### VideoTests.test_split_covers_every_source_frame_and_keeps_short_remainder

Vindplaats: [tests/test_video_and_mapping.py regel 72](../tests/test_video_and_mapping.py#L72), tot regel 101.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval split covers every source frame and keeps short remainder. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `abs`, `av.VideoFrame.from_ndarray`, `av.open`, `frames`, `list`, `list(frames(self.root / 'clips' / c['file']))[0][2].getpixel`, `np.full`, `out.add_stream`, `out.mux`, `range`, `read_json`, `self.assertAlmostEqual`, `self.assertEqual`, `self.assertLess`, `self.assertRaises`, `self.assertTrue`, `sources.mkdir`, `split_videos` en andere aanroepen.
Technische leespunten: with-context, lus.

### VideoTests.test_combined_selection_preserves_source_identity_and_splits

Vindplaats: [tests/test_video_and_mapping.py regel 103](../tests/test_video_and_mapping.py#L103), tot regel 115.
Argumenten: `(self)`. Retourtypehint: `niet opgegeven`.
Controleert het geval combined selection preserves source identity and splits. De test is geen onafhankelijke echte modelbenchmark.
Lees verder bij aanroepen: `(self.root / 'combined' / frame['image']).is_file`, `(self.root / 'combined' / frame['label']).exists`, `prepare_sources`, `read_json`, `self.assertEqual`, `self.assertFalse`, `self.assertTrue`, `str`, `write_json`.

# PowerShell starters

## Run-BallExperiment.ps1

Stuurt een baltraining of evaluatie aan.

Bron: [scripts/Run-BallExperiment.ps1](../scripts/Run-BallExperiment.ps1).

## Setup-Persoon1.ps1

Bereidt Pythonomgeving, PyTorch-build en appdependencies voor.

Bron: [scripts/Setup-Persoon1.ps1](../scripts/Setup-Persoon1.ps1).

## setup_tools.ps1

Haalt FFmpeg en ffprobe naar de lokale toolmap.

Bron: [scripts/setup_tools.ps1](../scripts/setup_tools.ps1).

## Start-Cursus.ps1

Eenvoudige P004-route met handmatige kalibratie; CheckOnly voert geen inference uit.

Bron: [scripts/Start-Cursus.ps1](../scripts/Start-Cursus.ps1).

## Start-FootballAnnotations.ps1

Start de lokale voetbalannotatieworkflow.

Bron: [scripts/Start-FootballAnnotations.ps1](../scripts/Start-FootballAnnotations.ps1).

## Start-Persoon1.ps1

Bedient de oorspronkelijke data-/modelworkflow.

Bron: [scripts/Start-Persoon1.ps1](../scripts/Start-Persoon1.ps1).

## Start-Spelermodel.ps1

Start app, annotatie, validatie, training of evaluatie volgens Mode.

Bron: [scripts/Start-Spelermodel.ps1](../scripts/Start-Spelermodel.ps1).

## Start-Wedstrijd.ps1

Gecombineerde rolpipeline met automatische veldruntime.

Bron: [scripts/Start-Wedstrijd.ps1](../scripts/Start-Wedstrijd.ps1).

## Train-RollenTeams.ps1

Start de afzonderlijke rol-/teamtraining vanuit een eerdere backbone.

Bron: [scripts/Train-RollenTeams.ps1](../scripts/Train-RollenTeams.ps1).


# Configuraties en datasets

configs/models*.json kiezen gewichten, klassen en inferentie-instellingen. configs/train*.json kiezen trainingsinstellingen. configs/bytetrack.yaml kiest trackergrenzen. Selectieplannen leggen bronmomenten en subsets vast. De datasetmanifesten leggen frames, labels, bronhashes en reviewstatus vast. Deze gegevensbestanden bevatten geen Pythonfuncties, maar sturen de werking wel aan.

Dekking van de Pythonindex: 84 bestanden, 437 functies en methoden en 31 classes. Daarvan staan 203 definities onder tests. De index wordt zonder importeren of uitvoeren van de ML-modules opgebouwd.
