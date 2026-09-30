import streamlit as st

st.set_page_config(page_title="TP – Saisie des résultats", page_icon="🧪")

st.title("🧪 Saisie des résultats de TP")
st.markdown(
    """
Choisissez votre TP dans le menu à gauche :

- **Polarographie** : masse de zinc dans la gélule de Rubozinc (µg)
- **UV-Visible** : pourcentages massiques de caféine et d'AGC

**Consignes de saisie**
- Indiquez l'année de votre promotion, votre groupe et votre numéro de binôme.
- Nombres uniquement, sans unité (l'unité est déjà indiquée dans l'intitulé).
- La virgule et la notation scientifique sont acceptées : `0,0125` ou `1,25e-2`.
- En cas d'erreur, renvoyez simplement le formulaire : la nouvelle saisie du binôme remplace l'ancienne.
"""
)
