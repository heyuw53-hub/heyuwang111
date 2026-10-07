"""Incertitudes par binôme, selon ECPM-TPSA-MOP-003 « Traitement des données ».

Règles appliquées
- Type B (mesure unique) :
    ±U donné par le fabricant (verrerie jaugée, pipetman) ........ u = U / √3
    incertitude non qualifiée / écart entre valeurs extrêmes ....... u = U / (2√3)
  incertitude élargie : v = 2 · u
- Type A (série de N mesures) : σ (N−1), u = σ / √N, v = t_S(N−1, 95 %) · u
- Produits / quotients : somme quadratique des incertitudes RELATIVES.
- Arrondi : incertitude à 1 chiffre significatif par excès, résultat au même rang
  (cf. analysis.arrondi_resultat).

Ce module contient les calculs (sans Streamlit) puis les formulaires de saisie.
"""
import math

import numpy as np
import streamlit as st

from analysis import arrondi_resultat, t_student_95

MODES = {
    "fabricant": "±U fabricant → u = U/√3",
    "extremes": "écart entre extrêmes → u = U/(2√3)",
}
K_TYPE_B = 2  # coefficient de Student pour une mesure unique (MOP-003 §3)


# ---------------------------------------------------------------------------
# Calculs
# ---------------------------------------------------------------------------
def u_type_b(U: float, mode: str) -> float:
    return U / math.sqrt(3) if mode == "fabricant" else U / (2 * math.sqrt(3))


def relative_quadratique(termes: list[dict]) -> float:
    """termes : [{"valeur": x, "u": u(x)}, ...] → √Σ (u/x)²"""
    return math.sqrt(sum((t["u"] / t["valeur"]) ** 2 for t in termes))


def verrerie(nom: str, V: float, U: float, mode: str, unite: str) -> dict:
    u = u_type_b(U, mode)
    return {"nom": nom, "valeur": V, "U": U, "mode": mode, "unite": unite, "u": u, "u_rel": u / V}


def calcul_polaro(masse: float, termes: list[dict]) -> dict:
    """m(Zn) = C · V_fiole · F_dilution ; seules les erreurs de verrerie (type B)."""
    u_rel = relative_quadratique(termes)
    u = masse * u_rel
    return {"masse": masse, "termes": termes, "u_rel": u_rel, "u": u, "v": K_TYPE_B * u}


def type_a(valeurs: list[float]) -> dict:
    x = np.asarray(valeurs, dtype=float)
    n = len(x)
    moy = float(x.mean())
    sigma = float(x.std(ddof=1)) if n > 1 else float("nan")
    u = sigma / math.sqrt(n) if n > 1 else float("nan")
    t = t_student_95(n - 1) if n > 1 else float("nan")
    return {"n": n, "moyenne": moy, "sigma": sigma, "u": u, "t": t, "v": t * u}


def calcul_uv(concentrations: list[float], pesee: dict, fiole200: dict, dilution: list[dict]) -> dict:
    """Pour UN analyte.
    C200 (mg/mL) : type A sur la série ; type B à partir de la verrerie de dilution.
    % massique = C200 · V200 / (m_café · 1000) · 100, incertitude calculée deux fois :
    avec u_A(C200) puis avec u_B(C200) (pesée et fiole 200 mL dans les deux cas)."""
    a = type_a(concentrations)
    C = a["moyenne"]
    uB_rel = relative_quadratique(dilution) if dilution else 0.0
    uB = C * uB_rel
    pct = C * fiole200["valeur"] / (pesee["valeur"] * 1000) * 100
    base = (pesee["u"] / pesee["valeur"]) ** 2 + fiole200["u_rel"] ** 2
    u_pct_A = pct * math.sqrt(base + (a["u"] / C) ** 2)
    u_pct_B = pct * math.sqrt(base + uB_rel ** 2)
    return {
        "C": C, "A": a, "uB": uB, "vB": K_TYPE_B * uB, "uB_rel": uB_rel,
        "pct": pct,
        "u_pct_A": u_pct_A, "v_pct_A": a["t"] * u_pct_A,   # t_S(N−1), comme le type A
        "u_pct_B": u_pct_B, "v_pct_B": K_TYPE_B * u_pct_B,  # t_S = 2, comme le type B
    }


# ---------------------------------------------------------------------------
# Saisie (Streamlit)
# ---------------------------------------------------------------------------
def _nombre(texte):
    from saisie import lire_nombre
    return lire_nombre(texte)


