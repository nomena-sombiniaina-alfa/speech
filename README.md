# IDOR Scanner

Ce script est un outil de test de sécurité automatisé conçu pour détecter les vulnérabilités de type Insecure Direct Object References (IDOR) dans une application web. Il utilise Selenium pour naviguer sur le site comme un utilisateur authentifié, intercepte les requêtes HTTP, et tente de rejouer ces requêtes en modifiant des identifiants (comme des ID d'utilisateur, des UUID, etc.) pour voir s'il peut accéder à des données qui ne devraient pas être accessibles.

## Fonctionnalités

- **Exploration automatique (Crawling)**: Navigue sur le site à partir d'une URL de départ pour découvrir des pages et des fonctionnalités.
- **Interception de requêtes**: Utilise `selenium-wire` pour capturer toutes les requêtes HTTP (GET, POST, etc.) effectuées par le navigateur.
- **Substitution d'ID**: Remplace les identifiants trouvés dans les URLs, les corps de requêtes et les en-têtes par des valeurs alternatives définies par l'utilisateur.
- **Rejeu de requêtes**: Rejoue les requêtes modifiées en utilisant la bibliothèque `requests`.
- **Analyse des réponses**: Compare la réponse de la requête modifiée avec la réponse originale. Si les codes de statut sont les mêmes (par exemple, `200 OK`) et que le contenu des pages est très similaire, cela peut indiquer une vulnérabilité IDOR.
- **Journalisation (Logging)**: Crée un fichier de log détaillé pour chaque vulnérabilité potentielle trouvée, contenant la requête originale et la requête modifiée.

## Prérequis

- Python 3.7+
- Google Chrome (ou un autre navigateur supporté par Selenium WebDriver)

## Installation

1.  **Clonez le projet ou téléchargez les fichiers.**

2.  **Installez les dépendances Python :**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Téléchargez le bon WebDriver :**
    Assurez-vous que `chromedriver` (ou le driver de votre navigateur) est dans votre `PATH` ou que son emplacement est connu de Selenium. Souvent, `selenium-wire` peut le gérer automatiquement s'il est installé via un gestionnaire de paquets.

## Configuration

Ouvrez le fichier `idor_scanner.py` et modifiez la section `main()` pour configurer le scanner selon vos besoins :

```python
def main():
    # --- CONFIGURATION ---
    # Remplacez ces valeurs par les vôtres
    config = {
        "start_url": "https://votre-site.com/dashboard",
        "cookies": [
            {'name': 'session', 'value': 'VOTRE_COOKIE_DE_SESSION', 'domain': '.votre-site.com'}
            # Ajoutez d'autres cookies si nécessaire
        ],
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        },
        # Dictionnaire des IDs à remplacer.
        # Clé = ID de l'utilisateur A (celui connecté)
        # Valeur = ID de l'utilisateur B (la cible)
        "id_map": {
            "12345": "67890",
            "user-a-uuid": "user-b-uuid",
        },
        # URLs à ne pas visiter (déconnexion, suppression de compte, etc.)
        "excluded_urls": [
            "/logout",
            "/account/delete"
        ],
        "output_dir": "idor_logs"
    }

    scanner = IDORScanner(config)
    scanner.crawl()
```

### Comment obtenir les cookies ?

1.  Connectez-vous à votre application web avec le compte de l'utilisateur A.
2.  Ouvrez les outils de développement de votre navigateur (F12).
3.  Allez dans l'onglet `Application` (ou `Stockage`).
4.  Trouvez les cookies de votre site et copiez la valeur du cookie de session (et d'autres si nécessaire).
5.  Collez ces informations dans la section `cookies` de la configuration.

## Utilisation

Une fois le script configuré, lancez-le depuis votre terminal :

```bash
python idor_scanner.py
```

Le script commencera à naviguer sur le site et à tester les vulnérabilités. Les logs des vulnérabilités potentielles seront sauvegardés dans le dossier `idor_logs` (ou celui que vous avez configuré).

## Avertissement

Cet outil est destiné à être utilisé dans un cadre légal, par exemple pour des tests d'intrusion autorisés (pentesting) sur vos propres applications ou celles pour lesquelles vous avez la permission de tester. L'utilisation de cet outil sur des systèmes sans autorisation préalable est illégale. 