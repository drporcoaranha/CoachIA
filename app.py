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

# --- Estilo CSS Personalizado (Visual Mobile) ---
st.markdown("""
<style>
    /* Aumentar botões para facilitar o toque */
    .stButton>button {
        width: 100%;
        height: 3.5em;
        font-weight: bold;
        border-radius: 12px;
        font-size: 16px;
    }
    /* Destaque para a caixa do cliente */
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
    /* Esconder menu padrão do Streamlit para limpar a tela */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Arquivos ---
ARQUIVO_HISTORICO = "historico_treinamento.csv"
ARQUIVO_EQUIPE = "equipe.csv"

# --- Funções de Dados ---
def carregar_equipe():
    if os.path.exists(ARQUIVO_EQUIPE):
        return pd.read_csv(ARQUIVO_EQUIPE)['Nome'].tolist()
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

# --- Função IA Inteligente ---
@st.cache_resource
def get_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods and 'flash' in m.name:
                return m.name
        return "models/gemini-pro"
    except: return "models/gemini-pro"

MODELO_ATUAL = get_model()

# --- ESTADO INICIAL ---
if "equipe" not in st.session_state: st.session_state.equipe = carregar_equipe()
if "cenario" not in st.session_state: st.session_state.cenario = ""
if "produtos" not in st.session_state: st.session_state.produtos = "Suprabio A-Z, Cabelos e Unhas, Mulher, Sênior, Cálcio MDK."
if "nota" not in st.session_state: st.session_state.nota = 0.0

# ==========================================
# HEADER E CONFIGURAÇÕES (BOTÃO DISCRETO)
# ==========================================
col_titulo, col_config = st.columns([5, 1])
with col_titulo:
    st.title("💊 Treino Suprabio")
with col_config:
    # O MENU DE CONFIGURAÇÃO FICA AQUI DENTRO
    with st.popover("⚙️", use_container_width=True):
        st.header("Ajustes do Gerente")
        
        # Gestão de Produtos
        st.session_state.produtos = st.text_area("Produtos Foco:", st.session_state.produtos, height=100)
        
        st.markdown("---")
        # Gestão de Equipe
        st.subheader("Equipe")
        novo = st.text_input("Adicionar Colaborador:", placeholder="Nome...")
        if st.button("➕ Adicionar") and novo:
            if novo not in st.session_state.equipe:
                st.session_state.equipe.append(novo)
                salvar_equipe(st.session_state.equipe)
                st.rerun()
        
        remover = st.selectbox("Remover:", ["Selecione..."] + st.session_state.equipe)
        if st.button("🗑️ Remover") and remover != "Selecione...":
            st.session_state.equipe.remove(remover)
            salvar_equipe(st.session_state.equipe)
            st.rerun()
            
        st.markdown("---")
        # Download
        df = carregar_historico()
        if not df.empty:
            st.download_button("📥 Baixar Relatório CSV", df.to_csv(index=False).encode('utf-8'), "treino.csv", "text/csv")

# ==========================================
# ÁREA PRINCIPAL (O PALCO)
# ==========================================

# 1. DESTAQUE PARA O COLABORADOR
st.write("### 👤 Quem vai treinar agora?")
colaborador = st.selectbox("Selecione o vendedor:", ["Clique para selecionar..."] + st.session_state.equipe, label_visibility="collapsed")

st.markdown("---")

if colaborador != "Clique para selecionar...":
    
    # 2. BOTÃO DE AÇÃO (GERAR)
    if not st.session_state.cenario:
        st.info("👆 Clique abaixo para trazer um cliente fictício até o balcão.")
        if st.button("🔔 CHAMAR PRÓXIMO CLIENTE", type="primary"):
            with st.spinner("Cliente entrando na loja..."):
                try:
                    model = genai.GenerativeModel(MODELO_ATUAL)
                    prompt = f"Crie uma fala curta (1 frase) de um cliente de farmácia com uma queixa que se resolve com: {st.session_state.produtos}. Use linguagem coloquial brasileira natural."
                    res = model.generate_content(prompt)
                    st.session_state.cenario = res.text.replace('"', '')
                    st.session_state.feedback = "" # Limpa anterior
                    st.rerun()
                except Exception as e:
                    st.error("Erro de conexão. Tente novamente.")

    # 3. O CENÁRIO (COM DESTAQUE VISUAL)
    else:
        # Caixa estilizada com HTML/CSS injetado acima
        st.markdown(f"""
        <div class="cliente-box">
            <span style="font-size:14px; color:#555;">🗣️ O CLIENTE DIZ:</span><br>
            <div class="cliente-texto">"{st.session_state.cenario}"</div>
        </div>
        """, unsafe_allow_html=True)

        # 4. RESPOSTA E AVALIAÇÃO
        resposta = st.text_area("✍️ O que o vendedor respondeu?", height=100, placeholder="Digite a resposta ou dite...")

        if st.button("✅ AVALIAR ATENDIMENTO"):
            if not resposta:
                st.warning("Preencha a resposta do vendedor!")
            else:
                with st.spinner("O Treinador está analisando..."):
                    try:
                        model = genai.GenerativeModel(MODELO_ATUAL)
                        prompt_av = f"""
                        Atue como treinador de vendas de farmácia.
                        Situação: "{st.session_state.cenario}"
                        Vendedor disse: "{resposta}"
                        Produtos alvo: {st.session_state.produtos}
                        
                        Avalie (0 a 10) com rigor em: Empatia, Perguntas de Sondagem e Oferta de Benefício.
                        SAÍDA: 
                        Nota: [Numero]
                        [Feedback curto e direto em tópicos]
                        """
                        res = model.generate_content(prompt_av)
                        
                        # Extração de nota
                        txt = res.text
                        match = re.search(r"(\d+[\.,]\d+|\d+)", txt.split('\n')[0])
                        st.session_state.nota = float(match.group(0).replace(',', '.')) if match else 0.0
                        st.session_state.feedback = txt
                        st.rerun() # Recarrega para mostrar o resultado limpo
                    except:
                        st.error("Erro ao avaliar.")

        # 5. RESULTADO (Só aparece se tiver feedback)
        if "feedback" in st.session_state and st.session_state.feedback:
            st.markdown("---")
            
            # Nota grande
            cor_nota = "green" if st.session_state.nota >= 7 else "red"
            st.markdown(f"<h1 style='text-align: center; color: {cor_nota}'>{st.session_state.nota}/10</h1>", unsafe_allow_html=True)
            
            with st.container(border=True):
                st.markdown(st.session_state.feedback)
            
            obs = st.text_input("📝 Obs. do Gerente (Opcional):")
            
            col_save, col_new = st.columns(2)
            with col_save:
                if st.button("💾 SALVAR", type="primary"):
                    salvar_sessao({
                        "Data": datetime.now().strftime("%d/%m %H:%M"),
                        "Colaborador": colaborador,
                        "Cenario": st.session_state.cenario,
                        "Resposta": resposta,
                        "Nota": st.session_state.nota,
                        "FeedbackIA": st.session_state.feedback,
                        "ObsGerente":
