"""Garde le projet Supabase (offre gratuite) actif : une requête de lecture par jour.

Supabase met en pause les projets gratuits avec trop peu d'activité sur 7 jours.
Lancé par .github/workflows/supabase-keepalive.yml ; lit DATABASE_URL (secret GitHub).
Lecture seule : aucune donnée n'est modifiée.
"""
import os
import sys

import psycopg2

TABLES = ["resultats_polaro_v3", "resultats_uv_v3"]


def main() -> int:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("ERREUR : le secret DATABASE_URL n'est pas défini dans GitHub "
              "(Settings → Secrets and variables → Actions).")
        return 1
    # même lien que dans Streamlit : on retire un éventuel « +psycopg2 »
    url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    try:
        conn = psycopg2.connect(url, connect_timeout=30)
    except Exception as e:  # ne jamais afficher le lien (il contient le mot de passe)
        print(f"ERREUR de connexion : {type(e).__name__}. Le projet Supabase est peut-être en pause "
              "(Dashboard → Resume) ou le mot de passe a changé.")
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
