# 🎬 ProTools Post Swiss Knife (PT SK 4.1)

Une application web complète conçue pour convertir les exports de session Avid Pro Tools (.txt, .csv, .xls, .xlsx) vers de multiples formats prêts pour la post-production (PDF, Excel, AAF, EDL).

## 📁 Fonctionnalités (Ce que fait le Swiss Knife)

L'application offre une interface simple (glisser-déposer) permettant de convertir des fichiers en un clic.

### 📍 Markers & Spotting (Entrée: `.txt`)
- **MARKERS** : Exporte les markers d'une session Pro Tools en PDF compact (Timecode + Nom).
- **SPOTTING** : Crée un PDF listant tous les clips par track avec timecodes IN/OUT, durée, nom du clip et état muté/non-muté.

### 🎙️ ADR (Entrée: `.txt`)
- **ADR CHARACTER ORDER** : Crée un fichier Excel organisé par personnage. Chaque section affiche le nom suivi du nombre de lignes, puis les cues avec timecodes, durée, texte et commentaire.
- **ADR TC ORDER** : Crée un fichier Excel avec tous les cues de tous les personnages dans une liste unique triée par timecode.
- **ADR RECORDING** : Génère un ZIP contenant deux PDFs par personnage (feuille ACTEUR et feuille TECHNICIEN avec prise alternative). 

### 🔄 Conversions & AAF
- **CSV VERS EDL** : Convertit un fichier CSV (provenant d'une template de notes) en EDL Pro Tools (.edl).
- **CSV VERS PDF (TC ORDER)** : Convertit un CSV de notes en PDF trié par timecode.
- **CSV VERS AAF (FAKE AUDIO TRACKS)** : Conversion directe d'un CSV vers un AAF contenant des clips audio vides, avec suffixe de mode (Production ou Conception).
- **XLS VERS AAF MARKERS** : Génère une piste de marqueurs (Memory Locations) à 23.976 fps directement à partir d'un fichier Excel. Recherche automatiquement les colonnes et contourne les limites de caractères de Pro Tools.

## 🚀 Utilisation (Local vs Cloud)

### Option 1 : Utilisation Locale
Le code fonctionne de manière autonome sur votre ordinateur.
1. Lancez le fichier `run_app.bat` (ou le script de démarrage Mac/Windows correspondant).
2. Ouvrez votre navigateur Web à l'adresse `http://localhost:5000`.

### Option 2 : Déploiement Web (Render.com)
L'application est 100% cloud-ready (gérée en mémoire vive via `io.BytesIO` et `tempfile` pour éviter les collisions entre utilisateurs) et peut être hébergée gratuitement.
1. Poussez le code sur un dépôt **GitHub** public.
2. Liez le dépôt à **Render.com** en créant un nouveau **Web Service**.
3. **Build Command** : `pip install -r requirements.txt`
4. **Start Command** : `gunicorn app:app`
5. L'application se mettra à jour automatiquement (CI/CD) à chaque fois qu'un "Push" est fait sur la branche principale GitHub.

## 🔧 Architecture & Dépendances

- **Web Framework** : Flask / Gunicorn
- **Manipulation PDF** : ReportLab
- **Manipulation Excel** : OpenPyXL
- **Manipulation AAF** : pyaaf2
- Le projet contient un fichier `.gitignore` et `requirements.txt` prêts pour la production.

---
*© Sébastien Bédard - 2025-2026*
