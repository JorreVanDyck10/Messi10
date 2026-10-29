# Codekaart: alle codebestanden

Lees eerst [Code begrijpen en verdedigen](Code_en_Verdediging.md). Deze kaart legt per bestand
de rol vast en noemt de daadwerkelijk aanwezige functies/klassen en lokale afhankelijkheden.
Bij scripts met een oorspronkelijke Engelse moduleuitleg blijft die technische samenvatting zichtbaar.
Functienamen zijn navigatiehulp; een lijst met namen vervangt het lezen van de implementatie niet.

Dekking: **295 codebestanden**, inclusief tests, datasethelpers en historische bronkopieën.
Niet-gevolgde virtuele omgevingen, externe modelrepositories en gegenereerde uitvoer horen hier niet bij.
Inline JavaScript van de puntenkiezer staat in `point_picker.py` en schaalt klikposities terug naar bronpixels.

Werk bij met `python scripts/build_code_guide.py`. `--check` controleert of de kaart actueel is.

## Leesroute voor de demonstratie

`Start-School.ps1` → `streamlit_app.py` → `pipeline.process_video` → `detection` + `geometry`
→ optioneel `tracking`/`teams` → `render` + `video.VideoWriter`.
`contracts.py` beschrijft de gegevens die tussen deze stappen worden uitgewisseld.

## Toepassing en uitbreidingen

De bibliotheek die interface en CLI aanroepen.

### [src/football_pipeline/__init__.py](../src/football_pipeline/__init__.py)

Bibliotheek voor voetbalvideoanalyse, los van de Streamlit-interface.

### [src/football_pipeline/__main__.py](../src/football_pipeline/__main__.py)

Start de commandoregelinterface via python -m football_pipeline.

Lokale koppelingen: `.cli`.

### [src/football_pipeline/app_results.py](../src/football_pipeline/app_results.py)

Toont opgeslagen analysevideo, instellingen en uitvoerbestanden in de interface.

Topniveaufuncties en klassen: `linked_result`, `show_result`, `show_details`.

Lokale koppelingen: `.contracts`, `.distance_ui`, `.field_review_ui`, `.pipeline`, `.team_ui`.

### [src/football_pipeline/appearance.py](../src/football_pipeline/appearance.py)

Verfijnt persoonsrollen op beeldcrops met een getrainde classifier; veldpositie is een afzonderlijke informatiebron.

Topniveaufuncties en klassen: `crop_tensor`, `jersey_feature`, `backbone`, `AppearanceClassifier`.

Lokale koppelingen: `.contracts`, `.geometry`, `.teams`.

### [src/football_pipeline/automatic_analysis_ui.py](../src/football_pipeline/automatic_analysis_ui.py)

Verbindt upload, automatische verwerking en resultaatweergave in de Streamlit-app.

Topniveaufuncties en klassen: `automatic_analysis`.

Lokale koppelingen: `.app_results`, `.contracts`, `.detection`, `.pipeline`, `.teams`, `.video`.

### [src/football_pipeline/automatic_calibration.py](../src/football_pipeline/automatic_calibration.py)

Leest veldwaarnemingen per frame en berekent bijbehorende projecties. Het neurale veldmodel draait in een apart proces met eigen dependencies.

Topniveaufuncties en klassen: `transform`, `estimate_frame`, `AutomaticCalibration`, `load_automatic_calibration`, `project_automatic`, `prepare_automatic_calibration`.

Lokale koppelingen: `.contracts`, `.field_bounds`, `.field_layout`, `.field_motion`, `.geometry`, `.pipeline`, `.video`.

### [src/football_pipeline/ball_tiles.py](../src/football_pipeline/ball_tiles.py)

Detecteert kleine ballen in overlappende beeldtegels. Boxen gaan terug naar bronpixels en globale NMS verwijdert dubbele tegelvoorspellingen.

Topniveaufuncties en klassen: `axis_starts`, `tile_windows`, `validate_ball_tile_config`, `predict_multiscale_ball`, `merge_ball_predictions`, `predict_ball_tiles`.

### [src/football_pipeline/broadcast_context_training.py](../src/football_pipeline/broadcast_context_training.py)

Traint aanvullende rolcontext op vooraf vastgelegde broadcasttrainingsbeelden.

