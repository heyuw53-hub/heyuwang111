"""Nettoyage des données, statistiques, histogrammes + gaussienne, export Excel.

Reprend la logique de Nettoyage_Polaro.py / Nettoyage_UV.py / Distribution_Normale.py.
"""
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd



def valeurs_aberrantes(df: pd.DataFrame, cols: list[str], seuil: float = 0.30,
                       reference: str = "moyenne") -> pd.DataFrame:
    """Tableau booléen de même forme que df[cols] : True = valeur hors de ±seuil de la référence.

    reference = "moyenne" (comme les scripts d'origine) ou "médiane"
    (plus robuste : une valeur aberrante ne décale pas la fenêtre).
    """
    masque = pd.DataFrame(False, index=df.index, columns=cols)
    for c in cols:
        x = df[c]
        ref = x.mean() if reference == "moyenne" else x.median()
        bas, haut = sorted((ref * (1 - seuil), ref * (1 + seuil)))
        masque[c] = x.notna() & ~x.between(bas, haut)
    return masque


def nettoyer(df: pd.DataFrame, cols: list[str], seuil: float = 0.30, reference: str = "moyenne"):
    """Garde les lignes dont TOUTES les valeurs sont à ±seuil de la référence.
    Retourne (df_gardé, df_exclu).
    """
    d = df.dropna(subset=cols)
    exclu = valeurs_aberrantes(d, cols, seuil, reference).any(axis=1)
    return d[~exclu], d[exclu]


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


JAUNE = "FFFF00"


def excel(df: pd.DataFrame, champs: list[dict], feuille: str, masque: pd.DataFrame | None = None) -> bytes:
    """Classeur à une seule feuille. Si `masque` est fourni (cf. valeurs_aberrantes),
    les cellules aberrantes sont surlignées en jaune ; aucune ligne n'est supprimée."""
    from openpyxl.styles import PatternFill

    vue = vers_format_modele(df, champs)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        vue.to_excel(w, sheet_name=feuille, index=False)
        ws = w.sheets[feuille]
        for j, nom in enumerate(vue.columns, start=1):  # largeur de colonne lisible
            ws.column_dimensions[ws.cell(1, j).column_letter].width = max(10, len(str(nom)) + 2)
        if masque is not None:
            jaune = PatternFill(start_color=JAUNE, end_color=JAUNE, fill_type="solid")
            for c in champs:
                j = vue.columns.get_loc(c["label"]) + 1
                for i, aberrant in enumerate(masque.loc[df.index, c["col"]].to_numpy(), start=2):
                    if aberrant:
                        ws.cell(i, j).fill = jaune
    return buf.getvalue()