def _ligne(cle: str, nom: str, unite: str, mode_defaut="fabricant", ex_V="", ex_U=""):
    """Une ligne de saisie : valeur, ±U, mode d'évaluation."""
    st.markdown(f"**{nom}**")
    c1, c2, c3 = st.columns([1, 1, 1.6])
    V = c1.text_input(f"Valeur ({unite})", key=f"{cle}_V", placeholder=ex_V)
    U = c2.text_input(f"Incertitude U ({unite})", key=f"{cle}_U", placeholder=ex_U)
    mode = c3.selectbox("Mode d'évaluation", list(MODES), format_func=MODES.get, key=f"{cle}_m",
                        index=list(MODES).index(mode_defaut))
    return {"nom": nom, "unite": unite, "V": V, "U": U, "mode": mode}


def _valider_ligne(l: dict, erreurs: list, facultatif=False):
    vide = not (l["V"] or "").strip() and not (l["U"] or "").strip()
    if facultatif and vide:
        return None
    try:
        V, U = _nombre(l["V"]), _nombre(l["U"])
    except ValueError:
        erreurs.append(f"« {l['nom']} » : valeur et incertitude U doivent être des nombres.")
        return None
    if V <= 0 or U < 0:
        erreurs.append(f"« {l['nom']} » : valeur > 0 et U ≥ 0 attendus.")
        return None
    return verrerie(l["nom"], V, U, l["mode"], l["unite"])


def _tableau_termes(termes: list[dict]):
    st.dataframe([{"Source": t["nom"], "Valeur": f"{t['valeur']:g} {t['unite']}", "U": f"{t['U']:g}",
                   "u": f"{t['u']:.3g}", "u relative": f"{100 * t['u_rel']:.3f} %"} for t in termes],
                 hide_index=True)


# ---- Polaro ----------------------------------------------------------------
def saisir_polaro(exp):
    c = exp["champs"][0]
    e = {"masse": st.text_input(c["label"], placeholder=c.get("exemple"))}
    st.subheader("Incertitude de type B (verrerie)")
    st.caption("Recopiez les valeurs gravées sur la verrerie / la notice du pipetman. "
               "Seules les erreurs expérimentales sont prises en compte.")
    e["pip"] = _ligne("po_pip", "Pipetman – prélèvement de la solution étalon de Zn", "µL", ex_V="ex. 500", ex_U="ex. 4")
    e["f25"] = _ligne("po_f25", "Fiole jaugée des étalons", "mL", ex_V="ex. 25", ex_U="ex. 0,04")
    e["f100"] = _ligne("po_f100", "Fiole jaugée de l'échantillon", "mL", ex_V="ex. 100", ex_U="ex. 0,10")
    st.caption("Dilution de l'échantillon : **facultatif**, laisser vide s'il n'y a pas eu de dilution.")
    e["dp"] = _ligne("po_dp", "Dilution – pipette jaugée", "mL", ex_V="ex. 10", ex_U="ex. 0,02")
    e["df"] = _ligne("po_df", "Dilution – fiole jaugée", "mL", ex_V="ex. 100", ex_U="ex. 0,10")
    return e


def valider_polaro(exp, e):
    erreurs = []
    c = exp["champs"][0]
    try:
        m = _nombre(e["masse"])
        if m <= 0:
            erreurs.append(f"« {c['label']} » doit être > 0.")
    except ValueError:
        erreurs.append(f"« {c['label']} » : nombre invalide ({e['masse']!r}).")
        m = None
    termes = [_valider_ligne(e[k], erreurs) for k in ("pip", "f25", "f100")]
    dil = [_valider_ligne(e[k], erreurs, facultatif=True) for k in ("dp", "df")]
    if (dil[0] is None) != (dil[1] is None) and not erreurs:
        erreurs.append("Dilution : renseignez la pipette ET la fiole (ou aucune des deux).")
    if erreurs:
        return None, None, erreurs
    r = calcul_polaro(m, termes + [d for d in dil if d])
    return {c["col"]: m, "v_" + c["col"]: r["v"]}, r, []


def afficher_polaro(exp, r):
    c = exp["champs"][0]
    st.markdown(f"#### Résultat : m(Zn) = ({arrondi_resultat(r['masse'], r['v'])}) µg")
    st.caption(f"Type B, 95 % : u relative = {100 * r['u_rel']:.3f} %, u = {r['u']:.3g} µg, "
               f"v = 2·u = {r['v']:.3g} µg")
    _tableau_termes(r["termes"])


# ---- UV ----------------------------------------------------------------------
ANALYTES_UV = [("pct_cafeine", "caféine", "ex. 0,105"), ("pct_agc", "AGC", "ex. 1,75")]
N_MESURES_MAX = 6


