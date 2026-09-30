"""Configuration centrale : groupes, années, expériences et champs des formulaires.

Pour ajouter / modifier un champ, il suffit d'éditer ce fichier.
- col    : nom de la colonne dans la base de données (ASCII, sans espace)
- label  : intitulé affiché et utilisé dans l'export Excel (identique au modèle d'origine)
- min/max: bornes de validation (None = pas de borne). Les bornes min sont exclusives
           pour 0 (une concentration doit être > 0).
- theorique (optionnel) : valeur de référence (ex. étiquette de la boîte), dans l'unité du champ.
"""

GROUPES = ["A", "B", "C", "D","CBT"]

# Année de la promotion : bornes acceptées dans le formulaire
ANNEE_MIN, ANNEE_MAX = 2000, 2100

# Numéro de binôme : bornes acceptées (entier)
BINOME_MIN, BINOME_MAX = 1, 99

# En dessous de ce nombre de binômes, on n'ajuste pas de gaussienne (trop peu fiable) :
# on montre seulement l'histogramme / les points.
N_MIN_GAUSS = 5

SEUIL_DEFAUT = 0.30  # ±30 % autour de la référence, comme dans les scripts d'origine

EXPERIENCES = {
    "polaro": {
        "titre": "TP Polarographie",
        # Nouvelle table : l'ancienne (resultats_polaro, 3 concentrations) est conservée telle quelle.
        "table": "resultats_polaro_v2",
        "fichier_export": "TP_Polaro",
        "champs": [
            {"col": "masse_zn_ug", "label": "Masse de zinc dans la gélule (µg)", "min": 0, "max": None,
             "exemple": "ex. 14 600",
             "theorique": 15000},  # Rubozinc : 15 mg de zinc par gélule (étiquette de la boîte)
        ],
    },
    "uv": {
        "titre": "TP UV-Visible",
        "table": "resultats_uv",
        "fichier_export": "TP_UV-Vis",
        "champs": [
            {"col": "pct_cafeine", "label": "pctg massique caféine", "min": 0, "max": 100, "exemple": "ex. 2,15"},
            {"col": "pct_agc", "label": "pctg massique AGC", "min": 0, "max": 100, "exemple": "ex. 35,4"},
        ],
    },
}
