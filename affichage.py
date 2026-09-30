"""Affichage Streamlit des graphiques (rendus en PNG de façon thread-safe, cf. analysis.rendre_png)."""
import streamlit as st

from analysis import rendre_png


def graphique(fonction, *args, **kwargs):
    png = rendre_png(fonction, *args, **kwargs)
    # taille naturelle (réduite automatiquement si plus large que la page) :
    # un graphique à 1 panneau ne se retrouve pas étiré sur toute la largeur
    st.image(png)
