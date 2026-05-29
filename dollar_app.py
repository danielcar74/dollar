import streamlit as st
import requests
import pandas as pd
import pytz
import plotly.express as px
from datetime import datetime, timedelta
from groq import Groq

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA E ESTILOS (UI/UX)
# ==============================================================================

st.set_page_config(page_title="Monitor de Câmbio", layout="wide")

# Injeção de CSS para mudar a cor do fundo e ajustar tamanhos das métricas
st.markdown(
    """
    <style>
    .stApp {
        background-color: #e6ffed; /* Verde claro suave */
    }
    /* Diminui o valor principal do st.metric */
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
    }
    /* Diminui o rótulo do st.metric */
    [data-testid="stMetricLabel"] {
        font-size: 14px !important;
    }
    /* Diminui a variação percentual do st.metric */
    [data-testid="stMetricDelta"] {
        font-size: 14px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==============================================================================
# VALIDAÇÃO DE SEGURANÇA (SECRETS)
# ==============================================================================

try:
    token = st.secrets["AWESOME_TOKEN"]
    api_key_news = st.secrets["NEWS_API_KEY"]
    api_key_groq = st.secrets["GROQ_API_KEY"]
except Exception as e:
    st.error(f"Erro: Chaves de segurança não configuradas no Secrets! {e}")
    st.stop()

# ==============================================================================
# CLIENTE E FUNÇÕES DE INTELIGÊNCIA ARTIFICIAL (BACKEND)
# ==============================================================================

try:
    client = Groq(api_key=api_key_groq)
except Exception as e:
    st.error("Erro ao configurar Groq. Verifique a chave nos Secrets.")

def analisar_noticias_com_ia(noticias, tema, valor_dolar):
    if not noticias:
        return "Nenhuma notícia encontrada para este tema nos últimos 7 dias."
    
    texto_noticias = ""
    for i, art in enumerate(noticias):
        texto_noticias += f"[{i}] Título: {art['title']} | Resumo: {art['description']}\n\n"
    
    prompt = f"""
    Assuma o papel de um FX Trader sênior e Estrategista de Câmbio de um grande banco de investimento
     global. Você é especialista em geopolítica, macroeconomia e fluxo cambial, 
     sabendo exatamente como eventos geopolíticos e indicadores econômicos impactam o par USD/BRL 
     (Dólar/Real).
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

# ==============================================================================
# FUNÇÕES DE CONSUMO DE API (DATA INGESTION)
# ==============================================================================

def buscar_cotacao():
    url = f"https://economia.awesomeapi.com.br/json/last/USD-BRL?token={token}"
    try:
        response = requests.get(url)
        dados = response.json()
        return dados['USDBRL']
    except Exception as e:
        st.error(f"Erro na API de Cotação: {e}")
        return None

def buscar_historico():
    url = f"https://economia.awesomeapi.com.br/json/daily/USD-BRL/15?token={token}"
    try:
        response = requests.get(url)
        dados = response.json()
        
        lista_precos = []
        for dia in dados:
            lista_precos.append({
                "Data": datetime.fromtimestamp(int(dia['timestamp'])).strftime('%d/%m/%Y'),
                "Preço": float(dia['bid'])
            })
        
        df = pd.DataFrame(lista_precos)
        return df.iloc[::-1]  # Inverter para a data mais antiga vir primeiro
    except Exception as e:
        st.error(f"Erro ao carregar histórico de 15 dias: {e}")
        return pd.DataFrame()
        
def buscar_noticias(termo):
    hoje = datetime.now()
    sete_dias_atras = hoje - timedelta(days=7)
    
    data_fim = hoje.strftime('%Y-%m-%d')
    data_inicio = sete_dias_atras.strftime('%Y-%m-%d')    
    
    url = (
        f"https://newsapi.org/v2/everything?q={termo}"
        f"&from={data_inicio}"
        f"&to={data_fim}"
        f"&language=pt"
        f"&sortBy=publishedAt"
        f"&pageSize=20"
        f"&apiKey={api_key_news}"
    )
    
    try:
        response = requests.get(url)
        dados = response.json()
        return dados.get("articles", [])
    except Exception as e:
        st.error(f"Erro ao buscar notícias: {e}")
        return []

# ==============================================================================
# INTERFACE DO USUÁRIO (FRONTEND STREAMLIT)
# ==============================================================================

# Executa as buscas de dados essenciais para o Cabeçalho (Hero)
cotacao = buscar_cotacao()
df_hist = buscar_historico()

if cotacao:
    # --- CABEÇALHO LADO A LADO ---
    # col_titulo (40% da tela), col_cotacao (25% da tela), col_grafico (35% da tela)
    col_titulo, col_cotacao, col_grafico = st.columns([4, 2.5, 3.5])
    
    with col_titulo:
        st.title("Analista AI e Monitor de Dólar")
        st.markdown(
            '<p style="font-size: 14px; color: #555; margin-top: -20px;">Integração via AwesomeAPI</p>', 
            unsafe_allow_html=True
        )
        
    with col_cotacao:
        fuso_sp = pytz.timezone('America/Sao_Paulo')
        data_hora_sp = datetime.fromtimestamp(int(cotacao['timestamp']), tz=pytz.utc).astimezone(fuso_sp)
        data_hora_formatada = data_hora_sp.strftime('%d/%m/%Y %H:%M')
        
        # Métrica limpa e minimalista
        st.metric("Dólar Comercial", f"R$ {float(cotacao['bid']):.2f}", f"{cotacao['pctChange']}%")
        st.caption(f"Atualizado em: {data_hora_formatada}")
        
    with col_grafico:
        if not df_hist.empty:
            # Criação do Sparkline (mini gráfico minimalista)
            fig = px.line(df_hist, x="Data", y="Preço", markers=False)
            fig.update_layout(
                margin=dict(l=5, r=5, t=15, b=5),
                height=85,
                xaxis_title="",
                yaxis_title="",
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            # Oculta grades e eixos para um efeito limpo de dashboard financeiro
            fig.update_xaxes(showgrid=False, visible=False)
            fig.update_yaxes(showgrid=False, visible=False)
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- SEÇÃO DE BUSCA CENTRALIZADA ---
st.markdown('<hr style="margin-top: 10px; margin-bottom: 25px; border: 0; border-top: 1px solid #ccc;">', unsafe_allow_html=True)

# Grid invisível para empurrar o conteúdo para o meio [Margem 20%, Conteúdo 60%, Margem 20%]
col_esq, col_centro, col_dir = st.columns([2, 6, 2])

with col_centro:
    st.markdown("""
        <div style="text-align: center; margin-bottom: 15px;">
            <h2 style="margin-bottom: 0px;">Analista Geopolítico IA</h2>
            <p style="font-size: 16px; color: #555; margin-top: 5px;">
                Pesquise um tema para ver a correlação com o Dólar
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Input de texto sem label externa, usando apenas placeholder
    tema_livre = st.text_input(label="", placeholder="Ex: Trump, Iran, Israel, Taxa Selic, Eleições EUA...", value="", key="busca_tema")
    
    # Sub-grid interno para centralizar o botão de execução
    btn_col1, btn_col2, btn_col3 = st.columns([3.5, 5, 3.5])
    with btn_col2:
        botao_clicado = st.button("Gerar Relatório de Impacto", use_container_width=True)

# ==============================================================================
# PROCESSAMENTO E EXIBIÇÃO DE RESULTADOS DA IA
# ==============================================================================

if botao_clicado and tema_livre:
    with col_centro:
        with st.spinner("IA minerando notícias e gerando insights..."):
            # 1. Busca as notícias correspondentes
            raw_noticias = buscar_noticias(tema_livre)
            valor_atual = cotacao['bid'] if cotacao else "Não disponível"
            
            # 2. Executa a análise via Llama 3 (Groq)
            analise = analisar_noticias_com_ia(raw_noticias, tema_livre, valor_atual)
            
            # --- RENDERIZAÇÃO NA TELA ---
            st.markdown("### Relatório de Inteligência")
            st.info(analise)

            st.warning("""
                **Atenção:** As análises acima são geradas por IA e podem conter imprecisões (alucinações). 
                Este dashboard tem fins puramente educacionais e **não constitui recomendação de investimento**.
                
                **Sobre a Inteligência Artificial:** Este sistema utiliza o modelo Llama 3 via Groq. A análise deve ser interpretada como uma síntese informativa e não como verdade absoluta.
            """)        
            
            st.divider()
            st.subheader("🔗 Fontes Analisadas")
            
            if raw_noticias:
                # Exibe até as 6 primeiras notícias como cards estruturados
                for art in raw_noticias[:6]:
                    try:
                        data_noticia = datetime.strptime(art['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d/%m/%Y %H:%M')
                    except:
                        data_noticia = "Data indisponível"
                        
                    with st.container(border=True):
                        st.write(f"**{art['title']}**")
                        st.caption(f"📅 {data_noticia} | Fonte: {art['source']['name']}")
                        st.link_button("Ver notícia completa", art['url'])
            else:
                st.warning("Nenhuma notícia encontrada para listar como fonte.")

# ==============================================================================
# RODAPÉ DO PRODUTO (FOOTER)
# ==============================================================================

st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #777; font-size: 14px;">
        <p>Created by <strong>Daniel G. Carvalho</strong> | Senior Product Manager</p>
        <p style="font-size: 12px; margin-top: -10px;">Real time data by AwesomeAPI & NewsAPI</p>
        <p>
            <a href="https://github.com/danielcar74" target="_blank" style="color: #1d5c3d; text-decoration: none;">GitHub</a> | 
            <a href="https://www.linkedin.com/in/danielcar" target="_blank" style="color: #1d5c3d; text-decoration: none;">LinkedIn</a>
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)