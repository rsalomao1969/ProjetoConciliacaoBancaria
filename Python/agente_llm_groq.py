"""
Agente Autônomo de Conciliação Bancária usando Groq
100% GRÁTUS - Llama 3.1 8B (Modelo de Alta Estabilidade)
VERSÃO FINAL - LÓGICA HÍBRIDA DETERMINÍSTICA (Prioriza ID no Python)
"""

import os
from typing import List, Dict, Tuple
import json
from groq import Groq
import time


class AgenteConcialiadorLLM:
    """
    Agente Autônomo que usa Groq (GRÁTIS) para conciliação inteligente
    """

    def __init__(self, api_key: str = None):
        """
        Inicializa o agente com a API do Groq
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY')

        if not self.api_key:
            raise ValueError(
                "❌ API key do Groq não encontrada!\n\n"
                "Para ativar a IA:\n"
                "1. Crie arquivo .env na raiz do projeto\n"
                "2. Adicione: GROQ_API_KEY=gsk_...\n"
                "3. Obtenha GRÁTIS em: https://console.groq.com/keys"
            )

        try:
            self.client = Groq(api_key=self.api_key)
        except Exception as e:
            raise ValueError(f"❌ Erro ao inicializar Groq: {str(e)}")

        # Migração para modelo de alta estabilidade
        self.model = "llama-3.1-8b-instant"

        self.historico_pensamento = []

        print(f"✅ Agente Groq inicializado: {self.model}")
        print(f"   💚 100% GRÁTIS | Muito rápido!")

    def _aplicar_penalidade_tipo(self, nfe: Dict, trans: Dict, score: int) -> Tuple[int, str]:
        """
        Penaliza o score se houver INCOMPATIBILIDADE DE FLUXO DE CAIXA ou
        INCONSISTÊNCIA INTERNA de RÓTULO DE EXTRATO.
        """
        tipo_nfe = nfe.get('tipo_operacao', '').upper()

        # O campo 'tipo' da transação É O TIPO NORMALIZADO (DEBITO/CREDITO)
        tipo_normalizado = trans.get('tipo', '').upper()
        rotulo_bruto = trans.get('rotulo_extrato_original', tipo_normalizado).upper()

        penalidade_msg = ""

        # 1. Cheque de Inconsistência Interna (Rótulo vs. Sinal) - Descarte Total (Score 0)
        # Se o rótulo (CRÉDITO) for oposto ao fluxo de caixa (DÉBITO), é um erro de dado fonte.
        if (('DEBITO' in tipo_normalizado and 'CREDITO' in rotulo_bruto) or
                ('CREDITO' in tipo_normalizado and 'DEBITO' in rotulo_bruto)):
            score = 0
            penalidade_msg = f"INCOMPATIBILIDADE CRÍTICA DE DADOS: O fluxo de caixa (Valor {tipo_normalizado}) não corresponde ao rótulo original do extrato ('{rotulo_bruto}'). Match descartado."
            return score, penalidade_msg

        # 2. Cheque de Incompatibilidade de Fluxo de Caixa (NFe vs. Transação)

        # 2.1. ENTRADA (compra/custo) deve ser DÉBITO
        incompativel_entrada = (tipo_nfe == 'ENTRADA' and tipo_normalizado != 'DEBITO')

        # 2.2. SAÍDA (venda/receita) deve ser CRÉDITO
        incompativel_saida = (tipo_nfe == 'SAIDA' and tipo_normalizado != 'CREDITO')

        if incompativel_entrada or incompativel_saida:
            # Penalidade CRÍTICA: Reduz o score para no máximo 30%
            novo_score = min(score, 30)
            return novo_score, f"Tipo de operação CRITICAMENTE INCOMPATÍVEL ({tipo_nfe} vs {tipo_normalizado})."

        return score, ""

    def fazer_conciliacao(
            self,
            nfes: List[Dict],
            transacoes: List[Dict]
    ) -> Dict:
        """
        Usa o agente Groq para fazer conciliação inteligente
        """

        print("\n" + "=" * 60)
        print("🤖 AGENTE AUTÔNOMO INICIANDO (GROQ)")
        print("=" * 60)
        print(f"📋 NFes: {len(nfes)}")
        print(f"💳 Transações: {len(transacoes)}")

        print(f"🤖 Modelo: {self.model}")
        print(f"💚 Status: GRÁTIS | Muito rápido!")
        print("-" * 60)

        try:
            # Etapa 1: Análise contextual
            print("\n🔍 Etapa 1: Analisando contexto...")
            contexto = self._analisar_contexto(nfes, transacoes)
            print(f"✅ Contexto: {contexto.get('tipo_empresa', 'N/A')}")

            # Etapa 2: Fazer matching
            print("\n🎯 Etapa 2: Iniciando matching inteligente...")
            resultados = self._fazer_matching_com_llm(nfes, transacoes, contexto)

            print("\n" + "=" * 60)
            print("✅ CONCILIAÇÃO CONCLUÍDA")
            print("=" * 60)
            print(f"   ✅ Matches: {len(resultados['matches_confirmados'])}")
            print(f"   🤔 Sugestões: {len(resultados['sugestoes'])}")
            print(f"   ❌ Sem match: {len(resultados['sem_match'])}")
            print("=" * 60 + "\n")

            return resultados

        except Exception as e:
            print(f"❌ Erro durante conciliação: {str(e)}")
            raise ValueError(f"❌ Erro durante conciliação: {str(e)}")

    def _analisar_contexto(self, nfes: List[Dict], transacoes: List[Dict]) -> Dict:

        prompt = f"""Analise e responda em JSON puro:

