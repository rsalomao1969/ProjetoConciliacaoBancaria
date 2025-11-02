"""
Chatbot Assistente Inteligente
Permite conversar sobre os resultados da conciliação em linguagem natural
"""

import os
from typing import Dict, List
from groq import Groq
import json


class ChatbotAssistente:
    """
    Chatbot que responde perguntas sobre a conciliação
    usando contexto dos dados processados
    """

    def __init__(self, api_key: str = None):
        """Inicializa chatbot com Groq"""
        self.api_key = api_key or os.getenv('GROQ_API_KEY')

        if not self.api_key:
            raise ValueError("❌ API key do Groq não encontrada!")

        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"

        # Contexto da conversa
        self.contexto = None
        self.historico = []

        print("✅ Chatbot Assistente inicializado!")

    def carregar_contexto(
            self,
            nfes: List[Dict],
            transacoes: List[Dict],
            resultados: Dict,
            anomalias: Dict = None
    ):
        """
        Carrega contexto da conciliação para o chatbot

        Args:
            nfes: Lista de NFes
            transacoes: Lista de transações
            resultados: Resultados da conciliação
            anomalias: Anomalias detectadas (opcional)
        """

        matches = resultados.get('matches_confirmados', [])
        sugestoes = resultados.get('sugestoes', [])
        sem_match = resultados.get('sem_match', [])

        # Calcular estatísticas
        total_nfes = len(nfes)
        total_trans = len(transacoes)
        valor_total_nfes = sum(n.get('valor_total', 0) for n in nfes)
        valor_conciliado = sum(m['nfe'].get('valor_total', 0) for m in matches)

        taxa_conciliacao = (len(matches) / total_nfes * 100) if total_nfes > 0 else 0

        self.contexto = {
            'total_nfes': total_nfes,
            'total_transacoes': total_trans,

            # Contagens (inteiros)
            'matches_confirmados_count': len(matches),  # ALTERADO
            'sugestoes_count': len(sugestoes),  # ALTERADO
            'sem_match_count': len(sem_match),  # ALTERADO

            'taxa_conciliacao': taxa_conciliacao,
            'valor_total_nfes': valor_total_nfes,
            'valor_conciliado': valor_conciliado,
            'valor_pendente': valor_total_nfes - valor_conciliado,

            # Dados detalhados (Listas)
            'nfes_list': nfes,  # ALTERADO
            'transacoes_list': transacoes,  # ALTERADO
            'matches_list': matches,  # ALTERADO
            'sugestoes_list': sugestoes,  # ALTERADO
            'sem_match_list': sem_match,  # ALTERADO
            'anomalias': anomalias
        }

        print(f"✅ Contexto carregado: {total_nfes} NFes, {total_trans} transações")

    def perguntar(self, pergunta: str) -> Dict:
        """
        Faz uma pergunta ao chatbot

        Args:
            pergunta: Pergunta em linguagem natural

        Returns:
            Dict com resposta e informações adicionais
        """

        if not self.contexto:
            return {
                'resposta': "❌ Nenhum contexto carregado. Processe uma conciliação primeiro!",
                'tipo': 'erro'
            }

        print(f"\n💬 Pergunta: {pergunta}")

        # Adicionar ao histórico
        self.historico.append({'tipo': 'pergunta', 'texto': pergunta})

        # Identificar tipo de pergunta
        tipo_pergunta = self._identificar_tipo_pergunta(pergunta)

        # Gerar resposta baseada no tipo
        if tipo_pergunta == 'estatistica':
            resposta = self._responder_estatistica(pergunta)
        elif tipo_pergunta == 'detalhe_match':
            resposta = self._responder_detalhe_match(pergunta)
        elif tipo_pergunta == 'anomalia':
            resposta = self._responder_anomalia(pergunta)
        elif tipo_pergunta == 'recomendacao':
            resposta = self._responder_recomendacao(pergunta)
        else:
            resposta = self._responder_geral(pergunta)

        # Adicionar ao histórico
        self.historico.append({'tipo': 'resposta', 'texto': resposta['resposta']})

        print(f"🤖 Resposta: {resposta['resposta'][:100]}...")

        return resposta

    def _identificar_tipo_pergunta(self, pergunta: str) -> str:
        """Identifica o tipo de pergunta"""

        pergunta_lower = pergunta.lower()

        # Palavras-chave para cada tipo
        if any(palavra in pergunta_lower for palavra in
               ['quantas', 'quanto', 'total', 'taxa', 'percentual', 'porcentagem']):
            return 'estatistica'

        elif any(palavra in pergunta_lower for palavra in
                 ['match', 'nfe', 'transação', 'detalhe', 'específic']):
            return 'detalhe_match'

        elif any(palavra in pergunta_lower for palavra in
                 ['anomalia', 'suspeito', 'problema', 'erro', 'alerta']):
            return 'anomalia'

        elif any(palavra in pergunta_lower for palavra in
                 ['recomend', 'sugest', 'fazer', 'ação', 'melhorar']):
            return 'recomendacao'

        else:
            return 'geral'

    def _responder_estatistica(self, pergunta: str) -> Dict:
        """Responde perguntas sobre estatísticas"""

        ctx = self.contexto

        # Preparar estatísticas formatadas (USANDO AS NOVAS CHAVES DE CONTAGEM)
        stats = f"""**Estatísticas da Conciliação:**

📊 **Geral:**
- Total de NFes: {ctx['total_nfes']}
- Total de Transações: {ctx['total_transacoes']}
- Taxa de Conciliação: {ctx['taxa_conciliacao']:.1f}%

✅ **Matches:**
- Confirmados: {ctx['matches_confirmados_count']}
- Sugestões: {ctx['sugestoes_count']}
- Sem Match: {ctx['sem_match_count']}

💰 **Valores:**
- Total NFes: R$ {ctx['valor_total_nfes']:,.2f}
- Conciliado: R$ {ctx['valor_conciliado']:,.2f}
- Pendente: R$ {ctx['valor_pendente']:,.2f}"""

        return {
            'resposta': stats,
            'tipo': 'estatistica',
            'dados': {
                'total_nfes': ctx['total_nfes'],
                'taxa': ctx['taxa_conciliacao'],
                'valor_total': ctx['valor_total_nfes']
            }
        }

    def _responder_detalhe_match(self, pergunta: str) -> Dict:
        """Responde perguntas sobre matches específicos"""

        # Extrair número da NFe se mencionado
        import re
        numeros = re.findall(r'\d+', pergunta)

        # USANDO A LISTA DE MATCHES COMPLETA
        matches_list = self.contexto['matches_list']

        if numeros and matches_list:
            # Procurar NFe específica
            numero_busca = numeros[0]

            for match in matches_list:
                if str(match['nfe'].get('numero')) == numero_busca:
                    nfe = match['nfe']
                    trans = match['transacao']
                    score = match.get('score', 0)

                    detalhes = f"""**Detalhes do Match - NFe {numero_busca}:**

📋 **NFe:**
- Número: {nfe.get('numero')}
- Valor: R$ {nfe.get('valor_total', 0):,.2f}
- Data: {nfe.get('data_emissao')}
- Tipo: {nfe.get('tipo_operacao')}
- Emitente: {nfe.get('nome_emitente', 'N/A')}

💳 **Transação:**
- ID: {trans.get('id')}
- Valor: R$ {trans.get('valor', 0):,.2f}
- Data: {trans.get('data')}
- Tipo: {trans.get('tipo')}

🎯 **Score:** {score:.1f}%"""

                    if 'explicacao_ia' in match:
                        exp = match['explicacao_ia']
                        detalhes += f"\n\n🤖 **Explicação da IA:**\n{exp.get('resumo', 'N/A')}"

                    return {
                        'resposta': detalhes,
                        'tipo': 'detalhe_match',
                        'match': match
                    }

        # Resposta genérica se não encontrou
        return {
            'resposta': f"Encontrei {self.contexto['matches_confirmados_count']} matches. Você pode perguntar sobre uma NFe específica mencionando o número!",
            'tipo': 'detalhe_match'
        }

    def _responder_anomalia(self, pergunta: str) -> Dict:
        """Responde perguntas sobre anomalias"""

        if not self.contexto.get('anomalias'):
            return {
                'resposta': "Nenhuma análise de anomalias disponível. Execute a detecção de anomalias primeiro!",
                'tipo': 'anomalia'
            }

        anomalias = self.contexto['anomalias']

        resposta = f"""**🚨 Análise de Anomalias:**

**Score de Risco:** {anomalias['score']}/100
**Nível de Alerta:** {anomalias['nivel_alerta']}

**Anomalias Detectadas:**
- Valores atípicos: {len(anomalias['valores_atipicos'])}
- Problemas temporais: {len(anomalias['temporal'])}
- NFes suspeitas: {len(anomalias['sem_match_suspeito'])}
- Duplicatas: {len(anomalias['duplicatas_potenciais'])}
- Inconsistências: {len(anomalias['inconsistencias'])}"""

        if anomalias.get('analise_ia'):
            ia = anomalias['analise_ia']
            resposta += f"\n\n**🤖 Análise da IA:**\n"
            resposta += f"- Gravidade: {ia.get('gravidade', 'N/A')}\n"
            resposta += f"- Principais Riscos: {', '.join(ia.get('principais_riscos', []))}"

        return {
            'resposta': resposta,
            'tipo': 'anomalia',
            'anomalias': anomalias
        }

    def _responder_recomendacao(self, pergunta: str) -> Dict:
        """Responde com recomendações"""

        ctx = self.contexto

        recomendacoes = ["**💡 Recomendações:**\n"]

        # Baseado na taxa de conciliação
        if ctx['taxa_conciliacao'] < 50:
            recomendacoes.append("🔴 **URGENTE:** Taxa de conciliação muito baixa (<50%)")
            recomendacoes.append("   → Revisar qualidade dos dados de entrada")
            recomendacoes.append("   → Verificar se as datas estão corretas")
            recomendacoes.append("   → Considerar ajustar os thresholds")

        elif ctx['taxa_conciliacao'] < 80:
            recomendacoes.append("🟡 Taxa de conciliação moderada")
            recomendacoes.append("   → Revisar os itens sem match")
            recomendacoes.append("   → Validar sugestões manualmente")

        else:
            recomendacoes.append("🟢 Excelente taxa de conciliação!")
            recomendacoes.append("   → Revisar apenas os poucos itens pendentes")

        # Sugestões específicas (USANDO A NOVA CHAVE DE CONTAGEM)
        if ctx['sugestoes_count'] > 0:
            recomendacoes.append(f"\n📋 Revisar {ctx['sugestoes_count']} sugestões manualmente")

        # Sem match (USANDO A NOVA CHAVE DE CONTAGEM)
        if ctx['sem_match_count'] > 0:
            recomendacoes.append(f"\n⚠️ Investigar {ctx['sem_match_count']} NFes sem match")

        # Anomalias
        if ctx.get('anomalias'):
            score = ctx['anomalias']['score']
            if score > 25:
                recomendacoes.append(f"\n🚨 Atenção: Score de risco elevado ({score}/100)")
                recomendacoes.append("   → Verificar anomalias detectadas")

        return {
            'resposta': '\n'.join(recomendacoes),
            'tipo': 'recomendacao'
        }

    def _responder_geral(self, pergunta: str) -> Dict:
        """Responde perguntas gerais usando IA"""

        # Preparar contexto para a IA
        ctx = self.contexto

        contexto_resumido = f"""Você é um assistente especializado em conciliação bancária.

**Contexto da Conciliação:**
- Total NFes: {ctx['total_nfes']}
- Total Transações: {ctx['total_transacoes']}
- Matches: {ctx['matches_confirmados_count']}
- Taxa: {ctx['taxa_conciliacao']:.1f}%
- Valor Total: R$ {ctx['valor_total_nfes']:,.2f}
- Valor Conciliado: R$ {ctx['valor_conciliado']:,.2f}

**Pergunta do usuário:** {pergunta}

Responda de forma clara, objetiva e profissional. Use os dados acima para contextualizar sua resposta."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system",
                     "content": "Você é um assistente especializado em conciliação bancária. Responda de forma clara e profissional."},
                    {"role": "user", "content": contexto_resumido}
                ],
                temperature=0.6,
                max_tokens=400
            )

            resposta_ia = response.choices[0].message.content.strip()

            return {
                'resposta': resposta_ia,
                'tipo': 'geral'
            }

        except Exception as e:
            return {
                'resposta': f"Desculpe, não consegui processar sua pergunta. Erro: {str(e)}",
                'tipo': 'erro'
            }

    def sugerir_perguntas(self, primeira_nfe_num: str = None) -> List[str]:
        """Sugere perguntas que o usuário pode fazer"""

        if not self.contexto:
            return [
                "Carregue uma conciliação primeiro para fazer perguntas!"
            ]

        sugestoes = [
            "Qual a taxa de conciliação?",
            "Quantas NFes foram conciliadas?",
            "Quais são os principais problemas?",
            "O que devo fazer agora?",
            "Há alguma anomalia detectada?",
        ]

        # Sugestões específicas baseadas no contexto
        # USANDO A NOVA CHAVE DE LISTA
        if self.contexto['matches_list']:
            # Se não foi passado o número da NFe (como no app principal), tenta pegar da lista
            if not primeira_nfe_num:
                primeira_nfe = self.contexto['matches_list'][0]['nfe'].get('numero')
                sugestoes.append(f"Me mostre detalhes da NFe {primeira_nfe}")
            else:
                sugestoes.append(f"Me mostre detalhes da NFe {primeira_nfe_num}")

        # USANDO A NOVA CHAVE DE CONTAGEM
        if self.contexto['sem_match_count'] > 0:
            sugestoes.append("Por que algumas NFes não tiveram match?")

        return sugestoes

    def limpar_historico(self):
        """Limpa histórico da conversa"""
        self.historico = []
        print("✅ Histórico limpo!")


def criar_chatbot(api_key: str = None):
    """Cria instância do chatbot"""
    return ChatbotAssistente(api_key=api_key)


# ============================================================================
# TESTE DO CHATBOT
# ============================================================================

if __name__ == "__main__":
    print("🧪 Testando Chatbot Assistente...\n")

    # Dados de teste
    nfes_teste = [
        {'numero': '12345', 'valor_total': 2500.00, 'data_emissao': '2024-01-10', 'tipo_operacao': 'ENTRADA'}
    ]

    transacoes_teste = [
        {'id': 'T001', 'valor': -2500.00, 'data': '2024-01-11', 'tipo': 'DEBITO'}
    ]

    resultados_teste = {
        'matches_confirmados': [{
            'nfe': nfes_teste[0],
            'transacao': transacoes_teste[0],
            'score': 95.5
        }],
        'sugestoes': [],
        'sem_match': []
    }

    try:
        chatbot = criar_chatbot()
        chatbot.carregar_contexto(nfes_teste, transacoes_teste, resultados_teste)

        # Testar perguntas
        perguntas = [
            "Qual a taxa de conciliação?",
            "Me mostre detalhes da NFe 12345"
        ]

        for pergunta in perguntas:
            resp = chatbot.perguntar(pergunta)
            print(f"\n✅ {pergunta}")
            print(f"   {resp['resposta'][:100]}...\n")

    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")