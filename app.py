import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime
import re

# --- CONFIGURAÇÃO DA CHAVE DE API ---
API_KEY = "AIzaSyD7sS0C6UIITfgkHAd9oJs4YzDHfELV_us"
genai.configure(api_key=API_KEY)

# --- Configuração da Página (Mobile Friendly) ---
st.set_page_config(
    page_title="Treinador Suprabio",
    page_icon="💊",
    layout="centered", # Melhor para celular
    initial_sidebar_state="collapsed" # Esconde a barra lateral para ganhar espaço
)

# --- Arquivos ---
ARQUIVO_HISTORICO = "historico_treinamento.csv"
ARQUIVO_EQUIPE = "equipe.csv"

# --- Funções de Dados ---
def carregar_equipe():
    if os.path.exists(ARQUIVO_EQUIPE):
        return pd.read_csv(ARQUIVO_EQUIPE)['Nome'].tolist()
    else:
        # Lista inicial padrão
        padrao = ["André", "Bruna", "Eliana", "Gabriel", "Leticia", "Marcella", "Layana"]
        salvar_equipe(padrao)
        return padrao

def salvar_equipe(lista_nomes):
    pd.DataFrame({'Nome': lista_nomes}).to_csv(ARQUIVO_EQUIPE, index=False)

def carregar_historico():
    colunas = ["Data", "Colaborador", "Cenario", "Resposta", "Nota", "FeedbackIA", "ObsGerente"]
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            return pd.read_csv(ARQUIVO_HISTORICO)
        except:
            return pd.DataFrame(columns=colunas)
    return pd.DataFrame(columns=colunas)

def salvar_sessao(dados):
    df = carregar_historico()
    novo = pd.DataFrame([dados])
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO_HISTORICO, index=False)

# --- Função de Inteligência (Auto-Adaptável) ---
@st.cache_resource
def get_model():
    # Tenta descobrir qual modelo funciona na conta
    try:
        modelos = genai.list_models()
        for m in modelos:
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: return m.name # Prioridade pro Flash
        return "models/gemini-pro"
    except:
        return "models/gemini-pro"

MODELO_ATUAL = get_model()

