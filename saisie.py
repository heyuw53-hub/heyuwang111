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


def normaliser_nom(nom: str) -> str:
    return " ".join(nom.split()).title()


def former_binome(noms: list[str]) -> str:
    """Noms normalisés et triés alphabétiquement, pour que l'ordre de saisie ne compte pas."""
    return " / ".join(sorted(noms, key=str.casefold))


def page_saisie(cle: str):
    exp = EXPERIENCES[cle]
    st.title(exp["titre"])
    st.caption("Une seule saisie par binôme et par année : si vous renvoyez le formulaire, "
               "votre résultat précédent est remplacé.")

    with st.form(f"form_{cle}"):
        c1, c2 = st.columns(2)
        annee = c1.number_input("Année", min_value=ANNEE_MIN, max_value=ANNEE_MAX, value=None,
                                step=1, format="%d", placeholder=f"ex. {dt.date.today().year}")
        groupe = c2.selectbox("Groupe", GROUPES, index=None, placeholder="Choisir…")

        st.markdown(f"**Binôme** ({BINOME_MIN} à {BINOME_MAX} personnes)")
        noms_bruts = [
            st.text_input(f"Nom Prénom {i + 1}" + ("" if i < BINOME_MIN else " (facultatif)"),
                          placeholder="ex. Dupont Marie", key=f"{cle}_nom{i}")
            for i in range(BINOME_MAX)
        ]
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

    noms = [normaliser_nom(n) for n in noms_bruts if n and n.strip()]
    if len(noms) < BINOME_MIN:
        erreurs.append(f"Indiquez au moins {BINOME_MIN} noms pour le binôme.")
    for n in noms:
        if " " not in n:
            erreurs.append(f"« {n} » : indiquez le nom ET le prénom.")
    if len({n.casefold() for n in noms}) < len(noms):
        erreurs.append("Le même nom apparaît deux fois dans le binôme.")

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

    binome = former_binome(noms)
    remplace = db.enregistrer(cle, int(annee), groupe, binome, valeurs)
    st.success(("Résultat mis à jour" if remplace else "Résultat enregistré")
               + f" – {int(annee)}, groupe {groupe}, binôme : {binome}.")
    st.table({c["label"]: [f"{valeurs[c['col']]:.6g}"] for c in exp["champs"]})
