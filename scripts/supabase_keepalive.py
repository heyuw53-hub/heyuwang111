"""Garde le projet Supabase (offre gratuite) actif : une requête de lecture par jour.

Supabase met en pause les projets gratuits avec trop peu d'activité sur 7 jours.
Lancé par .github/workflows/supabase-keepalive.yml ; lit DATABASE_URL (secret GitHub).
Lecture seule : aucune donnée n'est modifiée.
"""
import os
import sys

import psycopg2

TABLES = ["resultats_polaro_v3", "resultats_uv_v3"]


def nettoyer_lien(url: str) -> str:
    """Tolère les erreurs de copier-coller depuis les Secrets Streamlit :
    DATABASE_URL = "postgresql+psycopg2://..."  →  postgresql://..."""
    url = url.strip()
    if url.upper().startswith("DATABASE_URL"):
        url = url.split("=", 1)[1].strip()
    url = url.strip("\"'").strip()
    for prefixe in ("postgresql+psycopg2://", "postgres://"):
        if url.startswith(prefixe):
            url = "postgresql://" + url[len(prefixe):]
    return url


def masquer(texte: str, url: str) -> str:
    """Retire le lien et le mot de passe d'un message d'erreur avant de l'afficher."""
    texte = texte.replace(url, "<lien masqué>")
    try:
        mdp = url.split("://", 1)[1].split("@", 1)[0].split(":", 1)[1]
        if mdp:
            texte = texte.replace(mdp, "****")
    except IndexError:
        pass
    return " ".join(texte.split())[:300]


def main() -> int:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("ERREUR : le secret DATABASE_URL n'est pas défini dans GitHub "
              "(Settings → Secrets and variables → Actions).")
        return 1
    url = nettoyer_lien(url)
    if not url.startswith("postgresql://"):
        print("ERREUR : le secret ne ressemble pas à un lien PostgreSQL. Il doit commencer par "
              "« postgresql:// » (sans guillemets, sans « DATABASE_URL = »).")
        return 1
    try:
        conn = psycopg2.connect(url, connect_timeout=30)
    except Exception as e:
        print(f"ERREUR de connexion ({type(e).__name__}) : {masquer(str(e), url)}")
        print("Causes possibles : projet Supabase en pause (Dashboard → Resume), mot de passe modifié, "
              "ou lien « Direct connection » au lieu de « Session pooler ».")
        return 1
    with conn, conn.cursor() as cur:
        cur.execute("SELECT now()")
        print("Connexion OK –", cur.fetchone()[0])
        for t in TABLES:
            cur.execute("SELECT to_regclass(%s)", (f"public.{t}",))
            if cur.fetchone()[0] is None:
                print(f"  {t} : table absente (sera créée par le site à la première saisie)")
                continue
            cur.execute(f'SELECT count(*) FROM "{t}"')
            print(f"  {t} : {cur.fetchone()[0]} saisies")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
