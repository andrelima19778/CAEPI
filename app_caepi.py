import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Gestor CAEPI", layout="wide")

st.title("🛡️ Gestor de Consultas CAEPI")
st.markdown("Suba o arquivo gerado pelo seu atualizador para iniciar a análise.")

# 1. Upload do Arquivo
uploaded_file = st.file_uploader("Escolha o arquivo base_caepi_atualizada.csv", type="csv")

if uploaded_file is not None:
    # Lendo a base com o encoding correto para garantir os acentos
    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig', low_memory=False)
    
    # Padronização das colunas
    df.columns = [c.strip().upper() for c in df.columns]

    # Identificação das colunas (Tratando possíveis variações de nome)
    col_ca = "NR_CA" if "NR_CA" in df.columns else df.columns[0]
    col_laudo = "APROVADO PARA LAUDO" if "APROVADO PARA LAUDO" in df.columns else "APROVADO_PARA_LAUDO"
    col_fabricante = "RAZAO SOCIAL" if "RAZAO SOCIAL" in df.columns else "RAZAO_SOCIAL"

    # Criação das Abas
    tab1, tab2 = st.tabs(["🔍 Buscador CA", "🏗️ Equipamento (Válido)"])

    # --- ABA 1: BUSCADOR CA ---
    with tab1:
        st.header("Busca por Registro Individual")
        ca_procurado = st.text_input("Digite o número do CA:", placeholder="Ex: 12345").strip()

        if ca_procurado:
            resultado = df[df[col_ca].astype(str) == ca_procurado]
            if not resultado.empty:
                st.success(f"Registro encontrado para o CA {ca_procurado}")
                for _, row in resultado.iterrows():
                    st.json(row.to_dict())
            else:
                st.warning("Número de CA não localizado na base.")

    # --- ABA 2: EQUIPAMENTO (Agrupado por Fabricante) ---
    with tab2:
        st.header("Análise de Equipamentos Válidos")
        st.write("**Somente equipamentos com CA e situação 'VÁLIDO'**")
        
        # Verificação se as colunas necessárias existem
        colunas_necessarias = ["SITUACAO", "EQUIPAMENTO", col_fabricante]
        if all(c in df.columns for c in colunas_necessarias):
            
            # Filtro inicial: Apenas Válidos
            df_validos = df[df["SITUACAO"].str.upper() == "VÁLIDO"].copy()
            
            # Seleção de Equipamento
            lista_equipamentos = sorted(df_validos["EQUIPAMENTO"].unique())
            equip_selecionado = st.selectbox("Selecione um Equipamento:", ["Selecione..."] + lista_equipamentos)

            if equip_selecionado != "Selecione...":
                st.subheader(f"Equipamento: {equip_selecionado}")
                st.write("O resultado da busca de CAs está filtrado por tipo de laudo e agrupado por fabricante")
                
                # Filtrar registros para o equipamento escolhido
                df_filtrado = df_validos[df_validos["EQUIPAMENTO"] == equip_selecionado]
                laudos_unicos = df_filtrado[col_laudo].dropna().unique()
                
                if len(laudos_unicos) > 0:
                    for laudo in laudos_unicos:
                        if str(laudo).strip() == "": continue
                        
                        with st.expander(f"📋 LAUDO: {laudo}", expanded=True):
                            # Filtra o dataframe para este laudo específico
                            df_laudo_especifico = df_filtrado[df_filtrado[col_laudo] == laudo]
                            
                            # Agrupa por Fabricante e coleta os CAs
                            agrupado = df_laudo_especifico.groupby(col_fabricante)[col_ca].unique()
                            
                            for fabricante, cas in agrupado.items():
                                st.markdown(f"**🏢 {fabricante}**")
                                # Lista linear horizontal de CAs para este fabricante
                                lista_cas = " • ".join(map(str, sorted(cas)))
                                st.info(lista_cas)
                else:
                    st.info("Nenhum laudo específico encontrado para este equipamento.")
        else:
            st.error(f"Erro: Certifique-se de que as colunas 'SITUACAO', 'EQUIPAMENTO' e '{col_fabricante}' existem no arquivo.")

else:
    st.info("Aguardando upload do arquivo CSV...")
        else:
            st.error("As colunas 'SITUACAO' ou 'EQUIPAMENTO' não foram encontradas no CSV.")

else:
    st.info("Aguardando upload do arquivo CSV...")
