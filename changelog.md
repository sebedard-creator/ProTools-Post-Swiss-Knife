# Changelog

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
