# Handoff - ProTools Post Swiss Knife

## Accomplissements de la journée
- **CSV vers PTX — Playback Notes Sync** : Ajout du flux qui lit l'export CSV UTF-8 de Playback Notes Sync et recrée les Clip Groups vides de 2 secondes sur les pistes du template natif. Il accepte les formats `MMSS` et `HH:MM:SS:`, et refuse les timecodes impossibles avec le numéro de ligne concerné.
- **Template et dépendance PTX** : Ajout de `pb_notes_sync_template.ptx` et verrouillage de `pt_api` à la version 1.5.1 dans `requirements.txt`.
- **Résolution de bugs sur Render** : Réglage d'un problème avec uBlock Origin et correction des extensions manquantes (`.xls`, `.xlsx`) dans `ALLOWED_EXTENSIONS` dans `app.py`.
- **Intégration de pt_api** : Remplacement complet du système de conversion "XLS vers AAF" par "XLS vers PTX". L'API `pt_api` a été liée avec succès. Le système charge `template_markers.ptx`, convertit les timecodes via `TimecodeEngine`, et ré-encode le tout en natif.
- **Hygiène du code** : Nettoyage du code mort. `aaf_generator.py` a été supprimé puisque nous utilisons exclusivement `ptx_generator.py` pour les marqueurs Excel.
- **Correction JS** : Correction d'un bug JavaScript de sélection automatique dans `index.html` qui bloquait l'utilisation des boutons radio après renommage en `xls_to_ptx`.

## État Actuel (Bugs Connus)
- Aucun bug connu sur les flux validés localement : XLS vers PTX Markers et CSV vers PTX Playback Notes Sync.
- `pt_api` est installé depuis Git dans la version 1.5.1 définie par `requirements.txt`; aucun clone local de `Y:\pt_api` n'est nécessaire.

## Prochaines étapes exactes
1. Déployer sur le serveur cloud (Render.com) via un *Commit and Push* (déjà prêt).
2. Tester les conversions XLS vers PTX et CSV vers PTX en ligne.
3. Si un nouveau format ou outil doit être ajouté, consulter `architecture.md` pour comprendre comment le lier correctement à `app.py` via un nouveau `parser` et un nouveau `generator`.
