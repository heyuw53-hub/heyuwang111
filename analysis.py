"""Nettoyage des données, statistiques, histogrammes + gaussienne, export Excel.

Reprend la logique de Nettoyage_Polaro.py / Nettoyage_UV.py / Distribution_Normale.py.
"""
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd



def nettoyer(df: pd.DataFrame, cols: list[str], seuil: float = 0.30, reference: str = "moyenne"):
    """Garde les lignes dont TOUTES les valeurs sont à ±seuil de la référence.

    reference = "moyenne" (comme les scripts d'origine) ou "médiane"
    (plus robuste : une valeur aberrante ne décale pas la fenêtre).
    Retourne (df_gardé, df_exclu).
    """
    d = df.dropna(subset=cols)
    masque = pd.Series(True, index=d.index)
    for c in cols:
        ref = d[c].mean() if reference == "moyenne" else d[c].median()
        bas, haut = sorted((ref * (1 - seuil), ref * (1 + seuil)))
        masque &= d[c].between(bas, haut)
    return d[masque], d[~masque]


def statistiques(df: pd.DataFrame, champs: list[dict]) -> pd.DataFrame:
    lignes = []
    for c in champs:
        x = df[c["col"]].dropna()
        moy = x.mean() if len(x) else np.nan
        ecart = x.std(ddof=1) if len(x) > 1 else np.nan
        lignes.append({
            "Grandeur": c["label"],
            "n": len(x),
            "Moyenne": moy,
            "Écart-type": ecart,
            "CV (%)": 100 * ecart / moy if moy else np.nan,
            "Min": x.min() if len(x) else np.nan,
            "Max": x.max() if len(x) else np.nan,
        })
    return pd.DataFrame(lignes)


def figure_distribution(df: pd.DataFrame, champs: list[dict]):
    """Un histogramme (densité) par grandeur + loi normale ajustée (μ, σ des données)."""
    n = len(champs)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4), squeeze=False)
    for ax, c in zip(axes[0], champs):
        x = df[c["col"]].dropna().to_numpy(dtype=float)
        ax.set_xlabel(c["label"])
        ax.set_ylabel("Densité")
        if len(x) == 0:
            ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center", transform=ax.transAxes)
            continue
        ax.hist(x, bins="auto", density=True, color="#4C72B0", alpha=0.7, edgecolor="white")
        if len(x) >= 2 and x.std(ddof=1) > 0:
            mu, sigma = x.mean(), x.std(ddof=1)
            xs = np.linspace(min(x.min(), mu - 4 * sigma), max(x.max(), mu + 4 * sigma), 300)
            ys = np.exp(-0.5 * ((xs - mu) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))
            ax.plot(xs, ys, color="#C44E52", lw=2)
            ax.axvline(mu, color="#C44E52", ls="--", lw=1)
            ax.set_title(f"μ = {mu:.4g}   σ = {sigma:.3g}   n = {len(x)}", fontsize=10)
        else:
            ax.set_title(f"n = {len(x)} (pas assez de données pour la gaussienne)", fontsize=10)
    fig.tight_layout()
    return fig


def vers_format_modele(df: pd.DataFrame, champs: list[dict]) -> pd.DataFrame:
    """Colonnes renommées pour l'affichage et l'export Excel."""
    renommage = {"annee": "Année", "groupe": "Groupe", "binome": "Binôme",
                 **{c["col"]: c["label"] for c in champs}}
    return df[list(renommage)].rename(columns=renommage)


def excel(df: pd.DataFrame, champs: list[dict], feuille: str) -> bytes:
    """Classeur à une seule feuille."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        vers_format_modele(df, champs).to_excel(w, sheet_name=feuille, index=False)
    return buf.getvalue()
