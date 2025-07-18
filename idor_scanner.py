import os
import json
import re
import time
import logging
import asyncio
from urllib.parse import urlparse, parse_qs, urljoin, parse_qsl
import requests
from playwright.async_api import async_playwright, Error as PlaywrightError

import config

# --- NOUVELLE LOGIQUE DE SITEMAP ET NORMALISATION ---

VISITED_PATTERNS = set()
SITEMAP_FILE = "sitemap.log"
REQUESTS_TO_TEST = [] # Liste pour stocker les requêtes à tester

# Regex pour la normalisation
UUID_PATTERN = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.I)
NUMBER_PATTERN = re.compile(r'/\d+')
GQL_OPERATION_PATTERN = re.compile(r'(?:query|mutation)\s*\w*\s*{?\s*(\w+)')

def normalize_url(url, method='GET'):
    """Normalise une URL en remplaçant les parties dynamiques."""
    parsed_url = urlparse(url)
    
    # Remplacer les nombres et UUIDs dans le chemin
    path = NUMBER_PATTERN.sub('/{id}', parsed_url.path)
    path = UUID_PATTERN.sub('{id}', path)

    # Normaliser les paramètres de la query string
    query_params = parse_qsl(parsed_url.query)
    if query_params:
        sorted_keys = sorted([key for key, val in query_params])
        query = '&'.join(f'{key}={{...}}' for key in sorted_keys)
    else:
        query = ''

    pattern_path = f"{path}{'?' + query if query else ''}"
    return f"{method.upper()} {pattern_path}"

def normalize_graphql_request(request, body_bytes):
    """Normalise une requête GraphQL en extrayant l'opération principale."""
    path = urlparse(request.url).path
    operation_name = '[unknown_operation]'
    if body_bytes:
        try:
            body_str = body_bytes.decode('utf-8')
            data = json.loads(body_str)
            query = data.get('query', '')
            match = GQL_OPERATION_PATTERN.search(query)
            if match:
                operation_name = match.group(1)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    return f"POST {path} [{operation_name}]"

def add_to_sitemap(pattern):
    """Ajoute un nouveau pattern au sitemap et retourne True si c'est nouveau."""
    if pattern in VISITED_PATTERNS:
        return False
    
    VISITED_PATTERNS.add(pattern)
    with open(os.path.join(config.LOG_DIR, SITEMAP_FILE), 'a') as f:
        f.write(f"{pattern}\n")
    logging.info(f"New endpoint discovered: {pattern}")
    return True

# --- FIN DE LA NOUVELLE LOGIQUE ---


async def setup_browser(playwright):
    """Configure et lance le navigateur avec Playwright."""
    browser = await playwright.chromium.launch(headless=config.HEADLESS_BROWSER)
    context = await browser.new_context(
        user_agent=config.HEADERS.get('User-Agent'),
        extra_http_headers={'Authorization': config.HEADERS.get('Authorization')}
    )
    # Ajout des cookies au contexte
    if config.INITIAL_URLS:
        hostname = urlparse(config.INITIAL_URLS[0]).hostname
        if hostname:
            await context.add_cookies([
                {'name': name, 'value': value, 'domain': hostname, 'path': '/'}
                for name, value in config.COOKIES.items()
            ])
    
    page = await context.new_page()
    return browser, page

def is_in_scope(url):
    """Vérifie si l'URL est dans le scope défini."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith('www.'):
        domain = domain[4:]

    for scope_domain in config.SCOPE:
        if scope_domain.startswith('*.'):
            if domain.endswith(scope_domain[2:]) or domain == scope_domain[2:]:
                return not is_excluded(domain)
        elif domain == scope_domain:
            return not is_excluded(domain)
    return False

def is_excluded(domain):
    """Vérifie si le domaine est dans la liste d'exclusion."""
    for excluded_domain in config.EXCLUDED_DOMAINS:
        if domain == excluded_domain:
            return True
    return False

def is_asset(url):
    """Vérifie si l'URL correspond à un asset statique."""
    path = urlparse(url).path
    return any(path.lower().endswith(ext) for ext in config.EXCLUDED_EXTENSIONS)

def find_key_in_url(url, keys):
    """Recherche une clé exacte dans les segments de l'URL ou les paramètres GET."""
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.strip('/').split('/')
    query_params = parse_qs(parsed_url.query)

    for key in keys:
        str_key = str(key)
        if str_key in path_segments:
            return True
        for param_values in query_params.values():
            if str_key in param_values:
                return True
    return False

