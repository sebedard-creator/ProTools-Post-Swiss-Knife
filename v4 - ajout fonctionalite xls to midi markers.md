# Master Prompt : Intégration de Marqueurs (CommentMarkers) XLS vers AAF via pyaaf2

## Contexte du Projet
Je développe une application en Python qui génère et manipule des fichiers AAF pour **Pro Tools** en utilisant la librairie `pyaaf2`. Le but actuel est d'ajouter une nouvelle fonctionnalité : importer une liste de repères (cues) depuis un fichier Excel (`.xlsx` ou `.xls`) et les injecter sous forme de marqueurs de timeline (**Memory Locations** dans Pro Tools) directement dans le fichier AAF généré par mon pipeline.

## Objectif
Tu dois agir comme un ingénieur logiciel expert en Python et en formats de métadonnées de postproduction audio/vidéo (AAF). Ton but est de générer un module de code propre, robuste et modulaire que je pourrai intégrer directement dans mon script existant pour accomplir cette tâche.

## Spécifications Techniques

### 1. Entrées (Inputs)
- **Fichier Excel (`.xlsx`)** : Contient une liste de cues avec au minimum deux colonnes :
  - `tc_in` : Le Timecode de début au format chaîne de caractères (ex: `01:00:15:12`).
  - `commentaire` : Le texte ou la note associée au marqueur (ex: `Effet sonore - Ambiance`).
- **Configuration du projet** :
  - `framerate` (Edit Rate) : La cadence de la session (ex: 24, 25, 23.976, 29.97).
  - `start_timecode` : Le timecode de départ de la timeline AAF (ex: `01:00:00:00`) pour calculer un offset si nécessaire.

### 2. Logique de Traitement attendue
1. **Parsing de l'Excel** : Utiliser `pandas` (avec le moteur `openpyxl`) pour lire le fichier Excel et itérer sur les lignes de manière propre.
2. **Conversion de Timecode en Frames** : Écrire une fonction de parsing capable de convertir une chaîne `HH:MM:SS:FF` en un nombre absolu de frames (entier), basé sur le `framerate`. Gérer idéalement les séparateurs classiques (`:`, `;`, `.`).
3. **Gestion des Objets AAF (`pyaaf2`)** :
   - Cibler ou créer la `CompositionMob` principale (la timeline).
   - Récupérer la définition de données requise pour les métadonnées descriptives : `f.dictionary.lookup_datadef("DescriptiveMetadata")`.
   - Créer une `Sequence` de type `DescriptiveMetadata`.
   - Pour chaque ligne du fichier Excel, instancier un objet `f.create.CommentMarker()`.
   - Configurer minutieusement ses attributs obligatoires pour Pro Tools :
     - `.data_def = descriptive_def`
     - `.position = position_en_frames` (calculée par rapport au zéro absolu de la timeline)
     - `.length = 1` (un marqueur Pro Tools est un point fixe, sa durée doit être de 1 frame)
     - `.name = f"Cue_{index}"` (ou une valeur par défaut)
     - `.comment = commentaire_du_xls`
   - Ajouter chaque `CommentMarker` aux composants (`components`) de la séquence.
   - Attacher cette séquence à la `CompositionMob` en tant que nouveau slot de timeline (`append_new_timeline_slot`).

## Ce que tu dois me fournir :
1. **Une fonction de conversion robuste** : `timecode_to_frames(tc_str, framerate)` bien documentée avec gestion des erreurs si le format est invalide.
2. **Une fonction principale d'injection** : `inject_excel_markers(aaf_file_path, excel_path, framerate, target_sheet=0)` contenant toute la logique d'ouverture de l'AAF (en mode lecture/écriture ou modification) et d'insertion des données.
3. **Gestion des cas aux limites (Edge Cases)** : 
   - Que faire si une cellule `commentaire` ou `tc_in` est vide (sauter la ligne proprement avec un log).
   - Prise en compte de l'offset si la session ne commence pas à `00:00:00:00`.
4. **Explications claires** : Ajoute des commentaires détaillés dans le code pour expliquer l'arborescence des objets AAF utilisés (`CompositionMob` -> `TimelineMobSlot` -> `Sequence` -> `CommentMarker`).

Donne-moi un code Python moderne, typé (Type Hinting) et hautement optimisé pour l'intégration.
