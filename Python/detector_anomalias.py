"""
Módulo de Detecção de Anomalias com IA
Detecta padrões suspeitos e transações anômalas usando Groq
"""

import os
from typing import Dict, List, Tuple
from groq import Groq
import json
from datetime import datetime, timedelta


class DetectorAnomalias:
    """
    Detecta anomalias em transações e NFes usando IA
    - Valores atípicos
    - Padrões suspeitos
    - Discrepâncias temporais
    - Inconsistências de dados
    """

    def __init__(self, api_key: str = None):
        """Inicializa detector com Groq"""
        self.api_key = api_key or os.getenv('GROQ_API_KEY')

        if not self.api_key:
            raise ValueError("❌ API key do Groq não encontrada!")

        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.1-8b-instant"

        print("✅ Detector de Anomalias IA inicializado!")

    def detectar_anomalias_gerais(
            self,
            nfes: List[Dict],
            transacoes: List[Dict],
            matches: List[Dict],
            nfes_sem_match_llm: List[Dict] = None
    ) -> Dict:
        """
        Detecta anomalias gerais no dataset
        """

        print("\n🚨 Iniciando detecção de anomalias...")

        anomalias = {
            'valores_atipicos': [],
            'temporal': [],
            'sem_match_suspeito': [],
            'duplicatas_potenciais': [],
            'inconsistencias': [],
            'score': 0,
            'nivel_alerta': 'BAIXO'
        }

        # 1. Detectar valores atípicos
        print("   📊 Analisando valores atípicos...")
        anomalias['valores_atipicos'] = self._detectar_valores_atipicos(nfes, transacoes)

        # 2. Detectar problemas temporais
        print("   📅 Analisando padrões temporais...")
        anomalias['temporal'] = self._detectar_anomalias_temporais(matches)

        # 3. NFes sem match suspeitas (combina a análise estatística com a penalidade do LLM)
        print("   ⚠️ Analisando NFes sem match...")

        nfes_sem_match_bruto = self._identificar_nfes_sem_match(nfes, matches)
        suspeitas_estatisticas = self._analisar_nfes_suspeitas(nfes_sem_match_bruto, transacoes)

        anomalias['sem_match_suspeito'] = suspeitas_estatisticas

        if nfes_sem_match_llm is not None:
            nfes_penalizadas = self._detectar_nfes_penalizadas(nfes_sem_match_llm)
            anomalias['sem_match_suspeito'].extend(nfes_penalizadas)

        # 4. Detectar possíveis duplicatas
        print("   🔄 Detectando duplicatas potenciais...")
        anomalias['duplicatas_potenciais'] = self._detectar_duplicatas(nfes, transacoes)

        # 5. Inconsistências de dados
        print("   🔍 Verificando inconsistências...")
        anomalias['inconsistencias'] = self._detectar_inconsistencias(matches)

        # 6. Calcular score de risco e nível de alerta
        anomalias['score'] = self._calcular_score_risco(anomalias)
        anomalias['nivel_alerta'] = self._determinar_nivel_alerta(anomalias['score'])

        # 7. Análise inteligente com IA
        print("   🤖 Analisando com IA...")
        anomalias['analise_ia'] = self._analisar_com_ia(anomalias, nfes, transacoes)

        print(f"✅ Detecção concluída! Nível: {anomalias['nivel_alerta']} (Score: {anomalias['score']}/100)\n")

        return anomalias

    def _detectar_nfes_penalizadas(self, nfes_sem_match_llm: List[Dict]) -> List[Dict]:
        """Extrai NFes cuja não conciliação foi motivada pela penalidade crítica de tipo/integridade."""
        penalizadas = []
        for item in nfes_sem_match_llm:
            raciocinio = item.get('raciocinio', '')

            # Checa penalidade de tipo (Entrada vs Crédito) OU penalidade de integridade (Rótulo vs Sinal)
            if "CRITICAMENTE INCOMPATÍVEL" in raciocinio or "INCONSISTÊNCIA DE DADOS CRÍTICA" in raciocinio:
                nfe = item['nfe']
                motivo_completo = "Tipo/Sinal Incompatível" if "CRITICAMENTE INCOMPATÍVEL" in raciocinio else "Rótulo de Extrato Falso"

                penalizadas.append({
                    'tipo': 'NFE_REJEITADA_TIPO_ERRADO',
                    'nfe': nfe.get('numero'),
                    'valor': nfe.get('valor_total', 0),
                    'severidade': 'CRITICA',
                    'descricao': f"NFe {nfe.get('numero')} (R$ {nfe.get('valor_total', 0):,.2f}) rejeitada. Causa: {motivo_completo}."
                })
        return penalizadas

    def _detectar_valores_atipicos(
            self,
            nfes: List[Dict],
            transacoes: List[Dict]
    ) -> List[Dict]:
        """Detecta valores estatisticamente atípicos"""

        atipicos = []

        # Calcular estatísticas das NFes
        valores_nfes = [n.get('valor_total', 0) for n in nfes if n.get('valor_total', 0) > 0]

        if not valores_nfes:
            return atipicos

        media = sum(valores_nfes) / len(valores_nfes)
        desvio = (sum((v - media) ** 2 for v in valores_nfes) / len(valores_nfes)) ** 0.5

        # Valores > 2 desvios padrão da média são atípicos
        limite_superior = media + (2 * desvio)
        limite_inferior = max(0, media - (2 * desvio))

        for nfe in nfes:
            valor = nfe.get('valor_total', 0)

            if valor > limite_superior:
                atipicos.append({
                    'tipo': 'VALOR_MUITO_ALTO',
                    'item': 'NFe',
                    'id': nfe.get('numero'),
                    'valor': valor,
                    'media': media,
                    'desvio_padrao': desvio,
                    'percentual_acima': ((valor - media) / media) * 100,
                    'severidade': 'ALTA' if valor > limite_superior * 1.5 else 'MEDIA',
                    'descricao': f"NFe {nfe.get('numero')} com valor {((valor - media) / media) * 100:.0f}% acima da média"
                })

            elif valor < limite_inferior and valor > 0:
                atipicos.append({
                    'tipo': 'VALOR_MUITO_BAIXO',
                    'item': 'NFe',
                    'id': nfe.get('numero'),
                    'valor': valor,
                    'media': media,
                    'percentual_abaixo': ((media - valor) / media) * 100,
                    'severidade': 'BAIXA',
                    'descricao': f"NFe {nfe.get('numero')} com valor {((media - valor) / media) * 100:.0f}% abaixo da média"
                })

        return atipicos

    def _detectar_anomalias_temporais(self, matches: List[Dict]) -> List[Dict]:
        """Detecta anomalias em datas (NFe vs Transação)"""

        anomalias = []

        for match in matches:
            nfe = match['nfe']
            trans = match['transacao']

            try:
                # Parsear datas
                data_nfe = datetime.strptime(nfe.get('data_emissao', ''), '%Y-%m-%d')
                data_trans = datetime.strptime(trans.get('data', ''), '%Y-%m-%d')

                diff_dias = abs((data_trans - data_nfe).days)

                id_nfe = nfe.get('numero', 'N/A')
                id_trans = trans.get('id', 'N/A')

                # Transação muito antes da NFe (suspeito!)
                if data_trans < data_nfe - timedelta(days=2):
                    anomalias.append({
                        'tipo': 'TRANSACAO_ANTES_NFE',
                        'nfe': id_nfe,
                        'transacao': id_trans,
                        'diff_dias': diff_dias,
                        'severidade': 'ALTA',
                        'descricao': f"NFe {id_nfe} (Emissão: {nfe.get('data_emissao')}) | Transação {id_trans} (Data: {trans.get('data')}) está {diff_dias} dias ANTES da emissão da NFe."
                    })

                # Diferença muito grande (> 30 dias)
                elif diff_dias > 30:
                    anomalias.append({
                        'tipo': 'DIFERENCA_TEMPORAL_GRANDE',
                        'nfe': id_nfe,
                        'transacao': id_trans,
                        'diff_dias': diff_dias,
                        'severidade': 'MEDIA',
                        'descricao': f"NFe {id_nfe} | Diferença de {diff_dias} dias entre NFe e transação {id_trans}."
                    })

            except (ValueError, TypeError):
                pass

        return anomalias

    def _identificar_nfes_sem_match(
            self,
            nfes: List[Dict],
            matches: List[Dict]
    ) -> List[Dict]:
        """Identifica NFes que não tiveram match (baseado apenas nos matches confirmados)"""

        nfes_com_match = {m['nfe'].get('numero') for m in matches}

        return [
            nfe for nfe in nfes
            if nfe.get('numero') not in nfes_com_match
        ]

    def _analisar_nfes_suspeitas(
            self,
            nfes_sem_match: List[Dict],
            transacoes: List[Dict]
    ) -> List[Dict]:
        """Analisa se NFes sem match são suspeitas (baseado em critérios estatísticos: valor/idade)"""

        suspeitas = []

        # Calcular valor médio das transações
        valores_trans = [abs(t.get('valor', 0)) for t in transacoes if t.get('valor', 0) != 0]

        media_trans = sum(valores_trans) / len(valores_trans) if valores_trans else 0

        for nfe in nfes_sem_match:
            valor = nfe.get('valor_total', 0)
            id_nfe = nfe.get('numero', 'N/A')

            # 1. NFe com valor alto sem match é suspeita
            if valor > media_trans * 2 and media_trans > 0:
                suspeitas.append({
                    'tipo': 'NFE_ALTO_VALOR_SEM_MATCH',
                    'nfe': id_nfe,
                    'valor': valor,
                    'severidade': 'ALTA',
                    'descricao': f"NFe {id_nfe} de R$ {valor:,.2f} sem transação correspondente (2x > média de transações)"
                })

            # 2. NFe muito antiga sem match
            try:
                data_nfe = datetime.strptime(nfe.get('data_emissao', ''), '%Y-%m-%d')
                dias_passados = (datetime.now() - data_nfe).days

                if dias_passados > 60:
                    suspeitas.append({
                        'tipo': 'NFE_ANTIGA_SEM_MATCH',
                        'nfe': id_nfe,
                        'dias': dias_passados,
                        'severidade': 'MEDIA',
                        'descricao': f"NFe {id_nfe} de {dias_passados} dias atrás ainda sem conciliação"
                    })
            except (ValueError, TypeError):
                pass

        return suspeitas

    def _detectar_duplicatas(
            self,
            nfes: List[Dict],
            transacoes: List[Dict]
    ) -> List[Dict]:
        """Detecta possíveis duplicatas"""

        duplicatas = []

        # Detectar NFes duplicadas (mesmo número)
        numeros_vistos = {}
        for nfe in nfes:
            numero = nfe.get('numero')
            if numero in numeros_vistos:
                duplicatas.append({
                    'tipo': 'NFE_DUPLICADA',
                    'id': numero,
                    'severidade': 'CRITICA',
                    'descricao': f"NFe {numero} aparece múltiplas vezes"
                })
            else:
                numeros_vistos[numero] = True

        # Detectar transações duplicadas (mesmo ID)
        ids_vistos = {}
        for trans in transacoes:
            trans_id = trans.get('id')
            if trans_id in ids_vistos:
                duplicatas.append({
                    'tipo': 'TRANSACAO_DUPLICADA',
                    'id': trans_id,
                    'severidade': 'CRITICA',
                    'descricao': f"Transação {trans_id} aparece múltiplas vezes"
                })
            else:
                ids_vistos[trans_id] = True

        return duplicatas

    def _detectar_inconsistencias(self, matches: List[Dict]) -> List[Dict]:
        """Detecta inconsistências em matches (apenas aqueles que foram aceitos!)"""

        inconsistencias = []

        for match in matches:
            nfe = match['nfe']
            trans = match['transacao']

            tipo_nfe = nfe.get('tipo_operacao', '').upper()
            valor_trans = trans.get('valor', 0)
            id_nfe = nfe.get('numero', 'N/A')
            id_trans = trans.get('id', 'N/A')

            # 1. TIPO INCOMPATÍVEL ACEITO
            tipo_normalizado = trans.get('tipo', '').upper()
            incompativel_entrada = (tipo_nfe == 'ENTRADA' and tipo_normalizado != 'DEBITO')
            incompativel_saida = (tipo_nfe == 'SAIDA' and tipo_normalizado != 'CREDITO')

            if incompativel_entrada or incompativel_saida:
                descricao_erro = f"NFe {id_nfe} (R$ {nfe.get('valor_total', 0):,.2f}): Tipo NFe ({tipo_nfe}) incompatível com Transação {id_trans} ({tipo_normalizado})."
                inconsistencias.append({
                    'tipo': 'TIPO_INCOMPATIVEL_ACEITO',
                    'nfe': id_nfe,
                    'transacao': id_trans,
                    'severidade': 'ALTA',
                    'descricao': descricao_erro
                })

            # 2. Diferença de valor muito grande
            diff_valor = abs(nfe.get('valor_total', 0) - abs(trans.get('valor', 0)))
            tolerancia_pct = 0.10
            tolerancia_abs = nfe.get('valor_total', 1) * tolerancia_pct

            # CORREÇÃO DA MENSAGEM DE ERRO (Para garantir que não haja caracteres ilegíveis)
            if diff_valor > tolerancia_abs:
                inconsistencias.append({
                    'tipo': 'DIFERENCA_VALOR_GRANDE',
                    'nfe': id_nfe,
                    'transacao': id_trans,
                    'diff': diff_valor,
                    'severidade': 'MEDIA',
                    'descricao': f"NFe {id_nfe} | Diferença de R$ {diff_valor:,.2f} entre NFe e transação {id_trans} (Tolerância: R$ {tolerancia_abs:,.2f})."
                })

        return inconsistencias

    def _calcular_score_risco(self, anomalias: Dict) -> int:
        """Calcula score de risco (0-100, onde 100 = muito arriscado)"""

        score = 0

        # Valores atípicos (peso: 2 por item)
        score += len(anomalias['valores_atipicos']) * 2

        # Anomalias temporais (peso: 3 por item)
        score += len(anomalias['temporal']) * 3

        # Inconsistências (inclui TIPO_INCOMPATIVEL_ACEITO, peso: 4 por item)
        score += len(anomalias['inconsistencias']) * 4

        # NFes suspeitas (peso: 5 por item)
        score += len(anomalias['sem_match_suspeito']) * 5

        # Duplicatas (peso: 10 por item - MUITO GRAVE!)
        score += len(anomalias['duplicatas_potenciais']) * 10

        # Limitar a 100
        return min(score, 100)

    def _determinar_nivel_alerta(self, score: int) -> str:
        """Determina nível de alerta baseado no score"""

        if score >= 40:
            return 'CRITICO'
        elif score >= 25:
            return 'ALTO'
        elif score >= 10:
            return 'MEDIO'
        else:
            return 'BAIXO'

    def _analisar_com_ia(
            self,
            anomalias: Dict,
            nfes: List[Dict],
            transacoes: List[Dict]
    ) -> Dict:
        """Usa IA para analisar anomalias e gerar insights"""

        # Preparar resumo para a IA
        resumo = f"""Analise estas anomalias detectadas em conciliação bancária:

**Estatísticas:**
- Total NFes: {len(nfes)}
- Total Transações: {len(transacoes)}
- Score de Risco: {anomalias['score']}/100
- Nível de Alerta: {anomalias['nivel_alerta']}

**Anomalias Detectadas:**
- Valores atípicos: {len(anomalias['valores_atipicos'])}
- Problemas temporais: {len(anomalias['temporal'])}
- NFes suspeitas sem match: {len(anomalias['sem_match_suspeito'])}
- Duplicatas potenciais: {len(anomalias['duplicatas_potenciais'])}
- Inconsistências: {len(anomalias['inconsistencias'])}

Gere análise em JSON:
{{
  "gravidade": "Baixa/Média/Alta/Crítica",
  "principais_riscos": ["Risco 1", "Risco 2"],
  "acoes_imediatas": ["Ação 1", "Ação 2"],
  "recomendacoes": ["Rec 1", "Rec 2"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": resumo}],
                temperature=0.4,
                max_tokens=400
            )

            texto = response.choices[0].message.content.strip()

            # Extrair JSON
            if '```' in texto:
                texto = texto.split('```')[1].replace('json', '').strip()

            inicio = texto.find('{')
            fim = texto.rfind('}') + 1

            if inicio >= 0 and fim > inicio:
                return json.loads(texto[inicio:fim])

        except Exception as e:
            print(f"⚠️ Erro na análise IA: {str(e)}")

        # Fallback
        return {
            "gravidade": anomalias['nivel_alerta'].capitalize(),
            "principais_riscos": ["Revisar anomalias detectadas"],
            "acoes_imediatas": ["Validar itens identificados"],
            "recomendacoes": ["Verificar documentação"]
        }


def criar_detector(api_key: str = None):
    """Cria instância do detector"""
    return DetectorAnomalias(api_key=api_key)