def find_key_in_body(body, keys):
    """Recherche une clé exacte dans le corps de la requête (JSON)."""
    if not body:
        return False
    try:
        # Tenter de décoder le corps de la requête
        body_str = body.decode('utf-8', errors='ignore')
        data = json.loads(body_str)
        
        # Ignorer les mutations GraphQL
        if "mutation" in data.get("query", ""):
             return False

        values_to_check = []
        if isinstance(data, dict):
            # Recherche récursive dans les valeurs du JSON
            q = list(data.values())
            while q:
                val = q.pop(0)
                if isinstance(val, dict):
                    q.extend(list(val.values()))
                elif isinstance(val, list):
                    q.extend(val)
                else:
                    values_to_check.append(str(val)) # Convertir en str pour comparaison
        
        for key in keys:
            if str(key) in values_to_check:
                return True

    except (json.JSONDecodeError, AttributeError):
        # Le corps n'est pas du JSON ou n'a pas la structure attendue
        pass
    return False

def log_ignored_request(url, reason):
    """Logue les requêtes ignorées pour le débogage."""
    with open(os.path.join(config.LOG_DIR, config.IGNORED_LOG_FILE), 'a') as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ignored: {url} | Reason: {reason}\n")

def log_vulnerable_request(original_req_data, replayed_response):
    """Enregistre la requête originale et la réponse de la requête rejouée."""
    url = original_req_data['url']
    sanitized_path = re.sub(r'[^a-zA-Z0-9_-]', '_', urlparse(url).path)
    filename = f"{config.VULNERABLE_LOG_FILE_PREFIX}{time.strftime('%Y%m%d_%H%M%S')}_{sanitized_path}.txt"
    filepath = os.path.join(config.LOG_DIR, filename)

    with open(filepath, 'w') as f:
        f.write("--- Original Request ---\n")
        f.write(f"URL: {url}\n")
        f.write(f"Method: {original_req_data['method']}\n")
        f.write("Headers:\n")
        for name, value in original_req_data['headers'].items():
            f.write(f"  {name}: {value}\n")
        if original_req_data['body']:
            f.write("Body:\n")
            try:
                f.write(json.dumps(json.loads(original_req_data['body']), indent=2))
            except (json.JSONDecodeError, TypeError):
                f.write(original_req_data['body'].decode('utf-8', errors='ignore'))
        
        f.write("\n\n\n\n\n====================\n\n\n\n\n")
        
        f.write("--- Replayed Response (Anonymized) ---\n")
        f.write(f"Status Code: {replayed_response.status_code}\n")
        f.write(f"Content-Length: {len(replayed_response.content)}\n")
        f.write("Headers:\n")
        for name, value in replayed_response.headers.items():
            f.write(f"  {name}: {value}\n")
        f.write("Body:\n")
        f.write(replayed_response.text)

    logging.info(f"Potential IDOR found. Log saved to: {filepath}")


async def handle_overlays(page):
    """Detects and closes overlays like cookie banners or pop-ups."""
    logging.info("Checking for overlays...")

    for sel in config.OVERLAY_SELECTORS:
        try:
            overlays = page.locator(sel)
            for i in range(await overlays.count()):
                overlay = overlays.nth(i)
                if await overlay.is_visible():
                    logging.info(f"Found a visible overlay: {sel}. Searching for a close button.")
                    
                    # 1. Try to find by text
                    try:
                        close_button = overlay.locator('button, a, [role="button"]', has_text=config.CLOSE_BUTTON_TEXTS).first
                        if await close_button.is_visible():
                            logging.info(f"Clicking button with text: '{await close_button.text_content()}'")
                            await close_button.click(timeout=3000)
                            await page.wait_for_timeout(500)
                            if not await overlay.is_visible():
                                logging.info("Overlay closed.")
                                continue 
                    except PlaywrightError:
                        pass

                    # 2. Try to find by aria-label
                    for aria_sel in config.ARIA_CLOSE_SELECTORS:
                        try:
                            close_button = overlay.locator(aria_sel).first
                            if await close_button.is_visible():
                                logging.info(f"Clicking button with aria-label selector: {aria_sel}")
                                await close_button.click(timeout=3000)
                                await page.wait_for_timeout(500)
                                if not await overlay.is_visible():
                                    logging.info("Overlay closed.")
                                    break 
                        except PlaywrightError:
                            continue
                    
                    if await overlay.is_visible():
                        logging.warning(f"Could not close overlay '{sel}'. It may interfere with the crawl.")
        except PlaywrightError as e:
            logging.warning(f"Error when handling overlay selector '{sel}': {e}")