Topniveaufuncties en klassen: `features`, `train`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.broadcast_refine`, `football_pipeline.contracts`, `football_pipeline.role_context`, `football_pipeline.video`.

### [src/football_pipeline/broadcast_data.py](../src/football_pipeline/broadcast_data.py)

Zet broadcastproviderlabels om naar ontwikkeldata en behoudt rollen, teams en brontracks.

Topniveaufuncties en klassen: `labelled_people`, `prepare`.

Lokale koppelingen: `.contracts`, `.course_dataset`, `.research_archive`, `.video`.

### [src/football_pipeline/broadcast_dataset.py](../src/football_pipeline/broadcast_dataset.py)

Bouwt en controleert een hervatbare broadcastdataset uit SoccerNet-providerlabels.

Topniveaufuncties en klassen: `unpack_member`, `MemberArchive`, `load_clip`, `eligible_images`, `choose_frames`, `prepare_frame`, `audit`, `prepare`, `_prepare`, `main`.

Lokale koppelingen: `.contracts`, `.course_dataset`, `.research_archive`, `persoon1.core`.

### [src/football_pipeline/broadcast_detector_refine.py](../src/football_pipeline/broadcast_detector_refine.py)

Traint de speler-/scheidsrechterdetector verder met gedetailleerde persoonsvoorbeelden.

Topniveaufuncties en klassen: `initialize_two_roles`, `train`.

Lokale koppelingen: `.contracts`, `.training_budget`, `.video`.

### [src/football_pipeline/broadcast_evaluation.py](../src/football_pipeline/broadcast_evaluation.py)

Meet afzonderlijke detectie-, rol- en teamstappen en registreert waar de referentiegeometrie vandaan komt.

Topniveaufuncties en klassen: `reference_geometry`, `evaluate_profile`.

Lokale koppelingen: `.automatic_calibration`, `.contracts`, `.detection`, `.kit_embedding`, `.teams`, `persoon1.metrics`.

### [src/football_pipeline/broadcast_multisource_training.py](../src/football_pipeline/broadcast_multisource_training.py)

Combineert aanvullende voetbalbronnen voor fine-tuning en controleert de dataset vóór training.

Topniveaufuncties en klassen: `validate_dataset`, `train`.

Lokale koppelingen: `.contracts`, `.sportsmot_data`, `.training_budget`, `.video`.

### [src/football_pipeline/broadcast_observed_context.py](../src/football_pipeline/broadcast_observed_context.py)

Leert rolcontext uit echte detectorcrops die aan providerlabels zijn gekoppeld.

Topniveaufuncties en klassen: `matched_targets`, `scene_features`, `collect`, `train`.

Lokale koppelingen: `.automatic_calibration`, `.broadcast_evaluation`, `.contracts`, `.detection`, `.role_context`, `.video`.

### [src/football_pipeline/broadcast_refine.py](../src/football_pipeline/broadcast_refine.py)

Voert aanvullende trainingen voor veldrollen, shirtkenmerken en detectie uit.

Topniveaufuncties en klassen: `pretrained_person_weights`, `crop_cache`, `roles`, `teams`, `detector`.

Lokale koppelingen: `.appearance`, `.broadcast_training`, `.contracts`, `.training_budget`, `.video`, `persoon1.role_training`.

### [src/football_pipeline/broadcast_release.py](../src/football_pipeline/broadcast_release.py)

Vergelijkt broadcastkandidaten en verpakt geselecteerde modelprofielen met meetrapporten.

Topniveaufuncties en klassen: `build_profile`, `candidate_score`, `evaluation_directory`, `compare_and_package`, `demonstrate`, `write_card`, `write_report`.

Lokale koppelingen: `.automatic_calibration`, `.broadcast_evaluation`, `.broadcast_training`, `.contracts`, `.pipeline`, `.teams`, `.video`.

### [src/football_pipeline/broadcast_resume.py](../src/football_pipeline/broadcast_resume.py)

Inspecteert of hervat bestaande broadcastwerkstappen zonder voltooide resultaten opnieuw te trainen.

Topniveaufuncties en klassen: `status`, `download`, `training`.

Lokale koppelingen: `.contracts`, `.sportsmot_data`, `.video`.

### [src/football_pipeline/broadcast_training.py](../src/football_pipeline/broadcast_training.py)

Voert begrensde speler-, rol- en teamtraining uit op vastgelegde wedstrijdsplits.

Topniveaufuncties en klassen: `sample_rows`, `features`, `train_roles`, `team_metrics`, `team_selection_score`, `train_teams`, `run`.

Lokale koppelingen: `.appearance`, `.contracts`, `.course_experiments`, `.kit_embedding`, `.training_budget`, `.video`, `.video_teams`, `persoon1.role_training`.

### [src/football_pipeline/calibration_evaluation.py](../src/football_pipeline/calibration_evaluation.py)

Vergelijkt automatische veldprojecties met afzonderlijk gereviewde menselijke referentiepunten.

Topniveaufuncties en klassen: `evaluate_calibration`.

Lokale koppelingen: `.automatic_calibration`, `.contracts`, `.pipeline`.

### [src/football_pipeline/calibration_input.py](../src/football_pipeline/calibration_input.py)

Levert bekende veldcoördinaten voor aangeklikte punten, waaronder een gedeeltelijk zichtbaar strafschopgebied.

Topniveaufuncties en klassen: `penalty_area_points`, `point_label`, `panoris_point_suggestion`.

Lokale koppelingen: `.contracts`, `.video`.

### [src/football_pipeline/cli.py](../src/football_pipeline/cli.py)

Verwerkt commandoregelargumenten en roept inspectie, verwerking en evaluatie aan.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `.automatic_calibration`, `.calibration_evaluation`, `.contracts`, `.demo`, `.evaluation`, `.geometry`, `.model_handoff`, `.pipeline`, `.video`.

### [src/football_pipeline/contracts.py](../src/football_pipeline/contracts.py)

Definieert de gedeelde gegevensstructuren voor video, detecties en frames. JSON en hashes maken opgeslagen resultaten controleerbaar.

Topniveaufuncties en klassen: `PipelineError`, `sha256_file`, `digest_json`, `read_json`, `write_json`, `atomic_replace`, `VideoMetadata`, `Detection`, `FrameRecord`, `RunResult`.

Lokale koppelingen: `.participants`.

### [src/football_pipeline/course_dataset.py](../src/football_pipeline/course_dataset.py)

Maakt wedstrijdgescheiden ontwikkeldata uit providerannotaties voor de cursusproeven.

Topniveaufuncties en klassen: `archive_url`, `catalog`, `select_games`, `selected_clips`, `object_labels`, `prepare`.

Lokale koppelingen: `.contracts`, `.research_archive`.

### [src/football_pipeline/course_experiments.py](../src/football_pipeline/course_experiments.py)

Vergelijkt transferlearninginstellingen op dezelfde vastgelegde ontwikkeldata.

Topniveaufuncties en klassen: `timestamp`, `evaluate_model`, `train_candidate`, `run`.

Lokale koppelingen: `.contracts`, `.course_dataset`, `.training_budget`, `.video`, `persoon1.metrics`.

### [src/football_pipeline/course_field_evaluation.py](../src/football_pipeline/course_field_evaluation.py)

Selecteert veldinstellingen op trainingswedstrijden en vergelijkt geometrie op andere validatiewedstrijden.

Topniveaufuncties en klassen: `score`, `observations_for`, `improves_geometry`, `compare`.

Lokale koppelingen: `.contracts`, `.field_learning`, `.field_line_geometry`, `.field_motion`.

### [src/football_pipeline/demo.py](../src/football_pipeline/demo.py)

Maakt synthetische beelden voor softwarecontroles. Deze fixtures meten geen herkenningskwaliteit op echte voetbalwedstrijden.

Topniveaufuncties en klassen: `default_points`, `SyntheticDetector`, `generate_demo`.

Lokale koppelingen: `.contracts`, `.geometry`, `.video`.

### [src/football_pipeline/detection.py](../src/football_pipeline/detection.py)

Laadt expliciete modelprofielen en zet YOLO-uitvoer om naar gedeelde Detection-objecten. Optionele rol- en shirtmodellen verfijnen die uitvoer.

Topniveaufuncties en klassen: `load_model_manifest`, `available_roles`, `player_detection_sources`, `merge_person_proposals`, `prefer_person_geometry`, `validate_detection_devices`, `UltralyticsDetector`.

Lokale koppelingen: `.appearance`, `.ball_tiles`, `.contracts`, `.kit_embedding`, `.participants`, `.role_context`, `.teams`.

### [src/football_pipeline/distance_ui.py](../src/football_pipeline/distance_ui.py)

Toont afstandsschattingen uit opgeslagen waarnemingen zonder detectie opnieuw uit te voeren.

Topniveaufuncties en klassen: `distance_tables`, `show_distances`, `distance_panel`.

Lokale koppelingen: `.contracts`, `.distances`.

### [src/football_pipeline/distances.py](../src/football_pipeline/distances.py)

Schat waargenomen afstanden op basis van geldige veldposities. Ontbrekende frames en cameraresets onderbreken een meettraject.

Topniveaufuncties en klassen: `DistanceSettings`, `recorded_dimensions`, `estimate_distances`.

Lokale koppelingen: `.contracts`, `.participants`.

### [src/football_pipeline/evaluation.py](../src/football_pipeline/evaluation.py)

Koppelt voorspelde boxen aan trackingreferenties en telt projectgebonden fouten; dit is geen officiële MOT-metriekimplementatie.

Topniveaufuncties en klassen: `iou_matrix`, `evaluate_frames`, `evaluate_run`.

Lokale koppelingen: `.contracts`, `.pipeline`.

### [src/football_pipeline/field_bounds.py](../src/football_pipeline/field_bounds.py)

Berekent het zichtbare veldgebied in bronpixels en controleert of voetpunten daarin liggen.

Topniveaufuncties en klassen: `visible_field_polygon`, `contains_footpoint`, `attach_visible_field`.

### [src/football_pipeline/field_comparison.py](../src/football_pipeline/field_comparison.py)

Vergelijkt veldkandidaten en registreert voorwaarden voor ingebruikname.

Topniveaufuncties en klassen: `summarize_field_records`, `evaluate_field_records`, `release_decision`.

Lokale koppelingen: `.automatic_calibration`, `.contracts`, `.field_review`.

### [src/football_pipeline/field_data.py](../src/football_pipeline/field_data.py)

Verzamelt begrensde veldtrainingsdata en bewaart broninformatie, wedstrijdsplits en duplicaatcontroles.

Topniveaufuncties en klassen: `CorpusBudget`, `download`, `extract_archive`, `collect_dataset`, `match_split`, `identify_match`, `discover_highlights`, `collect_highlights`, `frame_signature`, `near_duplicate`, `sampled_frames`, `prepare_frames`, `main`.

Lokale koppelingen: `.contracts`, `.video`.

### [src/football_pipeline/field_layout.py](../src/football_pipeline/field_layout.py)

Legt de semantische veldpunten en lijnen van het aangenomen 105 × 68-meter-template vast.

Lokale koppelingen: `.field_model_spec`.

### [src/football_pipeline/field_learning.py](../src/football_pipeline/field_learning.py)

Traint en vergelijkt de PnLCalib-punten- en lijnnetwerken; voorstellen blijven onderscheiden van gereviewde labels.

Topniveaufuncties en klassen: `timestamp`, `validate_labels`, `clip_provider_lines`, `labels_for_row`, `dataset_index`, `upstream_runtime`, `load_model`, `read_yaml`, `masked_heatmap_loss`, `FieldDataset`, `atomic_torch_save`, `publish_epoch_checkpoint`, `run_epoch`, `_train`, `train`, `make_runtime`, `image_observation`, `_propose`, `propose`, `reprojection_metrics`, `_compare`, `compare`, `main`.

Lokale koppelingen: `.automatic_calibration`, `.contracts`, `.field_data`, `.field_layout`, `.field_model_spec`, `.field_motion`, `.video`.

### [src/football_pipeline/field_lens.py](../src/football_pipeline/field_lens.py)

Schat optionele lenscorrectie uit witte lijnen en controleert die op apart gehouden lijnen.

Topniveaufuncties en klassen: `validate_lens`, `lens_scale`, `rectify_points`, `distort_points`, `_maps`, `rectify_image`, `thin`, `white_chains`, `line_rmse`, `estimate_lens`.

### [src/football_pipeline/field_line_experiment.py](../src/football_pipeline/field_line_experiment.py)

Vergelijkt een alternatieve veldprojectie uit lijnen op bevroren modelwaarnemingen.

Topniveaufuncties en klassen: `compare`.

Lokale koppelingen: `.contracts`, `.course_field_evaluation`, `.field_learning`, `.field_motion`.

### [src/football_pipeline/field_line_geometry.py](../src/football_pipeline/field_line_geometry.py)

Berekent een experimentele homography uit semantische lijnen en houdt punten apart als controle.

Topniveaufuncties en klassen: `line_inverse`, `estimate_from_lines`.

Lokale koppelingen: `.automatic_calibration`, `.field_layout`, `.field_motion`.

### [src/football_pipeline/field_model_spec.py](../src/football_pipeline/field_model_spec.py)

Legt veldmodelherkomst en runtimecontroles vast zonder zware ML-imports tijdens installatie.

Topniveaufuncties en klassen: `validate_runtime_models`.

### [src/football_pipeline/field_motion.py](../src/football_pipeline/field_motion.py)

Controleert veldgeometrie en overbrugt korte uitval met gemeten camerabeweging en begrensde geldigheid.

Topniveaufuncties en klassen: `validate_settings`, `_spread`, `checked_matrix`, `line_checks`, `estimate_checked`, `LegacyCameraCalibration`, `CameraCalibration`, `status_label`.

Lokale koppelingen: `.automatic_calibration`, `.contracts`, `.field_bounds`, `.field_layout`.

### [src/football_pipeline/field_pose.py](../src/football_pipeline/field_pose.py)

Voert veldpuntinferentie uit met herleidbare bronpixelcoördinaten en optionele lenscorrectie.

Topniveaufuncties en klassen: `field_crop`, `validate_pose_runtime`, `FieldPoseEstimator`.

Lokale koppelingen: `.contracts`, `.field_layout`, `.field_lens`, `.field_motion`.

### [src/football_pipeline/field_pose_dataset.py](../src/football_pipeline/field_pose_dataset.py)

Zet providerlijnen om naar veldpunttrainingsdata met gescheiden wedstrijden.

Topniveaufuncties en klassen: `flip_indices`, `worker_initialize`, `targets`, `match_key`, `prepare`.

Lokale koppelingen: `.contracts`, `.field_layout`, `.field_learning`.

### [src/football_pipeline/field_pose_training.py](../src/football_pipeline/field_pose_training.py)

Traint een YOLO-veldpuntenmodel via transfer learning op vastgelegde providerannotaties.

Topniveaufuncties en klassen: `train`.

Lokale koppelingen: `.contracts`, `.pipeline`.

### [src/football_pipeline/field_review.py](../src/football_pipeline/field_review.py)

Slaat menselijke veldreferenties afzonderlijk van modelvoorspellingen op.

Topniveaufuncties en klassen: `failure_intervals`, `save_review`, `finalize_review`.

Lokale koppelingen: `.contracts`, `.field_layout`.

### [src/football_pipeline/field_review_ui.py](../src/football_pipeline/field_review_ui.py)

Toont bronframe, veldprojectie en minimap op hetzelfde tijdstip voor visuele review.

Topniveaufuncties en klassen: `review_records`, `source_frame`, `visual_review`.

Lokale koppelingen: `.calibration_evaluation`, `.calibration_input`, `.contracts`, `.field_layout`, `.field_motion`, `.field_review`, `.pipeline`, `.point_picker`, `.render`, `.video`.

### [src/football_pipeline/geometry.py](../src/football_pipeline/geometry.py)

Berekent een handmatige homography en projecteert boxvoetpunten naar het vlakke veld. Onafhankelijke controlepunten toetsen de aangeklikte koppelingen.

Topniveaufuncties en klassen: `CalibrationControlError`, `point_coordinate_issues`, `Calibration`, `create_calibration`, `valid_box`, `project_detection`.

Lokale koppelingen: `.contracts`.

### [src/football_pipeline/joint_data.py](../src/football_pipeline/joint_data.py)

Past lokale datasets aan voor de gezamenlijke taken, met behoud van labels en bronsplits.

Topniveaufuncties en klassen: `names_of`, `unique_rows`, `load_boxes`, `gather_frames`, `link_file`, `detector_dataset`, `write_yaml`, `ball_dataset`, `role_dataset`, `unique_role_pixels`, `prepare_role_pixel_overlay`, `check_split_leakage`, `field_dataset`, `prepare`.

Lokale koppelingen: `.appearance`, `.ball_tiles`, `.contracts`, `.field_learning`, `.video`, `persoon1.modeling`.

### [src/football_pipeline/joint_field.py](../src/football_pipeline/joint_field.py)

Traint een begrensd deel van het veldmodel en vergelijkt de verkregen checkpoints.

Topniveaufuncties en klassen: `train`, `compare_trained_checkpoints`, `compare`.

Lokale koppelingen: `.contracts`, `.field_learning`, `.field_motion`, `.training_budget`.

### [src/football_pipeline/joint_report.py](../src/football_pipeline/joint_report.py)

Schrijft het gezamenlijke rapport uit werkelijk opgeslagen trainings- en demonstratieresultaten.

Topniveaufuncties en klassen: `write_report`.

Lokale koppelingen: `.contracts`, `.video`.

### [src/football_pipeline/joint_training.py](../src/football_pipeline/joint_training.py)

Orkestreert gezamenlijke training, kandidaatselectie en demonstratie van de afzonderlijke deelsystemen.

Topniveaufuncties en klassen: `choose_player`, `choose_roles`, `choose_ball`, `choose_field`, `players`, `roles`, `refit_role_pixels`, `evaluate_ball`, `ball`, `field`, `stage`, `make_profile`, `demonstrate`, `field_coverage`, `run`.

Lokale koppelingen: `.automatic_calibration`, `.ball_tiles`, `.contracts`, `.course_experiments`, `.detection`, `.field_motion`, `.joint_data`, `.joint_report`, `.pipeline`, `.training_budget`, `.video`, `persoon1.metrics`, `persoon1.modeling`, `persoon1.role_training`.

### [src/football_pipeline/kit_embedding.py](../src/football_pipeline/kit_embedding.py)

Leert shirtkenmerken uit paren van hetzelfde of verschillende teams; teamnamen blijven wedstrijdafhankelijk.

Topniveaufuncties en klassen: `projection_head`, `KitEmbedding`, `dominant_teams`, `PitchTeamSamples`, `embedding_candidate`.

Lokale koppelingen: `.appearance`, `.contracts`, `.teams`, `.video_teams`.

### [src/football_pipeline/model_handoff.py](../src/football_pipeline/model_handoff.py)

Registreert modelprofielen met expliciete bronklassen en herkomst voor overdracht naar de toepassing.

Topniveaufuncties en klassen: `available_model_profiles`, `register_player_model`.

Lokale koppelingen: `.contracts`, `.detection`.

### [src/football_pipeline/participants.py](../src/football_pipeline/participants.py)

Houdt modelrollen, veldgeldigheid, zichtbaarheid en spelertelling gescheiden. Een persoon op het veld is niet automatisch een speler.

Topniveaufuncties en klassen: `player_exclusion_reason`, `field_exclusion_reason`, `visible_detection`, `field_available`, `count_exclusion_reason`, `counted_as_player`, `normalized_team_id`, `player_summary`.

Lokale koppelingen: `.contracts`, `.geometry`.

### [src/football_pipeline/pipeline.py](../src/football_pipeline/pipeline.py)

Verbindt video-inspectie, detectie, projectie, optionele tracking en uitvoer. Ieder bronframe krijgt één gedeeld gegevensrecord voor beeld en minimap.

Topniveaufuncties en klassen: `code_identity`, `dependencies`, `processing_lock`, `validate_completed`, `accept_mvp`, `check_mvp_acceptance`, `process_video`.

Lokale koppelingen: `.automatic_calibration`, `.contracts`, `.detection`, `.field_motion`, `.geometry`, `.participants`, `.render`, `.replay`, `.team_results`, `.teams`, `.tracking`, `.video`.

### [src/football_pipeline/point_picker.py](../src/football_pipeline/point_picker.py)

Verwerkt klikken in het bronbeeld via een Streamlit-component en bewaart oorspronkelijke pixelcoördinaten.

Topniveaufuncties en klassen: `apply_point_click`, `_register_picker`, `point_picker`.

Lokale koppelingen: `.calibration_input`, `.contracts`.

### [src/football_pipeline/referee_dataset.py](../src/football_pipeline/referee_dataset.py)

Bouwt aanvullende scheidsrechterdata met expliciete negatieve voorbeelden en gescheiden clips.

Topniveaufuncties en klassen: `source_bytes`, `clip_split`, `download_row`, `prepare`.

Lokale koppelingen: `.contracts`, `persoon1.core`.

### [src/football_pipeline/render.py](../src/football_pipeline/render.py)

Tekent detecties en veldposities samen op één uitvoerframe. Beide helften gebruiken hetzelfde FrameRecord en blijven daardoor gesynchroniseerd.

Topniveaufuncties en klassen: `label`, `field_pixel`, `detection_color`, `detection_label`, `render_frame`, `automatic_preview`, `calibration_preview`, `calibration_target_preview`, `calibrated_field_preview`.

Lokale koppelingen: `.automatic_calibration`, `.calibration_input`, `.contracts`, `.field_layout`, `.field_motion`, `.geometry`, `.participants`, `.teams`, `.tracking`.

### [src/football_pipeline/replay.py](../src/football_pipeline/replay.py)

Leest opgeslagen detecties terug om vervolgstappen te herhalen zonder opnieuw YOLO-inferentie te doen.

Topniveaufuncties en klassen: `replay_detections`.

Lokale koppelingen: `.contracts`.

### [src/football_pipeline/research_archive.py](../src/football_pipeline/research_archive.py)

Leest geselecteerde ZIP-onderdelen met gecontroleerde HTTP-rangeverzoeken om volledige corpusdownloads te vermijden.

Topniveaufuncties en klassen: `RangeArchive`.

### [src/football_pipeline/role_context.py](../src/football_pipeline/role_context.py)

Combineert geleerde rolkenmerken met relatieve shirt- en positiecontext voor aanvullende classificatie.

Topniveaufuncties en klassen: `context_features`, `context_head`, `RoleContext`.

Lokale koppelingen: `.contracts`.

### [src/football_pipeline/sportsmot_data.py](../src/football_pipeline/sportsmot_data.py)

Voegt gelabelde voetbalsporters uit SportsMOT toe en bewaart de betekenis van de bronlabels.

Topniveaufuncties en klassen: `football_selection`, `athlete_boxes`, `prepare_football`, `mixed_player_dataset`.

Lokale koppelingen: `.contracts`, `.video`.

### [src/football_pipeline/team_results.py](../src/football_pipeline/team_results.py)

Berekent en bewaart teamuitvoer; correcties maken een afgeleide run met dezelfde waargenomen geometrie en IDs.

Topniveaufuncties en klassen: `fit_team_file`, `render_team_file`, `finish_teams`, `correction_origin`, `validate_corrections`, `apply_team_corrections`.

Lokale koppelingen: `.contracts`, `.participants`, `.pipeline`, `.render`, `.teams`, `.tracking`, `.video`.

### [src/football_pipeline/team_ui.py](../src/football_pipeline/team_ui.py)

Toont teamtellingen en laat expliciete teamcorrecties indienen via Streamlit.

Topniveaufuncties en klassen: `team_tables`, `frame_window`, `count_chart`, `show_teams`.

Lokale koppelingen: `.contracts`, `.field_review_ui`, `.participants`, `.render`, `.team_results`, `.teams`, `.tracking`.

### [src/football_pipeline/teams.py](../src/football_pipeline/teams.py)

Verzamelt shirtwaarnemingen, zoekt twee wedstrijdgebonden teams en stabiliseert toekenningen over de tijd. Bij onvoldoende bewijs blijft het team onbekend.

Topniveaufuncties en klassen: `configured_team_path`, `load_team_settings`, `rgb_to_lab`, `hex_rgb`, `lab_to_hex`, `shirt_color`, `TeamSamples`, `validate_team_model`, `team_context`, `refine_referee_consensus`, `TeamAssigner`.

Lokale koppelingen: `.contracts`, `.geometry`, `.kit_embedding`, `.video`, `.video_teams`.

### [src/football_pipeline/tracking.py](../src/football_pipeline/tracking.py)

Koppelt actuele spelerboxen over opeenvolgende frames met ByteTrack. Een tijdelijk track-ID is geen herkende naam of gegarandeerde identiteit.

Topniveaufuncties en klassen: `load_tracker_config`, `ByteTrackAdapter`, `_IndexedBoxes`, `Trajectories`.

Lokale koppelingen: `.contracts`, `.geometry`, `.participants`, `.tracking_motion`.

### [src/football_pipeline/tracking_motion.py](../src/football_pipeline/tracking_motion.py)

Meet achtergrondbeweging voor cameracompensatie van tracks, onafhankelijk van veldpuntherkenning.

Topniveaufuncties en klassen: `warp_xyah`, `BackgroundMotion`.

Lokale koppelingen: `.geometry`.

### [src/football_pipeline/training_budget.py](../src/football_pipeline/training_budget.py)

Begrenst gezamenlijke training in tijd en controleert het budget tussen optimalisatiestappen.

Topniveaufuncties en klassen: `TrainingBudget`, `train_yolo`, `resume_yolo`.

Lokale koppelingen: `.contracts`.

### [src/football_pipeline/training_status_ui.py](../src/football_pipeline/training_status_ui.py)

Toont opgeslagen trainingsstatus naast de analyse-interface.

Topniveaufuncties en klassen: `show_training_status`.

Lokale koppelingen: `.contracts`.

### [src/football_pipeline/video.py](../src/football_pipeline/video.py)

Controleert videometadata met ffprobe, leest frames met OpenCV en schrijft uitvoer met FFmpeg. De pipeline vereist constante frametiming.

Topniveaufuncties en klassen: `find_tool`, `probe_json`, `inspect_video`, `read_frame`, `tool_versions`, `VideoWriter`.

Lokale koppelingen: `.contracts`.

### [src/football_pipeline/video_teams.py](../src/football_pipeline/video_teams.py)

Groepeert shirtkleuren per video; een nieuwe wedstrijd krijgt eigen teamprototypes.

Topniveaufuncties en klassen: `kit_feature`, `VideoTeams`.

Lokale koppelingen: `.geometry`.

## Data, training en evaluatie

De afzonderlijke datatools en hun commandoregelinterface.

### [persoon1/__init__.py](../persoon1/__init__.py)

Gereedschappen voor herleidbare datasets, modeltraining en detectie-evaluatie.

### [persoon1/__main__.py](../persoon1/__main__.py)

Start de datacommandos via python -m persoon1 en geeft argumenten aan de juiste werkstap door.

Topniveaufuncties en klassen: `parser`, `execute`, `main`.

Lokale koppelingen: `.annotation`, `.core`, `.modeling`, `.video`.

### [persoon1/annotation.py](../persoon1/annotation.py)

Lokale bounding-boxeditor voor labelcorrecties met afzonderlijke voorstellen en reviewstatus.

Topniveaufuncties en klassen: `save_annotation`, `serve`.

Lokale koppelingen: `.core`.

### [persoon1/appearance_evaluation.py](../persoon1/appearance_evaluation.py)

Meet de echte detector-plus-rolclassifier; cropclassificatie blijft onderscheiden van detectie-AP.

Topniveaufuncties en klassen: `run`.

Lokale koppelingen: `.metrics`, `.modeling`, `.role_training`, `football_pipeline.contracts`, `football_pipeline.detection`, `football_pipeline.render`.

### [persoon1/appearance_video_probe.py](../persoon1/appearance_video_probe.py)

Voert een ontwikkelvideo door de herkenningsmodellen zonder ontbrekende veldkalibratie te verzinnen.

Topniveaufuncties en klassen: `run`.

Lokale koppelingen: `.modeling`, `.role_training`, `football_pipeline.contracts`, `football_pipeline.detection`, `football_pipeline.render`, `football_pipeline.video`.

### [persoon1/core.py](../persoon1/core.py)

Controleert datasetmanifesten, labels, bronhashes en reviewvoorwaarden vóór training of evaluatie.

Topniveaufuncties en klassen: `now`, `read_json`, `write_json`, `sha256`, `canonical_hash`, `environment`, `load_manifest`, `dataset_path`, `read_labels`, `label_pixels`, `validate_dataset`, `require_approval`, `require_experiment_data`.

### [persoon1/error_review.py](../persoon1/error_review.py)

Maakt detailbeelden van geselecteerde false positives en false negatives voor foutenanalyse.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `.core`.

### [persoon1/metrics.py](../persoon1/metrics.py)

Berekent boxoverlap, één-op-één klassekoppelingen en AP met 101 recallpunten voor volledig gelabelde beelden.

Topniveaufuncties en klassen: `iou`, `match_class`, `ap101`, `evaluate`.

### [persoon1/modeling.py](../persoon1/modeling.py)

Voert inferentie, fine-tuning en herleidbare evaluatie uit; testdata en reviewstatus krijgen afzonderlijke controles.

Topniveaufuncties en klassen: `yolo`, `fresh_output`, `class_mapping`, `assert_final_access`, `predict_manifest`, `build_yolo_dataset`, `train`, `evaluate_run`.

Lokale koppelingen: `.core`, `.metrics`.

### [persoon1/participant_baseline.py](../persoon1/participant_baseline.py)

Vergelijkt lokalisatie van geannoteerde deelnemers zonder COCO-personen achteraf spelersrollen te geven.

Topniveaufuncties en klassen: `compare`.

Lokale koppelingen: `.core`, `.metrics`, `.modeling`.

### [persoon1/preprocessing_audit.py](../persoon1/preprocessing_audit.py)

Controleert hoeveel echte labels behouden blijven na de geïnstalleerde YOLO-trainingsaugmentaties.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `.core`.

### [persoon1/project_dataset.py](../persoon1/project_dataset.py)

Reconstrueert de voorlopige baldataset uit de exacte bronvideo en expliciete annotaties.

Topniveaufuncties en klassen: `prepare`.

Lokale koppelingen: `.core`.

### [persoon1/review_sheets.py](../persoon1/review_sheets.py)

Maakt overzichtsbladen en detailcrops voor visuele labelreview zonder labels te veranderen.

Topniveaufuncties en klassen: `create_sheets`.

Lokale koppelingen: `.core`.

### [persoon1/role_training.py](../persoon1/role_training.py)

Traint aanvullende rol- en teamkenmerken op gereviewde of expliciet voorlopige ontwikkeldata.

Topniveaufuncties en klassen: `save`, `build`, `scores`, `load_training_manifest`, `supervised_team_videos`, `augment_role_tensor`, `train`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`, `football_pipeline.training_budget`.

