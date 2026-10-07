"""Configuration centrale : groupes, années, expériences et champs des formulaires.

Pour ajouter / modifier un champ, il suffit d'éditer ce fichier.
- col    : nom de la colonne dans la base de données (ASCII, sans espace)
- label  : intitulé affiché et utilisé dans l'export Excel (identique au modèle d'origine)
- min/max: bornes de validation (None = pas de borne). Les bornes min sont exclusives
           pour 0 (une concentration doit être > 0).
- theorique (optionnel) : valeur de référence (ex. étiquette de la boîte), dans l'unité du champ.

incertitudes : incertitudes élargies (95 %) par binôme, calculées à la saisie (cf. incertitudes.py).
- col : colonne en base ; de : champ concerné ; label : intitulé de la colonne « a ± v » dans l'export Excel.
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
        # v3 : ajout des incertitudes. Les anciennes tables sont conservées telles quelles.
        "table": "resultats_polaro_v3",
        "fichier_export": "TP_Polaro",
        "champs": [
            {"col": "masse_zn_ug", "label": "Masse de zinc dans la gélule (µg)", "min": 0, "max": None,
             "exemple": "ex. 14 600",
             "theorique": 15000},  # Rubozinc : 15 mg de zinc par gélule (étiquette de la boîte)
        ],
        "incertitudes": [
            {"col": "v_masse_zn_ug", "de": "masse_zn_ug", "label": "Masse de zinc (µg) ± v (type B, 95 %)"},
        ],
    },
    "uv": {
        "titre": "TP UV-Visible",
        "table": "resultats_uv_v3",
        "fichier_export": "TP_UV-Vis",
        # % massiques CALCULÉS par le site à partir de la pesée, de la fiole et des concentrations
        "champs": [
            {"col": "pct_cafeine", "label": "pctg massique caféine", "min": 0, "max": 100},
            {"col": "pct_agc", "label": "pctg massique AGC", "min": 0, "max": 100},
        ],
        "incertitudes": [
            {"col": "va_pct_cafeine", "de": "pct_cafeine", "label": "% caféine ± v (avec u_A)"},
            {"col": "vb_pct_cafeine", "de": "pct_cafeine", "label": "% caféine ± v (avec u_B)"},
            {"col": "va_pct_agc", "de": "pct_agc", "label": "% AGC ± v (avec u_A)"},
            {"col": "vb_pct_agc", "de": "pct_agc", "label": "% AGC ± v (avec u_B)"},
        ],
    },
}
