import streamlit as st
import pandas as pd
import unicodedata
import re
import datetime

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
        # Garante que tratamos o valor como string antes de formatar, útil para CAs
        num = int(float(str(valor).replace(',', '.')))
        return f"{num:,}".replace(",", ".")
    except:
        return str(valor)

st.title("🛡️ Gestor de Consultas CAEPI")

# 3. CARREGAMENTO DE DADOS
uploaded_file = st.file_uploader("Suba o arquivo base_caepi_atualizada.csv", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig', low_memory=False)
    df.columns = [c.strip().upper() for c in df.columns]

    # Mapeamento Dinâmico de Colunas para evitar KeyError
    col_ca = next((c for c in df.columns if c in ["NR_CA", "NUMERO_CA"]), df.columns[0])
    col_laudo = next((c for c in df.columns if c in ["APROVADO PARA LAUDO", "APROVADO_PARA_LAUDO"]), "APROVADO PARA LAUDO")
    col_fabricante = next((c for c in df.columns if c in ["RAZAO SOCIAL", "RAZAO_SOCIAL"]), "RAZAO SOCIAL")
    col_validade = next((c for c in df.columns if c in ["DATA VALIDADE", "DATA_VALIDADE", "DATA DE VALIDADE"]), "DATA DE VALIDADE")
    col_natureza = next((c for c in df.columns if c in ["NATUREZA", "NATUREZA_NACIONAL_IMPORTADO"]), "NATUREZA")

    # 4. DEFINIÇÃO DAS CINCO ABAS
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 CONSULTA INDIVIDUAL (CA)", 
        "📋 CONSULTA EM LOTE (CA)",
        "📊 RELATÓRIO DE EQUIPAMENTOS",
        "📈 ANÁLISE DA BASE DE DADOS",
        "ℹ️ VERSÃO"
    ])

    # --- ABA 1: CONSULTA INDIVIDUAL ---
    with tab1:
        st.header("🔎 Ficha Consolidada do Registro")
        ca_procurado = st.text_input("Digite o número do CA:", placeholder="Ex: 37750", key="indiv").strip()
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
                        # Formatação de milhar específica para o campo NR_CA na exibição
                        #if k == col_ca: v = formatar_milhar(v)
                        if k == col_ca: v = v.astype(str)
                        if k == "EQUIPAMENTO":
                            v = f"**{v}**"
                        
                        if k == "SITUACAO": v = f'<span style="color:{"#28a745" if sit == "VÁLIDO" else "#dc3545"}; font-weight:bold;">{v}</span>'
                        elif k == col_validade: v = f'<span style="background-color:{"#28a745" if sit == "VÁLIDO" else "#dc3545"}; color:white; padding:2px 10px; border-radius:5px; font-weight:bold; display:inline-block;">{v}</span>'
                        (c1 if i < len(ordem)//2 else c2).markdown(f"**{k}:** {v}", unsafe_allow_html=True)

    # --- ABA 2: CONSULTA EM LOTE (CORRIGIDA) ---
    with tab2:
        st.header("📋 Consulta de múltiplos CAs")
        st.markdown("Cole os números de CA (um por linha) para obter os dados principais.")
        ca_texto = st.text_area("Lista de CAs:", placeholder="37750\n41234", height=200)
        
        if ca_texto:
            lista_cas = [ca.strip() for ca in ca_texto.split('\n') if ca.strip()]
            if lista_cas:
                # Busca os CAs na base (CAs únicos)
                df_lote = df[df[col_ca].astype(str).isin(lista_cas)].drop_duplicates(subset=[col_ca])
                
                if not df_lote.empty:
                    # Seleção explícita das 3 colunas solicitadas
                    resultado = df_lote[[col_ca, 'EQUIPAMENTO', col_validade, 'SITUACAO']].copy()
                    
                    # Formatação do número do CA (substituindo vírgula por ponto)
                    #resultado[col_ca] = resultado[col_ca].apply(formatar_milhar)

                    # Converte todo o DataFrame para string (texto puro)
                    resultado = resultado.astype(str)
                    
                    # Renomeia para exibição amigável
                    resultado.columns = ['Nº CA', 'EQUIPAMENTO', 'DATA DE VALIDADE', 'SITUACAO']
                    
                    st.markdown(f"A lista apresentou {len(lista_cas)} CA(s). Encontrados {len(resultado)} registro(s).")
                    st.dataframe(resultado, use_container_width=True, hide_index=True)
                    
                    csv_lote = resultado.to_csv(index=False, sep=';', encoding='utf-8-sig')
                    st.download_button("📥 Baixar Resultado (CSV)", csv_lote, "consulta_lote.csv", "text/csv")
                else:
                    st.error("Nenhum dos CAs informados foi encontrado na base.")

    # --- ABA 3: RELATÓRIO DE EQUIPAMENTOS ---
    with tab3:
        st.header("⛑ Análise por Tipo de Equipamento")
        st.markdown("##### Filtragem dos CAs *'válidos'*, por tipo de laudo e por fabricante")
        df_validos = df[df["SITUACAO"].str.upper() == "VÁLIDO"].copy()
        lista_eq = sorted(df_validos["EQUIPAMENTO"].unique())
        equip_sel = st.selectbox("Selecione o Equipamento:", ["Selecione..."] + lista_eq)
        if equip_sel != "Selecione...":
            df_filtrado = df_validos[df_validos["EQUIPAMENTO"] == equip_sel]
            laudos = df_filtrado[col_laudo].dropna().unique()
            for laudo in laudos:
                if str(laudo).strip() == "": continue
                with st.expander(f"📋 LAUDO: {laudo}", expanded=True):
                    agrupado = df_filtrado[df_filtrado[col_laudo] == laudo].groupby(col_fabricante)[col_ca].unique()
                    for fab, cas in agrupado.items():
                        st.markdown(f"**🏢 {fab}**")
                        # Formata os CAs na lista horizontal
                        #cas_formatados = [formatar_milhar(c) for c in sorted(cas)]
                        cas_formatados = [c.astype(str) for c in sorted(cas)]
                        st.info(" • ".join(cas_formatados))

    # --- ABA 4: ANÁLISE DO BANCO DE DADOS ---
    with tab4:
        st.subheader("📈 Visão Geral da Base de Dados")
        df_unicos = df.drop_duplicates(subset=[col_ca])
        #data_proc = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")
        #st.info(f"📅 **Base:** {uploaded_file.name} | **Processado em:** {data_proc}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total de Registros", formatar_milhar(len(df)))
        m2.metric("CAs Únicos", formatar_milhar(len(df_unicos)))
        m3.metric("Fabricantes", formatar_milhar(df[col_fabricante].nunique()))
        m4.metric("Tipos de Equipamento", formatar_milhar(df['EQUIPAMENTO'].nunique()))
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📌 Situação dos CAs únicos")
            st.bar_chart(df_unicos["SITUACAO"].value_counts())
        with c2:
            st.subheader("🏢 Top 10 Fabricantes")
            top_10 = df_unicos[col_fabricante].value_counts().head(10).index
            df_top = df_unicos[df_unicos[col_fabricante].isin(top_10)]
            tabela = df_top.groupby([col_fabricante, col_natureza]).size().unstack(fill_value=0)
            tabela['TOTAL'] = tabela.sum(axis=1)
            tabela = tabela.sort_values(by='TOTAL', ascending=False).drop(columns=['TOTAL'])
            st.table(tabela.map(formatar_milhar))
        st.subheader("📋 Detalhamento por Equipamento (Baseado em CAs únicos)")
        resumo_eq = df_unicos.groupby(['EQUIPAMENTO', 'SITUACAO']).size().unstack(fill_value=0)
        resumo_eq_invertido = resumo_eq.iloc[:, ::-1]
        st.dataframe(resumo_eq_invertido.map(formatar_milhar), use_container_width=True)

    # --- ABA 5: VERSÃO ---
    with tab5:
        st.subheader("ℹ️ Informações do Sistema")
        
        # Criando os dados da tabela de versão
        dados_versao = {
            "Data de Versionamento": ["2026.03"],
            "Descrição": ["Versão inicial"]
        }
        df_versao = pd.DataFrame(dados_versao)
        
        # Exibindo a tabela formatada
        st.table(df_versao)
        
        st.divider()

        # Texto centralizado utilizando HTML
        #st.markdown('<p style="text-align: center; font-size: 20px; font-weight: bold;">DIVISÃO DE PERÍCIAS PRT5</p>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; font-size: 20px;">DIVISÃO DE PERÍCIAS PRT5</p>', unsafe_allow_html=True)

else:
    st.info("Aguardando upload do arquivo base_caepi_atualizada.csv...")
