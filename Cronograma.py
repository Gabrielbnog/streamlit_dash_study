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

# === CONFIGURAÇÕES DA PÁGINA E LAYOUT =====================================

st.set_page_config(layout="wide", page_title="Cronograma")

#st.set_option('deprecation.showPyplotGlobalUse', False)

# === FUNÇÃO: CLASSIFICAR PERCENTUAL DE ACERTO =============================

def classificar_percentual_acerto(df, coluna_percentual):
    df[coluna_percentual] = df[coluna_percentual].astype(str).str.replace('%', '').astype(float)
    conditions = [
        (df[coluna_percentual] > 85),
        (df[coluna_percentual] > 75) & (df[coluna_percentual] <= 85),
        (df[coluna_percentual] > 60) & (df[coluna_percentual] <= 75),
        (df[coluna_percentual] <= 60),
    ]
    classifications = ['Excelente', 'Bom', 'Ruim', 'Urgente']
    df['Classificação'] = np.select(conditions, classifications, default='Não Classificado')
    return df

# === FUNÇÃO: GERAR DATA DE REVISÃO ========================================
def gerar_data_revisao(df):
    """
    Gera a coluna 'Data Revisão' com base na 'Classificação':
      - Excelente -> +75 dias
      - Bom       -> +60 dias
      - Ruim      -> +20 dias
      - Urgente   -> +15 dias
    """
    offset_dict = {
        'Excelente': 75,
        'Bom': 60,
        'Ruim': 20,
        'Urgente': 15
    }
    
    # Garante que 'Data do estudo' seja datetime
    df['Data do estudo'] = pd.to_datetime(df['Data do estudo'], errors='coerce')
    
    df['Data Revisão'] = df.apply(
        lambda row: row['Data do estudo'] + timedelta(days=offset_dict.get(row['Classificação'], 0))
        if pd.notnull(row['Data do estudo']) else np.nan,
        axis=1
    )
    
    # Converte ambas as colunas para o formato dd/mm/yyyy
    df['Data do estudo'] = df['Data do estudo'].dt.strftime('%d/%m/%Y')
    df['Data Revisão'] = pd.to_datetime(df['Data Revisão'], errors='coerce').dt.strftime('%d/%m/%Y')

    return df

# === CABEÇALHO: SIDEBAR E TOPO ===========================================

data_hoje = datetime.now().strftime('%d/%m/%Y') 

# SIDEBAR
st.sidebar.image(Image.open("medicina_logo.png"), width=80)
st.sidebar.write("### Bem-vindo, Cynthia!")
st.sidebar.write("#### Acompanhamento de performance")
st.sidebar.write(f"#### Data: {data_hoje}")

if st.sidebar.button("Recarregar"):
    st.experimental_rerun()

# TOPO (colunas para texto e imagem)
image = Image.open("user_cynthia.png")
col1, col2 = st.columns([0.05, 0.95])

with col1:
    st.image(image, width=50)
with col2:
    st.write("#### Cynthia Jardim - Cronograma:")

# === LEITURA DO ARQUIVO EXCEL ============================================

df_path = "tabela_acompanhamento_cynthia.xlsx"
df = pd.read_excel(df_path)

# Tratar colunas e recalcular percentuais
df['Percentual de Acerto'] = df.apply(lambda row: row['Qtd. acerto'] / row['Qtd. Realizada'] if row['Qtd. Realizada'] > 0 else 0.0, axis=1
)
df['Percentual de questões feitas'] = df.apply(lambda row: row['Qtd. Realizada'] / row['Qtd. Total de questões'] if row['Qtd. Total de questões'] > 0 else 0.0,axis=1)
df['Percentual de Acerto'] *= 100
df['Percentual de questões feitas'] *= 100

# Classificação
df = classificar_percentual_acerto(df, 'Percentual de Acerto')
df = gerar_data_revisao(df)

df.to_excel(df_path, index=False)
df_path = "tabela_acompanhamento_cynthia.xlsx"
df = pd.read_excel(df_path)

#Cria um df com uma chave para poder ser visualizado em outras pages(semelhante a um cache de um browser)
st.session_state["chave"] = df

