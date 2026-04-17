## Dollar App - AI Analyst

## Produto Digital
O objetivo do projeto é criar um código em Python que possa apresentar a cotação do dólar no momento da consulta e permitir fazer relações com notícias que possam
ter impactado a variação do preço da moeda Real em relação ao Dólar.
Essa se torna uma ferramenta interessante para ter uma análise em tempo real do LLM do Groq sobre o comportamento do dólar hoje e nos últimos 15 dias, diante das notícias 
de jornais nos últimos sete dias - via API News.
O objetivo é de estudo e não representa nenhuma sugestão de investimento, sem relação com agências, corretoras, nem bancos.
 
 Arquitetura e Pipeline de Dados (Visão de CS)
O coração da aplicação funciona como um pipeline de dados estruturado em três etapas:

1. Extração (Data Ingestion)
A função buscar_noticias utiliza a biblioteca requests para realizar chamadas assíncronas à NewsAPI.
requests.get(url): Realiza o handshake com o servidor e retorna um objeto response contendo o status code (ex: 200 OK), headers e o payload bruto.
response.json(): O servidor envia dados em formato JSON. Esta linha serializa o texto bruto em um dicionário Python manipulável.
dados.get("articles", []): Como a API retorna metadados (total de resultados, status), extraímos apenas a lista de artigos aninhada na chave articles.

2. Transformação (Data Wrangling)
Os dados brutos são filtrados e limpos. Criamos uma string otimizada contendo apenas títulos e descrições para reduzir a latência e o consumo de tokens na próxima etapa.

3. Processamento (Inference)
Os dados transformados são injetados em um prompt de engenharia avançada e enviados ao Groq. O modelo de linguagem processa o contexto e gera uma análise preditiva sobre a tendência do câmbio (Alta, Baixa ou Estabilidade).

Stack Tecnológica
Python 3.x: Linguagem base.
Streamlit: Framework para a interface web.
Plotly Express: Visualização de dados interativa.
Groq (Llama 3.3): Processamento de linguagem natural de ultra-baixa latência.
AwesomeAPI & NewsAPI: Fontes de dados em tempo real.

Segurança e Boas Práticas
Secret Management: Utilização de .streamlit/secrets.toml e Variáveis de Ambiente no Cloud para proteção de API Keys.

## ⚠️ Isenção de Responsabilidade (Disclaimer)

### Sobre a Inteligência Artificial
Este sistema utiliza o modelo Llama 3 via Groq. É importante notar que **Modelos de Linguagem de Grande Escala (LLMs) podem alucinar**, ou seja, gerar informações que parecem fatos, mas são imprecisas ou fictícias. A análise da IA deve ser interpretada como uma síntese de notícias e não como uma verdade absoluta.

### Sobre Investimentos
O objetivo deste projeto é estritamente de **estudo acadêmico e desenvolvimento técnico**. 
* **Não representa nenhuma sugestão de investimento.**
* Não possui qualquer relação com agências de notícias, corretoras de valores, bancos ou instituições financeiras.
* O autor não se responsabiliza por decisões tomadas com base nas informações geradas por esta ferramenta.
Git Hygiene: Arquivo .gitignore configurado para evitar o vazamento de credenciais e dependências locais (venv).

Autor
Daniel G. Carvalho
Senior Product Manager
