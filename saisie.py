"""Formulaire de saisie standardisé, commun aux deux TP."""
import datetime as dt
import math

import streamlit as st

import db
from config import ANNEE_MAX, ANNEE_MIN, BINOME_MAX, BINOME_MIN, EXPERIENCES, GROUPES


def lire_nombre(texte: str) -> float:
    """Accepte la virgule française et la notation scientifique : '1,25e-4', '12.3', '1 250'."""
    t = texte.strip().replace(" ", "").replace(" ", "").replace(",", ".")
    if not t:
        raise ValueError("champ vide")
    v = float(t)
    if not math.isfinite(v):
        raise ValueError("valeur non finie")
    return v


def page_saisie(cle: str):
    exp = EXPERIENCES[cle]
    st.title(exp["titre"])
    st.caption("Une seule saisie par binôme : si vous renvoyez le formulaire avec la même année, "
               "le même groupe et le même numéro de binôme, votre résultat précédent est remplacé.")

    with st.form(f"form_{cle}"):
        c1, c2, c3 = st.columns(3)
        annee = c1.number_input("Année", min_value=ANNEE_MIN, max_value=ANNEE_MAX, value=None,
                                step=1, format="%d", placeholder=f"ex. {dt.date.today().year}")
        groupe = c2.selectbox("Groupe", GROUPES, index=None, placeholder="Choisir…")
        binome = c3.number_input("N° de binôme", min_value=BINOME_MIN, max_value=BINOME_MAX, value=None,
                                 step=1, format="%d", placeholder="ex. 3")
        st.divider()
        bruts = {c["col"]: st.text_input(c["label"], placeholder=c.get("exemple")) for c in exp["champs"]}
        envoye = st.form_submit_button("Envoyer", type="primary")

    if not envoye:
        return

    erreurs = []
    if annee is None:
        erreurs.append("Indiquez l'année.")
    if not groupe:
        erreurs.append("Choisissez votre groupe.")

    if binome is None:
        erreurs.append("Indiquez votre numéro de binôme.")

    valeurs = {}
    for c in exp["champs"]:
        try:
            v = lire_nombre(bruts[c["col"]])
        except ValueError:
            erreurs.append(f"« {c['label']} » : nombre invalide ({bruts[c['col']]!r}).")
            continue
        if c["min"] is not None and v <= c["min"]:
            erreurs.append(f"« {c['label']} » doit être > {c['min']}.")
        elif c["max"] is not None and v > c["max"]:
            erreurs.append(f"« {c['label']} » doit être ≤ {c['max']}.")
        else:
            valeurs[c["col"]] = v

    if erreurs:
        for e in erreurs:
            st.error(e)
        return

    try:
        remplace = db.enregistrer(cle, int(annee), groupe, int(binome), valeurs)
    except Exception as e:  # message lisible au lieu de la page d'erreur générique
        st.error(f"Erreur de base de données – résultat NON enregistré.\n\n`{type(e).__name__}: {str(e).splitlines()[0][:300]}`")
        return
    # mémorisé pour la page « Résultats étudiants » (même onglet de navigateur)
    st.session_state["mon_binome"] = {"tp": cle, "annee": int(annee), "groupe": groupe, "binome": int(binome)}
    st.success(("Résultat mis à jour" if remplace else "Résultat enregistré")
               + f" – {int(annee)}, groupe {groupe}, binôme {int(binome)}.")
    st.table({c["label"]: [f"{valeurs[c['col']]:.6g}"] for c in exp["champs"]})
    st.page_link("pages/3_Resultats_etudiants.py", label="Voir où se situe mon résultat →", icon="📈")
