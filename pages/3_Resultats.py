"""Page enseignant : consultation en temps réel, nettoyage, distribution, export."""
import hmac

import streamlit as st

import db
from analysis import excel, figure_distribution, nettoyer, statistiques, vers_format_modele
from config import EXPERIENCES, GROUPES, SEUIL_DEFAUT

st.set_page_config(page_title="Résultats", page_icon="📊", layout="wide")


# ---------- Accès protégé ----------
def mot_de_passe_ok() -> bool:
    if st.session_state.get("auth"):
        return True
    try:
        attendu = st.secrets["ADMIN_PASSWORD"]
    except Exception:
        st.error("ADMIN_PASSWORD n'est pas défini dans .streamlit/secrets.toml.")
        return False
    mdp = st.text_input("Mot de passe", type="password")
    if mdp:
        if hmac.compare_digest(mdp, attendu):
            st.session_state["auth"] = True
            st.rerun()
        st.error("Mot de passe incorrect.")
    return False


st.title("📊 Résultats")
if not mot_de_passe_ok():
    st.stop()

# ---------- Paramètres ----------
with st.sidebar:
    cle = st.radio("TP", list(EXPERIENCES), format_func=lambda k: EXPERIENCES[k]["titre"])
    liste_annees = db.annees(cle)
    if not liste_annees:
        st.info("Aucune saisie pour ce TP.")
        st.stop()
    annee = st.selectbox("Année", liste_annees)
    groupes = st.multiselect("Groupes", GROUPES, default=GROUPES)
    seuil = st.slider("Seuil de nettoyage (± %)", 5, 100, int(SEUIL_DEFAUT * 100), step=5) / 100
    reference = st.radio("Référence du nettoyage", ["moyenne", "médiane"],
                         help="Moyenne = scripts d'origine. Médiane = plus robuste aux valeurs aberrantes.")
    donnees_affichees = st.radio("Distribution sur", ["données nettoyées", "données brutes"])
    auto = st.toggle("Actualisation automatique (10 s)", value=True)

exp = EXPERIENCES[cle]
champs = exp["champs"]
cols = [c["col"] for c in champs]
formats = {c["label"]: st.column_config.NumberColumn(format="%.4g") for c in champs}


@st.fragment(run_every=10 if auto else None)
def tableau_de_bord():
    df = db.charger(cle, annee)
    df = df[df["groupe"].isin(groupes)]
    garde, exclu = nettoyer(df, cols, seuil, reference)

    a, b, c = st.columns(3)
    a.metric("Saisies", len(df))
    b.metric("Gardées après nettoyage", len(garde))
    c.metric("Exclues", len(exclu))

    if df.empty:
        st.info(f"Aucune saisie pour {exp['titre']} – {annee} pour l'instant.")
        return

    base = garde if donnees_affichees == "données nettoyées" else df
    st.subheader(f"Distribution ({donnees_affichees})")
    st.pyplot(figure_distribution(base, champs), clear_figure=True)
    st.dataframe(statistiques(base, champs), hide_index=True,
                 column_config={k: st.column_config.NumberColumn(format="%.4g")
                                for k in ["Moyenne", "Écart-type", "CV (%)", "Min", "Max"]})

    t1, t2, t3 = st.tabs([f"Toutes les saisies ({len(df)})", f"Gardées ({len(garde)})", f"Exclues ({len(exclu)})"])
    for onglet, d in [(t1, df), (t2, garde), (t3, exclu)]:
        with onglet:
            vue = vers_format_modele(d, champs).drop(columns="Année")
            vue.insert(0, "id", d["id"].values)
            vue["Saisi le"] = d["cree_le"].values
            st.dataframe(vue, hide_index=True, column_config=formats)

    d1, d2 = st.columns(2)
    d1.download_button(f"⬇️ Données brutes {annee} (.xlsx)", excel(df, champs, str(annee)),
                       file_name=f"{exp['fichier_export']}_{annee}.xlsx")
    d2.download_button(f"⬇️ Données nettoyées {annee} (.xlsx)", excel(garde, champs, str(annee)),
                       file_name=f"{exp['fichier_export']}_{annee}_nettoye.xlsx")


tableau_de_bord()

# ---------- Suppression manuelle ----------
with st.expander("🗑️ Supprimer des saisies"):
    df = db.charger(cle, annee)
    choix = st.multiselect("Saisies à supprimer", df["id"].tolist(),
                           format_func=lambda i: f"#{i} – {df.loc[df['id'] == i, 'binome'].iloc[0]}")
    if st.button("Supprimer", disabled=not choix):
        n = db.supprimer(cle, choix)
        st.success(f"{n} saisie(s) supprimée(s).")
        st.rerun()
