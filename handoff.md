# Handoff - ProTools Post Swiss Knife

## Accomplissements de la journée
- **Résolution de bugs sur Render** : Réglage d'un problème avec uBlock Origin et correction des extensions manquantes (`.xls`, `.xlsx`) dans `ALLOWED_EXTENSIONS` dans `app.py`.
- **Intégration de pt_api** : Remplacement complet du système de conversion "XLS vers AAF" par "XLS vers PTX". L'API `pt_api` a été liée avec succès. Le système charge `template_markers.ptx`, convertit les timecodes via `TimecodeEngine`, et ré-encode le tout en natif.
- **Hygiène du code** : Nettoyage du code mort. `aaf_generator.py` a été supprimé puisque nous utilisons exclusivement `ptx_generator.py` pour les marqueurs Excel.
- **Correction JS** : Correction d'un bug JavaScript de sélection automatique dans `index.html` qui bloquait l'utilisation des boutons radio après renommage en `xls_to_ptx`.

## État Actuel (Bugs Connus)
- Il n'y a aucun bug connu actuellement. Le serveur tourne correctement, le bouton "Générer le PTX (Markers)" fonctionne à 100%, et l'exportation PTX a été validée localement.
- *Attention* : L'API `pt_api` est installée en mode éditable depuis `Y:\pt_api`. Si le projet est cloné sur une autre machine, il faudra s'assurer que l'API soit aussi clonée et installée au même endroit, ou bien adapter les imports.

## Prochaines étapes exactes
1. Déployer sur le serveur cloud (Render.com) via un *Commit and Push* (déjà prêt).
2. Tester la conversion XLS vers PTX en ligne.
3. Si un nouveau format ou outil doit être ajouté, consulter `architecture.md` pour comprendre comment le lier correctement à `app.py` via un nouveau `parser` et un nouveau `generator`.
