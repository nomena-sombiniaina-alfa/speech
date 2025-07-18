
"""
Configuration for the IDOR scanner.
"""
import re

# --- CIBLE ---
# Domaines à inclure dans le scan.
# Wildcards supportés: *.example.com
SCOPE = ['localhost:3000']

# URLs de départ pour le crawling.
INITIAL_URLS = [
    'http://localhost:3000/#/'
    # 'https://www.bhhs.com/bad-request-error'
]

# Domaines à exclure explicitement du scan.
EXCLUDED_DOMAINS = [
    # 'google.com', 
    # 'facebook.com', 
    # 'clarity.ms', 
    # 'vimeo.com',
    # 'livechatinc.com',
    # 'googletagmanager.com'
]

# --- SESSION & AUTHENTIFICATION ---
# Cookies à utiliser pour la session authentifiée.
COOKIES = {
    'csrftoken': 'tQWWPH9vidyOYcBWSTTAV5XZEBbadvGe',
    'continueCode': 'WM4D1MBbj7XPazZRm1x52LrpnoEALDfQ4AgyQ9ON3kvqDK8l6VJWw4eY7wbl',
    'language': 'en',
    'sessionid': 'uy1wff025s6zdqysozliqfy0pf88eo55',
    'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdGF0dXMiOiJzdWNjZXNzIiwiZGF0YSI6eyJpZCI6MjQsInVzZXJuYW1lIjoiIiwiZW1haWwiOiJ0ZXN0LTFAanVpY2Utc2hvcC5jb20iLCJwYXNzd29yZCI6IjA5YjNlYjFlNjlhYzBiNzQ1NDIxNDkxZDFjYzdmYTg2Iiwicm9sZSI6ImN1c3RvbWVyIiwiZGVsdXhlVG9rZW4iOiIiLCJsYXN0TG9naW5JcCI6IiIsInByb2ZpbGVJbWFnZSI6Ii9hc3NldHMvcHVibGljL2ltYWdlcy91cGxvYWRzL2RlZmF1bHQuc3ZnIiwidG90cFNlY3JldCI6IiIsImlzQWN0aXZlIjp0cnVlLCJjcmVhdGVkQXQiOiIyMDI1LTA3LTE4IDEwOjQ4OjEyLjI5MiArMDA6MDAiLCJ1cGRhdGVkQXQiOiIyMDI1LTA3LTE4IDEyOjE0OjEzLjA0MyArMDA6MDAiLCJkZWxldGVkQXQiOm51bGx9LCJpYXQiOjE3NTI4NDA5NDR9.vqf4LH7vWWkAyu9Okj-p3U9A0lEJLuyp6vftbpYHBg4AMUl5d1Fbv0CDkxaiWgreVP97vwgllIH4tt4p5BkcsdoIokVz_VaNTyT1PdFpEKPa1qJsk6nZ4KEOat4bGwttNxF_3r6gy4gr7MXFHdQ4cmC1faGN7DN_0NExTYNKaIw',
    'welcomebanner_status': 'dismiss',
    
    # 'session_id': '...',
    # 'remember_me': '...'
}

