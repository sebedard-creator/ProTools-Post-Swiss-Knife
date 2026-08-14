# Changelog

## [Unreleased]
- Suppression de `refactor.py` et `templates/index.old`, fichiers historiques non utilisés.

## CSV TO PTX — Playback Notes Sync
- Ajout de la conversion CSV UTF-8 exporté par Playback Notes Sync vers une session PTX native.
- Utilise le même template, les mêmes pistes et les mêmes Clip Groups de 2 secondes que Playback Notes Sync.
- Accepte les formats de temps `MMSS` et `HH:MM:SS:`; les timecodes impossibles sont rejetés avec le numéro de ligne CSV.

## [4.2.0] - PTX API Native Integration
- Remplacement du vieux moteur AAF par l'API native `pt_api` pour la génération des marqueurs.
- Création de `generators/ptx_generator.py` qui lit et injecte directement les marqueurs extraits dans une session `template_markers.ptx`.
- Suppression définitive du code mort (`aaf_generator.py`) pour maintenir l'hygiène du projet.
- Routage web mis à jour de `/xls-to-aaf` vers `/xls-to-ptx`.
## [4.1.0] - Web Deployment & CI/CD
- Refactorisation complète du système de gestion de fichiers dans `app.py` pour supporter les accès concurrents. Utilisation de `tempfile.TemporaryDirectory` et `io.BytesIO` pour un traitement 100% en mémoire vive (RAM) évitant les collisions.
- Ajout du fichier `.gitignore` et `requirements.txt` pour préparer le déploiement sur les serveurs cloud.
- Déploiement en ligne continu via Render.com couplé à un repository GitHub.
- Ajout du lien vers le code source GitHub dans le bas de la page web.

## [4.0.0] - XLS to AAF Markers Stable Release
- Finalisation de la fonctionnalité d'export de marqueurs depuis un fichier Excel vers un fichier AAF pour Pro Tools.
- Ajout d'une piste audio factice (Dummy Audio) pour forcer Pro Tools à lire la piste d'événements.
- Mappage des propriétés de marqueurs (`Comment` et balise cachée `UserComments`) pour contourner les limitations strictes de Pro Tools concernant les champs "Name" et "Comments".
- Retrait de la limite de 31 caractères pour le nom du marqueur.
- Version bump globale de l'interface et de la documentation vers v4.0.

## [2.1.0] - XLS to AAF Markers Feature
- Ajout de la fonctionnalité permettant de générer un fichier AAF de Memory Locations (marqueurs) depuis un fichier Excel.
- Création de `parsers/excel_parser.py` pour scanner l'Excel dynamiquement et extraire les en-têtes "TC IN", "Description" et "Notes particulières".
- Création de `generators/aaf_generator.py` pour la génération du fichier `.aaf` à 23.976 fps via `pyaaf2`.
- Mise à jour de l'interface web (`index.html`) pour autoriser le format `.xls`/`.xlsx`.

## [2.0.0] - Initial Migration
- Migrated code from `C:\CueSheetConverter` to `Y:\PT SK 2.0`.
- Established new modular architecture (`parsers/`, `generators/`, `utils/`).
- Setup local `venv` for a self-contained execution environment.
