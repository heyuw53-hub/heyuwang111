"""Accès à la base de données (SQLAlchemy).

- En local : SQLite (fichier tp_data.db), aucune configuration nécessaire.
- En ligne : définir DATABASE_URL dans .streamlit/secrets.toml
  (ex. PostgreSQL Supabase : postgresql+psycopg2://user:pwd@host:5432/postgres).
"""
import datetime as dt

import pandas as pd
import sqlalchemy as sa
import streamlit as st

from config import EXPERIENCES

metadata = sa.MetaData()
TABLES = {}
for _cle, _exp in EXPERIENCES.items():
    TABLES[_cle] = sa.Table(
        _exp["table"],
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("annee", sa.Integer, nullable=False, index=True),
        sa.Column("groupe", sa.String(8), nullable=False),
        sa.Column("binome", sa.Integer, nullable=False),
        *[sa.Column(c["col"], sa.Float, nullable=False) for c in _exp["champs"]],
        *[sa.Column(i["col"], sa.Float, nullable=True) for i in _exp.get("incertitudes", [])],
        sa.Column("details", sa.Text, nullable=True),  # données de saisie et calculs intermédiaires (JSON)
        sa.Column("cree_le", sa.DateTime(timezone=True), nullable=False),
        # un seul résultat par (année, groupe, binôme) : une nouvelle saisie remplace l'ancienne
        sa.UniqueConstraint("annee", "groupe", "binome", name=f"uq_{_exp['table']}_annee_groupe_binome"),
    )


def _database_url() -> str:
    try:
        url = st.secrets["DATABASE_URL"].strip()
    except Exception:
        return "sqlite:///tp_data.db"
    # Lien Supabase copié tel quel ("postgresql://..." ou "postgres://...") :
    # on impose le pilote psycopg2 installé via requirements.txt.
    for prefixe in ("postgresql://", "postgres://"):
        if url.startswith(prefixe):
            return "postgresql+psycopg2://" + url[len(prefixe):]
    return url


@st.cache_resource
def get_engine() -> sa.Engine:
    engine = sa.create_engine(_database_url(), pool_pre_ping=True)
    metadata.create_all(engine)
    return engine


def enregistrer(exp: str, annee: int, groupe: str, binome: int, valeurs: dict, details: str | None = None) -> bool:
    """Insère une saisie. Retourne True si une saisie précédente a été remplacée."""
    t = TABLES[exp]
    with get_engine().begin() as conn:
        res = conn.execute(sa.delete(t).where(t.c.annee == annee, t.c.groupe == groupe, t.c.binome == binome))
        conn.execute(
            sa.insert(t).values(
                annee=annee,
                groupe=groupe,
                binome=binome,
                details=details,
                cree_le=dt.datetime.now(dt.timezone.utc),
                **valeurs,
            )
        )
    return res.rowcount > 0


def annees(exp: str) -> list[int]:
    """Années présentes dans la base, de la plus récente à la plus ancienne."""
    t = TABLES[exp]
    with get_engine().connect() as conn:
        return [r[0] for r in conn.execute(sa.select(t.c.annee).distinct().order_by(t.c.annee.desc()))]


def charger(exp: str, annee: int | None = None) -> pd.DataFrame:
    """Saisies d'une année (ou de toutes les années si annee=None)."""
    t = TABLES[exp]
    q = sa.select(t).order_by(t.c.annee, t.c.groupe, t.c.binome)
    if annee is not None:
        q = q.where(t.c.annee == annee)
    with get_engine().connect() as conn:
        return pd.read_sql(q, conn)


def supprimer(exp: str, ids: list[int]) -> int:
    t = TABLES[exp]
    with get_engine().begin() as conn:
        return conn.execute(sa.delete(t).where(t.c.id.in_(ids))).rowcount
