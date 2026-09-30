"""Configuration centrale : groupes, années, expériences et champs des formulaires.

Pour ajouter / modifier un champ, il suffit d'éditer ce fichier.
- col    : nom de la colonne dans la base de données (ASCII, sans espace)
- label  : intitulé affiché et utilisé dans l'export Excel (identique au modèle d'origine)
- min/max: bornes de validation (None = pas de borne). Les bornes min sont exclusives
           pour 0 (une concentration doit être > 0).
"""

GROUPES = ["A", "B", "C", "D","CBT"]

# Année de la promotion : bornes acceptées dans le formulaire
ANNEE_MIN, ANNEE_MAX = 2000, 2100

# Binôme : nombre de noms (min obligatoires, max possibles)
BINOME_MIN, BINOME_MAX = 2, 3

SEUIL_DEFAUT = 0.30  # ±30 % autour de la référence, comme dans les scripts d'origine

EXPERIENCES = {
    "polaro": {
        "titre": "TP Polarographie",
        "table": "tp_polaro",
        "fichier_export": "TP_Polaro",
        "champs": [
            {"col": "conc_mol_l", "label": "Concentration (mol/L)", "min": 0, "max": None, "exemple": "ex. 1,25e-4"},
            {"col": "conc_ppm", "label": "Concentration (ppm)", "min": 0, "max": None, "exemple": "ex. 12,3"},
            {"col": "conc_ug", "label": "Concentration (µg)", "min": 0, "max": None, "exemple": "ex. 250"},
        ],
    },
    "uv": {
        "titre": "TP UV-Visible",
        "table": "tp_uv",
        "fichier_export": "TP_UV-Vis",
        "champs": [
            {"col": "pct_cafeine", "label": "pctg massique caféine", "min": 0, "max": 100, "exemple": "ex. 2,15"},
            {"col": "pct_agc", "label": "pctg massique AGC", "min": 0, "max": 100, "exemple": "ex. 35,4"},
        ],
    },
}