### [persoon1/teamtrack_dataset.py](../persoon1/teamtrack_dataset.py)

Zet MOT-persoonsboxen en expliciete rolboxen om naar speler-/scheidsrechterlabels.

Topniveaufuncties en klassen: `build`.

Lokale koppelingen: `.core`, `.review_sheets`.

### [persoon1/technical_check.py](../persoon1/technical_check.py)

Controleert GPU-training met synthetische rechthoeken; resultaten zijn geen voetbalmodelscore.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `.core`, `.modeling`.

### [persoon1/video.py](../persoon1/video.py)

Leest echte presentatietijdstippen met PyAV en kan daardoor ook variabele-frameratebronnen voor data-extractie verwerken.

Topniveaufuncties en klassen: `frames`, `inspect_video`, `extract`.

Lokale koppelingen: `.core`.

## Start-, trainings- en controlescripts

Voer alleen het script voor de bedoelde werkstap uit.

### [scripts/assemble_ball_comparison.py](../scripts/assemble_ball_comparison.py)

Assemble immutable per-frame measurements into one equal-population comparison.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`.

### [scripts/audit_ball_tiles.py](../scripts/audit_ball_tiles.py)

Independently verify derived training pixels and original-ball coordinate matches.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.video`.

### [scripts/audit_broadcast_extensions.py](../scripts/audit_broadcast_extensions.py)

Verify curated ball/referee exports and write their compact, reproducible handoff.

Topniveaufuncties en klassen: `audit`, `main`.

Lokale koppelingen: `football_pipeline.contracts`, `persoon1.core`.

### [scripts/audit_person1_data.py](../scripts/audit_person1_data.py)

Inventory P1 development data and prepare truthful human review, never inspect test pictures.

Topniveaufuncties en klassen: `difference_hash`, `audit_roles`, `audit_detection`, `render_new_role_sheets`, `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.video`, `persoon1.role_training`.

### [scripts/ball_resolution_experiment.py](../scripts/ball_resolution_experiment.py)

Frozen-weight whole-frame versus native/upsampled tile ball comparison.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.ball_tiles`, `football_pipeline.contracts`, `football_pipeline.pipeline`, `football_pipeline.video`, `persoon1.metrics`, `persoon1.modeling`.

### [scripts/broadcast_field_experiment.py](../scripts/broadcast_field_experiment.py)

Frozen, reproducible ablations on the user's development clip; no invented human references.

Topniveaufuncties en klassen: `summarize`, `main`.

Lokale koppelingen: `football_pipeline.automatic_calibration`, `football_pipeline.contracts`, `football_pipeline.field_motion`, `football_pipeline.field_review`, `football_pipeline.pipeline`, `football_pipeline.video`.

### [scripts/build_code_guide.py](../scripts/build_code_guide.py)

Bouw een leeskaart van alle gevolgde code zonder modules te importeren of uit te voeren.

Topniveaufuncties en klassen: `followed_files`, `first_sentence`, `describe`, `fallback_purpose`, `render`, `main`.

### [scripts/build_role_extension.py](../scripts/build_role_extension.py)

Versioned AI crop corrections after explicit visual inspection; no synthetic human review.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`, `football_pipeline.video`, `persoon1.role_training`.

### [scripts/build_role_round3.py](../scripts/build_role_round3.py)

Explicit AI visual decisions for rare-role development; preserves all earlier labels.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.video`, `persoon1.role_training`.

### [scripts/check_partial_calibration.py](../scripts/check_partial_calibration.py)

Audit penalty-area calibration against separate provider goal-area lines.

Topniveaufuncties en klassen: `line`, `intersection`, `required_lines`, `provider_points`, `audit`.

Lokale koppelingen: `football_pipeline.calibration_input`, `football_pipeline.contracts`, `football_pipeline.geometry`, `football_pipeline.render`.

### [scripts/check_team_integration.py](../scripts/check_team_integration.py)

Repeat a real-video engineering check; never substitute model output for human labels.

Topniveaufuncties en klassen: `check_result`, `main`.

Lokale koppelingen: `football_pipeline.automatic_calibration`, `football_pipeline.contracts`, `football_pipeline.pipeline`, `football_pipeline.video`.

### [scripts/Collect-BroadcastData.ps1](../scripts/Collect-BroadcastData.ps1)

Verzamelt en controleert de broadcastdataset.

Parameters: `Dataset`, `TrainCount`, `ValidCount`, `Workers`, `AuditOnly`.

### [scripts/collect_development_candidates.py](../scripts/collect_development_candidates.py)

Collect unlabelled, model-assisted candidates from existing TRAIN groups only.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.detection`, `football_pipeline.video`.

### [scripts/compare_field_reliability.py](../scripts/compare_field_reliability.py)

Prepare, replay and review a field-only v2/v3 comparison without new detection inference.

Topniveaufuncties en klassen: `prepare`, `comparison_canvas`, `run`, `evaluate`, `export_review`, `main`.

Lokale koppelingen: `football_pipeline.automatic_calibration`, `football_pipeline.contracts`, `football_pipeline.field_comparison`, `football_pipeline.field_layout`, `football_pipeline.field_motion`, `football_pipeline.participants`, `football_pipeline.pipeline`, `football_pipeline.render`, `football_pipeline.replay`, `football_pipeline.video`.

### [scripts/curate_broadcast_balls.py](../scripts/curate_broadcast_balls.py)

Deterministic visual review and explicit curation of broadcast ball labels.

Topniveaufuncties en klassen: `prepare`, `render`, `export`.

Lokale koppelingen: `football_pipeline.contracts`.

### [scripts/curate_referee_data.py](../scripts/curate_referee_data.py)

Export explicitly reviewed source clips without changing the published referee corpus.

Topniveaufuncties en klassen: `export`.

Lokale koppelingen: `football_pipeline.contracts`.

### [scripts/evaluate_fullframe_ball.py](../scripts/evaluate_fullframe_ball.py)

Evaluate frozen COCO ball detectors on new, provisional full-frame development labels.

Topniveaufuncties en klassen: `validation_truth`, `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.pipeline`, `football_pipeline.video`, `persoon1.metrics`, `persoon1.modeling`.

### [scripts/evaluate_role_extension.py](../scripts/evaluate_role_extension.py)

Compare two real classifiers on identical conditional crops, never report this as detection AP.

Topniveaufuncties en klassen: `infer`, `summarize`, `cohorts`, `main`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`, `football_pipeline.video`, `persoon1.role_training`.

### [scripts/evaluate_video_teams.py](../scripts/evaluate_video_teams.py)

Development-only colour clustering benchmark on fixed, visually reviewed crops.

Topniveaufuncties en klassen: `run`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.teams`, `football_pipeline.video`.

### [scripts/experiment_broadcast_v2.py](../scripts/experiment_broadcast_v2.py)

Bounded native-ball fine-tuning with frozen, equal-input baseline comparisons.

Topniveaufuncties en klassen: `measured`, `run`.

Lokale koppelingen: `football_pipeline.ball_tiles`, `football_pipeline.contracts`, `persoon1.metrics`.

### [scripts/experiment_broadcast_v3.py](../scripts/experiment_broadcast_v3.py)

One controlled comparison: frozen backbone versus all-layer ball fine-tuning.

Topniveaufuncties en klassen: `run`.

Lokale koppelingen: `football_pipeline.contracts`.

### [scripts/export_person1_handoff.py](../scripts/export_person1_handoff.py)

Real per-detector examples on one identified development video, in original pixels.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.detection`, `football_pipeline.geometry`, `football_pipeline.render`, `football_pipeline.video`, `persoon1.modeling`.

### [scripts/export_tiled_ball_handoff.py](../scripts/export_tiled_ball_handoff.py)

Execute combined roles/teams/tiled balls on real video and verify source coordinates.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.detection`, `football_pipeline.geometry`, `football_pipeline.render`, `football_pipeline.video`.

### [scripts/fetch_role_photos.py](../scripts/fetch_role_photos.py)

Download explicitly selected Commons sources with their attribution metadata.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`.

### [scripts/fetch_role_sources_v3.py](../scripts/fetch_role_sources_v3.py)

Fetch only explicitly selected Commons role-development images and attribution.

Topniveaufuncties en klassen: `plain`, `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.video`.

### [scripts/field_calibration_diagnostic.py](../scripts/field_calibration_diagnostic.py)

Exercise real field weights with artificial camera motion of the upstream example image.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.field_model_spec`, `football_pipeline.pipeline`, `football_pipeline.video`.