# --- CSS para melhorar visual no celular ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        height: 3em;
        font-weight: bold;
        border-radius: 10px;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.1rem;
        font-weight: bold;
    }
    .big-font {
        font-size: 18px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Título e Cabeçalho ---
st.title("💊 Treinador Suprabio")
st.caption(f"Conectado: {MODELO_ATUAL.split('/')[-1]}")

# --- Gerenciamento de Estado ---
if "equipe" not in st.session_state:
    st.session_state.equipe = carregar_equipe()
if "cenario" not in st.session_state: st.session_state.cenario = ""
if "nota" not in st.session_state: st.session_state.nota = 0.0
if "feedback" not in st.session_state: st.session_state.feedback = ""

# --- ÁREA DE CONFIGURAÇÃO (Expander para economizar espaço) ---
with st.expander("⚙️ Configurações & Equipe"):
    # Gestão de Equipe
    st.subheader("Gerenciar Equipe")
    col_add, col_btn = st.columns([3, 1])
    novo_nome = col_add.text_input("Novo nome", label_visibility="collapsed", placeholder="Nome...")
    if col_btn.button("➕"):
        if novo_nome and novo_nome not in st.session_state.equipe:
            st.session_state.equipe.append(novo_nome)
            salvar_equipe(st.session_state.equipe)
            st.rerun()
            
    colab_remove = st.selectbox("Remover alguém?", ["Selecione..."] + st.session_state.equipe)
    if colab_remove != "Selecione..." and st.button(f"🗑️ Remover {colab_remove}"):
        st.session_state.equipe.remove(colab_remove)
        salvar_equipe(st.session_state.equipe)
        st.rerun()

    st.markdown("---")
    produtos = st.text_area("Produtos Foco", "Suprabio A-Z, Cabelos e Unhas, Mulher, Sênior, Cálcio MDK.", height=70)

# --- SELEÇÃO DO VENDEDOR ---
colaborador = st.selectbox("Quem está treinando agora?", ["Selecione..."] + st.session_state.equipe)

# --- ÁREA PRINCIPAL ---
if colaborador != "Selecione...":
    st.markdown("---")
    
    # 1. BOTÃO GERAR CENÁRIO
    if st.button("🔄 CRIAR NOVO CLIENTE", type="primary", use_container_width=True):
        with st.spinner("Gerando cliente..."):
            try:
                model = genai.GenerativeModel(MODELO_ATUAL)
                prompt = f"Crie uma frase curta (apenas a fala) de um cliente de farmácia com uma queixa que se resolve com: {produtos}. Linguagem natural brasileira."
                res = model.generate_content(prompt)
                st.session_state.cenario = res.text.replace('"', '')
                st.session_state.feedback = ""
                st.session_state.nota = 0.0
            except Exception as e:
                st.error(f"Erro: {e}")

    # 2. EXIBIÇÃO DO CENÁRIO
    if st.session_state.cenario:
        st.success(f"🗣️ **Cliente diz:**\n\n\"{st.session_state.cenario}\"")
        
        # 3. RESPOSTA
        resposta = st.text_area("Sua resposta:", height=100, placeholder="Digite aqui o que você falaria...")
        
        # 4. BOTÃO AVALIAR
        if st.button("✅ AVALIAR RESPOSTA", use_container_width=True):
            if not resposta:
                st.warning("Digite algo primeiro!")
            else:
                with st.spinner("Analisando..."):
                    try:
                        model = genai.GenerativeModel(MODELO_ATUAL)
                        prompt_av = f"""
                        Atue como gerente de farmácia.
                        Cenário: "{st.session_state.cenario}"
                        Vendedor disse: "{resposta}"
                        Produtos: {produtos}
                        
                        Avalie (0-10) considerando: Empatia, Sondagem e Benefício.
                        SAÍDA: Comece com "NOTA: X". Depois dê dicas curtas.
                        """
                        res = model.generate_content(prompt_av)
                        
                        # Processar Nota
                        txt = res.text
                        match = re.search(r"(\d+[\.,]\d+|\d+)", txt.split('\n')[0])
                        nota = float(match.group(0).replace(',', '.')) if match else 5.0
                        
                        st.session_state.nota = nota
                        st.session_state.feedback = txt
                    except:
                        st.error("Erro na avaliação. Tente de novo.")

        # 5. FEEDBACK E SALVAR
        if st.session_state.feedback:
            st.markdown("---")
            cor = "green" if st.session_state.nota >= 7 else "red"
            st.markdown(f"### Nota: :{cor}[{st.session_state.nota}]")
            
            with st.container(border=True):
                st.markdown(st.session_state.feedback)
            
            obs = st.text_input("Obs do Gerente (Opcional):")
            
            if st.button("💾 SALVAR TREINAMENTO", use_container_width=True):
                salvar_sessao({
                    "Data": datetime.now().strftime("%d/%m %H:%M"),
                    "Colaborador": colaborador,
                    "Cenario": st.session_state.cenario,
                    "Resposta": resposta,
                    "Nota": st.session_state.nota,
                    "FeedbackIA": st.session_state.feedback,
                    "ObsGerente": obs
                })
                st.success("Salvo!")
                st.session_state.cenario = "" # Limpa para o próximo
                st.rerun()

else:
    st.info("👆 Selecione um nome acima para começar.")

# --- RODAPÉ / DOWNLOAD ---
st.markdown("---")
with st.expander("📂 Histórico & Relatórios"):
    df = carregar_historico()
    if not df.empty:
        st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Planilha", data=csv, file_name="treino_suprabio.csv", mime="text/csv", use_container_width=True)
    else:
        st.write("Sem dados ainda.")