NFes: {len(nfes)} documentos
Transações: {len(transacoes)} registros

Responda APENAS: {{"tipo_empresa": "comércio"}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )

            texto = response.choices[0].message.content.strip()

            # Extrair JSON
            if '```json' in texto:
                texto = texto.split('```json')[1].split('```')[0].strip()
            elif '```' in texto:
                texto = texto.split('```')[1].split('```')[0].strip()

            inicio = texto.find('{')
            fim = texto.rfind('}') + 1

            if inicio >= 0 and fim > inicio:
                contexto = json.loads(texto[inicio:fim])
            else:
                contexto = {"tipo_empresa": "Comércio"}

            return contexto

        except Exception as e:
            print(f"⚠️ Erro na análise: {str(e)}")
            return {"tipo_empresa": "Comércio"}

    def _fazer_matching_com_llm(
            self,
            nfes: List[Dict],
            transacoes: List[Dict],
            contexto: Dict
    ) -> Dict:

        matches_confirmados = []
        sugestoes = []
        sem_match = []
        transacoes_usadas = set()

        for i, nfe in enumerate(nfes):
            print(f"\n   🔍 Analisando NFe {i + 1}/{len(nfes)} (#{nfe.get('numero')})...")

            trans_disponiveis = [
                t for t in transacoes
                if t['id'] not in transacoes_usadas
            ]

            if not trans_disponiveis:
                sem_match.append({
                    'nfe': nfe,
                    'motivo': 'Sem transações disponíveis',
                    'raciocinio': 'Todas já foram usadas'
                })
                print(f"      ❌ Sem transações disponíveis")
                continue

            # Chama o método individual com Resiliência (Retry)
            resultado = self._matching_individual(nfe, trans_disponiveis)

            if resultado['match_encontrado']:
                trans_escolhida = resultado['transacao']
                score = resultado['score']

                # Aplica a penalidade crítica se o tipo for inconsistente
                score_penalizado, motivo_penalidade = self._aplicar_penalidade_tipo(
                    nfe,
                    trans_escolhida,
                    score
                )

                # Se o score foi penalizado, sobrescreve o resultado
                if score_penalizado != score:
                    resultado['score'] = score_penalizado
                    resultado['raciocinio'] += f" [PENALIDADE: {motivo_penalidade}]"
                    score = score_penalizado

                match = {
                    'nfe': nfe,
                    'transacao': trans_escolhida,
                    'score': score,
                    'raciocinio_llm': resultado['raciocinio'],
                    'detalhes': resultado.get('detalhes', {})
                }

                if score >= 70:
                    matches_confirmados.append(match)
                    transacoes_usadas.add(trans_escolhida['id'])
                    print(f"      ✅ Match confirmado (Score: {score}%)")
                elif score >= 50:
                    sugestoes.append(match)
                    transacoes_usadas.add(trans_escolhida['id'])
                    print(f"      🤔 Sugestão (Score: {score}%)")
                else:
                    sem_match.append({
                        'nfe': nfe,
                        'motivo': 'Score insuficiente (abaixo de 50%)',
                        'raciocinio': resultado['raciocinio']
                    })
                    print(f"      ❌ Score baixo ({score}%)")
            else:
                sem_match.append({
                    'nfe': nfe,
                    'motivo': resultado.get('motivo', 'Sem match'),
                    'raciocinio': resultado.get('raciocinio', 'N/A')
                })
                print(f"      ❌ Sem match")

        return {
            'matches_confirmados': matches_confirmados,
            'sugestoes': sugestoes,
            'sem_match': sem_match,
            'historico_pensamento': self.historico_pensamento,
            'total_nfes': len(nfes),
            'total_transacoes': len(transacoes),
            'total_matches': len(matches_confirmados),
            'total_sugestoes': len(sugestoes),
            'total_sem_match': len(sem_match)
        }

    def _matching_heuristico(
            self,
            nfe: Dict,
            transacoes: List[Dict],
            nfe_numero_alvo: str
    ) -> Dict:
        """
        Método LLM usado para: 1) Avaliar um match rígido de ID ou 2) Encontrar o melhor match heurístico.
        """

        # Determina se a busca atual é a busca rígida (apenas um candidato)
        is_rigid_search = len(transacoes) == 1

        trans_simplificadas = [{
            'id': t.get('id'),
            'valor': t.get('valor'),
            'data': t.get('data'),
            'tipo': t.get('tipo'),
            'rotulo_original': t.get('rotulo_extrato_original', t.get('tipo')),
            'descricao': (t.get('descricao', '') or '')[:50]
        } for t in transacoes[:10]]

        nfe_valor = nfe.get('valor_total', 0)

        # O prompt é adaptado para forçar o LLM a seguir regras rígidas de VALOR/SINAL

        prioridade_valor = (
            "1. PRIORIDADE MÁXIMA: O valor da transação deve ser EXATO ou com diferença inferior a 1% para ter score >= 95. "
            "Caso contrário, o score deve ser 0."
            if is_rigid_search
            else "1. O VALOR é o critério MAIS IMPORTANTE. Se a diferença de valor for superior a 15% do valor da NFe, o SCORE deve ser ZERO ou muito baixo (abaixo de 50)."
        )

        prompt = f"""Você é um sistema de conciliação bancária. Analise e responda APENAS com JSON válido.

NFe #{nfe.get('numero')} (ALVO DA BUSCA):
Valor: R$ {nfe_valor:.2f}
Tipo: {nfe.get('tipo_operacao')}

Transações Disponíveis:
{json.dumps(trans_simplificadas, ensure_ascii=False)}

REGRAS CRÍTICAS DE PRIORIZAÇÃO E INTEGRIDADE:
{prioridade_valor}
2. SAÍDA concilia com CRÉDITO; ENTRADA concilia com DÉBITO.
3. Se houver INCONSISTÊNCIA INTERNA de rótulo (Crédito vs. Valor Negativo), o match deve ser descartado (score 0).

Responda APENAS este JSON:
{{
  "match_encontrado": true,
  "transacao_id": "TRANS_00X",
  "score": 85,
  "raciocinio": "Melhor score heurístico encontrado.",
  "detalhes": {{
    "compatibilidade_valor": "Alta, diferença de R$ 0.00",
    "compatibilidade_data": "Alta, diferença de 1 dia",
    "compatibilidade_tipo": "Perfeita (ENTRADA vs DÉBITO)",
    "compatibilidade_texto": "Média, descrição da NFe e transação similar"
  }}
}}
"""

        # Parâmetros de Resiliência
        MAX_RETRIES = 3
        RETRY_DELAY = 1
        texto = None

        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3 if is_rigid_search else 0.5,
                    max_tokens=500
                )
                texto = response.choices[0].message.content.strip()
                break
            except Exception as e:
                time.sleep(RETRY_DELAY * (2 ** attempt))
                continue

        if texto:
            try:
                if '```json' in texto:
                    json_texto = texto.split('```json')[1].split('```')[0].strip()
                else:
                    inicio = texto.find('{')
                    fim = texto.rfind('}') + 1
                    json_texto = texto[inicio:fim]

                resultado = json.loads(json_texto)

                if resultado.get('match_encontrado') and resultado.get('transacao_id'):
                    trans_id = resultado['transacao_id']
                    trans_obj = next((t for t in transacoes if t['id'] == trans_id), None)
                    if trans_obj:
                        resultado['transacao'] = trans_obj

                # Garante que os detalhes existam, mesmo que vazios
                if 'detalhes' not in resultado:
                    resultado['detalhes'] = {}

                return resultado

            except:
                pass

        return {
            "match_encontrado": False,
            "transacao_id": None,
            "score": 0,
            "raciocinio": "Falha na busca heurística (LLM/JSON error).",
        }

    def _matching_individual(
            self,
            nfe: Dict,
            transacoes: List[Dict]
    ) -> Dict:
        """
        Implementa a lógica Híbrida DETERMINÍSTICA: 1. Cheque Rígido Python (ID 1:1), 2. Busca Heurística (Fallback).
        """
        nfe_numero = nfe.get('numero', 'N/A')
        transacao_alvo_id = f"TRANS_{nfe_numero.zfill(3)}"

        # --- ETAPA 1: Busca Rígida (Determinística - Feita pelo Python) ---

        transacao_rigida = next((t for t in transacoes if t['id'] == transacao_alvo_id), None)

        if transacao_rigida:
            nfe_valor = nfe.get('valor_total', 0)
            trans_valor_abs = abs(transacao_rigida.get('valor', 0))
            trans_tipo_normalizado = transacao_rigida.get('tipo', '').upper()
            trans_rotulo_bruto = transacao_rigida.get('rotulo_extrato_original', trans_tipo_normalizado).upper()

            # 1. Cheque de Valor (Tolerância de 1% para ser considerado Rígido)
            valor_diff = abs(nfe_valor - trans_valor_abs)
            tolerancia_max = nfe_valor * 0.01

            # 2. Cheque de Integridade do Rótulo Bruto (REJEIÇÃO CRÍTICA)
            is_label_inconsistent = ('DEBITO' in trans_tipo_normalizado and 'CREDITO' in trans_rotulo_bruto) or \
                                    ('CREDITO' in trans_tipo_normalizado and 'DEBITO' in trans_rotulo_bruto)

            if is_label_inconsistent:
                # Penalidade por Inconsistência de Rótulo (NF 007)
                return {
                    'match_encontrado': False,
                    'transacao_id': transacao_alvo_id,
                    'score': 0,
                    'raciocinio': f"Busca Rígida (ID 1:1) REJEITADA. INCOMPATIBILIDADE CRÍTICA DE DADOS (Rótulo Bruto {trans_rotulo_bruto} vs. Sinal {trans_tipo_normalizado}).",
                    'motivo': 'Inconsistência de Rótulo Bruto'
                }

            # 3. Cheque de Tipo/Sinal (ENTRADA vs. DÉBITO)
            tipo_nfe = nfe.get('tipo_operacao', '').upper()
            is_type_match = (
                    (tipo_nfe == 'ENTRADA' and trans_tipo_normalizado == 'DEBITO') or
                    (tipo_nfe == 'SAIDA' and trans_tipo_normalizado == 'CREDITO')
            )

            # 4. Confirmação Final do Match Rígido
            if valor_diff <= tolerancia_max and is_type_match:
                # Match Rígido CONFIRMADO pelo Python
                return {
                    'match_encontrado': True,
                    'transacao_id': transacao_alvo_id,
                    'transacao': transacao_rigida,
                    'score': 100,
                    'raciocinio': f"Busca Rígida (ID 1:1) CONFIRMADA pelo Python. Valor: {nfe_valor:.2f} | Diff: {valor_diff:.2f} (Tolerância Máx: {tolerancia_max:.2f})."
                }

            # Se falhou por valor ou tipo, o LLM decide no fallback (Etapa 2)

        # --- ETAPA 2: Fallback para Busca Heurística (Melhor Score Geral) ---

        print(
            f"      ⚠️ Falha na Busca Rígida ({transacao_alvo_id} não validado pelo Python). Tentando Fallback Heurístico...")

        resultado_heuristico = self._matching_heuristico(nfe, transacoes, transacao_alvo_id)

        if resultado_heuristico.get('match_encontrado'):
            resultado_heuristico['raciocinio'] = f"Busca Heurística (Fallback) ativada. " + resultado_heuristico.get(
                'raciocinio', '')
            return resultado_heuristico

        # --- ETAPA 3: Falha Total ---
        return {
            "match_encontrado": False,
            "transacao_id": None,
            "score": 0,
            "raciocinio": f"Falha na conciliação: ID ({transacao_alvo_id}) não encontrado e Busca Heurística não achou match > 50%."
        }


def criar_agente(api_key: str = None):
    """Cria instância do agente"""
    return AgenteConcialiadorLLM(api_key=api_key)