### [scripts/field_calibration_pilot.py](../scripts/field_calibration_pilot.py)

Download an attributed development clip, freeze a review selection, and run real field inference.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.automatic_calibration`, `football_pipeline.contracts`, `football_pipeline.pipeline`, `football_pipeline.video`.

### [scripts/field_calibration_worker.py](../scripts/field_calibration_worker.py)

PnLCalib network adapter. Execute with .tools/pnlcalib-env, never the player-training venv.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.automatic_calibration`, `football_pipeline.contracts`, `football_pipeline.field_layout`, `football_pipeline.field_model_spec`.

### [scripts/field_last_checkpoint_candidate.py](../scripts/field_last_checkpoint_candidate.py)

Expose an actual trained last epoch for geometric validation, without altering its loss selection.

Topniveaufuncties en klassen: `extract`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.field_learning`.

### [scripts/field_pose_worker.py](../scripts/field_pose_worker.py)

Write checked, traceable field-pose observations for a complete local video.

Topniveaufuncties en klassen: `run`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.field_layout`, `football_pipeline.field_lens`, `football_pipeline.field_motion`, `football_pipeline.field_pose`.

### [scripts/football48_ball_experiment.py](../scripts/football48_ball_experiment.py)

Reproducible, provisional ball fine-tuning on the delivered football48 crops.

Topniveaufuncties en klassen: `create_coco_view`, `truth_and_identity`, `measure`, `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.pipeline`, `football_pipeline.video`, `persoon1.metrics`, `persoon1.modeling`.

### [scripts/merge_role_heads.py](../scripts/merge_role_heads.py)

Measured head interpolation for identical frozen encoders; never average incompatible features.

Topniveaufuncties en klassen: `blend_role_states`, `main`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`, `persoon1.role_training`.

### [scripts/panoris_pilot.py](../scripts/panoris_pilot.py)

Reproduce the dev-00 pilot; never convert agent measurements into human approvals.

Topniveaufuncties en klassen: `prepare`, `assess_geometry`, `summarize`, `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.geometry`, `football_pipeline.pipeline`, `football_pipeline.render`, `football_pipeline.video`.

### [scripts/prepare_broadcast_v2.py](../scripts/prepare_broadcast_v2.py)

Native ball crops, explicitly reviewed negatives and less redundant player training.

Topniveaufuncties en klassen: `intersect`, `positive_window`, `tile`, `player_selection`, `negatives`, `render_negatives`, `prepare`, `finalize`.

Lokale koppelingen: `football_pipeline.contracts`, `persoon1.core`.

### [scripts/prepare_course_review.py](../scripts/prepare_course_review.py)

Create an editable review copy without changing any frozen experimental labels.

Topniveaufuncties en klassen: `prepare_review`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.video`.

### [scripts/prepare_school_review.py](../scripts/prepare_school_review.py)

Copy 80 ball frames for student review; never overwrite previous labels or reviews.

Topniveaufuncties en klassen: `prepare`.

Lokale koppelingen: `football_pipeline.contracts`.

### [scripts/prioritize_role_review.py](../scripts/prioritize_role_review.py)

Prioritize existing AI-labelled role disagreements without changing truth/review status.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.video`.

### [scripts/propose_role_sources_v3.py](../scripts/propose_role_sources_v3.py)

Assisted-label suggestions for fixed source groups; no prediction is a role label.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.video`, `persoon1.modeling`.

### [scripts/replay_role_training.py](../scripts/replay_role_training.py)

Replay a historical role training with its recorded source and unchanged dataset version.

Topniveaufuncties en klassen: `specification`, `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.video`.

### [scripts/Resume-Broadcast.ps1](../scripts/Resume-Broadcast.ps1)

Toont status of hervat een bestaande broadcastwerkstap.

Parameters: `Action`.

### [scripts/review_broadcast_data.py](../scripts/review_broadcast_data.py)

Create editable review labels and deterministic visual samples of the broadcast corpus.

Topniveaufuncties en klassen: `font`, `audit_field_labels`, `export_participants`, `prepare_review`, `preview`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.field_learning`.

### [scripts/Run-BallExperiment.ps1](../scripts/Run-BallExperiment.ps1)

Voert de afzonderlijke balexperimentworkflow uit.

Parameters: `Resolution`, `Device`, `RunName`, `CandidateWeights`.

### [scripts/Run-BroadcastSpelersTraining.ps1](../scripts/Run-BroadcastSpelersTraining.ps1)

Start begrensde broadcastspelertraining.

Parameters: `Dataset`, `Output`, `Refined`.

### [scripts/Run-CourseImprovement.ps1](../scripts/Run-CourseImprovement.ps1)

Start de cursusgerichte modelvergelijking.

Parameters: `Output`, `PlayerEpochs`, `FieldEpochs`, `FieldHeadEpochs`, `FieldConservativeEpochs`, `FieldBaseline`, `AllowFieldErrorReduction`, `phase`, `python`.

### [scripts/Run-GezamenlijkeTraining.ps1](../scripts/Run-GezamenlijkeTraining.ps1)

Start training en vergelijking van de gezamenlijke deelsystemen.

Parameters: `Dataset`, `Output`.

### [scripts/run_field_training.py](../scripts/run_field_training.py)

Run both networks and then compare, keeping durable status and subprocess logs.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`.

### [scripts/Setup-Persoon1.ps1](../scripts/Setup-Persoon1.ps1)

Bereidt de lokale omgeving van persoon 1 voor.

Parameters: `Python`, `CpuOnly`.

### [scripts/setup_field_model.py](../scripts/setup_field_model.py)

Install only the isolated field-model runtime and official release weights.

Topniveaufuncties en klassen: `checksum`, `run`, `main`.

Lokale koppelingen: `football_pipeline.field_model_spec`.

### [scripts/setup_field_training.py](../scripts/setup_field_training.py)

Extend the pinned inference runtime read-only in an isolated Windows training venv.

Topniveaufuncties en klassen: `main`.

### [scripts/setup_tools.ps1](../scripts/setup_tools.ps1)

Installeert lokale FFmpeg- en ffprobe-tools.

Parameters: `Destination`.

### [scripts/smoke_model.py](../scripts/smoke_model.py)

Exercise actual YOLO inference on a local reference image; this is not a detection evaluation.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.detection`, `football_pipeline.geometry`, `football_pipeline.video`.

### [scripts/Start-Gezamenlijk.ps1](../scripts/Start-Gezamenlijk.ps1)

Start het geselecteerde gezamenlijke modelprofiel.

Parameters: `TrainingRun`, `Port`.

### [scripts/Start-Persoon1.ps1](../scripts/Start-Persoon1.ps1)

Start de commandoregelworkflow voor data, training of evaluatie.

Parameters: `Mode`, `Split`, `Device`, `RunName`, `InferenceSize`, `Port`.

### [scripts/Start-School.ps1](../scripts/Start-School.ps1)

Start de schoolbasis met handmatige kalibratie; optioneel een tegelprofiel.

Parameters: `Device`, `Port`, `BroadcastTiles`, `CheckOnly`.

### [scripts/Start-Spelermodel.ps1](../scripts/Start-Spelermodel.ps1)

Start de toepassing met een expliciete herkenningskeuze.

Parameters: `Mode`, `Device`, `Recognition`, `FieldMode`, `RunName`, `Weights`, `TrainingConfig`.

### [scripts/Start-Wedstrijd.ps1](../scripts/Start-Wedstrijd.ps1)

Start de gezamenlijke wedstrijdworkflow met rollen en uitbreidingen.

Parameters: `Device`, `Recognition`, `FieldRuntime`.

### [scripts/summarize_ball_resolution.py](../scripts/summarize_ball_resolution.py)

Pool full-frame references correctly and separate in-play recall from all-ball AP.

Topniveaufuncties en klassen: `summarize`.

Lokale koppelingen: `football_pipeline.ball_tiles`, `football_pipeline.contracts`, `football_pipeline.video`, `persoon1.metrics`.

### [scripts/Train-RollenTeams.ps1](../scripts/Train-RollenTeams.ps1)

Start aanvullende rol- en teamtraining.

Parameters: `RunName`.

### [scripts/train_fullscene_ball.py](../scripts/train_fullscene_ball.py)

Train a ball specialist on native tiles from the delivered fullscene60 source.

Topniveaufuncties en klassen: `tile_ball_labels`, `build_dataset`, `main`.

Lokale koppelingen: `football_pipeline.ball_tiles`, `football_pipeline.contracts`, `football_pipeline.pipeline`, `football_pipeline.training_budget`, `football_pipeline.video`, `persoon1.modeling`.

### [scripts/verify_broadcast_v2.py](../scripts/verify_broadcast_v2.py)

Verify v2 data, measured improvements and optional model handoff without replacing defaults.

Topniveaufuncties en klassen: `gaps`, `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.detection`.

### [scripts/verify_person1_downloads.py](../scripts/verify_person1_downloads.py)

Fetch the published P1 models/data into a NEW LFS storage and verify actual loads.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`, `football_pipeline.video`, `persoon1.modeling`.

### [scripts/verify_player_pipeline.py](../scripts/verify_player_pipeline.py)

Run real player inference, field projection and video encoding, then audit the result.

Topniveaufuncties en klassen: `verify_records`, `main`.

Lokale koppelingen: `football_pipeline.automatic_calibration`, `football_pipeline.contracts`, `football_pipeline.detection`, `football_pipeline.participants`, `football_pipeline.pipeline`, `football_pipeline.video`.

### [scripts/verify_tiled_runtime.py](../scripts/verify_tiled_runtime.py)

Check that the application path reproduces the measured tiled boxes on real frames.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.detection`.

## Datasetbouwers en labelcontroles

Deze bestanden horen bij de specifieke datasetversie in hun pad.

### [assets/annotations/broadcast-new100/fetch_and_build.py](../assets/annotations/broadcast-new100/fetch_and_build.py)

Rebuild reviewed full-frame annotations from the exact original broadcast clips.

Topniveaufuncties en klassen: `digest`, `write_json`, `yolo_line`, `link_image`, `build`.

### [assets/annotations/football-fullframe40/build_dataset.py](../assets/annotations/football-fullframe40/build_dataset.py)

Reproduce full, untouched frames and saved annotations from the source video.

Topniveaufuncties en klassen: `read`, `write`, `digest`, `export`.

### [assets/annotations/football-fullframe40/make_ball_only.py](../assets/annotations/football-fullframe40/make_ball_only.py)

Export full-frame ball-only training; optionally restrict the target to match ball.

Topniveaufuncties en klassen: `create`.

### [assets/annotations/football-fullframe40/validate_dataset.py](../assets/annotations/football-fullframe40/validate_dataset.py)

Verify native full images, coordinates, file mapping and temporal separation.

Topniveaufuncties en klassen: `validate`.

### [assets/annotations/football-fullscene100/build_dataset.py](../assets/annotations/football-fullscene100/build_dataset.py)

Reproduce full, untouched frames and saved annotations from the source video.

Topniveaufuncties en klassen: `read`, `write`, `digest`, `export`.

### [assets/annotations/football-fullscene100/make_in_play_dataset.py](../assets/annotations/football-fullscene100/make_in_play_dataset.py)

Export full-frame ball-only training; optionally restrict the target to match ball.

Topniveaufuncties en klassen: `create`.

### [assets/annotations/football-fullscene100/validate_dataset.py](../assets/annotations/football-fullscene100/validate_dataset.py)

Verify full-frame identity, annotation exports, new source indices and splits.

Topniveaufuncties en klassen: `validate`.

### [assets/annotations/football-fullscene100/validate_in_play.py](../assets/annotations/football-fullscene100/validate_in_play.py)

Check the generated match-ball view against saved full-scene annotations.

Topniveaufuncties en klassen: `validate`.

### [assets/annotations/football-fullscene100b/build_dataset.py](../assets/annotations/football-fullscene100b/build_dataset.py)

Reproduce full, untouched frames and saved annotations from the source video.

Topniveaufuncties en klassen: `read`, `write`, `digest`, `export`.

### [assets/annotations/football-fullscene100b/make_in_play_dataset.py](../assets/annotations/football-fullscene100b/make_in_play_dataset.py)

Export full-frame ball-only training; optionally restrict the target to match ball.

Topniveaufuncties en klassen: `create`.

### [assets/annotations/football-fullscene100b/validate_dataset.py](../assets/annotations/football-fullscene100b/validate_dataset.py)

Verify full-frame identity, annotation exports, new source indices and splits.

Topniveaufuncties en klassen: `validate`.

### [assets/annotations/football-fullscene100b/validate_in_play.py](../assets/annotations/football-fullscene100b/validate_in_play.py)

Check the generated match-ball view against saved full-scene annotations.

Topniveaufuncties en klassen: `validate`.

### [assets/annotations/football-fullscene16/build_dataset.py](../assets/annotations/football-fullscene16/build_dataset.py)

Reproduce full, untouched frames and saved annotations from the source video.

Topniveaufuncties en klassen: `read`, `write`, `digest`, `export`.

### [assets/annotations/football-fullscene16/validate_dataset.py](../assets/annotations/football-fullscene16/validate_dataset.py)

Verify full-frame identity, annotation exports, new source indices and splits.

Topniveaufuncties en klassen: `validate`.

### [assets/annotations/football-fullscene20/build_dataset.py](../assets/annotations/football-fullscene20/build_dataset.py)

Reproduce full, untouched frames and saved annotations from the source video.

Topniveaufuncties en klassen: `read`, `write`, `digest`, `export`.

### [assets/annotations/football-fullscene20/validate_dataset.py](../assets/annotations/football-fullscene20/validate_dataset.py)

Verify full-frame identity, annotation exports, new source indices and splits.

Topniveaufuncties en klassen: `validate`.

### [assets/annotations/football-fullscene50/build_dataset.py](../assets/annotations/football-fullscene50/build_dataset.py)

Reproduce full, untouched frames and saved annotations from the source video.

Topniveaufuncties en klassen: `read`, `write`, `digest`, `export`.

### [assets/annotations/football-fullscene50/validate_dataset.py](../assets/annotations/football-fullscene50/validate_dataset.py)

Verify full-frame identity, annotation exports, new source indices and splits.

Topniveaufuncties en klassen: `validate`.

### [assets/annotations/football-fullscene60/build_dataset.py](../assets/annotations/football-fullscene60/build_dataset.py)

Reproduce full, untouched frames and saved annotations from the source video.

Topniveaufuncties en klassen: `read`, `write`, `digest`, `export`.

### [assets/annotations/football-fullscene60/make_in_play_dataset.py](../assets/annotations/football-fullscene60/make_in_play_dataset.py)

Export full-frame ball-only training; optionally restrict the target to match ball.

Topniveaufuncties en klassen: `create`.

### [assets/annotations/football-fullscene60/validate_dataset.py](../assets/annotations/football-fullscene60/validate_dataset.py)

Verify full-frame identity, annotation exports, new source indices and splits.

Topniveaufuncties en klassen: `validate`.

### [assets/annotations/football-fullscene60/validate_in_play.py](../assets/annotations/football-fullscene60/validate_in_play.py)

Check the generated match-ball view against saved full-scene annotations.

Topniveaufuncties en klassen: `validate`.

### [assets/annotations/football48/build_clips.py](../assets/annotations/football48/build_clips.py)

Export eight native-resolution, 20-second reference clips from the source.

Topniveaufuncties en klassen: `build`.

### [assets/annotations/football48/build_dataset.py](../assets/annotations/football48/build_dataset.py)

Recreate the fixed dataset from the original video and checked source boxes.

Topniveaufuncties en klassen: `read`, `write`, `digest`, `make_masked_crop`, `export`.

### [assets/annotations/football48/check_clip_alignment.py](../assets/annotations/football48/check_clip_alignment.py)

Check temporal correspondence in lossy reference clips against the source.

Topniveaufuncties en klassen: `check`.

### [assets/annotations/football48/make_ball_only.py](../assets/annotations/football48/make_ball_only.py)

Create a separate one-class view; keeps the original temporal split.

Topniveaufuncties en klassen: `create`.

### [assets/annotations/football48/validate_dataset.py](../assets/annotations/football48/validate_dataset.py)

Check the actual exported images, YOLO labels, COCO and temporal split.

Topniveaufuncties en klassen: `validate`.

### [assets/annotations/panorama128057/apply_annotations.py](../assets/annotations/panorama128057/apply_annotations.py)

Reproduce the saved, visually corrected AI annotations, without model inference.

Lokale koppelingen: `persoon1.annotation`, `persoon1.core`.

### [assets/annotations/panorama128057/recreate_clip.py](../assets/annotations/panorama128057/recreate_clip.py)

Recreate the exact excerpt: python recreate_clip.py /path/to/original.mp4

Lokale koppelingen: `persoon1.core`.

### [assets/annotations/teamtrack0750/apply_annotations.py](../assets/annotations/teamtrack0750/apply_annotations.py)

Reproduce the saved, visually corrected AI annotations, without model inference.

Lokale koppelingen: `persoon1.annotation`, `persoon1.core`.

## Softwaretests

Fixtures en assertions controleren gedrag; ze zijn geen voetbalbenchmark.

### [tests/conftest.py](../tests/conftest.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `video_metadata`, `calibration`, `demo_fixture`, `model_manifest`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.demo`, `football_pipeline.geometry`.