# Headers HTTP à envoyer avec chaque requête du navigateur.
# Le header 'Authorization' est particulièrement important.
HEADERS = {
    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdGF0dXMiOiJzdWNjZXNzIiwiZGF0YSI6eyJpZCI6MjQsInVzZXJuYW1lIjoiIiwiZW1haWwiOiJ0ZXN0LTFAanVpY2Utc2hvcC5jb20iLCJwYXNzd29yZCI6IjA5YjNlYjFlNjlhYzBiNzQ1NDIxNDkxZDFjYzdmYTg2Iiwicm9sZSI6ImN1c3RvbWVyIiwiZGVsdXhlVG9rZW4iOiIiLCJsYXN0TG9naW5JcCI6IiIsInByb2ZpbGVJbWFnZSI6Ii9hc3NldHMvcHVibGljL2ltYWdlcy91cGxvYWRzL2RlZmF1bHQuc3ZnIiwidG90cFNlY3JldCI6IiIsImlzQWN0aXZlIjp0cnVlLCJjcmVhdGVkQXQiOiIyMDI1LTA3LTE4IDEwOjQ4OjEyLjI5MiArMDA6MDAiLCJ1cGRhdGVkQXQiOiIyMDI1LTA3LTE4IDEyOjE0OjEzLjA0MyArMDA6MDAiLCJkZWxldGVkQXQiOm51bGx9LCJpYXQiOjE3NTI4NDA5NDR9.vqf4LH7vWWkAyu9Okj-p3U9A0lEJLuyp6vftbpYHBg4AMUl5d1Fbv0CDkxaiWgreVP97vwgllIH4tt4p5BkcsdoIokVz_VaNTyT1PdFpEKPa1qJsk6nZ4KEOat4bGwttNxF_3r6gy4gr7MXFHdQ4cmC1faGN7DN_0NExTYNKaIw',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
    # 'Authorization': 'Bearer ...'
}

# --- LOGIQUE DE DÉTECTION ---
# Clés (str ou int) à rechercher dans les requêtes. 
# La présence d'une de ces clés marque une requête comme "intéressante".
# Le matching est EXACT.
KEYS = [
    'test-1@juce-shop.com', # Exemple: UUID
    26,                              # Exemple: ID numérique
    7
]

# Chemins considérés comme des endpoints GraphQL.
GRAPHQL_PATHS = [
    # '/graphql', '/api/graphql'
    ]

# Mots-clés indiquant qu'une ressource n'est pas accessible.
# Utilisé pour vérifier la réponse des requêtes rejouées sans authentification.
# La recherche est insensible à la casse.
UNAUTHORIZED_KEYWORDS = [
    'unauthorized', 'forbidden', 'access denied', 'auth required', 
    'session expired', 'veuillez vous connecter'
]

# --- FILTRES ---
# Extensions de fichiers à ignorer.
# Les requêtes pour ces ressources ne seront pas analysées.
EXCLUDED_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico',
    '.css', '.js', '.map',
    '.woff', '.woff2', '.ttf', '.eot',
    '.mp4', '.webm',
    '.pdf'
]

# --- CONFIGURATION DU SCANNER ---
# Activer le mode headless pour le navigateur.
# Mettre à False pour voir le navigateur en action (utile pour le débogage).
HEADLESS_BROWSER = True

# --- GESTION DES OVERLAYS (POPUPS, BANNIÈRES DE COOKIES) ---
# Sélecteurs CSS pour identifier les overlays.
OVERLAY_SELECTORS = [
    '[role="dialog"]', '[aria-modal="true"]', '#onetrust-banner-sdk', 
    'div[class*="modal"]', 'div[class*="overlay"]', 'div[class*="popup"]',
    'div[class*="banner"]'
]

# Textes ou expressions régulières pour trouver les boutons de fermeture.
# Insensible à la casse.
CLOSE_BUTTON_TEXTS = re.compile(
    r"^(accept|agree|close|ok|continue|dismiss|got it|i agree|i accept|yes|allow all|accept all|j'accepte|fermer)$", 
    re.IGNORECASE
)

# Sélecteurs ARIA pour les boutons de fermeture.
ARIA_CLOSE_SELECTORS = [
    '[aria-label*="close" i]',
    '[aria-label*="accept" i]',
    '[aria-label*="agree" i]',
]

# --- LOGS ---
# Dossier où seront sauvegardés les logs.
LOG_DIR = 'idor_logs'

# Fichier pour les logs généraux.
APP_LOG_FILE = 'scan.log'

# Fichier pour les requêtes ignorées lors de la phase de replay.
IGNORED_LOG_FILE = 'ignored_requests.log'

# Fichier sitemap pour suivre les endpoints uniques découverts.
SITEMAP_FILE = "sitemap.log"

# Préfixe pour les fichiers de log des vulnérabilités potentielles.
VULNERABLE_LOG_FILE_PREFIX = 'VULNERABLE_' 