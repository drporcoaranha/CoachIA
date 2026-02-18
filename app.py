import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime
import re

# --- CONFIGURAÇÃO DA CHAVE DE API ---
API_KEY = "AIzaSyD7sS0C6UIITfgkHAd9oJs4YzDHfELV_us"
genai.configure(api_key=API_KEY)

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

def converter_para_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# --- FUNÇÃO DE AUTO-DESCOBERTA DE MODELO ---
@st.cache_resource
def obter_modelo_disponivel():
    """
    Busca automaticamente qual modelo está ativo na conta para evitar erro 404.
    """
    try:
        # Lista todos os modelos disponíveis para sua chave
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: # Prioriza o Flash (mais rápido)
                    return m.name
        
        # Se não achar flash, pega o primeiro genérico (ex: gemini-pro)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return m.name
                
    except Exception as e:
        return None
    return "models/gemini-pro" # Fallback final

# Define o modelo uma vez ao carregar
MODELO_NOME = obter_modelo_disponivel()

# --- Interface Principal ---
st.title("💊 Treinador de Vendas - Suprabio")

# --- Barra Lateral ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=50)
    st.header("Configurações")
    
    colaborador_atual = st.selectbox(
        "Quem está treinando?",
        ["Selecione...", "André", "Bruna", "Eliana", "Gabriel", "Leticia", "Marcella", "Layana"]
    )
    
    if MODELO_NOME:
        st.caption(f"✅ Conectado ao modelo: {MODELO_NOME.replace('models/', '')}")
    else:
        st.error("❌ Erro ao buscar modelos. Verifique a API Key.")

    produtos_suprabio = st.text_area(
        "Produtos do Treino",
        value="Suprabio A-Z, Suprabio Cabelos e Unhas, Suprabio Mulher, Suprabio Sênior, Suprabio Cálcio MDK.",
        height=100
    )

# --- Abas ---
tab1, tab2 = st.tabs(["🏋️ Simulação (Roleplay)", "📊 Relatórios"])

# --- ABA 1: SIMULAÇÃO ---
with tab1:
    if colaborador_atual != "Selecione...":
        
        if "cenario" not in st.session_state: st.session_state.cenario = ""
        if "feedback" not in st.session_state: st.session_state.feedback = ""
        if "nota" not in st.session_state: st.session_state.nota = 0.0

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("1. Cenário do Cliente")
            if st.button("🔄 Gerar Novo Cliente", type="primary"):
                with st.spinner("Criando cliente..."):
                    try:
                        model = genai.GenerativeModel(MODELO_NOME)
                        prompt = f"Crie uma fala curta (apenas a fala entre aspas) de um cliente de farmácia com uma queixa que se resolve com: {produtos_suprabio}. Seja natural e use linguagem coloquial brasileira."
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
                                model = genai.GenerativeModel(MODELO_NOME)
                                prompt_av = f"""
                                Aja como um gerente experiente de farmácia treinando a equipe.
                                Cenário: {st.session_state.cenario}
                                Resposta do Vendedor: {resposta}
                                Produtos Alvo: {produtos_suprabio}
                                
                                Avalie com rigor:
                                1. Empatia (conectou com a dor do cliente?)
                                2. Sondagem (fez perguntas investigativas?)
                                3. Benefício (focou no resultado e não na fórmula?)
                                
                                SAÍDA OBRIGATÓRIA:
                                A primeira linha deve ser EXATAMENTE assim: "Nota: X.X" (onde X é a nota).
                                Pule uma linha e dê o feedback detalhado.
                                """
                                res = model.generate_content(prompt_av)
                                txt = res.text.strip().split('\n')
                                
                                try:
                                    primeira_linha = txt[0]
                                    match = re.search(r"(\d+[\.,]\d+|\d+)", primeira_linha)
                                    if match:
                                        nota_str = match.group(0).replace(',', '.')
                                        st.session_state.nota = float(nota_str)
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
                    st.session_state.cenario = ""
                    st.session_state.feedback = ""
                    st.rerun()

    elif colaborador_atual == "Selecione...":
        st.warning("👈 Selecione o colaborador na barra lateral para começar.")

with tab2:
    st.header("Histórico da Sessão")
    st.warning("⚠️ Lembre-se: Baixe o CSV antes de fechar o navegador.")
    df = carregar_dados()
    if not df.empty:
        csv = converter_para_csv(df)
        st.download_button(label="📥 Baixar Relatório (CSV)", data=csv, file_name=f"treino_suprabio.csv", mime='text/csv')
        st.dataframe(df)
    else:
        st.info("Nenhum dado salvo ainda.")