### [tests/test_app.py](../tests/test_app.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_app_initial_screen_and_rerun`, `test_preloaded_calibration_processes_once_on_explicit_click`, `test_point_table_calculation_review_and_invalidation`, `test_image_click_workflow_advances_persists_and_invalidates_draft`, `test_failed_calibration_shows_named_errors_and_persists_until_correction`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.contracts`, `football_pipeline.demo`, `football_pipeline.detection`, `football_pipeline.video`.

### [tests/test_app_player_runtime.py](../tests/test_app_player_runtime.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_player_app_checks_runtime_and_preserves_automatic_tracking_limit`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.video`.

### [tests/test_appearance.py](../tests/test_appearance.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `fixed_classifier`, `person`, `test_trained_role_can_override_player_without_using_field_location`, `test_uncertain_role_abstains_and_new_video_does_not_inherit_supervised_team`, `test_person_proposals_are_merged_without_losing_ball_or_source_identity`, `test_contained_upper_body_uses_strong_full_body_proposal_and_real_feet`, `test_containment_does_not_merge_distinct_overlapping_people`, `test_kit_features_suppress_grey_hue_noise_and_keep_green_clothing`, `test_refining_video_clusters_keeps_team_names_stable`, `test_manifest_pins_appearance_weights_and_capabilities`, `test_new_video_colour_clusters_wait_for_two_kits_and_keep_other_roles_out`, `test_team_counts_and_replay_preserve_appearance_but_recompute_geometry`, `test_tiled_proposals_restore_source_coordinates_and_reject_cut_person_boxes`, `test_changing_video_identity_resets_only_video_local_team_calibration`, `test_role_dataset_builder_never_overwrites_recorded_human_review`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`, `football_pipeline.detection`, `football_pipeline.geometry`, `football_pipeline.participants`, `football_pipeline.replay`, `football_pipeline.teams`, `persoon1`.

### [tests/test_automatic_calibration.py](../tests/test_automatic_calibration.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `observation`, `bundle_for`, `test_pan_zoom_and_missing_corners_use_current_frame_transform`, `test_unreliable_frames_have_no_matrix`, `test_above_ground_points_never_enter_fit`, `test_automatic_projection_rejects_truncated_outside_and_invalid_boxes`, `test_full_pipeline_loss_recovery_artifacts_cache_and_frame_identity`, `test_bundle_rejects_different_video_and_corrupt_observations`, `test_timeline_errors_fail_even_if_bundle_hash_is_updated`, `test_automatic_replay_requires_same_calibration_and_recomputes_positions`, `test_automatic_ui_processes_only_on_click_and_invalidates_when_switching`, `test_independent_evaluation_reports_coverage_and_rejects_unreviewed_labels`, `test_upload_automatically_runs_field_players_tracking_and_does_not_repeat`, `test_automatic_analysis_failure_requires_explicit_retry_and_survives_repeated_failure`, `test_runtime_geometry_policy_is_used_and_explicit_policy_takes_precedence`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.automatic_calibration`, `football_pipeline.contracts`, `football_pipeline.demo`, `football_pipeline.field_layout`, `football_pipeline.pipeline`, `football_pipeline.video`.

### [tests/test_ball_tiles.py](../tests/test_ball_tiles.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_tiles_cover_every_pixel_including_small_and_last_edge`, `test_global_nms_removes_overlap_duplicates_but_preserves_nearby_balls`, `test_tiled_detector_maps_both_axes_to_original_pixels`, `test_training_tiles_cannot_turn_a_cut_ball_into_background`, `test_training_rejects_test_before_opening_images`, `test_manifest_rejects_unbounded_or_ambiguous_tile_work`, `test_runtime_routes_ball_tiles_without_changing_person_path`, `test_ball_tile_manifest_cannot_relabel_a_person`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.ball_tiles`, `football_pipeline.contracts`, `football_pipeline.detection`.

### [tests/test_broadcast_curation.py](../tests/test_broadcast_curation.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `candidates`, `decisions`, `test_curated_export_preserves_source_and_uses_corrected_full_image_coordinates`, `test_incomplete_ball_review_never_publishes_training_config`, `test_changed_review_candidates_and_match_leakage_are_rejected`, `test_auxiliary_referee_split_keeps_clips_together_and_contains_explicit_negatives`, `test_referee_quarantine_removes_whole_clip_and_requires_decisions_for_all_clips`, `test_invalid_ai_corrections_cannot_be_exported`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.referee_dataset`, `persoon1.core`.

### [tests/test_broadcast_dataset.py](../tests/test_broadcast_dataset.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_remote_zip_member_requires_matching_name_size_and_crc`, `clip`, `test_sampling_requires_annotations_and_excludes_ignored_images`, `test_selection_keeps_validation_games_out_of_training_and_samples_all_clips`, `test_selection_can_read_cached_annotations_without_retaining_full_clips`, `test_failed_collection_releases_its_lock_but_does_not_remove_another_writers_lock`, `test_real_image_export_preserves_roles_and_attributes_and_audit_detects_tampering`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.contracts`.

### [tests/test_broadcast_multisource.py](../tests/test_broadcast_multisource.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `dataset`, `test_mixed_training_keeps_original_validation_and_verifies_new_image_bytes`, `test_reserved_sports_split_is_rejected_before_reading_its_image`, `test_mixed_training_cannot_drop_hard_validation_frames`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.contracts`, `football_pipeline.sportsmot_data`.

### [tests/test_broadcast_players.py](../tests/test_broadcast_players.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `player`, `settings`, `test_provider_attributes_follow_annotation_id_and_goalkeepers_remain_players`, `test_pitch_policy_protects_real_players_but_does_not_rename_generic_people`, `test_classification_happens_only_for_people_projected_inside_the_current_field`, `test_outside_proposal_cannot_suppress_an_inside_player_at_the_touchline`, `test_embedding_groups_survive_short_tracks_and_exclude_people_outside_the_field`, `test_bad_embedding_models_are_rejected`, `test_kit_context_requires_trained_roles_valid_field_and_strong_player_prototypes`, `test_pitch_render_hides_external_people_without_mutating_saved_detections`, `test_profile_rejects_unknown_scope_and_role_policy`, `test_team_metric_allows_one_swap_per_clip_not_a_different_swap_every_frame`, `test_reference_geometry_requires_correspondences_and_is_not_an_automatic_field_claim`, `test_team_profile_is_selected_with_the_model_and_respects_explicit_override`, `test_two_overlapping_players_survive_while_duplicate_proposals_still_merge`, `test_nested_partial_box_at_same_feet_does_not_count_a_second_player`, `test_optional_box_fusion_retains_both_actual_sources_and_uses_the_refined_feet`, `test_fused_boxes_are_reprojected_before_crop_and_context_classification`, `test_box_fusion_profile_rejects_unbounded_weights_or_missing_person_geometry`, `test_unreadable_edge_crop_stays_unknown_instead_of_crashing_team_inference`, `test_renaming_teams_does_not_replace_a_valid_embedding_model_with_color_rejection`, `test_role_training_refuses_same_image_in_two_splits_even_if_the_crop_is_duplicate`, `test_three_class_field_checkpoint_uses_its_actual_class_names`, `test_person_geometry_retains_real_source_and_requires_trained_role_evidence`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.appearance`, `football_pipeline.automatic_calibration`, `football_pipeline.broadcast_data`, `football_pipeline.broadcast_evaluation`, `football_pipeline.broadcast_training`, `football_pipeline.contracts`, `football_pipeline.detection`, `football_pipeline.kit_embedding`, `football_pipeline.render`, `football_pipeline.team_results`, `football_pipeline.teams`.

### [tests/test_broadcast_v2.py](../tests/test_broadcast_v2.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_native_window_preserves_the_whole_ball_at_image_edges`, `test_native_window_does_not_silently_resize_small_sources`, `test_negative_candidates_require_complete_review_before_a_training_config_is_published`, `test_finalization_preserves_native_pixels_and_deduplicates_clamped_windows`, `test_player_selection_thins_training_only_and_keeps_all_validation_frames`.

Lokale koppelingen: `football_pipeline.contracts`.

### [tests/test_course_dataset.py](../tests/test_course_dataset.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `Response`, `test_range_archive_reads_zip_selectively_and_reuses_cached_blocks`, `test_range_archive_rejects_whole_download_and_budget_overflow`, `test_match_split_removes_shared_matches_and_never_uses_test_archives`, `test_provider_role_mapping_keeps_goalkeepers_players_and_unknown_people_separate`, `test_field_scoring_does_not_treat_internal_validity_as_ground_truth_accuracy`, `test_field_selection_does_not_hide_lost_coverage_behind_fewer_false_projections`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.course_dataset`, `football_pipeline.course_field_evaluation`, `football_pipeline.research_archive`.

### [tests/test_distance_app.py](../tests/test_distance_app.py)

The distance view reads existing records and never runs video inference.

Topniveaufuncties en klassen: `observed_run`, `result_view`, `test_distance_settings_filters_downloads_and_cache_do_not_modify_records`, `test_missing_tracking_is_unavailable_and_empty_saved_list_is_actionable`, `test_recorded_dimensions_are_reused`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.distance_ui`, `football_pipeline.video`.

### [tests/test_distances.py](../tests/test_distances.py)

Analytic paths and interrupted observations exercise the distance contract.

Topniveaufuncties en klassen: `frame`, `test_known_horizontal_vertical_and_diagonal_paths_and_field_scaling`, `test_stationary_is_zero_but_single_or_invalid_observations_are_unavailable`, `test_missing_or_invalid_samples_never_bridge`, `test_reset_separates_reused_id_and_different_ids_never_merge`, `test_large_jump_rejected_before_smoothing_and_speed_limit_is_configurable`, `test_roles_teams_and_unknown_intervals`, `test_recorded_dimensions_and_invalid_settings`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.distances`.

### [tests/test_field_comparison.py](../tests/test_field_comparison.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `reviewed_fixture`, `test_wrong_valid_missing_and_correct_projections_are_reported_separately`, `test_evaluation_rejects_untrusted_or_misaligned_references`, `metric_pair`, `test_release_requires_both_video_types_and_reviewed_improvement`, `test_release_rejects_regressions_and_missing_evidence`, `test_release_allows_exactly_five_percentage_points_and_lower_error`, `test_export_review_writes_original_frames_and_json_guide_without_labels`.

Lokale koppelingen: `football_pipeline.automatic_calibration`, `football_pipeline.contracts`, `football_pipeline.field_comparison`, `football_pipeline.field_layout`, `football_pipeline.field_motion`, `football_pipeline.video`.

### [tests/test_field_lens.py](../tests/test_field_lens.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_lens_coordinate_roundtrip_preserves_raw_player_footpoints`, `test_straight_or_uninformative_grass_does_not_invent_lens_correction`, `test_curved_touchline_has_held_out_pixels_and_separate_controls`.

Lokale koppelingen: `football_pipeline.field_lens`.

### [tests/test_field_lines.py](../tests/test_field_lines.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `example`, `test_dual_homography_preserves_unfitted_point_controls`.

Lokale koppelingen: `football_pipeline.automatic_calibration`, `football_pipeline.field_layout`, `football_pipeline.field_line_geometry`, `football_pipeline.field_motion`.

