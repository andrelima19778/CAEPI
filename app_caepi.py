import streamlit as st
import pandas as pd
import unicodedata
import re

# 1. CONFIGURAÇÃO E ESTILIZAÇÃO (CSS)
st.set_page_config(page_title="Gestor CAEPI Pro", layout="wide")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #f0f2f6; padding: 10px 10px 0px 10px; border-radius: 10px 10px 0px 0px; }
    .stTabs [data-baseweb="tab"] { height: 60px; background-color: #dee2e6; border-radius: 8px 8px 0px 0px; color: #495057; font-size: 18px; font-weight: bold; }
    .stTabs [aria-selected="true"] { background-color: #007bff !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÕES DE SUPORTE
def formatar_para_url(texto):
    if pd.isna(texto): return ""
    texto = unicodedata.normalize('NFKD', str(texto)).encode('ascii', 'ignore').decode('utf-8')
    texto = texto.lower().strip()
    texto = re.sub(r'[^a-z0-9]+', '-', texto)
    return re.sub(r'-+', '-', texto).strip('-')

def formatar_milhar(valor):
    """Formata números com ponto como separador de milhar (padrão brasileiro)"""
    try:
        return f"{int(valor):,}".replace(",", ".")
    except:
        return str(valor)

st.title("🛡️ Gestor de Consultas CAEPI")

# 3. CARREGAMENTO DE DADOS
uploaded_file = st.file_uploader("Suba o arquivo base_caepi_atualizada.csv", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig', low_memory=False)
    df.columns = [c.strip().upper() for c in df.columns]

    # Mapeamento de Colunas
    col_ca = "NR_CA" if "NR_CA" in df.columns else df.columns[0]
    col_laudo = "APROVADO PARA LAUDO" if "APROVADO PARA LAUDO" in df.columns else "APROVADO_PARA_LAUDO"
    col_fabricante = "RAZAO SOCIAL" if "RAZAO SOCIAL" in df.columns else "RAZAO_SOCIAL"
    col_validade = "DATA VALIDADE" if "DATA VALIDADE" in df.columns else "DATA_VALIDADE"
    col_natureza = "NATUREZA" if "NATUREZA" in df.columns else "NATUREZA_NACIONAL_IMPORTADO"

    # 4. DEFINIÇÃO DAS QUATRO ABAS
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 CONSULTA INDIVIDUAL (CA)", 
        "📊 RELATÓRIO DE EQUIPAMENTOS",
        "📈 ANÁLISE DA BASE DE DADOS",
        "ℹ️ VERSÃO"
    ])

    # --- ABA 1: BUSCADOR CA (AGLUTINADO) ---
    with tab1:
        st.header("🔎 Ficha Consolidada do Registro")
        ca_procurado = st.text_input("Digite o número do CA:", placeholder="Ex: 37750").strip()
        if ca_procurado:
            linhas_ca = df[df[col_ca].astype(str) == ca_procurado].copy()
            if not linhas_ca.empty:
                registro_unico = {col: (" / ".join(map(str, linhas_ca[col].dropna().unique())) if len(linhas_ca[col].dropna().unique()) > 1 else (linhas_ca[col].dropna().unique()[0] if len(linhas_ca[col].dropna().unique()) == 1 else "")) for col in linhas_ca.columns}
                eq_url = formatar_para_url(registro_unico.get("EQUIPAMENTO", ""))
                st.link_button(f"🔗 Ver Fotos e Detalhes no ConsultaCA", f"https://consultaca.com/{ca_procurado}/{eq_url}", type="primary")
                
                c1, c2 = st.columns(2)
                ordem = ["EQUIPAMENTO", "DESCRICAO EQUIPAMENTO", "SITUACAO", col_validade] + [c for c in registro_unico.keys() if c not in ["EQUIPAMENTO", "DESCRICAO EQUIPAMENTO", "SITUACAO", col_validade]]
                for i, k in enumerate(ordem):
                    if k in registro_unico:
                        v = registro_unico[k]
                        sit = str(registro_unico.get("SITUACAO", "")).upper()
                        if k == "SITUACAO": v = f'<span style="color:{"#28a745" if sit == "VÁLIDO" else "#dc3545"}; font-weight:bold;">{v}</span>'
                        elif k == col_validade: v = f'<span style="background-color:{"#28a745" if sit == "VÁLIDO" else "#dc3545"}; color:white; padding:2px 10px; border-radius:5px; font-weight:bold; display:inline-block;">{v}</span>'
                        (c1 if i < len(ordem)//2 else c2).markdown(f"**{k}:** {v}", unsafe_allow_html=True)
            else:
                st.warning("Número de CA não localizado.")

    # --- ABA 2: EQUIPAMENTO (AGRUPADO) ---
    with tab2:
        st.header("⛑ Análise por Tipo de Equipamento")
        st.write("**Somente EPIs com CA *'VÁLIDO'***")
        df_validos = df[df["SITUACAO"].str.upper() == "VÁLIDO"].copy()
        lista_eq = sorted(df_validos["EQUIPAMENTO"].unique())
        equip_sel = st.selectbox("Selecione o Equipamento:", ["Selecione..."] + lista_eq)
        if equip_sel != "Selecione...":
            st.subheader(f"📍 {equip_sel}")
            df_filtrado = df_validos[df_validos["EQUIPAMENTO"] == equip_sel]
            laudos = df_filtrado[col_laudo].dropna().unique()
            for laudo in laudos:
                if str(laudo).strip() == "": continue
                with st.expander(f"📋 LAUDO: {laudo}", expanded=True):
                    agrupado = df_filtrado[df_filtrado[col_laudo] == laudo].groupby(col_fabricante)[col_ca].unique()
                    for fab, cas in agrupado.items():
                        st.markdown(f"**🏢 {fab}**")
                        st.info(" • ".join(map(str, sorted(cas))))

    # --- ABA 3: ANÁLISE DO BANCO DE DADOS ---
    with tab3:
        st.header("📈 Visão Geral da Base de Dados")
        
        # Capturando propriedades do objeto carregado
        import datetime
        
        # Tamanho do arquivo em MB
        tamanho_mb = uploaded_file.size / (1024 * 1024)
        
        # No Streamlit, a 'data de modificação' original do arquivo no seu PC 
        # não é enviada pelo navegador. O que podemos registrar é o momento 
        # em que o arquivo foi disponibilizado para o sistema.
        data_leitura = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")

        st.write(f"### 📄 Propriedades do Arquivo")
        c_prop1, c_prop2 = st.columns(2)
        c_prop1.write(f"**Nome:** `{uploaded_file.name}`")
        c_prop1.write(f"**Tamanho:** {tamanho_mb:.2f} MB")
        c_prop2.write(f"**Tipo:** `{uploaded_file.type}`")
        c_prop2.write(f"**Processado em:** {data_leitura}")
        
        st.divider()
        
        # DataFrame de CAs únicos para estatísticas precisas
        df_unicos = df.drop_duplicates(subset=[col_ca])

        # Métricas de Resumo
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total de Registros (Linhas)", formatar_milhar(len(df)))
        m2.metric("CAs Únicos", formatar_milhar(len(df_unicos)))
        m3.metric("Fabricantes", formatar_milhar(df[col_fabricante].nunique()))
        m4.metric("Tipos de Equipamento", formatar_milhar(df['EQUIPAMENTO'].nunique()))
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📌 Situação dos CAs únicos")
            st.bar_chart(df_unicos["SITUACAO"].value_counts())
        with c2:
            st.subheader("🏢 Top 10 Fabricantes por Natureza")
            top_10_fab_list = df_unicos[col_fabricante].value_counts().head(10).index
            df_top10 = df_unicos[df_unicos[col_fabricante].isin(top_10_fab_list)]
            tabela_c2 = df_top10.groupby([col_fabricante, col_natureza]).size().unstack(fill_value=0)
            tabela_c2['TOTAL'] = tabela_c2.sum(axis=1)
            tabela_c2 = tabela_c2.sort_values(by='TOTAL', ascending=False).drop(columns=['TOTAL'])
            st.table(tabela_c2.map(formatar_milhar))
        st.subheader("📋 Detalhamento por Equipamento (Baseado em CAs Únicos)")
        resumo_eq = df_unicos.groupby(['EQUIPAMENTO', 'SITUACAO']).size().unstack(fill_value=0)
        st.dataframe(resumo_eq.map(formatar_milhar), use_container_width=True)

    # --- ABA 4: VERSÃO ---
    with tab4:
        st.header("ℹ️ Informações do Sistema")
        st.markdown("### Versão: 2026.03")
        st.divider()
        st.markdown("#### DIVISÃO DE PERÍCIAS PRT5")

else:
    st.info("Aguardando upload do arquivo base_caepi_atualizada.csv...")
