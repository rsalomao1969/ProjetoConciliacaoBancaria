"""
Sistema de Conciliação Bancária - Versão MELHORADA com IA
Versão Completa + 3 Novas Features de IA:
1. 💡 Explicações Inteligentes (IA explica cada match)
2. 🚨 Detector de Anomalias (IA detecta padrões suspeitos)
3. 💬 Chatbot Assistente (IA responde perguntas)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import time
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

# Importações locais - MÓDULOS ORIGINAIS
from nfe_processor import NFEProcessor
from bank_statement_processor import BankStatementProcessor
from agente_llm_groq import AgenteConcialiadorLLM
from report_generator import ReportGenerator
from validador_arquivos import ValidadorArquivos
from analise_final import (
    gerar_analise_final_llm,
    gerar_dados_graficos,
    criar_grafico_pizza,
    criar_grafico_scores,
    criar_grafico_valores
)

# Importações locais - NOVOS MÓDULOS DE IA
from explicador_ia import criar_explicador
from detector_anomalias import criar_detector
from chatbot_assistente import criar_chatbot

# Verificar se API key está disponível
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
IA_DISPONIVEL = bool(GROQ_API_KEY)

# Configuração da página
st.set_page_config(
    page_title="Conciliação Bancária com IA Avançada",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar contador de reset (para limpar uploads)
if 'reset_counter' not in st.session_state:
    st.session_state['reset_counter'] = 0


# ============================================================================
# STATUS DA IA
# ============================================================================

def mostrar_status_ia():
    """Mostra o status da IA no topo da página"""

    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.title("🦁 Sistema de Conciliação Bancária + IA")

    with col2:
        # Status da IA
        if st.session_state.get('processado', False):
            st.success("🤖 IA: ATIVA ✅", icon="✅")
        else:
            st.info("🤖 IA: AGUARDANDO", icon="⏳")

    with col3:
        st.caption("v2.0 + IA Avançada")


# Mostrar status da IA
mostrar_status_ia()
st.markdown("---")

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.header("⚙️ Configurações")

    # Status da IA (sem pedir API key)
    st.subheader("🤖 Status da IA Generativa")

    if IA_DISPONIVEL:
        st.success("**IA:** ATIVA ✅")
        st.caption("💚 Groq Llama 3.3 70B")
        st.caption("100% GRÁTIS | Muito Rápido!")

        st.info("""
        **3 Agentes de IA Ativos:**

        1. 💡 **Explicador** - Explica matches
        2. 🚨 **Detector** - Encontra anomalias
        3. 💬 **Chatbot** - Responde perguntas

        **Tecnologia:**
        - Groq Llama 3.3 70B
        - Chain of Thought
        - 100% Gratuito
        """)
    else:
        st.error("**IA:** INATIVA ❌")
        st.caption("API Key não encontrada")
        st.info("""
        Para ativar a IA GRÁTIS:
        1. Acesse: https://console.groq.com/keys
        2. Crie conta (grátis!)
        3. Gere API Key
        4. Crie arquivo `.env` na raiz
        5. Adicione: `GROQ_API_KEY=gsk_...`
        6. Reinicie o app
        """)

    st.markdown("---")

    # Status detalhado da IA
    st.subheader("📊 Estatísticas da IA")

    if st.session_state.get('processado', False):
        st.success("**Processamento:** CONCLUÍDO ✅")

        # Mostrar estatísticas
        resultados = st.session_state.get('resultados', {})
        matches = resultados.get('matches_confirmados', [])

        st.metric("Matches Encontrados", len(matches))

        if matches:
            score_medio = sum(m['score'] for m in matches) / len(matches)
            st.metric("Score Médio", f"{score_medio:.1f}%")

        # NOVO: Mostrar anomalias
        if 'anomalias' in resultados:
            anomalias = resultados['anomalias']
            nivel = anomalias['nivel_alerta']
            score_risco = anomalias['score']

            st.markdown("---")
            st.subheader("🚨 Anomalias")

            if nivel == 'CRITICO':
                st.error(f"**Nível:** {nivel} 🔴")
            elif nivel == 'ALTO':
                st.warning(f"**Nível:** {nivel} 🟠")
            elif nivel == 'MEDIO':
                st.info(f"**Nível:** {nivel} 🟡")
            else:
                st.success(f"**Nível:** {nivel} 🟢")

            st.metric("Score de Risco", f"{score_risco}/100")

            total_anomalias = (
                    len(anomalias.get('valores_atipicos', [])) +
                    len(anomalias.get('temporal', [])) +
                    len(anomalias.get('sem_match_suspeito', [])) +
                    len(anomalias.get('duplicatas_potenciais', [])) +
                    len(anomalias.get('inconsistencias', []))
            )

            st.caption(f"{total_anomalias} anomalias detectadas")

        st.caption(f"Última execução: {st.session_state.get('ultima_execucao', 'N/A')}")

    else:
        st.info("**Processamento:** AGUARDANDO")
        st.caption("Faça upload e processe os dados")

    st.markdown("---")

    # Thresholds
    st.subheader("⚙️ Thresholds de Score")

    threshold_confirmado = st.slider(
        "Confirmado (≥)",
        min_value=50,
        max_value=100,
        value=70,
        help="Score mínimo para match confirmado pelo LLM"
    )

    threshold_sugestao = st.slider(
        "Sugestão (≥)",
        min_value=0,
        max_value=threshold_confirmado - 1,
        value=50,
        help="Score mínimo para sugestão"
    )

    st.markdown("---")

    # Informações do sistema
    st.subheader("ℹ️ Sobre o Sistema")

    st.info("""
    **Conciliação com IA Avançada**

    - **IA:** Groq Llama 3.3 70B
    - **Tipo:** IA Generativa Real
    - **Método:** Chain of Thought

    **Recursos:**
    ✅ Raciocínio explícito
    ✅ Análise contextual
    ✅ Matching inteligente
    ✅ Explicações detalhadas
    ✅ Detecção de anomalias
    ✅ Chatbot assistente

    **Custo:** 💚 100% GRÁTIS!
    """)

    # Botão de reset
    if st.button("🔄 Resetar Sistema", use_container_width=True):
        # Incrementar contador para forçar recriação dos uploads
        st.session_state['reset_counter'] += 1

        # Limpar tudo
        for key in list(st.session_state.keys()):
            if key != 'reset_counter':
                del st.session_state[key]
        st.rerun()

# ============================================================================
# UPLOAD DE ARQUIVOS
# ============================================================================

st.header("📁 Upload de Arquivos")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Notas Fiscais (XML)")

    nfe_files = st.file_uploader(
        "Seleção de XMLs",
        type=['xml'],
        accept_multiple_files=True,
        key=f'nfe_upload_{st.session_state["reset_counter"]}',
        help="Segure Ctrl ou Shift para selecionar múltiplos arquivos"
    )

    if nfe_files:
        # Validar arquivos antes de processar
        with st.spinner("🔍 Validando arquivos NFe..."):
            validos, invalidos = ValidadorArquivos.validar_lote_nfes(nfe_files)

        # Armazenar apenas arquivos válidos
        st.session_state['nfe_files_validos'] = [v[0] for v in validos] if validos else []

        # Mostrar resultados da validação
        if validos:
            st.success(f"✅ {len(validos)} arquivo(s) válido(s)")

        if invalidos:
            st.warning(f"⚠️ {len(invalidos)} arquivo(s) inválido(s):")
            with st.expander("❌ Ver arquivos com erro", expanded=True):
                for nome, msg in invalidos:
                    st.error(f"**{nome}**: {msg}")

        # Mostrar lista de arquivos válidos
        if validos:
            with st.expander("📄 Ver arquivos válidos"):
                for i, (file, msg) in enumerate(validos, 1):
                    file_size_kb = file.size / 1024
                    st.text(f"{i}. {file.name} ({file_size_kb:.1f} KB) - {msg}")
    else:
        st.session_state['nfe_files_validos'] = []

with col2:
    st.subheader("💳 Extrato Bancário")

    extrato_file = st.file_uploader(
        "Selecione o arquivo do extrato",
        type=['csv', 'txt', 'ofx'],
        accept_multiple_files=False,
        key=f'extrato_upload_{st.session_state["reset_counter"]}',
        help="Arquivo CSV, TXT ou OFX do extrato bancário"
    )

    if extrato_file:
        # Validar extrato
        with st.spinner("🔍 Validando extrato bancário..."):
            eh_valido, mensagem = ValidadorArquivos.validar_extrato_csv(extrato_file)

        if eh_valido:
            file_size_kb = extrato_file.size / 1024
            st.success(f"✅ {extrato_file.name} ({file_size_kb:.1f} KB) - {mensagem}")
        else:
            st.error(f"❌ {extrato_file.name}: {mensagem}")

st.markdown("---")

# ============================================================================
# PROCESSAMENTO COM LLM + NOVAS FEATURES DE IA
# ============================================================================

col_btn1, col_btn2 = st.columns([3, 1])

with col_btn1:
    processar = st.button(
        "🤖 Processar Conciliação com IA Avançada",
        type="primary",
        use_container_width=True,
        disabled=not (nfe_files and extrato_file and IA_DISPONIVEL)
    )

with col_btn2:
    if st.session_state.get('processado', False):
        if st.button("🔄 Nova Análise", use_container_width=True):
            # Incrementar contador para forçar recriação dos uploads
            st.session_state['reset_counter'] += 1

            # Limpar dados processados
            st.session_state['processado'] = False

            # Limpar arquivos carregados
            if 'nfes' in st.session_state:
                del st.session_state['nfes']
            if 'transacoes' in st.session_state:
                del st.session_state['transacoes']
            if 'resultados' in st.session_state:
                del st.session_state['resultados']
            if 'chatbot' in st.session_state:
                del st.session_state['chatbot']

            st.success("✅ Sistema limpo! Faça novo upload dos arquivos.")
            st.rerun()

# Aviso se não tem IA ativa
if not IA_DISPONIVEL and (nfe_files or extrato_file):
    st.error("""
    ❌ **IA INATIVA**

    Para ativar a IA Generativa:
    1. Crie um arquivo `.env` na raiz do projeto
    2. Adicione a linha: `GROQ_API_KEY=sua-chave-aqui`
    3. Reinicie o aplicativo

    Obtenha sua chave em: https://console.groq.com/keys
    """)

if processar:
    # ====================================================================
    # PROCESSAMENTO COM FEEDBACK VISUAL
    # ====================================================================

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # ============================================================
        # ETAPA 1: Processamento de NFes
        # ============================================================

        status_text.info("📋 **Processando NFes...**")
        progress_bar.progress(10)
        time.sleep(0.3)

        nfe_processor = NFEProcessor()
        nfes = []

        # Usar apenas arquivos válidos
        arquivos_para_processar = st.session_state.get('nfe_files_validos', nfe_files)

        for i, nfe_file in enumerate(arquivos_para_processar):
            try:
                nfes_do_arquivo = nfe_processor.processar_xml(nfe_file)
                nfes.extend(nfes_do_arquivo)

                progresso = 10 + int((i + 1) / len(arquivos_para_processar) * 20)
                progress_bar.progress(progresso)
                status_text.info(f"📋 Processando NFe {i + 1}/{len(arquivos_para_processar)}...")
                time.sleep(0.1)

            except Exception as e:
                st.warning(f"⚠️ Erro ao processar {nfe_file.name}: {str(e)}")

        if not nfes:
            st.error("❌ Nenhuma NFe válida foi processada")
            st.stop()

        progress_bar.progress(30)
        status_text.success(f"✅ {len(nfes)} NFes processadas")
        time.sleep(0.3)

        # ============================================================
        # ETAPA 2: Processamento do Extrato
        # ============================================================

        status_text.info("💳 **Processando extrato bancário...**")
        progress_bar.progress(40)
        time.sleep(0.3)

        bank_processor = BankStatementProcessor()
        transacoes = bank_processor.processar_csv(extrato_file)

        progress_bar.progress(50)
        status_text.success(f"✅ {len(transacoes)} transações processadas")
        time.sleep(0.3)

        # ============================================================
        # ETAPA 3: ATIVAR AGENTE LLM
        # ============================================================

        status_text.info("🤖 **Ativando Agente de IA Generativa...**")
        progress_bar.progress(55)
        time.sleep(0.5)

        try:
            agente = AgenteConcialiadorLLM()  # Lê do .env automaticamente

            # Salvar qual modelo está sendo usado
            st.session_state['modelo_ia'] = agente.model

            status_text.success(f"✅ Agente de IA ativado! Usando: {agente.model}")
        except Exception as e:
            st.error(f"❌ Erro ao ativar IA: {str(e)}")
            st.info("💡 Verifique se o arquivo .env existe com GROQ_API_KEY")
            st.stop()

        progress_bar.progress(60)
        time.sleep(0.3)

        # ============================================================
        # ETAPA 4: Matching com IA (Chain of Thought)
        # ============================================================

        status_text.info("🤖 **IA está analisando e raciocinando...**")
        progress_bar.progress(65)

        # Criar expander para mostrar pensamento
        with st.expander("🧠 Raciocínio da IA em Tempo Real", expanded=True):
            pensamento = st.empty()

            pensamento.markdown("""
            **🤖 Etapa 1:** Analisando contexto geral...
            - Identificando tipo de empresa
            - Detectando padrões de operação
            """)
            progress_bar.progress(70)
            time.sleep(1)

            pensamento.markdown("""
            ✅ Etapa 1 concluída: Contexto analisado

            **🤖 Etapa 2:** Iniciando matching inteligente...
            - Aplicando regra HÍBRIDA de busca (ID Rígido -> Score Heurístico)
            - Aplicando cheque CRÍTICO de integridade de dados (Rótulo vs Sinal)
            """)
            progress_bar.progress(75)
            time.sleep(1)

        # Executar agente LLM
        try:
            resultados = agente.fazer_conciliacao(nfes, transacoes)
        except Exception as e:
            st.error(f"❌ Erro na IA: {str(e)}")
            st.exception(e)
            st.stop()

        progress_bar.progress(78)
        status_text.info("🤖 Matching concluído!")
        time.sleep(0.3)

        # ============================================================
        # ETAPA 5: NOVA FEATURE - EXPLICAÇÕES INTELIGENTES COM IA
        # ============================================================

        if resultados.get('matches_confirmados'):
            status_text.info("💡 **Gerando explicações inteligentes com IA...**")
            progress_bar.progress(80)
            time.sleep(0.3)

            try:
                explicador = criar_explicador()
                matches_explicados = explicador.explicar_lote(resultados['matches_confirmados'])
                resultados['matches_confirmados'] = matches_explicados

                progress_bar.progress(83)
                status_text.success("✅ Explicações inteligentes geradas!")
                time.sleep(0.3)
            except Exception as e:
                st.warning(f"⚠️ Explicações indisponíveis: {str(e)}")
                progress_bar.progress(83)

        # ============================================================
        # ETAPA 6: NOVA FEATURE - DETECÇÃO DE ANOMALIAS COM IA
        # ============================================================

        status_text.info("🚨 **Detectando anomalias com IA...**")
        progress_bar.progress(85)
        time.sleep(0.3)

        try:
            detector = criar_detector()
            # CHAMADA CORRIGIDA: Passando a lista de NFes sem match detalhada para o detector
            anomalias = detector.detectar_anomalias_gerais(
                nfes,
                transacoes,
                resultados['matches_confirmados'],
                nfes_sem_match_llm=resultados['sem_match']
            )
            resultados['anomalias'] = anomalias

            progress_bar.progress(88)
            nivel = anomalias['nivel_alerta']

            if nivel == 'CRITICO' or nivel == 'ALTO':
                status_text.warning(f"⚠️ Anomalias detectadas! Nível: {nivel}")
            else:
                status_text.success(f"✅ Anomalias detectadas! Nível: {nivel}")

            time.sleep(0.5)
        except Exception as e:
            st.warning(f"⚠️ Detecção de anomalias indisponível: {str(e)}")
            resultados['anomalias'] = None
            progress_bar.progress(88)

        progress_bar.progress(90)
        status_text.info("🤖 Finalizando análise...")
        time.sleep(0.3)

        # ============================================================
        # ETAPA 7: Salvar resultados
        # ============================================================

        # IMPORTANTE: Salvar TODOS os dados no session_state
        st.session_state['resultados'] = resultados
        st.session_state['nfes'] = nfes
        st.session_state['transacoes'] = transacoes
        st.session_state['processado'] = True
        st.session_state['ultima_execucao'] = datetime.now().strftime('%H:%M:%S')

        # Debug: verificar o que foi salvo
        print("\n=== DEBUG: Dados salvos no session_state ===")
        print(f"Matches confirmados: {len(resultados.get('matches_confirmados', []))}")
        print(f"Sugestões: {len(resultados.get('sugestoes', []))}")
        print(f"Sem match: {len(resultados.get('sem_match', []))}")
        print(f"NFes: {len(nfes)}")
        print(f"Transações: {len(transacoes)}")
        print("=" * 40)

        progress_bar.progress(100)
        status_text.success("✅ **IA concluiu a análise completa!**")
        time.sleep(0.5)

        # Mostrar resumo
        matches = resultados.get('matches_confirmados', [])
        sem_match = resultados.get('sem_match', [])
        anomalias = resultados.get('anomalias')

        st.balloons()

        # Card de sucesso
        modelo_usado = st.session_state.get('modelo_ia', 'Groq Llama 3.3 70B')

        resumo_msg = f"""
        ### 🎉 Conciliação com IA Avançada Concluída!

        **Resultados:**
        - ✅ {len(matches)} matches confirmados (≥{threshold_confirmado}%)
        - 🤔 {len(resultados.get('sugestoes', []))} sugestões ({threshold_sugestao}-{threshold_confirmado - 1}%)
        - ❌ {len(sem_match)} sem match
        - 📊 Taxa de conciliação: {(len(matches) / len(nfes) * 100):.1f}%

        **🤖 IA:** {modelo_usado} ✅

        **🆕 Novas Features:**
        - 💡 {len(matches)} explicações inteligentes geradas
        """

        if anomalias:
            nivel_icon = {'CRITICO': '🔴', 'ALTO': '🟠', 'MEDIO': '🟡', 'BAIXO': '🟢'}
            icon = nivel_icon.get(anomalias['nivel_alerta'], '⚪')
            resumo_msg += f"- 🚨 Anomalias: {anomalias['nivel_alerta']} {icon} (Score: {anomalias['score']}/100)\n"

        resumo_msg += """
        - 💬 Chatbot assistente disponível

        A IA usou raciocínio **Chain of Thought** + **Análise de Anomalias** + **Explicações Detalhadas**!
        """

        st.success(resumo_msg)

        # Limpar progresso
        time.sleep(2)
        progress_bar.empty()
        status_text.empty()

        st.rerun()

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Erro durante processamento: {str(e)}")
        st.exception(e)

# ============================================================================
# EXIBIÇÃO DE RESULTADOS
# ============================================================================

if st.session_state.get('processado', False):

    st.markdown("---")
    st.header("📊 Resultados da Conciliação")

    # Recuperar dados do session_state
    resultados = st.session_state.get('resultados', {})
    nfes = st.session_state.get('nfes', [])
    transacoes = st.session_state.get('transacoes', [])

    # DEBUG: Verificar se dados existem
    if not resultados:
        st.error("❌ Erro: Resultados não encontrados no session_state!")
        st.stop()

    if not nfes:
        st.error("❌ Erro: NFes não encontradas no session_state!")
        st.stop()

    if not transacoes:
        st.error("❌ Erro: Transações não encontradas no session_state!")
        st.stop()

    matches_confirmados = resultados.get('matches_confirmados', [])
    sugestoes = resultados.get('sugestoes', [])
    sem_match = resultados.get('sem_match', [])

    # DEBUG: Mostrar contagem
    print(f"\n=== DEBUG: Carregando resultados ===")
    print(f"Matches: {len(matches_confirmados)}")
    print(f"Sugestões: {len(sugestoes)}")
    print(f"Sem match: {len(sem_match)}")
    print(f"NFes: {len(nfes)}")
    print(f"Transações: {len(transacoes)}")
    print("=" * 40)

    # ========================================================================
    # MÉTRICAS PRINCIPAIS
    # ========================================================================

    st.subheader("📈 Estatísticas Gerais")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📋 NFes", len(nfes))

    with col2:
        st.metric("💳 Transações", len(transacoes))

    with col3:
        taxa = (len(matches_confirmados) / len(nfes) * 100) if nfes else 0
        st.metric("🎯 Taxa", f"{taxa:.1f}%")

    with col4:
        st.metric("✅ Confirmados", len(matches_confirmados))

    with col5:
        st.metric("🤔 Sugestões", len(sugestoes))

    st.markdown("---")

    # ========================================================================
    # ABAS DE RESULTADOS (ATUALIZADAS COM 2 NOVAS ABAS)
    # ========================================================================

    # DEFINIÇÃO DAS VARIÁVEIS TAB1, TAB2, ..., TAB7
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🧠 Raciocínio do LLM",
        "📄 Relatório",
        "✅ Matches",
        "⚠️ Não Conciliadas",
        "📊 Análise",
        "💡 Explicações IA",  # NOVA!
        "💬 Chatbot"  # NOVA!
    ])

    # IMPORTANTE: O USO DE CADA VARIÁVEL DEVE VIR DEPOIS DESTA DEFINIÇÃO

    # TAB 1: RACIOCÍNIO DA IA
    with tab1:
        st.subheader("🧠 Raciocínio e Explicações da IA")

        st.info("""
        **A IA (Groq Llama 3.3 70B) analisou cada match usando Chain of Thought:**
        - Raciocínio passo a passo
        - Análise de compatibilidade
        - Explicação transparente
        """)

        if matches_confirmados:
            st.success(f"**{len(matches_confirmados)} Matches com Raciocínio Explicado**")

            for i, match in enumerate(matches_confirmados):
                with st.expander(
                        f"🤖 Match #{i + 1}: NFe {match['nfe']['numero']} → {match['transacao']['id']} (Score: {match['score']}%)",
                        expanded=(i == 0)  # Primeiro expandido
                ):
                    # Dados
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**📋 NFe:**")
                        nfe = match['nfe']
                        st.write(f"• Número: {nfe.get('numero')}")
                        st.write(f"• Valor: R$ {nfe.get('valor_total', 0):.2f}")
                        st.write(f"• Data: {nfe.get('data_emissao')}")
                        st.write(f"• Tipo: {nfe.get('tipo_operacao')}")
                        st.write(f"• Emitente: {nfe.get('nome_emitente', 'N/A')[:40]}")

                    with col2:
                        st.markdown("**💳 Transação:**")
                        trans = match['transacao']
                        st.write(f"• ID: {trans.get('id')}")
                        st.write(f"• Valor: R$ {trans.get('valor', 0):.2f}")
                        st.write(f"• Data: {trans.get('data')}")
                        st.write(f"• Tipo: {trans.get('tipo')}")
                        st.write(f"• Rótulo Extrato Bruto: {trans.get('rotulo_extrato_original', 'N/A')}")
                        st.write(f"• Descrição: {trans.get('descricao', 'N/A')[:40]}")

                    # Raciocínio da IA
                    st.markdown("---")
                    st.markdown("### 🤖 Raciocínio da IA (Chain of Thought):")

                    if 'raciocinio_llm' in match:
                        # Formatar o raciocínio
                        raciocinio = match['raciocinio_llm']
                        st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 4px solid #1f77b4;">
                        {raciocinio}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("Raciocínio não disponível")

                    # Detalhes da análise
                    if 'detalhes' in match:
                        st.markdown("---")
                        st.markdown("### 📊 Análise Detalhada da IA:")

                        detalhes = match['detalhes']

                        col1, col2 = st.columns(2)

                        with col1:
                            compatibilidade_valor = detalhes.get('compatibilidade_valor', 'N/A')
                            compatibilidade_data = detalhes.get('compatibilidade_data', 'N/A')

                            st.write(f"**Compatibilidade de Valor:** {compatibilidade_valor}")
                            st.write(f"**Compatibilidade de Data:** {compatibilidade_data}")

                        with col2:
                            compatibilidade_tipo = detalhes.get('compatibilidade_tipo', 'N/A')
                            compatibilidade_texto = detalhes.get('compatibilidade_texto', 'N/A')

                            st.write(f"**Compatibilidade de Tipo:** {compatibilidade_tipo}")
                            st.write(f"**Compatibilidade de Texto:** {compatibilidade_texto}")

        else:
            st.warning("Nenhum match confirmado para mostrar raciocínio")

        # Sugestões com raciocínio
        if sugestoes:
            st.markdown("---")
            st.info(f"**{len(sugestoes)} Sugestões (Score {threshold_sugestao}-{threshold_confirmado - 1}%)**")

            for i, match in enumerate(sugestoes):
                with st.expander(f"🤔 Sugestão #{i + 1}: NFe {match['nfe']['numero']} → Score {match['score']}%"):
                    if 'raciocinio_llm' in match:
                        st.markdown(f"**🤖 Raciocínio da IA:** {match['raciocinio_llm']}")

    # TAB 2: RELATÓRIO
    with tab2:
        st.subheader("📄 Relatório Completo")

        report_gen = ReportGenerator()
        relatorio = report_gen.gerar_relatorio_completo(
            matches_confirmados=matches_confirmados,
            sugestoes=sugestoes,
            sem_match=sem_match,
            nfes=nfes,
            transacoes=transacoes
        )

        st.text_area(
            "Relatório de Conciliação",
            value=relatorio,
            height=600,
            disabled=True
        )

        st.download_button(
            label="📥 Baixar Relatório TXT",
            data=relatorio,
            file_name=f"relatorio_conciliacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )

    # TAB 3: MATCHES
    with tab3:
        st.subheader("✅ Matches Confirmados")

        if matches_confirmados:
            st.success(f"**{len(matches_confirmados)} Matches** (Score ≥ {threshold_confirmado}%)")

            data = []
            for i, match in enumerate(matches_confirmados):
                nfe = match['nfe']
                trans = match['transacao']

                data.append({
                    '#': i + 1,
                    'Score': f"{match['score']:.1f}%",
                    'NFe': nfe.get('numero', 'N/A'),
                    'Valor NFe': f"R$ {nfe.get('valor_total', 0):.2f}",
                    'Trans': trans.get('id', 'N/A'),
                    'Valor Trans': f"R$ {trans.get('valor', 0):.2f}",
                    'Descrição': trans.get('descricao', 'N/A')[:40]
                })

            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhum match encontrado.")

        if sugestoes:
            st.markdown("---")
            st.info(f"**{len(sugestoes)} Sugestões**")

            data_sug = []
            for i, match in enumerate(sugestoes):
                data_sug.append({
                    '#': i + 1,
                    'Score': f"{match['score']:.1f}%",
                    'NFe': match['nfe'].get('numero', 'N/A'),
                    'Trans': match['transacao'].get('id', 'N/A')
                })

            df_sug = pd.DataFrame(data_sug)
            st.dataframe(df_sug, use_container_width=True, hide_index=True)

    # TAB 4: NÃO CONCILIADAS
    with tab4:
        st.subheader("⚠️ Não Conciliados")

        if sem_match:
            st.warning(f"**{len(sem_match)} NFe(s) sem match**")

            data_sem = []
            for i, item in enumerate(sem_match):
                nfe = item['nfe']
                data_sem.append({
                    '#': i + 1,
                    'NFe': nfe.get('numero', 'N/A'),
                    'Valor': f"R$ {nfe.get('valor_total', 0):.2f}",
                    'Motivo': item.get('motivo', 'N/A')
                })

            st.dataframe(pd.DataFrame(data_sem), use_container_width=True, hide_index=True)

            # Mostrar raciocínio da IA para não matches
            with st.expander("🤖 Ver raciocínio da IA para itens sem match"):
                for item in sem_match:
                    if 'raciocinio' in item:
                        st.markdown(f"**NFe {item['nfe']['numero']}:** {item['raciocinio']}")
        else:
            st.success("✅ Todas as NFes conciliadas!")

        st.markdown("---")

        # Transações não conciliadas
        trans_usadas = set()
        for match in matches_confirmados + sugestoes:
            trans_usadas.add(match['transacao']['id'])

        trans_nao_conc = [t for t in transacoes if t['id'] not in trans_usadas]

        if trans_nao_conc:
            st.warning(f"**{len(trans_nao_conc)} Transação(ões) sem NFe**")

            data_trans = []
            for i, t in enumerate(trans_nao_conc):
                data_trans.append({
                    '#': i + 1,
                    'ID': t.get('id', 'N/A'),
                    'Valor': f"R$ {t.get('valor', 0):.2f}",
                    'Descrição': t.get('descricao', 'N/A')[:50]
                })

            st.dataframe(pd.DataFrame(data_trans), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Todas as transações conciliadas!")

    # TAB 5: ANÁLISE
    with tab5:
        st.subheader("📊 Análise")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📈 Scores")

            if matches_confirmados:
                scores = [m['score'] for m in matches_confirmados]
                st.metric("Score Médio", f"{sum(scores) / len(scores):.1f}%")
                st.metric("Score Máximo", f"{max(scores):.1f}%")
                st.metric("Score Mínimo", f"{min(scores):.1f}%")

        with col2:
            st.markdown("### 💰 Valores")

            # Calcular corretamente
            valor_nfes = sum(n.get('valor_total', 0) for n in nfes)

            valor_conciliado = 0
            for match in matches_confirmados:
                nfe = match.get('nfe', {})
                valor = nfe.get('valor_total', 0)
                valor_conciliado += valor

            st.metric("Total NFes", f"R$ {valor_nfes:,.2f}")
            st.metric("Total Conciliado", f"R$ {valor_conciliado:,.2f}")

            if valor_nfes > 0:
                pct = (valor_conciliado / valor_nfes * 100)
                st.metric("% Conciliado", f"{pct:.1f}%")

            valor_nao_conc = valor_nfes - valor_conciliado
            if valor_nao_conc > 0:
                st.metric("Não Conciliado", f"R$ {valor_nao_conc:,.2f}")

        # ========================================================================
        # NOVA SEÇÃO: ANÁLISE DE ANOMALIAS DETALHADA
        # ========================================================================

        st.markdown("---")
        st.markdown("### 🚨 Análise de Anomalias")

        if st.session_state.get('resultados', {}).get('anomalias'):
            anomalias = st.session_state['resultados']['anomalias']

            # Card de status
            nivel = anomalias['nivel_alerta']
            score = anomalias['score']

            col1, col2, col3 = st.columns(3)

            with col1:
                if nivel == 'CRITICO':
                    st.error(f"### 🔴 {nivel}")
                elif nivel == 'ALTO':
                    st.warning(f"### 🟠 {nivel}")
                elif nivel == 'MEDIO':
                    st.info(f"### 🟡 {nivel}")
                else:
                    st.success(f"### 🟢 {nivel}")

            with col2:
                st.metric("Score de Risco", f"{score}/100")

            with col3:
                total_anomalias = (
                        len(anomalias.get('valores_atipicos', [])) +
                        len(anomalias.get('temporal', [])) +
                        len(anomalias.get('sem_match_suspeito', [])) +
                        len(anomalias.get('duplicatas_potenciais', [])) +
                        len(anomalias.get('inconsistencias', []))
                )
                st.metric("Total Anomalias", total_anomalias)

            # Detalhamento
            st.markdown("#### 📊 Detalhamento das Anomalias")

            col1, col2 = st.columns(2)

            # --- CORREÇÃO DE VISUALIZAÇÃO AQUI ---
            anomalias = st.session_state['resultados']['anomalias']

            with col1:
                # 1. Valores atípicos
                num_atipicos = len(anomalias['valores_atipicos'])
                with st.expander(f"📊 Valores Atípicos ({num_atipicos})"):
                    if num_atipicos > 0:
                        for anom in anomalias['valores_atipicos']:
                            st.warning(f"**{anom['tipo']}:** {anom['descricao']}")
                    else:
                        st.success("Nenhum valor atípico detectado.")

                # 2. Problemas temporais
                num_temporal = len(anomalias['temporal'])
                with st.expander(f"📅 Problemas Temporais ({num_temporal})"):
                    if num_temporal > 0:
                        for anom in anomalias['temporal']:
                            st.warning(f"**{anom['tipo']}:** {anom['descricao']}")
                    else:
                        st.success("Nenhuma anomalia temporal detectada.")

                # 3. Duplicatas
                num_duplicatas = len(anomalias['duplicatas_potenciais'])
                with st.expander(f"🔄 Duplicatas ({num_duplicatas})"):
                    if num_duplicatas > 0:
                        for anom in anomalias['duplicatas_potenciais']:
                            st.error(f"**{anom['tipo']}:** {anom['descricao']}")
                    else:
                        st.success("Nenhuma duplicata potencial detectada.")

            with col2:
                # 4. NFes suspeitas (Inclui as NFes rejeitadas por tipo incompatível)
                num_suspeitas = len(anomalias['sem_match_suspeito'])
                with st.expander(f"⚠️ NFes Suspeitas ({num_suspeitas})"):
                    if num_suspeitas > 0:
                        for anom in anomalias['sem_match_suspeito']:
                            # Usamos um estilo de alerta mais forte para NFE_REJEITADA_TIPO_ERRADO
                            if anom['tipo'] == 'NFE_REJEITADA_TIPO_ERRADO':
                                st.error(f"**{anom['tipo']}:** {anom['descricao']}")
                            else:
                                st.warning(f"**{anom['tipo']}:** {anom['descricao']}")
                    else:
                        st.success("Nenhuma NFe suspeita detectada.")

                # 5. Inconsistências
                num_inconsistencias = len(anomalias['inconsistencias'])
                # Mantido expandido=True para destacar esta seção
                with st.expander(f"🔍 Inconsistências ({num_inconsistencias})", expanded=True):
                    if num_inconsistencias > 0:
                        for anom in anomalias['inconsistencias']:
                            st.warning(f"**{anom['tipo']}:** {anom['descricao']}")
                    else:
                        st.success("Nenhuma inconsistência detectada.")
            # --- FIM DA CORREÇÃO DE VISUALIZAÇÃO ---

            # Análise da IA
            if anomalias.get('analise_ia'):
                st.markdown("---")
                st.markdown("#### 🤖 Análise Inteligente")

                ia = anomalias['analise_ia']

                st.info(f"**Gravidade:** {ia.get('gravidade', 'N/A')}")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**⚠️ Principais Riscos:**")
                    for risco in ia.get('principais_riscos', []):
                        st.write(f"• {risco}")

                with col2:
                    st.markdown("**🎯 Ações Imediatas:**")
                    for acao in ia.get('acoes_imediatas', []):
                        st.write(f"• {acao}")

                st.markdown("**💡 Recomendações:**")
                for rec in ia.get('recomendacoes', []):
                    st.success(f"• {rec}")

        else:
            st.info("Detecção de anomalias não executada")

        # Análise com LLM
        st.markdown("---")
        st.markdown("### 🤖 Análise Inteligente com IA")

        if IA_DISPONIVEL:
            with st.spinner("🤖 IA analisando resultados..."):
                try:
                    analise = gerar_analise_final_llm(st.session_state['resultados'])

                    st.info(f"**📊 Diagnóstico:** {analise.get('diagnostico', 'N/A')}")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**💡 Insights:**")
                        for insight in analise.get('insights', []):
                            st.write(f"• {insight}")

                    with col2:
                        st.markdown("**🎯 Recomendações:**")
                        for rec in analise.get('recomendacoes', []):
                            st.write(f"• {rec}")

                except Exception as e:
                    st.warning(f"Análise automática indisponível: {str(e)}")
        else:
            st.warning("⚠️ Configure API Groq para análise automática")

        # Gráficos Visuais
        st.markdown("---")
        st.markdown("### 📊 Visualizações")

        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de pizza
            fig_pizza = criar_grafico_pizza(st.session_state['resultados'])
            st.plotly_chart(fig_pizza, use_container_width=True)

        with col2:
            # Gráfico de valores
            fig_valores = criar_grafico_valores(st.session_state['resultados'], nfes)
            st.plotly_chart(fig_valores, use_container_width=True)

        # Gráfico de scores (largura total)
        if matches_confirmados:
            st.markdown("### 📈 Scores de Confiança")
            fig_scores = criar_grafico_scores(st.session_state['resultados'])
            st.plotly_chart(fig_scores, use_container_width=True)

    # ========================================================================
    # TAB 6: NOVA - EXPLICAÇÕES INTELIGENTES COM IA
    # ========================================================================

    with tab6:
        st.subheader("💡 Explicações Inteligentes da IA")

        st.info("""
        **A IA analisa cada match e explica POR QUÊ ela achou que é um match!**

        Veja:
        - 🎯 Por que é um match
        - ✅ Pontos fortes
        - ⚠️ Pontos de atenção
        - 💡 Recomendações
        - 📊 Nível de confiança
        """)

        if matches_confirmados:
            for i, match in enumerate(matches_confirmados, 1):
                if 'explicacao_ia' not in match:
                    continue

                exp = match['explicacao_ia']
                nfe = match['nfe']

                # Card da explicação
                with st.expander(
                        f"💡 #{i} - {exp.get('titulo', 'Match')} | Score: {exp.get('score', 0):.0f}%",
                        expanded=(i == 1)
                ):
                    # Resumo
                    st.markdown(f"**📝 Resumo:** {exp.get('resumo', 'N/A')}")

                    # Porque match
                    st.markdown("---")
                    st.markdown("### 🎯 Por que é um Match?")
                    st.write(exp.get('porque_match', 'N/A'))

                    # Pontos fortes e atenção
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("### ✅ Pontos Fortes")
                        for ponto in exp.get('pontos_fortes', []):
                            st.success(f"• {ponto}")

                    with col2:
                        st.markdown("### ⚠️ Pontos de Atenção")
                        pontos_atencao = exp.get('pontos_atencao', [])
                        if pontos_atencao:
                            for ponto in pontos_atencao:
                                st.warning(f"• {ponto}")
                        else:
                            st.success("• Nenhum ponto de atenção!")

                    # Métricas
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Confiança", exp.get('confianca', 'N/A'))

                    with col2:
                        st.metric("Diferença", f"R$ {exp.get('diff_valor', 0):.2f}")

                    with col3:
                        st.metric("Diferença %", f"{exp.get('diff_valor_pct', 0):.1f}%")

                    # Recomendação
                    st.markdown("---")
                    st.markdown("### 💡 Recomendação")
                    st.info(exp.get('recomendacao', 'N/A'))

        else:
            st.warning("Nenhum match com explicação disponível")

    # ========================================================================
    # TAB 7: NOVA - CHATBOT ASSISTENTE
    # ========================================================================

    with tab7:
        st.subheader("💬 Assistente Virtual - Converse sobre seus Resultados")

        st.info("""
        🤖 **Faça perguntas sobre a conciliação em linguagem natural!**

        Exemplos:
        - "Qual a taxa de conciliação?"
        - "Por que a NFe 12345 não teve match?"
        - "Quais são os principais problemas?"
        - "O que devo fazer agora?"
        - "Há alguma anomalia grave?"
        """)

        # Inicializar chatbot
        if 'chatbot' not in st.session_state:
            try:
                chatbot_instance = criar_chatbot()
                # Passando listas completas e anomalias para carregar contexto
                chatbot_instance.carregar_contexto(
                    nfes=nfes,
                    transacoes=transacoes,
                    resultados=resultados,
                    anomalias=resultados.get('anomalias')
                )
                st.session_state['chatbot'] = chatbot_instance
            except Exception as e:
                st.error(f"❌ Erro ao inicializar chatbot: {str(e)}")
                st.stop()

        # Obter instância do chatbot
        chatbot_instance = st.session_state['chatbot']

        # Tentar obter o número da primeira NFe para sugestão
        primeira_nfe_num = None
        if matches_confirmados:
            primeira_nfe_num = matches_confirmados[0]['nfe'].get('numero')

        # Sugestões de perguntas
        st.markdown("### 💡 Perguntas Sugeridas:")

        # Variável de estado para forçar a execução automática
        if 'executar_chatbot_automaticamente' not in st.session_state:
            st.session_state['executar_chatbot_automaticamente'] = False

        sugestoes_perguntas = chatbot_instance.sugerir_perguntas(primeira_nfe_num)

        cols = st.columns(3)
        for i, sugestao in enumerate(sugestoes_perguntas[:6]):
            col = cols[i % 3]
            with col:
                # CORREÇÃO: Ao clicar, definimos a pergunta e acionamos o gatilho.
                if st.button(sugestao, key=f"sug_{i}", use_container_width=True):
                    st.session_state['pergunta_chatbot'] = sugestao
                    st.session_state['executar_chatbot_automaticamente'] = True
                    st.rerun()  # FORÇA O RELOAD PARA EXECUTAR A LÓGICA ABAIXO

        st.markdown("---")

        # Input de pergunta
        pergunta = st.text_input(
            "🗣️ Faça sua pergunta:",
            value=st.session_state.get('pergunta_chatbot', ''),
            placeholder="Digite sua pergunta aqui...",
            key="input_chatbot"
        )

        col1, col2 = st.columns([4, 1])

        # Verifica se o botão "Perguntar" foi pressionado
        perguntar_btn = False
        with col1:
            perguntar_btn = st.button("🤖 Perguntar", type="primary", use_container_width=True)

        with col2:
            if st.button("🗑️ Limpar", use_container_width=True):
                chatbot_instance.limpar_historico()
                st.session_state['pergunta_chatbot'] = ''
                st.session_state['executar_chatbot_automaticamente'] = False
                st.rerun()

        # LÓGICA DE PROCESSAMENTO CENTRALIZADA

        # Condição de execução: Ou o botão manual foi clicado, OU o gatilho automático foi acionado
        executar_pergunta = perguntar_btn or (st.session_state['executar_chatbot_automaticamente'] and pergunta)

        if executar_pergunta and pergunta:

            # Limpa o gatilho automático IMEDIATAMENTE após ser acionado
            st.session_state['executar_chatbot_automaticamente'] = False

            with st.spinner("🤖 Pensando..."):
                try:
                    resposta = chatbot_instance.perguntar(pergunta)

                    # Exibir resposta
                    st.markdown("---")
                    st.markdown("### 🤖 Resposta:")

                    if resposta['tipo'] == 'erro':
                        st.error(resposta['resposta'])
                    else:
                        st.success(resposta['resposta'])

                    # Limpar input após a execução manual, mas mantê-lo se for automático (para visualização)
                    if perguntar_btn:
                        st.session_state['pergunta_chatbot'] = ''
                        st.rerun()  # Força o rerun para limpar o input

                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")

        # Histórico
        if chatbot_instance.historico:
            st.markdown("---")
            st.markdown("### 📜 Histórico da Conversa")

            with st.expander("Ver histórico completo", expanded=False):
                for item in st.session_state['chatbot'].historico:
                    if item['tipo'] == 'pergunta':
                        st.markdown(f"**👤 Você:** {item['texto']}")
                    else:
                        st.markdown(f"**🤖 Assistente:** {item['texto'][:200]}...")
                    st.markdown("---")

else:
    st.info("""
    ### 👋 Sistema de Conciliação com IA Avançada!

    **🆕 Novas Features de IA Integradas:**

    **1. 💡 Explicações Inteligentes**
    - A IA explica POR QUÊ cada match foi identificado
    - Pontos fortes e de atenção
    - Nível de confiança detalhado

    **2. 🚨 Detector de Anomalias**
    - Detecta valores atípicos automaticamente
    - Identifica padrões suspeitos
    - Score de risco em tempo real
    - Análise inteligente de problemas

    **3. 💬 Chatbot Assistente**
    - Converse em linguagem natural
    - Faça perguntas sobre os resultados
    - Receba recomendações personalizadas
    - Histórico de conversas

    **Como usar:**

    1. **🤖 Verificar IA** no menu lateral
       - Se ATIVA ✅: pronto para usar!
       - Se INATIVA ❌: configure o arquivo .env

    2. **📋 Upload de NFes**
       - Selecione múltiplos XMLs (Ctrl/Shift+Click)

    3. **💳 Upload de Extrato**
       - Selecione o arquivo CSV

    4. **🤖 Processar com IA Avançada**
       - Veja 3 agentes de IA trabalhando
       - Matching + Explicações + Anomalias
       - Converse com o chatbot depois!

    **Diferencial:**
    - 🧠 3 agentes de IA especializados
    - 📊 Detecção automática de problemas
    - 💬 Interface conversacional
    - ✅ 100% Gratuito com Groq
    """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.caption("Sistema de Conciliação v2.0 + IA Avançada")

with col2:
    status = "🤖 ATIVA" if IA_DISPONIVEL else "⏳ INATIVA"
    st.caption(f"IA Generativa: {status}")

with col3:
    st.caption("Powered by Groq Llama 3.3 | 3 Agentes de IA")