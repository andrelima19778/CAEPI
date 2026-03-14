import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Gestor CAEPI", layout="wide")

st.title("🛡️ Gestor de Consultas CAEPI")
st.markdown("Suba o arquivo gerado pelo seu atualizador para iniciar a análise.")

# 1. Upload do Arquivo
uploaded_file = st.file_uploader("Escolha o arquivo base_caepi_atualizada.csv", type="csv")

if uploaded_file is not None:
    # Lendo a base (usando o padrão que definimos nos passos anteriores)
    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig', low_memory=False)
    
    # Padronização das colunas
    df.columns = [c.strip().upper() for c in df.columns]

    # Criação das Abas
    tab1, tab2 = st.tabs(["🔍 Buscador CA", "🏗️ Equipamento (Válidos)"])

    # --- ABA 1: BUSCADOR CA ---
    with tab1:
        st.header("Busca por Registro Individual")
        col_ca_nome = "NR_CA" if "NR_CA" in df.columns else df.columns[0]
        
        ca_procurado = st.text_input("Digite o número do CA:", placeholder="Ex: 12345").strip()

        if ca_procurado:
            resultado = df[df[col_ca_nome].astype(str) == ca_procurado]
            
            if not resultado.empty:
                st.success(f"Registro encontrado para o CA {ca_procurado}")
                # Exibe de forma organizada em um dicionário/lista
                for _, row in resultado.iterrows():
                    st.json(row.to_dict())
            else:
                st.warning("Número de CA não localizado na base.")

    # --- ABA 2: EQUIPAMENTO ---
    with tab2:
        st.header("Análise de Equipamentos Válidos")
        
        if "SITUACAO" in df.columns and "EQUIPAMENTO" in df.columns:
            # Filtro inicial: Apenas Válidos
            df_validos = df[df["SITUACAO"].str.upper() == "VÁLIDO"].copy()
            
            # Seleção de Equipamento (Sem repetição)
            lista_equipamentos = sorted(df_validos["EQUIPAMENTO"].unique())
            equip_selecionado = st.selectbox("Selecione um Equipamento:", ["Selecione..."] + lista_equipamentos)

            if equip_selecionado != "Selecione...":
                st.subheader(f"Equipamento: {equip_selecionado}")
                
                # Filtrar laudos para o equipamento escolhido
                # Ajustamos para o nome exato da coluna (com ou sem espaço)
                col_laudo = "APROVADO PARA LAUDO" if "APROVADO PARA LAUDO" in df.columns else "APROVADO_PARA_LAUDO"
                
                if col_laudo in df_validos.columns:
                    laudos = df_validos[df_validos["EQUIPAMENTO"] == equip_selecionado][col_laudo].unique()
                    
                    st.write("**Laudos Aprovados:**")
                    if len(laudos) > 0:
                        for l in laudos:
                            if pd.notna(l) and str(l).strip() != "":
                                st.info(l)
                    else:
                        st.write("Nenhum laudo específico encontrado.")
                else:
                    st.error(f"Coluna de laudos ('{col_laudo}') não encontrada.")
        else:
            st.error("As colunas 'SITUACAO' ou 'EQUIPAMENTO' não foram encontradas no CSV.")

else:
    st.info("Aguardando upload do arquivo CSV...")