### [tests/test_field_motion.py](../tests/test_field_motion.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_visible_field_line_can_be_checked_when_virtual_endpoints_straddle_horizon`, `test_points_are_checked_without_mandatory_lines_and_controls_are_not_refitted`, `test_exact_four_point_fit_needs_additional_nonparallel_line_controls`, `texture`, `unknown`, `test_actual_optical_flow_measures_pan_zoom_and_expires_without_refreshing_anchor`, `test_motion_failure_resets_then_direct_recognition_recovers`, `test_confidence_is_a_separate_profile_and_old_identity_is_preserved`, `test_confidence_comparison_filters_the_same_raw_observations`, `test_full_score_bundles_validate_completeness_before_comparisons`, `test_motion_also_checks_available_lines_and_resets_across_missing_indices`, `test_motion_rejects_fewer_than_twenty_or_low_ratio_inliers`, `test_recalibration_reuses_detections_but_recomputes_current_geometry`, `test_human_references_require_explicit_input_and_completion_is_separate`, `test_failed_intervals_include_first_last_and_empty`, `test_new_ui_saved_run_uses_same_frame_and_point_toggles`, `test_ui_human_reference_is_only_saved_after_explicit_input`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.automatic_calibration`, `football_pipeline.contracts`, `football_pipeline.demo`, `football_pipeline.field_layout`, `football_pipeline.field_motion`, `football_pipeline.field_review`, `football_pipeline.pipeline`, `football_pipeline.video`.

### [tests/test_field_reliability.py](../tests/test_field_reliability.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `detected`, `missing`, `test_visible_polygon_is_clipped_when_all_pitch_corners_are_offscreen`, `test_horizon_clipping_never_requires_virtual_corners_on_same_branch`, `test_projected_footpoints_use_polygon_and_uv_without_snapping`, `test_direct_semantic_jump_rejected_even_with_internally_perfect_points`, `test_real_pan_zoom_direct_recognition_agrees_with_measured_motion`, `test_cut_resets_history_even_with_valid_direct_recognition`, `test_no_motion_evidence_still_allows_independently_checked_direct_recognition`, `test_gap_failure_and_expiry_clear_all_calibration_metadata`, `test_legacy_profile_remains_active_and_does_not_gain_new_behavior`, `test_candidate_pipeline_and_saved_profile_roundtrip`.

Lokale koppelingen: `football_pipeline.automatic_calibration`, `football_pipeline.contracts`, `football_pipeline.demo`, `football_pipeline.field_bounds`, `football_pipeline.field_motion`, `football_pipeline.pipeline`, `football_pipeline.render`, `football_pipeline.video`.

### [tests/test_field_training.py](../tests/test_field_training.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_reference_error_includes_visible_lines_when_virtual_endpoints_cross_horizon`, `Response`, `test_download_resumes_and_rehashes_completed_files`, `test_budget_rejects_before_download_writes`, `test_complete_partial_download_publishes_without_request`, `test_exclusive_budget_tracking_accounts_atomic_metadata_and_refuses_overflow`, `test_zip_rejects_traversal_and_changed_extraction`, `test_mask_removes_invisible_error_and_gradient_before_reduction`, `test_interrupted_checkpoint_publication_preserves_previous_committed_epoch`, `test_invalid_normalized_labels_rejected`, `test_label_roundoff_is_clamped_without_changing_raw_labels`, `test_provider_border_clipping_preserves_line_geometry_without_changing_raw_labels`, `test_head_only_training_keeps_pretrained_normalization_statistics_frozen`, `test_duplicate_and_compilation_selection`, `test_frame_preparation_spacing_provenance_and_resume`, `make_dataset`, `test_both_networks_use_same_windows_safe_main_camera_index`, `test_match_overlap_rejected_even_when_images_differ`, `test_finetuned_runtime_requires_matching_completed_report`.

Lokale koppelingen: `football_pipeline.automatic_calibration`, `football_pipeline.contracts`, `football_pipeline.field_data`, `football_pipeline.field_learning`, `football_pipeline.field_model_spec`.

### [tests/test_fullframe_ball_evaluation.py](../tests/test_fullframe_ball_evaluation.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_fullframe_target_mapping_uses_names_and_original_pixels`, `test_fullframe_development_evaluation_rejects_test_before_opening_pixels`.

Lokale koppelingen: `football_pipeline.contracts`.

### [tests/test_geometry.py](../tests/test_geometry.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `detection`, `test_known_perspective_transform_and_independent_checks`, `test_invalid_calibrations_rejected`, `test_failed_independent_check_exposes_diagnostics_without_moving_click`, `test_projection_status_and_no_invented_position`, `test_loaded_matrix_scale_and_review_are_validated`, `test_display_resize_does_not_change_geometry`, `test_homogeneous_zero_divisor_never_creates_a_position`, `test_malformed_review_is_an_actionable_error`, `test_partial_field_calibration_projects_players_outside_the_fit_region`, `test_a_partial_view_does_not_accept_points_behind_the_camera`.

Lokale koppelingen: `football_pipeline.calibration_input`, `football_pipeline.contracts`, `football_pipeline.geometry`, `football_pipeline.render`.

### [tests/test_joint_integration.py](../tests/test_joint_integration.py)

Audit actual export contracts; fixtures below are explicitly synthetic software evidence.

Topniveaufuncties en klassen: `audit_fixture`, `write_rows`, `test_joint_audit_checks_team_roles_unknown_field_and_empty_frame`, `test_joint_audit_rejects_inconsistent_export`, `test_joint_app_runs_automatic_field_and_preserves_roles_teams_on_review`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.appearance`, `football_pipeline.contracts`, `football_pipeline.video`.

### [tests/test_joint_training.py](../tests/test_joint_training.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_budget_uses_elapsed_wall_time_and_rejects_invalid_limits`, `test_atomic_json_retries_windows_reader_lock_without_losing_old_record`, `test_worker_dispatch_uses_importable_module_when_launched_as_main`, `test_field_budget_stops_between_updates_and_returns_trained_progress`, `test_field_geometry_measures_trained_weights_when_baseline_wins_loss`, `test_deduplication_preserves_newest_and_blocks_source_frame_split_leaks`, `test_complete_frame_outranks_older_crop_of_the_same_source`, `test_role_validation_image_cannot_be_used_for_detector_training`, `test_role_pixel_deduplication_handles_rounding_and_copied_images`, `test_role_pixel_revision_retains_originals_and_remaining_budget`, `test_yolo_label_loader_preserves_person_semantics`, `test_candidate_selection_rejects_regressions_and_equal_scores`, `test_bounded_yolo_retries_only_batch_and_preserves_resolution`, `test_native_resume_preserves_optimizer_epochs_and_uses_remaining_budget`, `test_result_links_reject_paths_before_opening_files`, `test_app_result_link_opens_without_upload_and_rejects_bad_link`, `test_joint_export_check_rejects_mismatched_timestamps`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.app_results`, `football_pipeline.contracts`, `football_pipeline.joint_data`, `football_pipeline.joint_training`, `football_pipeline.training_budget`.

### [tests/test_model_handoff.py](../tests/test_model_handoff.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `handoff`, `test_register_player_model_verifies_names_hashes_and_preserves_previous_version`, `test_invalid_handoff_cannot_create_ready_profile`, `test_profile_discovery_adds_registered_model_without_restarting`, `test_equivalent_model_profiles_are_shown_once_despite_relative_paths`, `test_unavailable_optional_profiles_are_hidden_but_default_reports_its_error`, `test_profiles_with_the_same_detector_and_different_heads_remain_selectable`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.detection`, `football_pipeline.model_handoff`.

### [tests/test_models_and_evaluation.py](../tests/test_models_and_evaluation.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_duplicate_semantic_suppliers_rejected`, `test_person_never_becomes_a_specialized_role`, `test_handover_weight_hash_is_verified`, `test_non_object_manifest_is_an_actionable_error`, `test_cuda_profile_explains_cpu_environment_before_inference`, `test_explicit_cpu_and_available_cuda_devices`, `test_evaluation_switches_takeovers_gaps_and_full_occlusion`, `test_evaluation_uses_one_to_one_assignment`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.detection`, `football_pipeline.evaluation`.

### [tests/test_panoris_pilot.py](../tests/test_panoris_pilot.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `pilot_config`, `pitch_frame`, `test_static_geometry_passes_without_human_approval`, `test_failed_geometry_is_recorded_without_correcting_points`, `test_camera_shift_stops_pilot`.

Lokale koppelingen: `football_pipeline.contracts`.

### [tests/test_participants.py](../tests/test_participants.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `candidate`, `test_only_players_on_pitch_count_but_other_roles_and_off_pitch_predictions_are_preserved`, `test_field_loss_is_unknown_not_zero_and_recovery_uses_current_transform`, `test_claimed_valid_projection_without_valid_position_cannot_count`, `test_truncated_feet_and_invalid_boxes_do_not_count`, `test_generic_person_profile_has_no_available_player_count`.

Lokale koppelingen: `football_pipeline.automatic_calibration`, `football_pipeline.contracts`, `football_pipeline.geometry`, `football_pipeline.participants`.

### [tests/test_person1.py](../tests/test_person1.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `TempCase`, `MetricsTests`, `DatasetTests`.

Lokale koppelingen: `persoon1.annotation`, `persoon1.core`, `persoon1.metrics`, `persoon1.modeling`.

### [tests/test_person1_round3.py](../tests/test_person1_round3.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_role_cohorts_do_not_misreport_new_rare_photos_as_match_crops`, `test_coco_view_preserves_ball_32_and_generic_person_0`, `test_coco_view_rejects_test_frames_before_opening_their_images`, `test_head_interpolation_matches_logits_and_retains_original_team_model`, `test_low_resolution_photo_transform_really_removes_detail_and_keeps_full_crop`.

Lokale koppelingen: `football_pipeline.appearance`, `persoon1.role_training`.

### [tests/test_pipeline.py](../tests/test_pipeline.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_entire_clip_encoding_sync_empty_frames_cache_and_corruption`, `test_encoder_failure_never_marked_complete`, `test_tracking_requires_real_mvp_acceptance`, `test_only_one_processing_job_per_root`, `test_unavailable_detector_gpu_fails_before_field_worker`, `test_tracking_pipeline_preserves_empty_frame_without_predicted_position`, `test_pipeline_projects_before_tracking_and_preserves_nonplayers`, `test_technical_pilot_never_impersonates_human_review_or_enables_tracking`, `test_technical_pilot_requires_explicit_technical_evidence`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.contracts`, `football_pipeline.demo`, `football_pipeline.detection`, `football_pipeline.pipeline`, `football_pipeline.video`.

### [tests/test_point_picker.py](../tests/test_point_picker.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_click_updates_only_selected_point_in_original_pixels`, `test_invalid_or_stale_click_cannot_change_points`, `test_missing_coordinates_name_the_point_instead_of_numpy_error`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.geometry`, `football_pipeline.point_picker`, `football_pipeline.video`.

### [tests/test_role_context.py](../tests/test_role_context.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `model`, `person`, `test_context_features_are_permutation_equivariant_and_use_original_image_size`, `test_negative_refinement_protects_source_players_near_goals_and_ignores_outside_people`, `test_positive_refinement_requires_trained_crop_features_and_respects_specialist_referee`, `test_short_context_and_mismatched_teachers_do_not_change_roles`, `test_a_trained_goalkeeper_class_is_preserved_even_away_from_the_goal`, `test_context_training_rejects_reserved_splits_before_opening_images`, `test_color_recovery_cannot_undo_a_learned_negative_context_decision`, `test_observed_training_uses_unique_provider_matches_and_ignores_unlabelled_boxes`, `test_referee_consensus_requires_all_cues_and_protects_common_kits_and_keepers`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.broadcast_observed_context`, `football_pipeline.contracts`, `football_pipeline.kit_embedding`, `football_pipeline.role_context`, `football_pipeline.teams`.

### [tests/test_role_extension.py](../tests/test_role_extension.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `extension`, `test_extension_loads_without_mutating_existing_labels`, `test_extension_rejects_bad_data_before_training`, `test_role_only_match_never_inherits_an_untrained_supervised_team_head`, `test_extension_rejects_identical_pixels_copied_to_different_split_paths`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`, `persoon1`.

### [tests/test_school_app.py](../tests/test_school_app.py)

Exercise the school workflow through rendering, even with stale advanced settings.

Topniveaufuncties en klassen: `test_school_run_uses_manual_calibration_without_tracking_or_teams`, `test_switching_the_visible_field_region_discards_the_previous_calibration`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.demo`, `football_pipeline.video`.

### [tests/test_sync_integration.py](../tests/test_sync_integration.py)

Compatibility between the incoming appearance model and colour-team corrections.

Topniveaufuncties en klassen: `appearance_player`, `test_both_team_id_formats_use_identical_totals`, `test_colour_assignment_keeps_appearance_evidence_and_replay_restores_it`, `test_replay_discards_colour_labels_without_appearance_evidence`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.participants`, `football_pipeline.replay`, `football_pipeline.teams`.

### [tests/test_team_app.py](../tests/test_team_app.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `result_app`, `test_frame_counts_and_corrections_only_apply_on_submit`, `test_app_can_open_saved_result_without_upload_and_keeps_original_visible`, `test_chart_has_separate_segments_across_field_dropout`, `test_old_result_still_uses_shared_downloads_without_team_controls`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.contracts`, `football_pipeline.demo`, `football_pipeline.pipeline`, `football_pipeline.video`.

### [tests/test_team_pipeline.py](../tests/test_team_pipeline.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `TeamFixtureDetector`, `team_run`, `records`, `test_full_team_video_exports_and_cache`, `test_corrections_are_new_runs_preserve_observations_and_bind_to_root`, `test_correction_failure_leaves_original_and_failed_manifest`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.contracts`, `football_pipeline.demo`, `football_pipeline.geometry`, `football_pipeline.pipeline`, `football_pipeline.team_results`, `football_pipeline.video`.

### [tests/test_teams.py](../tests/test_teams.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `player`, `team_model`, `test_profile_is_versioned_and_rejects_invalid_settings`, `test_torso_color_preserves_green_white_and_black_shirts`, `test_background_tiny_and_mixed_crops_are_unknown_and_roles_stay_intact`, `test_fit_has_two_stable_prototypes_and_rejects_sparse_third_color`, `test_similar_colors_and_insufficient_observations_stay_unknown`, `test_single_frame_cannot_establish_team_prototypes`, `test_labels_need_confirmation_resist_single_error_and_reset_for_new_id`, `test_persistent_new_color_switches_only_after_threshold`, `test_manual_overrides_apply_whole_track_and_do_not_touch_nonplayers`, `test_team_totals_keep_existing_field_confidence_and_role_rules`, `test_old_and_new_records_roundtrip_without_trusting_exported_counts`, `test_reservoir_is_bounded_and_order_independent`, `test_correction_validation_binds_source_and_rejects_unknown_ids`, `test_equal_manual_prototypes_remain_ambiguous`, `test_team_rendering_colors_boxes_points_and_legend`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.participants`, `football_pipeline.render`, `football_pipeline.team_results`, `football_pipeline.teams`, `football_pipeline.video`.

