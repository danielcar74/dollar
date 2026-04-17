import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from groq import Groq


# Configuração da página
st.set_page_config(page_title="Monitor de Câmbio", layout="wide")

# Injeção de CSS para mudar a cor do fundo
st.markdown(
    """
    <style>
    .stApp {
        background-color: #e6ffed; /* Verde claro suave */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Monitor de Dólar")
        #st.caption("Integração via AwesomeAPI")
st.markdown(
    '<p style="font-size: 16px; color: #555; margin-top: -20px;">Integração via AwesomeAPI</p>', 
    unsafe_allow_html=True
)

# Recuperar token de segurança
try:
    token = st.secrets["AWESOME_TOKEN"]
except:
    st.error("Erro: Token AWESOME_TOKEN não configurado no Secrets!")
    st.stop()

# Função para buscar o preço atual do Dólar
def buscar_cotacao():
    url = f"https://economia.awesomeapi.com.br/json/last/USD-BRL?token={token}"
    try:
        response = requests.get(url)
        dados = response.json()
        return dados['USDBRL']
    except Exception as e:
        st.error(f"Erro na API: {e}")
        return None

# Função para buscar o histórico da cotação do Dólar dos últimos 15 dias
def buscar_historico():
    url = f"https://economia.awesomeapi.com.br/json/daily/USD-BRL/15?token={token}"
    try:
        response = requests.get(url)
        dados = response.json()
        
        # Transformar em DataFrame para facilitar o gráfico
        lista_precos = []
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
        
# Função para buscar dados de notícias via APINEWS

def buscar_noticias(termo):
    api_key = st.secrets["NEWS_API_KEY"]
    
    # Calcular as datas dinamicamente
    hoje = datetime.now()
    sete_dias_atras = hoje - timedelta(days=7)
    
    # Formatar para string (ISO 8601: YYYY-MM-DD)
    data_fim = hoje.strftime('%Y-%m-%d')
    data_inicio = sete_dias_atras.strftime('%Y-%m-%d')    
    
    # Montar a URL com as datas dinâmicas
    url = (
        f"https://newsapi.org/v2/everything?q={termo}"
        f"&from={data_inicio}"
        f"&to={data_fim}"
        f"&language=pt"
        f"&sortBy=publishedAt"
        f"&pageSize=20" # Pegamos mais notícias para o Groq analisar
        f"&apiKey={api_key}"
    )
    
    #url = f"https://newsapi.org/V2/everything?q={termo}&from=2026-04-15&to=2026-04-17&sortBy=publishedAt&apiKey={api_key}"
    # url = f"https://newsapi.org/V2/everything?{termo}&language=pt&sortBy=publishedAt&pageSize=5&apiKey={api_key}"
    
    try:
        response = requests.get(url)
        dados = response.json()
        return dados.get("articles", [])
    except Exception as e:
        st.error(f"Erro ao buscar notícias: {e}")
        return []
        

# --- INTERFACE ---

cotacao = buscar_cotacao()

if cotacao:
    # Exibir métricas principais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Dólar Comercial", f"R$ {float(cotacao['bid']):.2f}", f"{cotacao['pctChange']}%")
    with col2:
        st.metric("Máxima do Dia", f"R$ {float(cotacao['high']):.2f}")
    with col3:
        st.metric("Mínima do Dia", f"R$ {float(cotacao['low']):.2f}")
    with col4:
        data_hora = datetime.fromtimestamp(int(cotacao['timestamp'])).strftime('%d/%m/%Y %H:%M')
        st.metric("Horário", data_hora)

st.divider() # Uma linha fina para separar do conteúdo

########

##colocar GROQ


########





    

  
    
# Inicializa o cliente Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def analisar_noticias_com_ia(noticias, tema, valor_dolar):
    if not noticias:
        return "Nenhuma notícia encontrada para análise."
    
    # Preparar o texto para o LLM (mandamos apenas títulos/descrições para economizar tokens)
    texto_noticias = ""
    for i, art in enumerate(noticias):
        texto_noticias += f"[{i}] Título: {art['title']}\nDescrição: {art['description']}\n\n"
    
    prompt = f"""
    Você é um analista sênior geopolítico. Abaixo estão notícias sobre '{tema}'.
    Selecione as 3 mais importantes que podem afetar o dólar ou a estabilidade global.
    Para cada uma, escreva um resumo de 2 linhas e explique o porquê da importânciaa.
    Use também o valor do dólar do dia que está em Dollar.
    O dólar está em R$ {valor_dolar}. Com base nessas notícias, você acha que a tendência é de alta ou baixa?
    Responda em Português, formatado em Markdown.
    
    Notícias:
    {texto_noticias}

    """
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile", # Modelo rápido e inteligente
        messages=[{"role": "user", "content": prompt}]
    )
    
    return completion.choices[0].message.content

# --- GROQ NA INTERFACE ---

st.header("AI Analyst - Preço do Dólar e o Contexto Geopolítico")
st.markdown(
    '<p style="font-size: 16px; color: #555; margin-top: -20px;">Powered by Groq</p>', 
    unsafe_allow_html=True
)

    # 1. Cria o rótulo estilizado
st.markdown('<p style="font-size: 20px; color: #1d5c3d; font-weight: bold; margin-bottom: -10px;">O que você quer analisar hoje?</p>', unsafe_allow_html=True)

    # 2. Cria o input sem rótulo interno (label="")
tema_livre = st.text_input(label="", value="")

if st.button("Analisar Impacto"):
    with st.spinner("IA minerando notícias e gerando insights..."):
        # Pegamos o valor atual da variável 'cotacao' que você já definiu lá em cima
        valor_atual = cotacao['bid'] if cotacao else "Não disponível"
        
        raw_noticias = buscar_noticias(tema_livre)
        # Passamos o valor_atual para a função
        analise = analisar_noticias_com_ia(raw_noticias, tema_livre, valor_atual)
        st.markdown(analise)
    
# --------------- FIM DO CODE NOVO ------------    
###############################################    
    

# Exibir Gráfico Histórico
st.divider()
st.write("### Variação nos últimos 15 dias")

df_hist = buscar_historico() # Aqui a função roda e devolve os dados

if not df_hist.empty:
    # st.write("### Histórico de Preços")
    # st.dataframe(df_hist) # Exibe a tabela

# Cria o gráfico APENAS UMA VEZ com todas as configurações
    fig = px.line(
            df_hist, 
            x="Data", 
            y="Preço", 
            markers=True, 
            title="Tendência USD/BRL",
            labels={"Preço": "Valor em Reais (R$)"})
    
# 3. Exibe o gráfico no site 
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Não foi possível carregar o gráfico histórico.")
    
# --- INTERFACE NOTÍCIAS (Abaixo do gráfico) ---

st.divider()
st.subheader("Contexto Geopolítico e Notícias")

# Um seletor para o usuário escolher o tema (Visão de PM: interatividade!)
tema = st.selectbox("Escolha um tema para análise:", ["Irã", "Israel", "Eleições Brasil", "Fed Reserve"])

noticias = buscar_noticias(tema)

if noticias:
    for art in noticias:
        with st.expander(f"{art['title']}"):
            st.write(f"**Fonte:** {art['source']['name']} | **Data:** {art['publishedAt'][:10]}")
            st.write(art['description'])
            st.link_button("Ler notícia completa", art['url'])
else:
    st.info("Nenhuma notícia encontrada para este tema no momento.")


----------- INÍCIO DO CODE NOVO ---------------
###############################################   
  
st.divider()
st.header("Geopolítica & Contexto by IA")

# Filtros rápidos baseados nas suas ideias originais
col_filtro, col_vazia = st.columns([1, 2])
with col_filtro:
    tema_analise = st.selectbox(
        "Selecione o evento para correlacionar:",
        ["Conflito Irã", "Eleições Brasil", "Déficit Fiscal", "Guerra Ucrânia"]
    )

noticias = buscar_noticias(tema_analise)

# Exibição das Notícias em Cards
if noticias:
    for art in noticias:
        # Formatando a data da notícia
        data_noticia = datetime.strptime(art['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d/%m/%Y %H:%M')
        
        with st.container(border=True):
            st.write(f"**{art['title']}**")
            st.caption(f"📅 {data_noticia} | Fonte: {art['source']['name']}")
            st.write(art['description'][:200] + "...") # Limitando o texto
            st.link_button("Ler reportagem", art['url'])
else:
    st.info(f"Sem notícias recentes para '{tema_analise}'.")
    
    
# Footnote

st.divider() # Uma linha fina para separar do conteúdo
st.caption("Developed by **Daniel G. Carvalho** | Senior Product Manager")
st.caption("Real time data by AwesomeAPI.")
st.caption("Real time news by NewsAPI.")

# Cria link para instagram ou LinkedIn

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center;">
        <p>Created by <strong>Daniel G. Carvalho</strong></p>
        <p>
            <a href="https://github.com/danielcar74" target="_blank">GitHub</a> | 
            <a href="https://www.linkedin.com/in/danielcar" target="_blank">LinkedIn</a>
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)