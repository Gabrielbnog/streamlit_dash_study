import streamlit as st
import pandas as pd
import plotly.express as px
import subprocess
import numpy as np
import pytz
from datetime import datetime, date, timedelta
from PIL import Image
from streamlit_autorefresh import st_autorefresh
from streamlit_extras.app_logo import add_logo
import math
import openpyxl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import base64
from io import BytesIO

st.markdown("<h4 style='color:#333333;'>Tópicos para revisão</h4>", unsafe_allow_html=True)
hoje = pd.to_datetime(datetime.now().date()).strftime('%d/%m/%Y') 
st.write(f"#### Data: {hoje}")

if "chave" not in st.session_state:
    st.warning("Nenhum dado disponível para revisão.")
    st.stop()

df = st.session_state["chave"].copy()
df["Data Revisão"] = pd.to_datetime(df["Data Revisão"], format="%d/%m/%Y", errors="coerce")


df_para_revisar = df[df["Data Revisão"].notnull() & (df["Data Revisão"] <= hoje)]

df_classificacoes = {}
for classificacao in ["Urgente", "Ruim", "Bom", "Excelente"]:
    df_classif = df_para_revisar[df_para_revisar["Classificação"] == classificacao].copy()
    df_classif = df_classif.sort_values("Data Revisão").head(5)
    if df_classif.empty:
        df_classificacoes[classificacao] = [f"Não há revisões pendentes para {classificacao}."]
    else:
        linhas = []
        for _, row in df_classif.iterrows():
            data_str = row["Data Revisão"].strftime("%d/%m/%Y")
            semana = row["Semana"]
            tarefa = row["Tarefa"]
            descricao = row.get("Descrição", "")
            percentual = row["Percentual de Acerto"]
            linha = f"• {data_str} | S: {semana} | T: {tarefa} | {descricao} -> {row['Percentual de Acerto']:.1f}%"
            linhas.append(linha)
        df_classificacoes[classificacao] = linhas

# CSS: força layout em COLUNA e cria um ESPAÇO (gap) de 30px entre cada card
css_cards = """
<style>
.card-container {
    display: flex;
    flex-direction: column;  /* empilha um card em cima do outro */
    gap: 30px;               /* espaçamento vertical entre os cartões */
    margin-top: 10px;
}
.card {
    color: #ffffff;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
}
.card-title {
    font-size: 1.1em;
    font-weight: bold;
    margin-bottom: 10px;
}
.card-content {
    font-size: 0.95em;
    line-height: 1.4em;
    max-height: 180px;
    overflow-y: auto;
    white-space: pre-wrap;
    margin-bottom: 10px;
}
</style>
"""
st.markdown(css_cards, unsafe_allow_html=True)

cores = {
    "Excelente": "#011f4b",
    "Bom":       "#03396c",
    "Ruim":      "#005b96",
    "Urgente":   "#6497b1",
}

st.markdown("<div class='card-container'>", unsafe_allow_html=True)
for classificacao in ["Urgente", "Ruim", "Bom", "Excelente"]:
    cor_fundo = cores.get(classificacao, "#666666")
    titulo = f"{classificacao} "
    if classificacao == "Excelente":
        titulo += "(>85%)"
    elif classificacao == "Bom":
        titulo += "(75-85%)"
    elif classificacao == "Ruim":
        titulo += "(≤75%)"
    elif classificacao == "Urgente":
        titulo += "(≤60%)"
    
    corpo_texto = "\n".join(df_classificacoes[classificacao])
    st.markdown(f"""
    <div class='card' style='background-color:{cor_fundo};'>
        <div class='card-title'>{titulo}</div>
        <div class='card-content'>{corpo_texto}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)