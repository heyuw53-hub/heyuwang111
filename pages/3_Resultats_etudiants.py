"""Page étudiants : distribution de l'année + position de son binôme (point rouge)."""
import numpy as np
import streamlit as st

import db
from analysis import figure_distribution, nettoyer
from config import BINOME_MAX, BINOME_MIN, EXPERIENCES, GROUPES, N_MIN_GAUSS, SEUIL_DEFAUT

st.set_page_config(page_title="Résultats étudiants", page_icon="📈", layout="wide")
st.title("📈 Où se situe mon résultat ?")
st.caption("Distribution de toute la promotion (données nettoyées : ±"
           f"{SEUIL_DEFAUT:.0%} autour de la moyenne). Votre binôme apparaît en rouge. "
           "Les résultats des autres binômes ne sont pas affichés individuellement.")

moi = st.session_state.get("mon_binome", {})

tps = list(EXPERIENCES)
cle = st.radio("TP", tps, format_func=lambda k: EXPERIENCES[k]["titre"], horizontal=True,
               index=tps.index(moi["tp"]) if moi.get("tp") in tps else 0)
try:
    annees = db.annees(cle)
except Exception as e:
    st.error(f"Connexion à la base impossible : `{type(e).__name__}`")
    st.stop()
if not annees:
    st.info("Aucun résultat pour ce TP pour l'instant.")
    st.stop()

c1, c2, c3 = st.columns(3)
annee = c1.selectbox("Année", annees, index=annees.index(moi["annee"]) if moi.get("annee") in annees else 0)
groupe = c2.selectbox("Groupe", GROUPES, index=GROUPES.index(moi["groupe"]) if moi.get("groupe") in GROUPES else None,
                      placeholder="Choisir…")
binome = c3.number_input("N° de binôme", min_value=BINOME_MIN, max_value=BINOME_MAX, value=moi.get("binome"),
                         step=1, format="%d", placeholder="ex. 3")

exp = EXPERIENCES[cle]
champs = exp["champs"]
cols = [c["col"] for c in champs]


@st.fragment(run_every=15)
def distribution():
    df = db.charger(cle, annee)
    garde, _ = nettoyer(df, cols, SEUIL_DEFAUT, "moyenne")

    point = None
    if groupe and binome:
        ligne = df[(df["groupe"] == groupe) & (df["binome"] == int(binome))]
        if ligne.empty:
            st.warning(f"Aucun résultat trouvé pour le groupe {groupe}, binôme {int(binome)} en {annee} "
                       "pour ce TP. Vérifiez vos informations ou soumettez d'abord votre résultat.")
        else:
            point = {c: float(ligne.iloc[0][c]) for c in cols}
    else:
        st.info("Choisissez votre groupe et votre numéro de binôme pour voir votre position.")

    st.metric("Binômes pris en compte", len(garde))
    st.pyplot(figure_distribution(garde, champs, point=point), clear_figure=True)

    if point:
        lignes = []
        for c in champs:
            x = garde[c["col"]].to_numpy(dtype=float)
            v = point[c["col"]]
            if len(x) >= N_MIN_GAUSS and np.std(x, ddof=1) > 0:
                mu, s = x.mean(), np.std(x, ddof=1)
                z = (v - mu) / s
                pos = f"{z:+.2f} σ"
                commentaire = ("proche de la moyenne" if abs(z) < 1 else
                               "un peu éloigné de la moyenne" if abs(z) < 2 else "loin de la moyenne")
            else:
                mu, pos, commentaire = ((x.mean() if len(x) else float("nan")), "–",
                                        f"pas encore assez de binômes (min. {N_MIN_GAUSS})")
            lignes.append({"Grandeur": c["label"], "Votre valeur": f"{v:.4g}",
                           "Moyenne promo": f"{mu:.4g}", "Écart": pos, "": commentaire})
        st.dataframe(lignes, hide_index=True)
        if not ((garde["groupe"] == groupe) & (garde["binome"] == int(binome))).any():
            st.warning("Votre résultat est en dehors de la plage retenue (valeur aberrante) : "
                       "il n'est pas inclus dans la courbe, mais sa position est indiquée en rouge.")


distribution()