### [tests/test_teamtrack_dataset.py](../tests/test_teamtrack_dataset.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `test_rebuilding_preserves_actual_annotation_edits`.

Lokale koppelingen: `persoon1.teamtrack_dataset`.

### [tests/test_tracking.py](../tests/test_tracking.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `item`, `test_actual_bytetrack_indexes_low_confidence_and_empty_updates`, `test_tracking_excludes_off_field_players_and_all_other_roles_inside_field`, `test_observed_trajectories_keep_gaps_and_expire`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.tracking`, `football_pipeline.video`.

### [tests/test_tracking_motion.py](../tests/test_tracking_motion.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `background`, `view`, `test_compensation_preserves_ids_through_pan_zoom_and_field_dropout`, `test_camera_cuts_reset_ids_without_reusing_numbers_or_joining_trajectories`, `test_unmeasured_motion_resets_and_never_tracks_nonplayers_or_offfield_players`, `test_zoom_preserves_aspect_and_rotation_uses_a_box_envelope`, `test_player_id_survives_small_camera_rotation_and_zoom`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.tracking`, `football_pipeline.tracking_motion`, `football_pipeline.video`.

### [tests/test_video.py](../tests/test_video.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `payload`, `test_variable_framerate_rejected_even_if_nominal_rate_is_25`, `test_frame_size_change_rejected`.

Lokale koppelingen: `football_pipeline`, `football_pipeline.contracts`.

### [tests/test_video_and_mapping.py](../tests/test_video_and_mapping.py)

Controleert gedrag via de onderstaande testfuncties en fixtures.

Topniveaufuncties en klassen: `VideoTests`.

Lokale koppelingen: `persoon1.core`, `persoon1.modeling`, `persoon1.video`.

## Historische bronkopieën

Meetbewijs van eerdere experimenten. Dit zijn geen actuele runtimebestanden.

### [reports/appearance-experiments/EXP-R004/source-snapshot/appearance.py](../reports/appearance-experiments/EXP-R004/source-snapshot/appearance.py)

Supervised crop roles and match-specific team appearance, independent of pitch position.

Topniveaufuncties en klassen: `crop_tensor`, `jersey_feature`, `backbone`, `AppearanceClassifier`.

Lokale koppelingen: `.contracts`, `.geometry`, `.teams`.

### [reports/appearance-experiments/EXP-R004/source-snapshot/role_training.py](../reports/appearance-experiments/EXP-R004/source-snapshot/role_training.py)

Reproducible supervised appearance heads; no reserved test frames are opened.

Topniveaufuncties en klassen: `save`, `build`, `scores`, `train`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`.

### [reports/appearance-experiments/EXP-R004/source-snapshot/teams.py](../reports/appearance-experiments/EXP-R004/source-snapshot/teams.py)

Per-video kit-colour clustering; new videos never inherit another match's team identities.

Topniveaufuncties en klassen: `VideoTeams`.

Lokale koppelingen: `.appearance`, `.geometry`.

### [reports/appearance-experiments/EXP-R007/source-snapshot/appearance.py](../reports/appearance-experiments/EXP-R007/source-snapshot/appearance.py)

Supervised crop roles and match-specific team appearance, independent of pitch position.

Topniveaufuncties en klassen: `crop_tensor`, `jersey_feature`, `backbone`, `AppearanceClassifier`.

Lokale koppelingen: `.contracts`, `.geometry`, `.teams`.

### [reports/appearance-experiments/EXP-R007/source-snapshot/role_training.py](../reports/appearance-experiments/EXP-R007/source-snapshot/role_training.py)

Reproducible supervised appearance heads; no reserved test frames are opened.

Topniveaufuncties en klassen: `save`, `build`, `scores`, `train`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`.

### [reports/appearance-experiments/EXP-R007/source-snapshot/teams.py](../reports/appearance-experiments/EXP-R007/source-snapshot/teams.py)

Per-video kit-colour clustering; new videos never inherit another match's team identities.

Topniveaufuncties en klassen: `VideoTeams`.

Lokale koppelingen: `.appearance`, `.geometry`.

### [reports/broadcast-data/v3-source/evaluation-helper.py](../reports/broadcast-data/v3-source/evaluation-helper.py)

Bounded native-ball fine-tuning with frozen, equal-input baseline comparisons.

Topniveaufuncties en klassen: `measured`, `run`.

Lokale koppelingen: `football_pipeline.ball_tiles`, `football_pipeline.contracts`, `persoon1.metrics`.

### [reports/broadcast-data/v3-source/experiment-source.py](../reports/broadcast-data/v3-source/experiment-source.py)

One controlled comparison: frozen backbone versus all-layer ball fine-tuning.

Topniveaufuncties en klassen: `run`.

Lokale koppelingen: `football_pipeline.contracts`.

### [reports/broadcast-data/v3-source/metric-source.py](../reports/broadcast-data/v3-source/metric-source.py)

Explicit 101-recall-point AP for fully labelled boxes without ignore/crowd regions.

Topniveaufuncties en klassen: `iou`, `match_class`, `ap101`, `evaluate`.

### [reports/broadcast-data/v3-source/tiling-source.py](../reports/broadcast-data/v3-source/tiling-source.py)

Ball-only tiling with original-pixel coordinates and a global NMS pass.

Topniveaufuncties en klassen: `axis_starts`, `tile_windows`, `validate_ball_tile_config`, `predict_multiscale_ball`, `merge_ball_predictions`, `predict_ball_tiles`.

### [reports/football48-ball-experiments/source/build_role_extension.py](../reports/football48-ball-experiments/source/build_role_extension.py)

Versioned AI crop corrections after explicit visual inspection; no synthetic human review.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`, `football_pipeline.video`, `persoon1.role_training`.

### [reports/football48-ball-experiments/source/evaluate_role_extension.py](../reports/football48-ball-experiments/source/evaluate_role_extension.py)

Compare two real classifiers on identical conditional crops, never report this as detection AP.

Topniveaufuncties en klassen: `infer`, `summarize`, `main`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`, `football_pipeline.video`, `persoon1.role_training`.

### [reports/football48-ball-experiments/source/football48_ball_experiment.py](../reports/football48-ball-experiments/source/football48_ball_experiment.py)

Reproducible, provisional ball fine-tuning on the delivered football48 crops.

Topniveaufuncties en klassen: `truth_and_identity`, `measure`, `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.pipeline`, `football_pipeline.video`, `persoon1.metrics`, `persoon1.modeling`.

### [reports/football48-ball-experiments/source/role_training.py](../reports/football48-ball-experiments/source/role_training.py)

Reproducible supervised appearance heads; no reserved test frames are opened.

Topniveaufuncties en klassen: `save`, `build`, `scores`, `load_training_manifest`, `supervised_team_videos`, `train`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`.

### [reports/partial-calibration-v1/source-script.py](../reports/partial-calibration-v1/source-script.py)

Audit penalty-area calibration against separate provider goal-area lines.

Topniveaufuncties en klassen: `line`, `intersection`, `required_lines`, `provider_points`, `audit`.

Lokale koppelingen: `football_pipeline.calibration_input`, `football_pipeline.contracts`, `football_pipeline.geometry`, `football_pipeline.render`.

### [reports/partial-calibration-v2/calibration-input-source.py](../reports/partial-calibration-v2/calibration-input-source.py)

Known coordinate suggestions, never an automatic calibration approval.

Topniveaufuncties en klassen: `penalty_area_points`, `point_label`, `panoris_point_suggestion`.

Lokale koppelingen: `.contracts`, `.video`.

### [reports/partial-calibration-v2/geometry-source.py](../reports/partial-calibration-v2/geometry-source.py)

Vastgelegde broncode van het experiment in deze rapportmap; geen nieuw startcommando.

Topniveaufuncties en klassen: `CalibrationControlError`, `point_coordinate_issues`, `Calibration`, `create_calibration`, `valid_box`, `project_detection`.

Lokale koppelingen: `.contracts`.

### [reports/partial-calibration-v2/source-script.py](../reports/partial-calibration-v2/source-script.py)

Audit penalty-area calibration against separate provider goal-area lines.

Topniveaufuncties en klassen: `line`, `intersection`, `required_lines`, `provider_points`, `audit`.

Lokale koppelingen: `football_pipeline.calibration_input`, `football_pipeline.contracts`, `football_pipeline.geometry`, `football_pipeline.render`.

### [reports/partial-calibration-v3/calibration-input-source.py](../reports/partial-calibration-v3/calibration-input-source.py)

Known coordinate suggestions, never an automatic calibration approval.

Topniveaufuncties en klassen: `penalty_area_points`, `point_label`, `panoris_point_suggestion`.

Lokale koppelingen: `.contracts`, `.video`.

### [reports/partial-calibration-v3/geometry-source.py](../reports/partial-calibration-v3/geometry-source.py)

Vastgelegde broncode van het experiment in deze rapportmap; geen nieuw startcommando.

Topniveaufuncties en klassen: `CalibrationControlError`, `point_coordinate_issues`, `Calibration`, `create_calibration`, `valid_box`, `project_detection`.

Lokale koppelingen: `.contracts`.

### [reports/partial-calibration-v3/source-script.py](../reports/partial-calibration-v3/source-script.py)

Audit penalty-area calibration against separate provider goal-area lines.

Topniveaufuncties en klassen: `line`, `intersection`, `required_lines`, `provider_points`, `audit`.

Lokale koppelingen: `football_pipeline.calibration_input`, `football_pipeline.contracts`, `football_pipeline.geometry`, `football_pipeline.render`.

### [reports/person1-round3/data-audit-final/source.py](../reports/person1-round3/data-audit-final/source.py)

Inventory P1 development data and prepare truthful human review, never inspect test pictures.

Topniveaufuncties en klassen: `difference_hash`, `audit_roles`, `audit_detection`, `render_new_role_sheets`, `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.video`, `persoon1.role_training`.

### [reports/person1-round3/EXP-R013/training-source.py](../reports/person1-round3/EXP-R013/training-source.py)

Reproducible supervised appearance heads; no reserved test frames are opened.

Topniveaufuncties en klassen: `save`, `build`, `scores`, `load_training_manifest`, `supervised_team_videos`, `train`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`.

### [reports/person1-round3/EXP-R014/training-source.py](../reports/person1-round3/EXP-R014/training-source.py)

Reproducible supervised appearance heads; no reserved test frames are opened.

Topniveaufuncties en klassen: `save`, `build`, `scores`, `load_training_manifest`, `supervised_team_videos`, `train`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`.

### [reports/person1-round3/EXP-R015/source.py](../reports/person1-round3/EXP-R015/source.py)

Measured head interpolation for identical frozen encoders; never average incompatible features.

Topniveaufuncties en klassen: `blend_role_states`, `main`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`, `persoon1.role_training`.

### [reports/person1-round3/EXP-R016/source.py](../reports/person1-round3/EXP-R016/source.py)

Reproducible supervised appearance heads; no reserved test frames are opened.

Topniveaufuncties en klassen: `save`, `build`, `scores`, `load_training_manifest`, `supervised_team_videos`, `augment_role_tensor`, `train`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`.

### [reports/person1-round3/fullframe-ball-development/evaluation-source.py](../reports/person1-round3/fullframe-ball-development/evaluation-source.py)

Evaluate frozen COCO ball detectors on new, provisional full-frame development labels.

Topniveaufuncties en klassen: `validation_truth`, `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.pipeline`, `football_pipeline.video`, `persoon1.metrics`, `persoon1.modeling`.

### [reports/person1-round3/fullframe-ball-development/metrics-source.py](../reports/person1-round3/fullframe-ball-development/metrics-source.py)

Explicit 101-recall-point AP for fully labelled boxes without ignore/crowd regions.

Topniveaufuncties en klassen: `iou`, `match_class`, `ap101`, `evaluate`.

### [reports/person1-round3/source-snapshot/audit_person1_data.py](../reports/person1-round3/source-snapshot/audit_person1_data.py)

Inventory P1 development data and prepare truthful human review, never inspect test pictures.

Topniveaufuncties en klassen: `difference_hash`, `audit_roles`, `audit_detection`, `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.video`, `persoon1.role_training`.

### [reports/person1-round3/source-snapshot/build_role_round3.py](../reports/person1-round3/source-snapshot/build_role_round3.py)

Explicit AI visual decisions for rare-role development; preserves all earlier labels.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.video`, `persoon1.role_training`.

### [reports/person1-round3/source-snapshot/football48_ball_experiment.py](../reports/person1-round3/source-snapshot/football48_ball_experiment.py)

Reproducible, provisional ball fine-tuning on the delivered football48 crops.

Topniveaufuncties en klassen: `create_coco_view`, `truth_and_identity`, `measure`, `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.pipeline`, `football_pipeline.video`, `persoon1.metrics`, `persoon1.modeling`.

### [reports/person1-round3/source-snapshot/role_training.py](../reports/person1-round3/source-snapshot/role_training.py)

Reproducible supervised appearance heads; no reserved test frames are opened.

Topniveaufuncties en klassen: `save`, `build`, `scores`, `load_training_manifest`, `supervised_team_videos`, `train`.

Lokale koppelingen: `football_pipeline.appearance`, `football_pipeline.contracts`.

### [reports/person1-round4/EXP-F005/training-source.py](../reports/person1-round4/EXP-F005/training-source.py)

Train a ball specialist on native tiles from the delivered fullscene60 source.

Topniveaufuncties en klassen: `tile_ball_labels`, `build_dataset`, `main`.

Lokale koppelingen: `football_pipeline.ball_tiles`, `football_pipeline.contracts`, `football_pipeline.pipeline`, `football_pipeline.video`, `persoon1.modeling`.

### [reports/person1-round4/resolution-transfer/source.py](../reports/person1-round4/resolution-transfer/source.py)

Frozen-weight whole-frame versus native/upsampled tile ball comparison.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.ball_tiles`, `football_pipeline.contracts`, `football_pipeline.pipeline`, `football_pipeline.video`, `persoon1.metrics`, `persoon1.modeling`.

### [reports/person1-round4/source/assemble_ball_comparison.py](../reports/person1-round4/source/assemble_ball_comparison.py)

Assemble immutable per-frame measurements into one equal-population comparison.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`.

### [reports/person1-round4/source/audit_ball_tiles.py](../reports/person1-round4/source/audit_ball_tiles.py)

