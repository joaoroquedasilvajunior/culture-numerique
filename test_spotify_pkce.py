#!/usr/bin/env python3
"""
Test PKCE — les champs popularité/followers reviennent-ils avec un token
utilisateur (Authorization Code + PKCE) au lieu du token app (client
credentials) ?

Hypothèse à tester : le verrouillage de février 2026 est par palier d'app
(Development Mode), donc le type de token ne devrait rien changer. Mais
on mesure au lieu de présumer.

PRÉREQUIS (une fois, 2 minutes) :
  1. Dashboard Spotify → ton app → Settings → Redirect URIs
     → ajouter exactement :  http://127.0.0.1:8888/callback
  2. export SPOTIFY_CLIENT_ID="ton_client_id"   (pas besoin du secret : PKCE)

Usage :  python3 test_spotify_pkce.py
Le navigateur s'ouvre, tu autorises, le verdict s'affiche en console.
"""

import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
REDIRECT_URI = "http://127.0.0.1:8888/callback"
PORT = 8888
# Céline Dion — l'ID le plus sûr du catalogue pour un test
ARTIST_ID = "4S9EykWXhStSc15wEx8QFK"

if not CLIENT_ID:
    sys.exit("export SPOTIFY_CLIENT_ID=... d'abord.")

# --- PKCE ---
verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()
challenge = base64.urlsafe_b64encode(
    hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()

auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
    "client_id": CLIENT_ID,
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "code_challenge_method": "S256",
    "code_challenge": challenge,
    # Aucun scope : les métadonnées catalogue n'en demandent pas.
})

code_holder = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(qs)
        if "code" in params:
            code_holder["code"] = params["code"][0]
            body = "<h2>Autorisation reçue, retourne au terminal.</h2>".encode("utf-8")
        else:
            body = "<h2>Pas de code reçu.</h2>".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def main():
    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()

    print("Ouverture du navigateur pour autorisation...")
    webbrowser.open(auth_url)
    print("(Si rien ne s'ouvre, visite :\n" + auth_url + "\n)")

    import time
    for _ in range(120):
        if "code" in code_holder:
            break
        time.sleep(1)
    else:
        sys.exit("Délai dépassé — pas d'autorisation reçue en 2 minutes.")

    # Échange code → token (PKCE : pas de secret)
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "grant_type": "authorization_code",
        "code": code_holder["code"],
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
    }).encode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token", data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        token = json.load(resp)["access_token"]
    print("Token utilisateur obtenu (PKCE).")

    # L'appel décisif
    req = urllib.request.Request(
        f"https://api.spotify.com/v1/artists/{ARTIST_ID}",
        headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        artist = json.load(resp)

    print("\n" + "=" * 60)
    print(f"Artiste  : {artist.get('name')}")
    print(f"popularity : {artist.get('popularity')!r}")
    print(f"followers  : {artist.get('followers', {}).get('total')!r}")
    print(f"genres     : {artist.get('genres')!r}")
    print("=" * 60)
    if artist.get("popularity") is not None:
        print("VERDICT : le token utilisateur DÉBLOQUE les métriques.")
        print("→ On réécrit enrichir_spotify.py en mode PKCE.")
    else:
        print("VERDICT : champs toujours absents — le verrouillage est bien")
        print("au niveau du palier d'app. Seul l'Extended Quota Mode les rendra.")


if __name__ == "__main__":
    main()
