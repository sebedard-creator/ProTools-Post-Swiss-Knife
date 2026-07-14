# ProTools Post Swiss Knife - Architecture

## Stack Technique
- **Backend** : Python 3.11 avec le framework web Flask.
- **Frontend** : HTML, CSS Vanille, JS (dans `index.html`) pour une application single-page (SPA).
- **Dépendances tierces** : `openpyxl` (lecture/écriture Excel), `pyaaf2` (génération AAF), `reportlab` (générateur PDF).
- **API Externe Locale** : `pt_api` (manipulation native de sessions Pro Tools .ptx). L'API est installée via `pip install -e Y:\pt_api`.

## Structure du Projet
- `/app.py` : Le serveur Flask (contrôleur principal), qui route chaque requête web. Il s'occupe de la gestion des fichiers avec `tempfile` (100% en RAM via `io.BytesIO`).
- `/templates/index.html` : L'interface utilisateur. Contient des scripts JS pour valider les extensions de fichiers et mettre à jour l'état du formulaire.
- `/parsers/` : Les scripts qui lisent les fichiers entrants (ex: `excel_parser.py` pour extraire les marqueurs).
- `/generators/` : Les scripts qui formatent et écrivent le format de sortie (ex: `pdf_generator.py`, `ptx_generator.py`).
- `/utils/` : Boîte à outils générique (ex: `text_utils.py` pour nettoyer les strings).

## Conventions et Règles Strictes
1. **Zéro accès disque temporaire persistant** : Tous les fichiers générés par le serveur Flask au moment des requêtes web doivent utiliser `tempfile.TemporaryDirectory()` et être retournés depuis la RAM via `io.BytesIO`. Le backend doit supporter de multiples utilisateurs en parallèle sans collision.
2. **Hygiène du code** : Tout code mort, inutilisé ou toute fonction remplacée doit être immédiatement supprimée pour éviter l'accumulation de dette technique (ex: `aaf_generator.py` a été supprimé quand la génération PTX a été intégrée).
3. **Sécurité** : Aucun mot de passe ou secret ne doit être hardcodé (environnement de production vs local). Les dépendances locales (`Y:\pt_api`) sont documentées pour la pérennité.