Independently verify derived training pixels and original-ball coordinate matches.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.video`.

### [reports/person1-round4/source/ball_resolution_experiment.py](../reports/person1-round4/source/ball_resolution_experiment.py)

Frozen-weight whole-frame versus native/upsampled tile ball comparison.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.ball_tiles`, `football_pipeline.contracts`, `football_pipeline.pipeline`, `football_pipeline.video`, `persoon1.metrics`, `persoon1.modeling`.

### [reports/person1-round4/source/ball_tiles.py](../reports/person1-round4/source/ball_tiles.py)

Ball-only tiling with original-pixel coordinates and a global NMS pass.

Topniveaufuncties en klassen: `axis_starts`, `tile_windows`, `validate_ball_tile_config`, `predict_multiscale_ball`, `merge_ball_predictions`, `predict_ball_tiles`.

### [reports/person1-round4/source/detection.py](../reports/person1-round4/source/detection.py)

Vastgelegde broncode van het experiment in deze rapportmap; geen nieuw startcommando.

Topniveaufuncties en klassen: `load_model_manifest`, `available_roles`, `merge_person_proposals`, `validate_detection_devices`, `UltralyticsDetector`.

Lokale koppelingen: `.appearance`, `.ball_tiles`, `.contracts`, `.participants`, `.teams`.

### [reports/person1-round4/source/export_tiled_ball_handoff.py](../reports/person1-round4/source/export_tiled_ball_handoff.py)

Execute combined roles/teams/tiled balls on real video and verify source coordinates.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.detection`, `football_pipeline.geometry`, `football_pipeline.render`, `football_pipeline.video`.

### [reports/person1-round4/source/metrics.py](../reports/person1-round4/source/metrics.py)

Explicit 101-recall-point AP for fully labelled boxes without ignore/crowd regions.

Topniveaufuncties en klassen: `iou`, `match_class`, `ap101`, `evaluate`.

### [reports/person1-round4/source/prioritize_role_review.py](../reports/person1-round4/source/prioritize_role_review.py)

Prioritize existing AI-labelled role disagreements without changing truth/review status.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.video`.

### [reports/person1-round4/source/summarize_ball_resolution.py](../reports/person1-round4/source/summarize_ball_resolution.py)

Pool full-frame references correctly and separate in-play recall from all-ball AP.

Topniveaufuncties en klassen: `summarize`.

Lokale koppelingen: `football_pipeline.ball_tiles`, `football_pipeline.contracts`, `football_pipeline.video`, `persoon1.metrics`.

### [reports/person1-round4/source/train_fullscene_ball.py](../reports/person1-round4/source/train_fullscene_ball.py)

Train a ball specialist on native tiles from the delivered fullscene60 source.

Topniveaufuncties en klassen: `tile_ball_labels`, `build_dataset`, `main`.

Lokale koppelingen: `football_pipeline.ball_tiles`, `football_pipeline.contracts`, `football_pipeline.pipeline`, `football_pipeline.video`, `persoon1.modeling`.

### [reports/person1-round4/source/verify_tiled_runtime.py](../reports/person1-round4/source/verify_tiled_runtime.py)

Check that the application path reproduces the measured tiled boxes on real frames.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `football_pipeline.contracts`, `football_pipeline.detection`.

### [reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/__init__.py](../reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/__init__.py)

Reproducible data, detection and evaluation tools for Sports Vision.

### [reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/__main__.py](../reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/__main__.py)

Pakkettoegangspunt of pakketinitialisatie; zie de genoemde imports.

Topniveaufuncties en klassen: `parser`, `execute`, `main`.

Lokale koppelingen: `.annotation`, `.core`, `.modeling`, `.video`.

### [reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/annotation.py](../reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/annotation.py)

Small localhost-only box editor with separate automatic suggestions and reviews.

Topniveaufuncties en klassen: `save_annotation`, `serve`.

Lokale koppelingen: `.core`.

### [reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/core.py](../reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/core.py)

Dataset provenance and review gates. Heavy ML dependencies are loaded lazily.

Topniveaufuncties en klassen: `now`, `read_json`, `write_json`, `sha256`, `canonical_hash`, `environment`, `load_manifest`, `dataset_path`, `read_labels`, `label_pixels`, `validate_dataset`, `require_approval`, `require_experiment_data`.

### [reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/metrics.py](../reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/metrics.py)

Explicit 101-recall-point AP for fully labelled boxes without ignore/crowd regions.

Topniveaufuncties en klassen: `iou`, `match_class`, `ap101`, `evaluate`.

### [reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/modeling.py](../reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/modeling.py)

Inference, training and auditable evaluation. No fake labels or review approvals.

Topniveaufuncties en klassen: `yolo`, `fresh_output`, `class_mapping`, `assert_final_access`, `predict_manifest`, `build_yolo_dataset`, `train`, `evaluate_run`.

Lokale koppelingen: `.core`, `.metrics`.

### [reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/participant_baseline.py](../reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/participant_baseline.py)

Compare localization of the annotated participants without inventing COCO roles.

Topniveaufuncties en klassen: `compare`.

Lokale koppelingen: `.core`, `.metrics`, `.modeling`.

### [reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/project_dataset.py](../reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/project_dataset.py)

Rebuild the disclosed, provisional ball dataset from the exact LFS source video.

Topniveaufuncties en klassen: `prepare`.

Lokale koppelingen: `.core`.

### [reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/review_sheets.py](../reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/review_sheets.py)

Reproducible full-frame and individual-box sheets, without altering labels.

Topniveaufuncties en klassen: `create_sheets`.

Lokale koppelingen: `.core`.

### [reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/teamtrack_dataset.py](../reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/teamtrack_dataset.py)

Build explicit player/referee labels from source MOT boxes and reviewed role boxes.

Topniveaufuncties en klassen: `build`.

Lokale koppelingen: `.core`, `.review_sheets`.

### [reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/technical_check.py](../reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/technical_check.py)

One-epoch GPU software check on generated rectangles, never project results.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `.core`, `.modeling`.

### [reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/video.py](../reports/players-experiments/training/EXP-P003-teamtrack-players/source-snapshot/video.py)

Decode using actual presentation timestamps, including variable frame rate.

Topniveaufuncties en klassen: `frames`, `inspect_video`, `extract`.

Lokale koppelingen: `.core`.

### [reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/__init__.py](../reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/__init__.py)

Reproducible data, detection and evaluation tools for Sports Vision.

### [reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/__main__.py](../reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/__main__.py)

Pakkettoegangspunt of pakketinitialisatie; zie de genoemde imports.

Topniveaufuncties en klassen: `parser`, `execute`, `main`.

Lokale koppelingen: `.annotation`, `.core`, `.modeling`, `.video`.

### [reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/annotation.py](../reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/annotation.py)

Small localhost-only box editor with separate automatic suggestions and reviews.

Topniveaufuncties en klassen: `save_annotation`, `serve`.

Lokale koppelingen: `.core`.

### [reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/core.py](../reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/core.py)

Dataset provenance and review gates. Heavy ML dependencies are loaded lazily.

Topniveaufuncties en klassen: `now`, `read_json`, `write_json`, `sha256`, `canonical_hash`, `environment`, `load_manifest`, `dataset_path`, `read_labels`, `label_pixels`, `validate_dataset`, `require_approval`, `require_experiment_data`.

### [reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/metrics.py](../reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/metrics.py)

Explicit 101-recall-point AP for fully labelled boxes without ignore/crowd regions.

Topniveaufuncties en klassen: `iou`, `match_class`, `ap101`, `evaluate`.

### [reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/modeling.py](../reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/modeling.py)

Inference, training and auditable evaluation. No fake labels or review approvals.

Topniveaufuncties en klassen: `yolo`, `fresh_output`, `class_mapping`, `assert_final_access`, `predict_manifest`, `build_yolo_dataset`, `train`, `evaluate_run`.

Lokale koppelingen: `.core`, `.metrics`.

### [reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/participant_baseline.py](../reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/participant_baseline.py)

Compare localization of the annotated participants without inventing COCO roles.

Topniveaufuncties en klassen: `compare`.

Lokale koppelingen: `.core`, `.metrics`, `.modeling`.

### [reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/project_dataset.py](../reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/project_dataset.py)

Rebuild the disclosed, provisional ball dataset from the exact LFS source video.

Topniveaufuncties en klassen: `prepare`.

Lokale koppelingen: `.core`.

### [reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/review_sheets.py](../reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/review_sheets.py)

Reproducible full-frame and individual-box sheets, without altering labels.

Topniveaufuncties en klassen: `create_sheets`.

Lokale koppelingen: `.core`.

### [reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/teamtrack_dataset.py](../reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/teamtrack_dataset.py)

Build explicit player/referee labels from source MOT boxes and reviewed role boxes.

Topniveaufuncties en klassen: `build`.

Lokale koppelingen: `.core`, `.review_sheets`.

### [reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/technical_check.py](../reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/technical_check.py)

One-epoch GPU software check on generated rectangles, never project results.

Topniveaufuncties en klassen: `main`.

Lokale koppelingen: `.core`, `.modeling`.

### [reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/video.py](../reports/players-experiments/training/EXP-P004-teamtrack-players/source-snapshot/video.py)

Decode using actual presentation timestamps, including variable frame rate.

Topniveaufuncties en klassen: `frames`, `inspect_video`, `extract`.

Lokale koppelingen: `.core`.

### [reports/team-colour-v2/baseline/implementation.py](../reports/team-colour-v2/baseline/implementation.py)

Per-video kit-colour clustering; new videos never inherit another match's team identities.

Topniveaufuncties en klassen: `VideoTeams`.

Lokale koppelingen: `.appearance`, `.geometry`.

## Interface

Het toegangspunt van de lokale Streamlit-toepassing.

### [streamlit_app.py](../streamlit_app.py)

Streamlit-toegangspunt: kiest modelprofiel en workflow, verzamelt invoer en toont resultaten. De rekenstappen staan in football_pipeline zodat ze ook zonder interface bruikbaar zijn.

Topniveaufuncties en klassen: `navigate`, `cached_video_metadata`, `cached_frame`.

Lokale koppelingen: `football_pipeline.app_results`, `football_pipeline.automatic_analysis_ui`, `football_pipeline.calibration_input`, `football_pipeline.contracts`, `football_pipeline.demo`, `football_pipeline.detection`, `football_pipeline.field_review_ui`, `football_pipeline.geometry`, `football_pipeline.model_handoff`, `football_pipeline.pipeline`, `football_pipeline.point_picker`, `football_pipeline.render`, `football_pipeline.teams`, `football_pipeline.training_status_ui`, `football_pipeline.video`.

## Modelconfiguraties

Dit zijn instelbare profielen, geen verschillende implementaties van de hele pipeline.
Een profielnaam alleen bewijst niet dat zijn gewichten aanwezig, actief of onafhankelijk geëvalueerd zijn.
De loader controleert bestanden en mappings; de run bewaart wat daadwerkelijk is gebruikt.

| Profiel | Model-ID's | Aanvullende instellingen |
| --- | --- | --- |
| [models-ball-broadcast-v2.json](../configs/models-ball-broadcast-v2.json) | broadcast-ball-native-v2 | ball_tiles |
| [models-ball-broadcast-v3.json](../configs/models-ball-broadcast-v3.json) | broadcast-ball-native-v3-freeze-0 | ball_tiles |
| [models-ball-f003.json](../configs/models-ball-f003.json) | football48-coco-head-f003 | geen |
| [models-ball-f005.json](../configs/models-ball-f005.json) | fullscene-ball-f005-multiscale | ball_tiles |
| [models-ball-tiles.json](../configs/models-ball-tiles.json) | coco-ball-multiscale-tiles | ball_tiles |
| [models-broadcast.json](../configs/models-broadcast.json) | broadcast-pitch-players-v7, coco-person-proposals | appearance, kit_embedding, role_context, analysis_scope |
| [models-coco-baseline.json](../configs/models-coco-baseline.json) | coco_baseline | geen |
| [models-integrated-20261027.json](../configs/models-integrated-20261027.json) | joint-selected-players, coco-person-proposals, joint-selected-ball | appearance, ball_tiles |
| [models-panoris-pilot-1920.json](../configs/models-panoris-pilot-1920.json) | coco_baseline | geen |
| [models-persons.json](../configs/models-persons.json) | coco-persons-1920 | geen |
| [models-players-ball-broadcast-v2.json](../configs/models-players-ball-broadcast-v2.json) | exp-p006-gsr-multimatch-v3, broadcast-ball-native-v2 | ball_tiles |
| [models-players-ball-broadcast-v3.json](../configs/models-players-ball-broadcast-v3.json) | exp-p006-gsr-multimatch-v3, broadcast-ball-native-v3-freeze-0 | ball_tiles |
| [models-players-ball-f005.json](../configs/models-players-ball-f005.json) | exp-p004-teamtrack-v2_1, coco-person-proposals, fullscene-ball-f005-multiscale | appearance, ball_tiles |
| [models-players-ball-tiles.json](../configs/models-players-ball-tiles.json) | exp-p004-teamtrack-v2_1, coco-person-proposals, coco-ball-multiscale-tiles | appearance, ball_tiles |
| [models-players-base.json](../configs/models-players-base.json) | exp-p004-teamtrack-v2_1 | geen |
| [models-players-v2.json](../configs/models-players-v2.json) | exp-p004-teamtrack-v2_1 | geen |
| [models-players-v3.json](../configs/models-players-v3.json) | exp-p006-gsr-multimatch-v3 | geen |
| [models-players.json](../configs/models-players.json) | exp-p006-gsr-multimatch-v3 | geen |
| [models-roles-r007.json](../configs/models-roles-r007.json) | exp-p004-teamtrack-v2_1, coco-person-proposals | appearance |
| [models-roles-r009.json](../configs/models-roles-r009.json) | exp-p004-teamtrack-v2_1, coco-person-proposals | appearance |
| [models-roles-r010.json](../configs/models-roles-r010.json) | exp-p004-teamtrack-v2_1, coco-person-proposals | appearance |
| [models-roles-r015.json](../configs/models-roles-r015.json) | exp-p004-teamtrack-v2_1, coco-person-proposals | appearance |
| [models-roles-tiles.json](../configs/models-roles-tiles.json) | exp-p004-teamtrack-v2_1, coco-person-proposals | appearance |
| [models-school.json](../configs/models-school.json) | exp-p006-gsr-multimatch-v3, fullscene-ball-f005-multiscale | geen |
| [models.json](../configs/models.json) | exp-p006-gsr-multimatch-v3 | geen |

Bestandstypen: .ps1: 14, .py: 281.
