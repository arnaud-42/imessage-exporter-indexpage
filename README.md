# imessage-exporter-indexpage

# 💬 Conversation Index Generator (Indexation des Fichiers HTML de Chat)

## Introduction

Ce script Python (`index-generator.py`) est un outil d'analyse et d'indexation conçu pour faciliter la recherche et la gestion des conversations exportées au format HTML par le projet imessage-exporter.

Il analyse un dossier rempli de fichiers de conversation HTML (un fichier par contact/conversation), extrait les métadonnées clés (Nom du contact, Date du dernier message, Nombre de messages), et génère une page d'index HTML unique (`index.html`).

L'index généré est interactif et permet de **trier**, de **filtrer** par date et de réaliser des **recherches plein texte** ultra-rapides dans des milliers de messages, même sans connexion Internet.

## ✨ Fonctionnalités Clés

* **Indexation Rapide :** Génère un index à partir de tous les fichiers HTML d'un dossier spécifié.
* **Tri Dynamique :** Trie l'index directement dans le navigateur par Contact, Date du dernier message ou Nombre de messages.
* **Recherche Multifacette :** Filtre par nom de contact, par date, et par contenu des messages.
* **Recherche "Fuzzy" :** Inclut un mode de recherche approximative (Fuzzy search) pour trouver des termes même en cas de fautes de frappe ou d'orthographe légère.
* **Aperçu des Messages :** Affiche un extrait du message pertinent directement dans l'index lors d'une recherche par contenu.
* **Localisation :** Supporte le Français (`-l fr`) et l'Anglais (`-l en`), avec un changement de langue dynamique dans l'interface.

## ⚙️ Prérequis

Ce script est écrit en **Python 3**.

* **Python :** Assurez-vous d'avoir Python 3 installé sur votre système.
* **Fichiers Source :** Un dossier contenant uniquement les fichiers de conversation exportés au format `.html`.

## 🖥️ Utilisation

### 1. Téléchargement et Configuration

1.  Placez le script **`index-generator.py`** dans le répertoire de votre choix.
2.  Créez un dossier (par exemple, `conversations/`) et placez-y tous vos fichiers HTML de conversation.

### 2. Exécution du Script

Ouvrez votre terminal ou invite de commande, naviguez jusqu'au répertoire où se trouve **`index-generator.py`**, et exécutez la commande suivante en remplaçant `<VOTRE_DOSSIER_CONVERSATIONS>` par le chemin de votre dossier :

```bash
# Exemple en utilisant le français (par défaut)
python3 index-generator.py <VOTRE_DOSSIER_CONVERSATIONS>

# Exemple en utilisant l'anglais
python3 index-generator.py <VOTRE_DOSSIER_CONVERSATIONS> -l en

# Pour spécifier un nom de fichier de sortie différent (ex: mon_index.html)
python3 index-generator.py <VOTRE_DOSSIER_CONVERSATIONS> -o mon_index.html
