# ProTools Post Swiss Knife - Architecture

## Stack Technique
- **Backend** : Python 3.11 avec le framework web Flask.
- **Frontend** : HTML, CSS Vanille, JS (dans `index.html`) pour une application single-page (SPA).
- **Dépendances tierces** : `openpyxl` (lecture/écriture Excel), `pyaaf2` (génération AAF), `reportlab` (génération PDF) et `pt_api` 1.5.1 (sessions Pro Tools `.ptx`).
- **PTX** : `pt_api` est installé depuis Git, dans la version verrouillée par `requirements.txt`; aucune dépendance locale `Y:\pt_api` n'est requise.

## Structure du Projet
- `/app.py` : Le serveur Flask (contrôleur principal), qui route chaque requête web. Il s'occupe de la gestion des fichiers avec `tempfile` (100% en RAM via `io.BytesIO`).
- `/templates/index.html` : L'interface utilisateur. Contient des scripts JS pour valider les extensions de fichiers et mettre à jour l'état du formulaire.
- `/parsers/` : Les scripts qui lisent les fichiers entrants (ex: `excel_parser.py` pour extraire les marqueurs).
- `/generators/` : Les scripts qui formatent et écrivent le format de sortie (ex: `pdf_generator.py`, `ptx_generator.py`, `pb_notes_ptx_generator.py`).
- `/pb_notes_sync_template.ptx` : Template exact de Playback Notes Sync pour l'export CSV vers PTX (pistes MIX, DIAL, SFX, STEPS, FOLEY, ADR et CONCEP).
- `/utils/` : Boîte à outils générique (ex: `text_utils.py` pour nettoyer les strings).

## Conventions et Règles Strictes
1. **Aucun fichier persistant par requête** : Les fichiers entrants et sortants passent par `tempfile.TemporaryDirectory()` puis sont retournés avec `io.BytesIO`. Le backend doit supporter de multiples utilisateurs en parallèle sans collision ni conservation des uploads.
2. **Hygiène du code** : Tout code mort, inutilisé ou toute fonction remplacée doit être immédiatement supprimée pour éviter l'accumulation de dette technique (ex: `aaf_generator.py` a été supprimé quand la génération PTX a été intégrée).
3. **Sécurité** : Aucun mot de passe ou secret ne doit être hardcodé (environnement de production vs local). Les versions de dépendances qui écrivent des PTX doivent être verrouillées pour garantir des exports reproductibles.