# === SELEÇÃO DE SEMANA E DATA EDITOR =====================================

lista_semanas = sorted(df['Semana'].unique())
semana_selecionada = st.sidebar.selectbox("**Selecione a Semana** 📅", lista_semanas)

# Filtrar o DataFrame para a semana selecionada
df_semana_selecionada = df[df['Semana'] == semana_selecionada].copy()

# Botão para salvar alterações no Excel
if st.sidebar.button("Salvar Registros da Semana Selecionada"):
    for i, row_editado in df_editado.iterrows():
        df.loc[i] = row_editado
    df.to_excel(df_path, index=False)
    st.success("Alterações salvas com sucesso! A página será recarregada.")
    st.experimental_rerun()

# === KPIs ================================================================
media_acerto = df[df['Percentual de Acerto'] > 0]['Percentual de Acerto'].mean()
media_questoes_feitas = df[df['Percentual de questões feitas'] > 0]['Percentual de questões feitas'].mean()

st.markdown("""
    <style>
    .metric-box {
        background-color: #f9f9f9;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
    }
    .metric-box h5 {
        margin: 0;
        font-size: 1.5em;
        color: #333;
    }
    .metric-box .metric-value {
        font-size: 2em;
        font-weight: bold;
        color: #007bff;
    }
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
        <div class="metric-box">
            <h5>🎯 Média do Percentual de Acerto</h5>
            <div class="metric-value">{media_acerto:.1f}%</div>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div class="metric-box">
            <h5>📊 Média do Percentual de Questões Feitas</h5>
            <div class="metric-value">{media_questoes_feitas:.1f}%</div>
        </div>
    """, unsafe_allow_html=True)

# === GRÁFICO =============================================================

df_grafico = df[(df['Percentual de Acerto'] > 0) & (~df['Grande Área'].isin(['Questões', 'Prova', 'Tema Específico']))]

fig = px.bar(
    df_grafico,
    x='Grande Área',
    y='Percentual de Acerto',
    color='Classificação',
    title='Distribuição por Grande Área',
    labels={'Percentual de Acerto': 'Percentual de Acerto (%)'},
    barmode='group'
)
fig.update_layout(width=1200, height=300, title_x=0.5)

st.plotly_chart(fig, use_container_width=False)

# === CAIXAS URGENTE E RUIM ===============================================

textos = {}
for classificacao in ["Urgente", "Ruim"]:
    df_aux = df.copy()
    df_aux['Percentual de Acerto'] = df_aux['Percentual de Acerto'].astype(float)
    df_filtrado = df_aux[(df_aux["Classificação"] == classificacao) & (df_aux["Qtd. Realizada"] > 0)].copy()
    df_filtrado = df_filtrado.nsmallest(10, 'Percentual de Acerto')
    if df_filtrado.empty:
        textos[classificacao] = f"Não há tarefas com a classificação {classificacao} nesta semana."
    else:
        linhas_texto = [
            f"• S: {row['Semana']} | T: {row['Tarefa']} | {row['Descrição']} -> {row['Percentual de Acerto']:.1f}%"
            for _, row in df_filtrado.iterrows()
        ]
        textos[classificacao] = "\n".join(linhas_texto)

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
        <div style="background-color:#ff3232; color:white; padding:10px; border-radius:5px; 
                    height:150px; overflow-y:auto; font-size:12px; line-height:1.2;">
            <p><b>Urgente (&lt;60%)</b></p>
            <p style="white-space: pre-wrap;">{textos.get("Urgente", "")}</p>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div style="background-color:#993299; color:white; padding:10px; border-radius:5px; 
                    height:150px; overflow-y:auto; font-size:14px; line-height:1.2;">
            <p><b>Ruim (&lt;75%)</b></p>
            <p style="white-space: pre-wrap;">{textos.get("Ruim", "")}</p>
        </div>
    """, unsafe_allow_html=True)
st.write(f" ")
st.write(f" ")
st.write(f"##### Semana {semana_selecionada}")
df_editado = st.data_editor(df_semana_selecionada, key="editor_semana", hide_index=True)

