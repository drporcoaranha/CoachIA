import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# --- Configuração da Página ---
st.set_page_config(page_title="Treinador Suprabio", layout="wide", page_icon="💊")

# --- Variáveis Globais ---
ARQUIVO_HISTORICO = "historico_treinamento.csv"

# --- Funções Auxiliares ---
def carregar_dados():
    colunas_padrao = ["Data", "Colaborador", "Cenario", "Resposta", "Nota", "FeedbackIA", "ComentariosGerente"]
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            return pd.read_csv(ARQUIVO_HISTORICO)
        except:
            return pd.DataFrame(columns=colunas_padrao)
    else:
        return pd.DataFrame(columns=colunas_padrao)

def salvar_sessao(colaborador, cenario, resposta, nota, feedback_ia, comentario_gerente):
    df = carregar_dados()
    novo_registro = pd.DataFrame([{
        "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Colaborador": colaborador,
        "Cenario": cenario,
        "Resposta": resposta,
        "Nota": nota,
        "FeedbackIA": feedback_ia,
        "ComentariosGerente": comentario_gerente
    }])
    df = pd.concat([df, novo_registro], ignore_index=True)
    df.to_csv(ARQUIVO_HISTORICO, index=False)
    return df

# Função para converter DF para CSV baixável
def converter_para_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# --- Interface Principal ---
st.title("💊 Treinador de Vendas - Suprabio")

# --- Barra Lateral ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=50)
    st.header("Configurações")
    
    # Campo de senha (API Key)
    api_key = st.text_input("Cole sua API Key do Gemini aqui:", type="password")
    st.caption("A chave não fica salva quando a página recarrega.")
    
    colaborador_atual = st.selectbox(
        "Quem está treinando?",
        ["Selecione...", "André", "Bruna", "Eliana", "Gabriel", "Leticia", "Marcella", "Layana"]
    )
    
    # Produtos editáveis
    produtos_suprabio = st.text_area(
        "Produtos do Treino",
        value="Suprabio A-Z, Suprabio Cabelos e Unhas, Suprabio Mulher, Suprabio Sênior, Suprabio Cálcio MDK.",
        height=100
    )

# --- Abas ---
tab1, tab2 = st.tabs(["🏋️ Simulação (Roleplay)", "📊 Relatórios"])

# --- ABA 1: SIMULAÇÃO ---
with tab1:
    if api_key and colaborador_atual != "Selecione...":
        genai.configure(api_key=api_key)
        
        # Estados da sessão
        if "cenario" not in st.session_state: st.session_state.cenario = ""
        if "feedback" not in st.session_state: st.session_state.feedback = ""
        if "nota" not in st.session_state: st.session_state.nota = 0.0

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("1. Cenário do Cliente")
            if st.button("🔄 Gerar Novo Cliente", type="primary"):
                with st.spinner("Criando cliente..."):
                    try:
                        # CORREÇÃO AQUI: Mudado para 'gemini-pro'
                        model = genai.GenerativeModel('gemini-pro')
                        prompt = f"Crie uma fala curta de um cliente de farmácia com uma queixa que se resolve com: {produtos_suprabio}. Seja natural."
                        res = model.generate_content(prompt)
                        st.session_state.cenario = res.text
                        st.session_state.feedback = ""
                        st.session_state.nota = 0.0
                    except Exception as e:
                        st.error(f"Erro na API: {e}")

            if st.session_state.cenario:
                st.info(f"🗣️ **Cliente:** {st.session_state.cenario}")
                
                st.subheader("2. Resposta do Vendedor")
                resposta = st.text_area("O que o colaborador respondeu?", height=100)
                
                if st.button("🤖 Avaliar Resposta"):
                    if resposta:
                        with st.spinner("O Treinador IA está analisando..."):
                            try:
                                # CORREÇÃO AQUI: Mudado para 'gemini-pro'
                                model = genai.GenerativeModel('gemini-pro')
                                prompt_av = f"""
                                Avalie venda farmácia. Cenário: {st.session_state.cenario}. Resposta: {resposta}. Produtos: {produtos_suprabio}.
                                Critérios: Empatia, Sondagem, Benefício.
                                SAÍDA: 1ª linha apenas número da nota (ex: 7.5). Linhas seguintes: feedback.
                                """
                                res = model.generate_content(prompt_av)
                                txt = res.text.strip().split('\n')
                                try:
                                    # Lógica para pegar a nota mesmo se vier texto antes
                                    primeira_linha = txt[0]
                                    import re
                                    # Procura o primeiro número float na linha
                                    match = re.search(r"(\d+(\.\d+)?)", primeira_linha)
                                    if match:
                                        st.session_state.nota = float(match.group(1))
                                    else:
                                        st.session_state.nota = 5.0
                                    
                                    st.session_state.feedback = "\n".join(txt[1:])
                                except:
                                    st.session_state.nota = 0.0
                                    st.session_state.feedback = res.text
                            except Exception as e:
                                st.error(f"Erro na avaliação: {e}")

        with col2:
            if st.session_state.feedback:
                st.subheader("3. Feedback")
                cor = "green" if st.session_state.nota >= 7 else "red"
                st.markdown(f"### Nota IA: :{cor}[{st.session_state.nota}/10]")
                st.write(st.session_state.feedback)
                
                st.markdown("---")
                comentario_gerente = st.text_input("Observação do Gerente (Opcional):")
                
                if st.button("💾 Salvar Treinamento"):
                    salvar_sessao(colaborador_atual, st.session_state.cenario, resposta, st.session_state.nota, st.session_state.feedback, comentario_gerente)
                    st.success("Salvo! Vá para a aba Relatórios para baixar.")

    elif colaborador_atual == "Selecione...":
        st.warning("👈 Selecione o colaborador na barra lateral.")
    else:
        st.warning("👈 Cole sua API Key na barra lateral.")

# --- ABA 2: RELATÓRIOS ---
with tab2:
    st.header("Histórico da Sessão")
    st.warning("⚠️ Importante: Baixe o CSV antes de fechar o navegador, ou os dados serão perdidos na nuvem.")
    
    df = carregar_dados()
    if not df.empty:
        csv = converter_para_csv(df)
        
        st.download_button(
            label="📥 Baixar Relatório em Excel (CSV)",
            data=csv,
            file_name=f"treino_suprabio_{datetime.now().strftime('%d-%m')}.csv",
            mime='text/csv',
        )
        
        st.dataframe(df)
    else:
        st.info("Nenhum dado salvo ainda.")
