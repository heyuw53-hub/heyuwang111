"""Page enseignant : vue d'ensemble, comparaisons intra-groupe / inter-groupes / inter-annuelle, export."""
import hmac

import pandas as pd
import streamlit as st

import db
from affichage import graphique
from analysis import (COLONNES_NUMERIQUES, excel, figure_comparaison, figure_distribution, figure_intra_groupe, nettoyer,
                      statistiques, statistiques_par, valeurs_aberrantes, vers_format_modele)
from config import EXPERIENCES, GROUPES, SEUIL_DEFAUT

st.set_page_config(page_title="Résultats enseignant", page_icon="📊", layout="wide")


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


MODES = ["Vue d'ensemble", "Intra-groupe", "Inter-groupes", "Inter-annuel"]

st.title("📊 Résultats – enseignant")
if not mot_de_passe_ok():
    st.stop()

# ---------- Paramètres ----------
with st.sidebar:
    cle = st.radio("TP", list(EXPERIENCES), format_func=lambda k: EXPERIENCES[k]["titre"])
    try:
        liste_annees = db.annees(cle)
    except Exception as e:
        st.error(f"Connexion à la base impossible : `{type(e).__name__}: {str(e).splitlines()[0][:300]}`")
        st.stop()
    if not liste_annees:
        st.info("Aucune saisie pour ce TP.")
        st.stop()
    mode = st.radio("Affichage", MODES)
    if mode != "Inter-annuel":
        annee = st.selectbox("Année", liste_annees)
    else:
        annees_choisies = sorted(st.multiselect("Années", liste_annees, default=liste_annees))
    if mode == "Intra-groupe":
        groupe_seul = st.selectbox("Groupe", GROUPES)
    else:
        groupes = st.multiselect("Groupes", GROUPES, default=GROUPES)
    seuil = st.slider("Seuil de nettoyage (± %)", 5, 100, int(SEUIL_DEFAUT * 100), step=5) / 100
    reference = st.radio("Référence du nettoyage", ["moyenne", "médiane"],
                         help="Moyenne = scripts d'origine. Médiane = plus robuste aux valeurs aberrantes.")
    donnees_affichees = st.radio("Graphiques sur", ["données nettoyées", "données brutes"],
                                 help="Nettoyage calculé séparément pour chaque année, sur tous les groupes.")
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
    aberrant = valeurs_aberrantes(df, cols, seuil, reference)

    a, b, c = st.columns(3)
    a.metric("Saisies", len(df))
    b.metric("Gardées après nettoyage", len(garde))
    c.metric("Exclues", len(exclu))

    if df.empty:
        st.info(f"Aucune saisie pour {exp['titre']} – {annee} pour l'instant.")
        return

    base = garde if donnees_affichees == "données nettoyées" else df
    st.subheader(f"Distribution ({donnees_affichees})")
    graphique(figure_distribution, base, champs)
    st.dataframe(statistiques(base, champs), hide_index=True,
                 column_config={k: st.column_config.NumberColumn(format="%.4g") for k in COLONNES_NUMERIQUES})

    t1, t2, t3 = st.tabs([f"Toutes les saisies ({len(df)})", f"Gardées ({len(garde)})", f"Exclues ({len(exclu)})"])
    for onglet, d in [(t1, df), (t2, garde), (t3, exclu)]:
        with onglet:
            vue = vers_format_modele(d, champs).drop(columns="Année")
            vue.insert(0, "id", d["id"].values)
            vue["Saisi le"] = d["cree_le"].values
            # même code couleur que l'export Excel : valeurs aberrantes en jaune
            fond = pd.DataFrame("", index=vue.index, columns=vue.columns)
            for c in champs:
                fond[c["label"]] = aberrant.loc[d.index, c["col"]].map(
                    {True: "background-color: #FFFF00; color: black", False: ""}).values
            st.dataframe(vue.style.apply(lambda _: fond, axis=None), hide_index=True, column_config=formats)

    st.download_button(
        f"⬇️ Excel {annee} – toutes les saisies, valeurs aberrantes en jaune",
        excel(df, champs, str(annee), masque=aberrant, incertitudes=exp.get("incertitudes")),
        file_name=f"{exp['fichier_export']}_{annee}.xlsx",
        help=f"Aucune ligne supprimée. Jaune = valeur hors ±{seuil:.0%} de la {reference}.",
    )




def preparer(df):
    """Nettoie année par année (sur tous les groupes) si demandé."""
    if donnees_affichees == "données brutes" or df.empty:
        return df
    return pd.concat([nettoyer(d, cols, seuil, reference)[0] for _, d in df.groupby("annee")])


def tableau_stats(t):
    st.dataframe(t, hide_index=True, column_config={
        k: st.column_config.NumberColumn(format="%.4g") for k in COLONNES_NUMERIQUES if k in t.columns})


@st.fragment(run_every=10 if auto else None)
def intra_groupe():
    d = preparer(db.charger(cle, annee))
    d = d[d["groupe"] == groupe_seul] if not d.empty else d
    st.subheader(f"Groupe {groupe_seul} – {annee} ({donnees_affichees})")
    if d.empty:
        st.info("Aucune donnée pour ce groupe.")
        return
    graphique(figure_intra_groupe, d, champs)
    st.caption("Boîte à moustaches : médiane, quartiles, étendue ; chaque point est un binôme (n° au-dessus).")
    tableau_stats(statistiques(d, champs).drop(columns=["Min", "Max"]))


@st.fragment(run_every=10 if auto else None)
def inter_groupes():
    d = preparer(db.charger(cle, annee))
    presents = [g for g in groupes if not d.empty and (d["groupe"] == g).any()]
    st.subheader(f"Comparaison des groupes – {annee} ({donnees_affichees})")
    if not presents:
        st.info("Aucune donnée pour les groupes choisis.")
        return
    graphique(figure_comparaison, d, champs, "groupe", presents, "boite")
    tableau_stats(statistiques_par(d, champs, "groupe", presents, "Groupe"))


@st.fragment(run_every=10 if auto else None)
def inter_annuel():
    d = preparer(db.charger(cle))
    if not d.empty:
        d = d[d["annee"].isin(annees_choisies) & d["groupe"].isin(groupes)]
    presentes = [a for a in annees_choisies if not d.empty and (d["annee"] == a).any()]
    st.subheader(f"Comparaison entre années ({donnees_affichees})")
    if not presentes:
        st.info("Aucune donnée pour les années choisies.")
        return
    graphique(figure_comparaison, d, champs, "annee", presentes, "nuage")
    tableau_stats(statistiques_par(d, champs, "annee", presentes, "Année"))


if mode == "Intra-groupe":
    intra_groupe()
    st.stop()
if mode == "Inter-groupes":
    inter_groupes()
    st.stop()
if mode == "Inter-annuel":
    inter_annuel()
    st.stop()

tableau_de_bord()

# ---------- Suppression manuelle ----------
with st.expander("🗑️ Supprimer des saisies"):
    df = db.charger(cle, annee)
    choix = st.multiselect("Saisies à supprimer", df["id"].tolist(),
                           format_func=lambda i: "#{} – groupe {} binôme {}".format(
                               i, *df.loc[df["id"] == i, ["groupe", "binome"]].iloc[0]))
    if st.button("Supprimer", disabled=not choix):
        n = db.supprimer(cle, choix)
        st.success(f"{n} saisie(s) supprimée(s).")
        st.rerun()
