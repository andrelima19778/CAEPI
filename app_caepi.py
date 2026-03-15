import streamlit as st
import pandas as pd
import unicodedata
import re

# 1. Configuração da página e Estilo Visual (CSS)
st.set_page_config(page_title="Gestor CAEPI", layout="wide")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #f0f2f6; padding: 10px 10px 0px 10px; border-radius: 10px 10px 0px 0px; }
    .stTabs [data-baseweb="tab"] { height: 60px; white-space: pre-wrap; background-color: #dee2e6; border-radius: 8px 8px 0px 0px; color: #495057; font-size: 18px; font-weight: bold; transition: all 0.3s; }
    .stTabs [aria-selected="true"] { background-color: #007bff !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# Função para transformar o nome do Equipamento no padrão de URL
def formatar_para_url(texto):
    if pd.isna(texto): return ""
    # Remove acentos
    texto = unicodedata.normalize('NFKD', str(texto)).encode('ascii', 'ignore').decode('utf-8')
    # Minúsculas e substitui espaços/caracteres especiais por hífen
    texto = texto.lower().strip()
    texto = re.sub(r'[^a-z0-9]+', '-', texto)
    # Remove hífens duplicados ou no final/início
    texto = re.sub(r'-+', '-', texto).strip('-')
    return texto

st.title("🛡️ Gestor de Consultas CAEPI")

uploaded_file = st.file_uploader("Suba o arquivo base_caepi_atualizada.csv", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig', low_memory=False)
    df.columns = [c.strip().upper() for c in df.columns]

    col_ca = "NR_CA" if "NR_CA" in df.columns else df.columns[0]
    col_laudo = "APROVADO PARA LAUDO" if "APROVADO PARA LAUDO" in df.columns else "APROVADO_PARA_LAUDO"
    col_fabricante = "RAZAO SOCIAL" if "RAZAO SOCIAL" in df.columns else "RAZAO_SOCIAL"

    tab1, tab2 = st.tabs(["⛑ CONSULTA INDIVIDUAL (CA)", "📑 RELATÓRIO DE EQUIPAMENTOS"])

    # --- ABA 1: BUSCADOR CA COM LINK EXTERNO ---
    with tab1:
        st.header("🔎 Ficha do Registro")
        ca_procurado = st.text_input("Digite o número do CA:", placeholder="Ex: 37750").strip()

        if ca_procurado:
            linhas_ca = df[df[col_ca].astype(str) == ca_procurado].copy()

            if not linhas_ca.empty:
                # Aglutinação das informações
                registro_unico = {}
                for coluna in linhas_ca.columns:
                    valores_unicos = linhas_ca[coluna].dropna().unique()
                    registro_unico[coluna] = " / ".join(map(str, valores_unicos)) if len(valores_unicos) > 1 else (valores_unicos[0] if len(valores_unicos) == 1 else "")

                # Geração do Link Dinâmico (conforme sua estrutura)
                eq_original = registro_unico.get("EQUIPAMENTO", "")
                eq_url = formatar_para_url(eq_original)
                link_externo = f"https://consultaca.com/{ca_procurado}/{eq_url}"

                st.success(f"Dados consolidados para o CA {ca_procurado}")
                
                # Botão de Link com destaque
                st.link_button(f"🔗 Ver Fotos e Detalhes no ConsultaCA", link_externo, type="primary")

                # Exibição dos dados em colunas
                cols_prioritarias = ["EQUIPAMENTO", "SITUACAO"]
                outras_cols = [c for c in registro_unico.keys() if c not in cols_prioritarias]
                lista_ordenada = cols_prioritarias + outras_cols

                c1, c2 = st.columns(2)
                meio = len(lista_ordenada) // 2
                
                for i, k in enumerate(lista_ordenada):
                    if k not in registro_unico: continue
                    v = registro_unico[k]
                    valor_exibir = str(v)
                    if k == "EQUIPAMENTO": valor_exibir = f"**{v}**"
                    elif k == "SITUACAO":
                        cor = "green" if str(v).upper() == "VÁLIDO" else "red"
                        valor_exibir = f":{cor}[**{v}**]"

                    if i < meio: c1.markdown(f"**{k}:** {valor_exibir}")
                    else: c2.markdown(f"**{k}:** {valor_exibir}")
            else:
                st.warning("Número de CA não localizado.")

    # --- ABA 2: EQUIPAMENTO (Mantida) ---
    with tab2:
        st.header("📑 Análise por Tipo de Equipamento")
        st.write("**Somente equipamentos com situação *'VÁLIDO'***")
        if "SITUACAO" in df.columns and "EQUIPAMENTO" in df.columns:
            df_validos = df[df["SITUACAO"].str.upper() == "VÁLIDO"].copy()
            lista_equipamentos = sorted(df_validos["EQUIPAMENTO"].unique())
            equip_selecionado = st.selectbox("Selecione o Equipamento:", ["Selecione..."] + lista_equipamentos)

            if equip_selecionado != "Selecione...":
                st.subheader(f"📍{equip_selecionado}")
                st.write("O resultado da busca de CAs está filtrado por tipo de **laudo** e agrupado por **fabricante**")
                df_filtrado = df_validos[df_validos["EQUIPAMENTO"] == equip_selecionado]
                laudos_unicos = df_filtrado[col_laudo].dropna().unique()
                
                for laudo in laudos_unicos:
                    if str(laudo).strip() == "": continue
                    with st.expander(f"📋 LAUDO: {laudo}", expanded=True):
                        df_laudo_especifico = df_filtrado[df_filtrado[col_laudo] == laudo]
                        agrupado = df_laudo_especifico.groupby(col_fabricante)[col_ca].unique()
                        for fabricante, cas in agrupado.items():
                            st.markdown(f"**🏢 {fabricante}**")
                            st.info(" • ".join(map(str, sorted(cas))))
else:
    st.info("Aguardando upload do arquivo base_caepi_atualizada.csv...")
