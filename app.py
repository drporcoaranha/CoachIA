import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime
import re

# --- CONFIGURAÇÃO DA CHAVE DE API ---
# Verifique se esta chave está correta e ativa no Google AI Studio
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

# --- Função de Teste de Modelo (ROBUSTA) ---
def tentar_gerar(prompt_texto):
    """Tenta modelos em sequência até um funcionar"""
    lista_tentativas = ["gemini-1.5-flash", "gemini-pro", "models/gemini-1.5-flash-latest"]
    
    ultimo_erro = ""
    
    for modelo in lista_tentativas:
        try:
            model = genai.GenerativeModel(modelo)
            return model.generate_content(prompt_texto)
        except Exception as e:
            ultimo_erro = str(e)
            continue # Tenta o próximo
            
    # Se chegou aqui, nenhum funcionou. Lança o erro para aparecer na tela.
    raise Exception(f"Falha em todos os modelos. Último erro: {ultimo_erro}")

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
            with st.spinner("Conectando..."):
                try:
                    # TENTA GERAR USANDO A NOVA FUNÇÃO DE DIAGNÓSTICO
                    res = tentar_gerar(f"Crie uma fala curta (1 frase entre aspas) de um cliente de farmácia com queixa para: {st.session_state.produtos}. Natural.")
                    st.session_state.cenario = res.text.replace('"', '')
                    st.session_state.feedback = ""
                    st.rerun()
                except Exception as e:
                    # MOSTRA O ERRO REAL NA TELA
                    st.error(f"ERRO TÉCNICO: {e}")
                    st.warning("Dica: Verifique se o arquivo requirements.txt no GitHub tem a linha: google-generativeai>=0.8.3")

    else:
        st.markdown(f"""<div class="cliente-box"><span style="color:#555;">🗣️ O CLIENTE DIZ:</span><br><div class="cliente-texto">"{st.session_state.cenario}"</div></div>""", unsafe_allow_html=True)
        resposta = st.text_area("✍️ Resposta:", height=100)

        if st.button("✅ AVALIAR"):
            if not resposta:
                st.warning("Escreva a resposta!")
            else:
                with st.spinner("Avaliando..."):
                    try:
                        res = tentar_gerar(f"Avalie venda farmacia. Cenario: {st.session_state.cenario}. Resposta: {resposta}. Produtos: {st.session_state.produtos}. Dê nota 0-10 e feedback.")
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
