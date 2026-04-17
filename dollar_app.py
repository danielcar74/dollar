import streamlit as st
import requests
import pandas as pd
import pytz
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
    # Define o fuso horário de Brasília/São Paulo
        fuso_sp = pytz.timezone('America/Sao_Paulo')
    
    # Converte o timestamp vindo da API para o fuso correto
        data_hora_sp = datetime.fromtimestamp(int(cotacao['timestamp']), tz=pytz.utc).astimezone(fuso_sp)
        data_hora_formatada = data_hora_sp.strftime('%d/%m/%Y %H:%M')
    
        st.metric("Horário (Brasília)", data_hora_formatada)




#st.divider() # Uma linha fina para separar do conteúdo

# ... (mantenha suas funções buscar_cotacao, buscar_historico e buscar_noticias no topo)

# --- INICIALIZAÇÃO GROQ ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Erro ao configurar Groq. Verifique a chave nos Secrets.")

def analisar_noticias_com_ia(noticias, tema, valor_dolar):
    if not noticias:
        return "Nenhuma notícia encontrada para este tema nos últimos 7 dias."
    
    texto_noticias = ""
    for i, art in enumerate(noticias):
        texto_noticias += f"[{i}] Título: {art['title']} | Resumo: {art['description']}\n\n"
    
    prompt = f"""
    Você é um analista sênior geopolítico e de mercado financeiro. 
    O dólar atual está em R$ {valor_dolar}.
    
    Analise as seguintes notícias sobre '{tema}':
    {texto_noticias}
    
    Com base nessas notícias e no valor atual do dólar, forneça:
    1. Os 3 pontos de maior impacto.
    2. Uma análise se a tendência é de alta, baixa ou estabilidade para os próximos dias.
    3. Justificativa técnica baseada nos fatos apresentados.
    
    Responda em Português Brasil, de forma executiva (bullet points), formatado em Markdown.
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Erro na análise da IA: {e}"

# --- INTERFACE PRINCIPAL ---
cotacao = buscar_cotacao()

if cotacao:
    # Métricas (Col1 a Col4) - Mantenha seu código original aqui
    col1, col2, col3, col4 = st.columns(4)
    valor_atual = cotacao['bid']
    # ... (restante das suas colunas de métricas)

# --- SEÇÃO DE INTELIGÊNCIA (IA) ---
#st.divider()

st.markdown("""
    <hr style="margin-top: 20px; margin-bottom: 20px; border: 0; border-top: 1px solid #ccc;">
    <h2 style="margin-top: -10px;">Analista Geopolítico IA</h2>
    <p style="font-size: 16px; color: #555; margin-top: -15px;">Pesquise um tema para ver a correlação com o Dólar</p>
""", unsafe_allow_html=True)


# st.header("Analista Geopolítico IA")
# st.markdown(
    # '<p style="font-size: 16px; color: #555; margin-top: -20px;">Ai powered by Groq</p>', 
    # unsafe_allow_html=True
# )
# st.markdown('<p style="font-size: 18px; color: #1d5c3d;">Pesquise um tema para ver a correlação com o Dólar</p>', unsafe_allow_html=True)

tema_livre = st.text_input(label="", placeholder="Ex: Tensão Irã x Israel, Taxa Selic, Eleições EUA...", value="")

# if st.button("Gerar Relatório de Impacto"):
    # with st.spinner("IA analisando notícias e tendências de mercado..."):
        # dados_noticias = buscar_noticias(tema_livre)
        # relatorio = analisar_noticias_com_ia(dados_noticias, tema_livre, valor_atual)
        
        # st.markdown("### 📊 Relatório da IA")
        # st.info(relatorio)
        
        
##novo
if st.button("Gerar Relatório de Impacto"):
    with st.spinner("IA minerando notícias e gerando insights..."):
        # 1. Busca as notícias brutas
        raw_noticias = buscar_noticias(tema_livre)
        
        # 2. Pega o valor do dólar para o contexto
        valor_atual = cotacao['bid'] if cotacao else "Não disponível"
        
        # 3. Gera a análise da IA
        analise = analisar_noticias_com_ia(raw_noticias, tema_livre, valor_atual)
        
        # --- EXIBIÇÃO NO FRONT-END ---

        
        # Exibe o relatório da IA primeiro (Ouro do projeto)
        st.markdown("### Relatório de Inteligência")
        st.info(analise)

        st.warning("""
                **Atenção:** As análises acima são geradas por IA e podem conter imprecisões (alucinações). 
                Este dashboard tem fins puramente educacionais e **não constitui recomendação de investimento**.
            """)        
        
        # Exibe as notícias que serviram de base (Transparência/Fontes)
        st.divider()
        st.subheader("🔗 Fontes Analisadas")
        
        if raw_noticias:
            # Criamos colunas para as notícias não ficarem gigantes na vertical
            for art in raw_noticias[:6]: # Limitamos às 6 primeiras para não poluir
                # Formata a data para o padrão BR
                data_noticia = datetime.strptime(art['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d/%m/%Y %H:%M')
                
                with st.container(border=True):
                    col_logo, col_txt = st.columns([1, 4])
                    with col_txt:
                        st.write(f"**{art['title']}**")
                        st.caption(f"📅 {data_noticia} | Fonte: {art['source']['name']}")
                        # Link direto para a notícia
                        st.link_button("Ver notícia completa", art['url'])
        else:
            st.warning("Nenhuma notícia encontrada para listar como fonte.")        
        
        
        
        

# --- GRÁFICO HISTÓRICO ---
st.divider()
df_hist = buscar_historico()
if not df_hist.empty:
    st.write("### Variação nos últimos 15 dias")
    fig = px.line(df_hist, x="Data", y="Preço", markers=True, title="Tendência USD/BRL")
    st.plotly_chart(fig, use_container_width=True)


    
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