async def analyze_and_replay_requests():
    """Analyse les requêtes collectées et les rejoue de manière anonyme."""
    logging.info(f"\n--- Starting Analysis Phase: Testing {len(REQUESTS_TO_TEST)} requests ---\n")
    
    for req_data in REQUESTS_TO_TEST:
        original_response = await req_data['response']
        if not original_response or original_response.status >= 400:
            log_ignored_request(req_data['url'], f"Original request failed (status: {original_response.status if original_response else 'N/A'})")
            continue

        logging.info(f"Replaying anonymously: {req_data['method']} {req_data['url']}")

        headers = {h: v for h, v in req_data['headers'].items() if h.lower() not in ['authorization', 'cookie']}
        
        try:
            replayed_response = requests.request(
                method=req_data['method'],
                url=req_data['url'],
                headers=headers,
                data=req_data['body'],
                verify=False,
                timeout=10
            )
            
            is_ok = replayed_response.status_code < 400
            content_lower = replayed_response.text.lower()
            has_unauthorized_word = any(keyword in content_lower for keyword in config.UNAUTHORIZED_KEYWORDS)
            
            if is_ok and not has_unauthorized_word:
                log_vulnerable_request(req_data, replayed_response)
            else:
                reason = f"Replay failed with status {replayed_response.status_code}"
                if has_unauthorized_word:
                    reason += " (contains unauthorized keyword)"
                log_ignored_request(req_data['url'], reason)

        except requests.exceptions.RequestException as e:
            logging.error(f"Error replaying request to {req_data['url']}: {e}")


async def crawl(page):
    """Parcourt le site en cliquant sur tous les éléments interactifs de manière robuste."""
    urls_to_visit = list(config.INITIAL_URLS)
    visited_urls = set()
    interacted_elements = set() # Pour suivre les éléments interactifs uniques

    def get_url_base(u):
        """Retourne l'URL sans la query string pour éviter les doublons de crawl."""
        parsed = urlparse(u)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    while urls_to_visit:
        url = urls_to_visit.pop(0)
        
        url_base = get_url_base(url)
        if url_base in visited_urls:
            continue
        
        # CORRECTION: Marquer l'URL de base comme visitée AVANT la navigation
        # pour empêcher les boucles infinies dues aux redirections.
        visited_urls.add(url_base)

        if not is_in_scope(url):
            continue

        try:
            logging.info(f"Crawling page: {url}")
            await page.goto(url, wait_until='networkidle', timeout=20000)
            await page.wait_for_timeout(2000) # Extra wait for dynamic content
            
            await handle_overlays(page)
            
            current_url = page.url
            # S'assurer que l'URL finale (après redirection) est aussi marquée
            visited_urls.add(get_url_base(current_url))

            # --- 1. Collecter tous les liens href pour le crawling ---
            all_links = await page.locator('a[href]').all()
            for link_element in all_links:
                href = await link_element.get_attribute('href')
                if not href:
                    continue
                
                absolute_url = urljoin(current_url, href)
                if is_in_scope(absolute_url) and get_url_base(absolute_url) not in visited_urls:
                    if absolute_url not in urls_to_visit:
                        logging.info(f"Found new URL to visit: {absolute_url}")
                        urls_to_visit.append(absolute_url)

            # --- 2. Cliquer sur les éléments interactifs pour déclencher des requêtes ---
            clickable_selector = "a, button, [role='button'], [role='link'], [onclick]"
            elements = page.locator(clickable_selector)
            num_elements = await elements.count()
            logging.info(f"Found {num_elements} clickable elements on {current_url} to interact with.")

            for i in range(num_elements):
                # On doit re-localiser l'élément à chaque itération car le DOM peut changer
                element = page.locator(clickable_selector).nth(i)
                try:
                    if not await element.is_visible() or not await element.is_enabled():
                        continue

                    # --- NOUVEAU: GESTION D'ÉTAT POUR LES ÉLÉMENTS INTERACTIFS ---
                    tag = (await element.tag_name() or '').lower()
                    text = (await element.text_content() or '').strip()
                    
                    signature_content = text.lower()
                    element_signature = f"{tag}:{signature_content}"

                    # Pour les liens sans texte, une signature basée sur le href est plus fiable
                    if tag == 'a' and not signature_content:
                        href = (await element.get_attribute('href') or '').strip()
                        if href and not href.startswith(('javascript:', '#')):
                            element_signature = f"a:href:{urlparse(href).path}"
                        else:
                            # Ignorer les ancres simples ou liens javascript non signifiants
                            continue
                    
                    # Ignorer les boutons/éléments sans texte pour éviter les clics répétitifs sur des icones génériques
                    if not signature_content and tag != 'a':
                        continue
                        
                    if element_signature in interacted_elements:
                        continue # Déjà interagi avec un élément similaire, on ignore.
                    
                    interacted_elements.add(element_signature)
                    # --- FIN DE LA GESTION D'ÉTAT ---

                    logging.info(f"Clicking element #{i+1}/{num_elements}: '{text or 'No text'}' (Signature: {element_signature})")
                    
                    # --- NOUVEAU: Gérer la navigation après un clic ---
                    url_before_click = page.url
                    
                    await element.click(timeout=5000, no_wait_after=True)
                    await page.wait_for_timeout(1500) # Attendre pour que la navigation/requête se déclenche

                    # Si l'URL a changé, une navigation a eu lieu.
                    if page.url != url_before_click:
                        logging.info(f"Navigation detected after click, from {url_before_click} to {page.url}.")
                        new_url = page.url
                        if is_in_scope(new_url) and get_url_base(new_url) not in visited_urls:
                            if new_url not in urls_to_visit:
                                urls_to_visit.append(new_url)
                        # On arrête de traiter les éléments de la page précédente.
                        break
                    
                    await handle_overlays(page) # Gérer les overlays qui peuvent apparaître après un clic

                except PlaywrightError as click_error:
                    # Si l'élément a disparu (ex: navigation), on ignore et continue
                    logging.warning(f"Could not interact with element #{i+1}: {click_error.__class__.__name__}. Skipping.")
                    if "navigation" in str(click_error).lower():
                        logging.warning("Breaking interaction loop due to navigation error.")
                        break
                    continue
        
        except PlaywrightError as page_error:
            logging.error(f"Playwright error on page {url}: {page_error}. Moving to next URL.")
            continue
        except Exception as e:
            logging.error(f"A general error occurred on page {url}: {e}. Moving to next URL.")
            continue


