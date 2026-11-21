# Strawberry Studio — version 0.4 (préparation EXE)

Cette archive prépare la création d'une application Windows autonome. Le fichier `.exe` est construit sur un environnement Windows via GitHub Actions ; aucun Python ne sera nécessaire sur le PC qui utilisera le fichier final.

## Création du fichier StrawberryStudio.exe

1. Décompressez cette archive.
2. Créez un dépôt GitHub (Public ou Private) et ajoutez-y le contenu du dossier `Strawberry_Studio` en conservant le dossier `.github`.
3. Dans GitHub, ouvrez l'onglet **Actions**.
4. Sélectionnez **Build Strawberry Studio for Windows**, puis **Run workflow**.
5. À la fin, ouvrez l'exécution terminée et téléchargez l'artefact **StrawberryStudio-Windows**.
6. Décompressez l'artefact : il contient `StrawberryStudio.exe`.

Le workflow installe Python uniquement sur le serveur de compilation GitHub. Python n'est pas requis sur le PC qui exécute le `.exe`.

## Utilisation

- Lancez `StrawberryStudio.exe`.
- Ouvrez la rubrique **Connexion ZEPETO** puis cliquez sur **Ouvrir ZEPETO LIVE**.
- Connectez-vous dans la fenêtre Chrome/Edge dédiée.
- L'overlay OBS est servi localement à `http://127.0.0.1:8765/overlay`.

Les paramètres sont conservés dans `%LOCALAPPDATA%\StrawberryStudio`.

## État du projet

Le connecteur ZEPETO est expérimental et dépend de la structure HTML actuelle de ZEPETO LIVE. La compilation réussie ne garantit pas encore que la récupération du chat et des cadeaux fonctionne sur toutes les versions du site. Le connecteur doit être testé avec un vrai live.
