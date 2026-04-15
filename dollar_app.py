import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Monitor de Câmbio", layout="wide")

st.title("💵 Monitor de Dólar em Tempo Real")
st.subheader("Integração via AwesomeAPI")

# 0.Recuperar token de segurança
try:
    token = st.secrets["AWESOME_TOKEN"]
except:
    st.error("Erro: Token AWESOME_TOKEN não configurrado no Secrets!")
    st.stop()

# 1. Função para buscar o preço atual
def buscar_cotacao():
    url = f"https://economia.awesomeapi.com.br/json/last/USD-BRL?token={token}"
    try:
        response = requests.get(url)
        dados = response.json()
        return dados['USDBRL']
    except Exception as e:
        st.error(f"Erro na API: {e}")
        return None

# 2. Função para buscar o histórico dos últimos 15 dias
def buscar_historico():
    url = f"https://economia.awesomeapi.com.br/json/daily/USD-BRL/15?token={token}"
    try:
        response = requests.get(url)
        dados = respose.json()
        
        # Transformar em DataFrame para facilitar o gráfico
        lista_de_precos = []
        for dia in dados:
            lista_precos.append({
                "Data": datetime.fromtimestamp(int(dia['timestamp'])).strftime('%d/%m/%Y'),
                "Preço": float(dia['bid'])
            })
        
        df = pd.DataFrame(lista_precos)
        return df.iloc[::-1] # Inverter para a data mais antiga vir primeiro
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
        return pd.DataFrame()

# --- INTERFACE ---

cotacao = buscar_cotacao()

if cotacao:
    # Exibir métricas principais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Dólar Comercial", f"R$ {float(cotacao['bid']):.2f}", f"{cotacao['pctChange']}, f"{cotacao['create_date']}%")
    with col2:
        st.metric("Máxima do Dia", f"R$ {float(cotacao['high']):.2f}")
    with col3:
        st.metric("Mínima do Dia", f"R$ {float(cotacao['low']):.2f}")
    with col4:
        datetime.fromtimestamp(int(dia['timestamp'])).strftime('%d/%m/%Y')})

# Exibir Gráfico Histórico
st.divider()
st.write("### Variação nos últimos 15 dias")

df_hist = buscar_historico()

if not df_hist.empty:
    fig = px.line(df_hist, x="Data", y="Preço", 
                  markers=True, 
                  title="Tendência USD/BRL",
                  labels={"Preço": "Valor em Reais (R$)"})
    
    fig.update_traces(line_color='#1f77b4')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Não foi possível carregar o gráfico histórico.")