def saisir_uv(exp):
    e = {}
    st.subheader("Pesée et fiole de 200 mL")
    e["pesee"] = _ligne("uv_m", "Masse de café vert pesée", "g", mode_defaut="extremes", ex_V="ex. 1,0003", ex_U="ex. 0,0001")
    e["f200"] = _ligne("uv_f200", "Fiole jaugée de l'échantillon", "mL", ex_V="ex. 200", ex_U="ex. 0,15")
    st.subheader("Concentrations dans la fiole de 200 mL (mg/mL)")
    st.caption(f"Au moins 3 mesures (jusqu'à {N_MESURES_MAX}), déjà ramenées à la fiole de 200 mL "
               "(dilution prise en compte). → incertitude de type A.")
    for col, nom, ex in ANALYTES_UV:
        st.markdown(f"**{nom[0].upper() + nom[1:]}**")
        cs = st.columns(N_MESURES_MAX)
        e[col] = [cs[i].text_input(f"Mesure {i + 1}", key=f"uv_{col}_{i}", placeholder=ex if i == 0 else "")
                  for i in range(N_MESURES_MAX)]
    st.subheader("Dilution utilisée pour la mesure → incertitude de type B sur la concentration")
    st.caption("**Facultatif** : laisser vide si la solution a été mesurée sans dilution.")
    e["dp"] = _ligne("uv_dp", "Dilution – pipette jaugée", "mL", ex_V="ex. 5", ex_U="ex. 0,015")
    e["df"] = _ligne("uv_df", "Dilution – fiole jaugée", "mL", ex_V="ex. 50", ex_U="ex. 0,06")
    return e


def valider_uv(exp, e):
    erreurs = []
    pesee = _valider_ligne(e["pesee"], erreurs)
    f200 = _valider_ligne(e["f200"], erreurs)
    dil = [_valider_ligne(e[k], erreurs, facultatif=True) for k in ("dp", "df")]
    if (dil[0] is None) != (dil[1] is None) and not erreurs:
        erreurs.append("Dilution : renseignez la pipette ET la fiole (ou aucune des deux).")
    series = {}
    for col, nom, _ in ANALYTES_UV:
        vals = []
        for t in e[col]:
            if t and t.strip():
                try:
                    v = _nombre(t)
                    if v <= 0:
                        raise ValueError
                    vals.append(v)
                except ValueError:
                    erreurs.append(f"Concentration {nom} : valeur invalide ({t!r}).")
        if len(vals) < 3:
            erreurs.append(f"Concentration {nom} : au moins 3 mesures sont nécessaires (type A).")
        series[col] = vals
    if erreurs:
        return None, None, erreurs
    dil = [d for d in dil if d]
    res, valeurs = {}, {}
    for col, nom, _ in ANALYTES_UV:
        r = calcul_uv(series[col], pesee, f200, dil)
        if not 0 < r["pct"] <= 100:
            erreurs.append(f"% massique {nom} calculé = {r['pct']:.4g} % : hors de ]0 ; 100], "
                           "vérifiez les unités (mg/mL, g, mL).")
        res[col] = r
        valeurs.update({col: r["pct"], f"va_{col}": r["v_pct_A"], f"vb_{col}": r["v_pct_B"]})
    res["termes"] = [pesee, f200] + dil
    return (None, None, erreurs) if erreurs else (valeurs, res, [])


def afficher_uv(exp, res):
    for col, nom, _ in ANALYTES_UV:
        r, a = res[col], res[col]["A"]
        st.markdown(f"#### {nom[0].upper() + nom[1:]}")
        st.markdown(
            f"- C (fiole 200 mL), **type A** : ({arrondi_resultat(r['C'], a['v'])}) mg/mL "
            f"— N = {a['n']}, σ = {a['sigma']:.3g}, u = σ/√N = {a['u']:.3g}, t_S = {a['t']:g}\n"
            f"- C (fiole 200 mL), **type B** : ({arrondi_resultat(r['C'], r['vB'])}) mg/mL "
            f"— u relative verrerie = {100 * r['uB_rel']:.3f} %, t_S = 2\n"
            f"- **% massique avec u_A** : ({arrondi_resultat(r['pct'], r['v_pct_A'])}) %  (t_S = {a['t']:g})\n"
            f"- **% massique avec u_B** : ({arrondi_resultat(r['pct'], r['v_pct_B'])}) %  (t_S = 2)")
    st.caption("Sources de type B (pesée, fiole, dilution) :")
    _tableau_termes(res["termes"])


FORMULAIRES = {
    "polaro": (saisir_polaro, valider_polaro, afficher_polaro),
    "uv": (saisir_uv, valider_uv, afficher_uv),
}
