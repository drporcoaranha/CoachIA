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
st.set_page_config(
    page_title="Treinador Suprabio",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS Mobile ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        height: 3.5em;
        font-weight: bold;
        border-radius: 12px;
        font-size: 16px;
    }
    .cliente-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 20px;
    }
    .cliente-texto {
        font-size: 18px;
        font-weight: 600;
        color: #31333F;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Arquivos ---
ARQUIVO_HISTORICO = "historico_treinamento.csv"
ARQUIVO_EQUIPE = "equipe.csv"

# --- Funções ---
def carregar_equipe():
    if os.path.exists(ARQUIVO_EQUIPE):
        try: return pd.read_csv(ARQUIVO_EQUIPE)['Nome'].tolist()
        except: pass
    padrao = ["André", "Bruna", "Eliana", "Gabriel", "Leticia", "Marcella", "Layana"]
    salvar_equipe(padrao)
    return padrao

def salvar_equipe(lista):
    pd.DataFrame({'Nome': lista}).to_csv(ARQUIVO_EQUIPE, index=False)

def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try: return pd.read_csv(ARQUIVO_HISTORICO)
        except: pass
    return pd.DataFrame(columns=["Data", "Colaborador", "Cenario", "Resposta", "Nota", "FeedbackIA", "ObsGerente"])

def salvar_sessao(dados):
    df = carregar_historico()
    df = pd.concat([df, pd.DataFrame([dados])], ignore_index=True)
    df.to_csv(ARQUIVO_HISTORICO, index=False)

# --- FUNÇÃO INTELIGENTE DE SELEÇÃO DE MODELO ---
@st.cache_resource
def encontrar_modelo_disponivel():
    """
    Em vez de adivinhar, esta função lista o que o servidor aceita
    e escolhe o melhor disponível.
    """
    try:
        modelos_disponiveis = []
        # Tenta listar todos os modelos da sua conta
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelos_disponiveis.append(m.name)
        
        # Se não achou nada, força o padrão antigo
        if not modelos_disponiveis:
            return "models/gemini-pro"

        # Prioridade: Tenta achar o 1.5 Flash (mais rápido), senão o Pro, senão o primeiro da lista
        for m in modelos_disponiveis:
            if "flash" in m: return m
        for m in modelos_disponiveis:
            if "pro" in m and "1.5" in m: return m
        for m in modelos_disponiveis:
            if "gemini-pro" in m: return m
            
        return modelos_disponiveis[0] # Retorna qualquer um que funcione
        
    except Exception as e:
        return None # Retorna erro para tratar na interface

# Descobre o modelo ao iniciar
MODELO_NOME = encontrar_modelo_disponivel()

# --- ESTADO INICIAL ---
if "equipe" not in st.session_state: st.session_state.equipe = carregar_equipe()
if "cenario" not in st.session_state: st.session_state.cenario = ""
if "nota" not in st.session_state: st.session_state.nota = 0.0

lista_suprabio = "Magnesio dimalato, cloreto de magnesio, melatonina, Coenzima Q10, Complexo B, Vitamina C, Omega 3, Poliviaminico Suprabio Homem, Suprabio Mulher, Suprabio 50+, Suprabio Cabelos e unhas, Fibras, Collageno, Luteina, Calcio MDK, Clamvit Zen, Lactulose."

if "produtos" not in st.session_state: 
    st.session_state.produtos = lista_suprabio

# --- INTERFACE ---
col_titulo, col_config = st.columns([5, 1])
with col_titulo:
    st.title("💊 Treino Suprabio")
    # Debug discreto para sabermos qual modelo foi escolhido
    if MODELO_NOME:
        st.caption(f"Conectado via: {MODELO_NOME.replace('models/', '')}")
    else:
        st.error("⚠️ Erro crítico: Não foi possível listar modelos. Verifique API Key.")

with col_config:
    with st.popover("⚙️", use_container_width=True):
        st.header("Ajustes")
        st.session_state.produtos = st.text_area("Produtos:", st.session_state.produtos, height=150)
        st.markdown("---")
        novo = st.text_input("Add Colaborador:")
        if st.button("➕") and novo:
            st.session_state.equipe.append(novo)
            salvar_equipe(st.session_state.equipe)
            st.rerun()
        df = carregar_historico()
        if not df.empty:
            st.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "treino.csv", "text/csv")

st.write("### 👤 Quem vai treinar agora?")
colaborador = st.selectbox("Vendedor:", ["Clique..."] + st.session_state.equipe, label_visibility="collapsed")
st.markdown("---")

if colaborador != "Clique...":
    if not st.session_state.cenario:
        if st.button("🔔 CHAMAR PRÓXIMO CLIENTE", type="primary"):
            if not MODELO_NOME:
                st.error("Sistema offline. Verifique a chave API ou requirements.txt")
            else:
                with st.spinner(f"Gerando cliente usando {MODELO_NOME.split('/')[-1]}..."):
                    try:
                        model = genai.GenerativeModel(MODELO_NOME)
                        res = model.generate_content(f"Crie uma fala curta (1 frase entre aspas) de um cliente de farmácia com queixa para: {st.session_state.produtos}. Natural.")
                        st.session_state.cenario = res.text.replace('"', '')
                        st.session_state.feedback = ""
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao gerar: {e}")

    else:
        st.markdown(f"""<div class="cliente-box"><span style="color:#555;">🗣️ O CLIENTE DIZ:</span><br><div class="cliente-texto">"{st.session_state.cenario}"</div></div>""", unsafe_allow_html=True)
        resposta = st.text_area("✍️ Resposta:", height=100)

        if st.button("✅ AVALIAR"):
            if not resposta:
                st.warning("Escreva a resposta!")
            else:
                with st.spinner("Avaliando..."):
                    try:
                        model = genai.GenerativeModel(MODELO_NOME)
                        res = model.generate_content(f"Avalie venda farmacia. Cenario: {st.session_state.cenario}. Resposta: {resposta}. Produtos: {st.session_state.produtos}. Dê nota 0-10 e feedback.")
                        st.session_state.feedback = res.text
                        match = re.search(r"(\d+[\.,]\d+|\d+)", res.text)
                        st.session_state.nota = float(match.group(0).replace(',', '.')) if match else 0.0
                        st.rerun()
                    except Exception as e:
                        st.error(f"ERRO AO AVALIAR: {e}")

        if st.session_state.feedback:
            st.markdown("---")
            cor = "green" if st.session_state.nota >= 7 else "red"
            st.markdown(f"<h1 style='text-align: center; color: {cor}'>{st.session_state.nota}/10</h1>", unsafe_allow_html=True)
            st.info(st.session_state.feedback)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 SALVAR"):
                    salvar_sessao({"Data": datetime.now().strftime("%d/%m %H:%M"), "Colaborador": colaborador, "Nota": st.session_state.nota})
                    st.success("Salvo!")
                    st.session_state.cenario = ""
                    st.session_state.feedback = ""
                    st.rerun()
            with col2:
                if st.button("🗑️ DESCARTAR"):
                    st.session_state.cenario = ""
                    st.session_state.feedback = ""
                    st.rerun()