def request_handler(request):
    """Intercepte et filtre les requêtes pour les ajouter à la liste de test."""
    url = request.url

    if not is_in_scope(url) or is_asset(url):
        return

    method = request.method
    is_get = method.upper() == 'GET'
    is_graphql_post = (method.upper() == 'POST' and 
                       urlparse(url).path in config.GRAPHQL_PATHS)

    pattern = None
    if is_get:
        pattern = normalize_url(url, 'GET')
    elif is_graphql_post:
        pattern = normalize_graphql_request(request, request.post_data_buffer)
    else:
        return

    if not add_to_sitemap(pattern):
        return
        
    key_found_in_url = find_key_in_url(url, config.KEYS)
    key_found_in_body = False
    if is_graphql_post:
        key_found_in_body = find_key_in_body(request.post_data_buffer, config.KEYS)

    if not key_found_in_url and not key_found_in_body:
        return

    logging.info(f"Request added to test queue: {pattern}")
    REQUESTS_TO_TEST.append({
        "url": url,
        "method": method,
        "headers": request.headers,
        "body": request.post_data_buffer,
        "response": request.response()
    })

async def main():
    """Fonction principale du script."""
    if not os.path.exists(config.LOG_DIR):
        os.makedirs(config.LOG_DIR)
        
    log_files_to_clear = [config.IGNORED_LOG_FILE, config.SITEMAP_FILE, config.APP_LOG_FILE]
    for log_file_name in log_files_to_clear:
        log_file = os.path.join(config.LOG_DIR, log_file_name)
        if os.path.exists(log_file):
            open(log_file, 'w').close()
            
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(config.LOG_DIR, config.APP_LOG_FILE)),
            logging.StreamHandler()
        ]
    )

    # --- Phase 1: Spidering & Collecte ---
    async with async_playwright() as p:
        browser, page = await setup_browser(p)
        page.on('request', request_handler)
        
        logging.info("--- Starting Spidering Phase ---")
        try:
            await crawl(page)
        except Exception as e:
            logging.error(f"An unexpected error occurred during crawl: {e}")
        finally:
            logging.info("Crawl finished. Shutting down browser.")
            await browser.close()

    # --- Phase 2: Analyse hors-ligne ---
    await analyze_and_replay_requests()
    
    logging.info("--- Scan complete ---")

if __name__ == "__main__":
    # Ignorer les avertissements InsecureRequestWarning de 'requests'
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    asyncio.run(main()) 