import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime
import re
import random

# --- CONFIGURAÇÃO DA CHAVE DE API (SEGURA) ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    CONEXAO_OK = True
except:
    API_KEY = ""
    CONEXAO_OK = False

# --- Configuração da Página ---
st.set_page_config(
    page_title="Treinador Suprabio",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS ---
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

# --- ARQUIVOS ---
ARQUIVO_HISTORICO = "historico_treinamento.csv"
ARQUIVO_EQUIPE = "equipe.csv"

# --- BANCO DE DADOS DE CASOS REAIS (FARMÁCIA) ---
CASOS_REAIS = [
    # Situações Originais
    {"queixa": "Moça, eu ando muito esquecido, a cabeça parece que não funciona direito e tô sem energia mental.", "produto_alvo": "Magnésio Dimalato ou Complexo B"},
    {"queixa": "Tenho sentido muita dor nas articulações, meu joelho estala quando subo escada. Tem algo pra 'lubrificar'?", "produto_alvo": "Cloreto de Magnésio ou Colágeno"},
    {"queixa": "Eu deito na cama e fico rolando. O corpo cansa, mas a mente não desliga. Queria algo natural pra dormir.", "produto_alvo": "Melatonina ou Clamvit Zen"},
    {"queixa": "Tô sentindo uma fraqueza no coração, me sinto muito cansado depois que fiz 40 anos. O médico falou de uma vitamina pro coração.", "produto_alvo": "Coenzima Q10"},
    {"queixa": "Minha boca tá cheia de afta e eu pego resfriado toda semana. Minha imunidade deve estar no chão.", "produto_alvo": "Vitamina C ou Suprabio A-Z"},
    {"queixa": "O médico mandou eu baixar meu triglicerídeos e colesterol ruim, mas queria algo pra ajudar junto com a dieta.", "produto_alvo": "Ômega 3"},
    {"queixa": "Tô me sentindo fraco, sem disposição pra trabalhar. Sou homem, tenho 35 anos, queria um tônico geral.", "produto_alvo": "Suprabio Homem"},
    {"queixa": "Menina, tô na menopausa, sentindo uns calores e muito desânimo. Tem alguma vitamina completa pra mulher?", "produto_alvo": "Suprabio Mulher"},
    {"queixa": "Já passei dos 50 anos e sinto que meus ossos estão fracos e me falta energia pro dia a dia.", "produto_alvo": "Suprabio 50+"},
    {"queixa": "Olha o estado da minha unha! Tá quebrando igual papel. E meu cabelo cai muito no banho.", "produto_alvo": "Suprabio Cabelos e Unhas"},
    {"queixa": "Meu intestino é um relógio... parado! Fico 3 dias sem ir ao banheiro e me sinto inchada.", "produto_alvo": "Fibras ou Lactulose"},
    {"queixa": "Toda tarde minha visão fica cansada, embaçada, parece que forço muito pra ler.", "produto_alvo": "Luteína"},
    {"queixa": "Fiz um exame e deu osteopenia. O médico mandou tomar cálcio, mas disseram que tem um que vai direto pro osso.", "produto_alvo": "Cálcio MDK"},
    {"queixa": "Tô muito estressado, pavio curto, qualquer coisa eu explodo. Queria algo pra acalmar sem dar sono.", "produto_alvo": "Clamvit Zen"},
    
    # Novas Situações
    {"queixa": "Sinto muitas cãibras na panturrilha de madrugada, acordo gemendo de dor. Tem alguma vitamina pra isso?", "produto_alvo": "Magnésio Dimalato ou Cloreto de Magnésio"},
    {"queixa": "Comecei a tomar estatina pra colesterol e agora sinto muita dor muscular, parece que fui atropelado. O médico falou de um suplemento.", "produto_alvo": "Coenzima Q10"},
    {"queixa": "Sinto um formigamento constante nas mãos e nos pés, além de um cansaço que não passa com nada.", "produto_alvo": "Complexo B"},
    {"queixa": "Tenho hemorroida e sofro demais pra ir ao banheiro porque as fezes ficam muito ressecadas. Preciso amolecer isso urgente.", "produto_alvo": "Lactulose ou Fibras"},
    {"queixa": "Estou sentindo minha pele do rosto e dos braços muito flácida, perdendo a firmeza da juventude.", "produto_alvo": "Colágeno"},
    {"queixa": "Minha memória tá terrível, esqueço onde coloquei a chave, o que ia falar... Queria algo pro cérebro e que fizesse bem pro coração.", "produto_alvo": "Ômega 3"},
    {"queixa": "Trabalho o dia inteiro sentado no computador, chego em casa exausto, sem pique nem pra brincar com meus filhos.", "produto_alvo": "Suprabio Homem"},
    {"queixa": "Eu viajo muito a trabalho e meu fuso horário vira uma bagunça, perco totalmente a hora de dormir.", "produto_alvo": "Melatonina"},
    {"queixa": "Minha mãe tem 68 anos e está comendo muito mal. Quase não come carne e tá ficando muito fraquinha.", "produto_alvo": "Suprabio 50+"},
    {"queixa": "Fico o dia todo olhando pra tela do computador e do celular. No final do dia meu olho arde muito e fica seco.", "produto_alvo": "Luteína"},
    {"queixa": "Tenho uns bicos de papagaio na coluna e acordo com as juntas todas travadas, duro igual um robô.", "produto_alvo": "Cloreto de Magnésio"},
    {"queixa": "Estou numa ansiedade terrível por conta de problemas na família. Meu coração até acelera, mas tenho pavor de tomar tarja preta.", "produto_alvo": "Clamvit Zen"},
    {"queixa": "As mulheres da minha família têm histórico de osteoporose. Eu já passei dos 40 e queria começar a prevenir.", "produto_alvo": "Cálcio MDK"},
    {"queixa": "Meu nariz vive escorrendo. Basta o tempo mudar um pouquinho ou bater um vento gelado que eu já fico resfriada.", "produto_alvo": "Vitamina C"},
    {"queixa": "Faço academia todo dia, me sinto bem, mas queria um suplemento focado em dar energia pra render mais no treino e no trabalho.", "produto_alvo": "Magnésio Dimalato ou Coenzima Q10"}
]

# --- FUNÇÕES ---
def carregar_equipe():
    if os.path.exists(ARQUIVO_EQUIPE):
        try: return pd.read_csv(ARQUIVO_EQUIPE)['Nome'].tolist()
        except: pass
    # Equipe Atualizada
    padrao = ["André", "Bruna", "Eliana", "Leticia", "Marcella", "Jessica", "Diego", "Anderson"]
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

# Função para pegar modelo disponível (Auto-fix)
@st.cache_resource
def encontrar_modelo():
    if not API_KEY: return None
    try:
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if not modelos: return "models/gemini-pro"
        # Prioridade
        for m in modelos:
            if "flash" in m: return m
        return modelos[0]
    except: return None

MODELO_NOME = encontrar_modelo()

# --- ESTADO INICIAL ---
if "equipe" not in st.session_state: st.session_state.equipe = carregar_equipe()
if "cenario" not in st.session_state: st.session_state.cenario = ""
if "produto_alvo" not in st.session_state: st.session_state.produto_alvo = ""
if "nota" not in st.session_state: st.session_state.nota = 0.0

# --- INTERFACE ---
col_titulo, col_config = st.columns([5, 1])
with col_titulo:
    st.title("💊 Treino Real Suprabio")
    if not CONEXAO_OK:
        st.error("⚠️ Configure a API Key nos 'Secrets'!")

with col_config:
    with st.popover("⚙️", use_container_width=True):
        st.header("Ajustes")
        # Se não configurou Secrets, permite digitar aqui
        if not CONEXAO_OK:
            nova_key = st.text_input("Cole API Key aqui:", type="password")
            if nova_key:
                genai.configure(api_key=nova_key)
                st.rerun()
                
        st.info(f"Banco de dados carregado com {len(CASOS_REAIS)} situações reais.")
        
        novo = st.text_input("Add Colaborador:")
        if st.button("➕") and novo:
            st.session_state.equipe.append(novo)
            salvar_equipe(st.session_state.equipe)
            st.rerun()
            
        df = carregar_historico()
        if not df.empty:
            st.download_button("📥 Baixar Histórico", df.to_csv(index=False).encode('utf-8'), "treino.csv", "text/csv")

st.write("### 👤 Quem vai treinar agora?")
colaborador = st.selectbox("Vendedor:", ["Clique..."] + st.session_state.equipe, label_visibility="collapsed")
st.markdown("---")

if colaborador != "Clique...":
    if not st.session_state.cenario:
        # BOTÃO AGORA SORTEIA DO BANCO DE DADOS
        if st.button("🔔 CHAMAR PRÓXIMO CLIENTE", type="primary"):
            caso = random.choice(CASOS_REAIS)
            st.session_state.cenario = caso["queixa"]
            st.session_state.produto_alvo = caso["produto_alvo"]
            st.session_state.feedback = ""
            st.rerun()

    else:
        st.markdown(f"""
        <div class="cliente-box">
            <span style="color:#555;">🗣️ O CLIENTE DIZ:</span><br>
            <div class="cliente-texto">"{st.session_state.cenario}"</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Dica só pro gerente (opcional, pode tirar se quiser)
        with st.expander("👀 Ver Produto Esperado (Só para Gerente)"):
            st.write(f"**Indicação ideal:** {st.session_state.produto_alvo}")

        resposta = st.text_area("✍️ Resposta do Vendedor:", height=100)

        if st.button("✅ AVALIAR"):
            if not resposta:
                st.warning("Escreva a resposta!")
            else:
                if not MODELO_NOME and not CONEXAO_OK:
                    st.error("Configure a chave API para avaliar.")
                else:
                    with st.spinner("O Treinador está analisando..."):
                        try:
                            # Prompt de avaliação rigorosa
                            modelo_uso = MODELO_NOME if MODELO_NOME else "models/gemini-pro"
                            model = genai.GenerativeModel(modelo_uso)
                            
                            prompt = f"""
                            Aja como um gerente técnico de farmácia.
                            
                            DADOS DO ATENDIMENTO:
                            Queixa do Cliente: "{st.session_state.cenario}"
                            Resposta do Vendedor: "{resposta}"
                            Produto que deveria indicar: {st.session_state.produto_alvo}
                            
                            CRITÉRIOS DE AVALIAÇÃO (Seja exigente):
                            1. Fez sondagem? (Perguntou sintomas, a quanto tempo ocorre, etc antes de ofertar?)
                            2. Criou conexão? (Não foi robô?)
                            3. Indicou o produto correto ({st.session_state.produto_alvo}) focando no BENEFÍCIO pro cliente?
                            
                            SAÍDA:
                            Nota: [0 a 10]
                            [Feedback prático e direto]
                            """
                            
                            res = model.generate_content(prompt)
                            st.session_state.feedback = res.text
                            
                            # Tenta extrair a nota
                            match = re.search(r"(\d+[\.,]\d+|\d+)", res.text)
                            st.session_state.nota = float(match.group(0).replace(',', '.')) if match else 0.0
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao avaliar: {e}")

        if st.session_state.feedback:
            st.markdown("---")
            cor = "green" if st.session_state.nota >= 7 else "red"
            st.markdown(f"<h1 style='text-align: center; color: {cor}'>{st.session_state.nota}/10</h1>", unsafe_allow_html=True)
            st.info(st.session_state.feedback)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 SALVAR"):
                    salvar_sessao({"Data": datetime.now().strftime("%d/%m %H:%M"), "Colaborador": colaborador, "Nota": st.session_state.nota, "Cenario": st.session_state.cenario})
                    st.success("Salvo!")
                    st.session_state.cenario = ""
                    st.session_state.feedback = ""
                    st.rerun()
            with col2:
                if st.button("🗑️ DESCARTAR"):
                    st.session_state.cenario = ""
                    st.session_state.feedback = ""
                    st.rerun()
