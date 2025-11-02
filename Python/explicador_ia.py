"""
Módulo de Explicações Inteligentes com IA
Gera explicações detalhadas para cada match usando Groq
"""

import os
from typing import Dict, List
from groq import Groq
import json


class ExplicadorIA:
    """
    Gera explicações inteligentes e detalhadas para matches
    usando IA Generativa (Groq Llama 3.3 70B)
    """

    def __init__(self, api_key: str = None):
        """Inicializa o explicador com Groq"""
        self.api_key = api_key or os.getenv('GROQ_API_KEY')

        if not self.api_key:
            raise ValueError("❌ API key do Groq não encontrada!")

        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"

        print("✅ Explicador IA inicializado!")

    def explicar_match(self, match: Dict) -> Dict:
        """
        Gera explicação detalhada para um match específico

        Args:
            match: Dicionário com nfe, transacao e score

        Returns:
            Dict com explicação estruturada
        """

        nfe = match['nfe']
        trans = match['transacao']
        score = match.get('score', 0)

        # Calcular diferenças
        diff_valor = abs(nfe.get('valor_total', 0) - abs(trans.get('valor', 0)))
        diff_valor_pct = (diff_valor / nfe.get('valor_total', 1)) * 100

        # Preparar dados para a IA
        prompt = f"""Você é um especialista em conciliação bancária. Explique de forma clara e objetiva POR QUÊ este match foi identificado.

**NFe #{nfe.get('numero')}:**
- Valor: R$ {nfe.get('valor_total', 0):,.2f}
- Data: {nfe.get('data_emissao')}
- Tipo: {nfe.get('tipo_operacao')}
- Emitente: {nfe.get('nome_emitente', 'N/A')}
- Descrição: {nfe.get('descricao', 'N/A')}

**Transação {trans.get('id')}:**
- Valor: R$ {trans.get('valor', 0):,.2f}
- Data: {trans.get('data')}
- Tipo: {trans.get('tipo')}
- Descrição: {trans.get('descricao', 'N/A')}

**Score do Match:** {score:.1f}%

**Diferenças Identificadas:**
- Diferença de valor: R$ {diff_valor:,.2f} ({diff_valor_pct:.1f}%)

Gere uma explicação em JSON com esta estrutura EXATA:
{{
  "titulo": "Título curto explicativo (max 60 chars)",
  "resumo": "Uma frase resumindo o match (max 100 chars)",
  "porque_match": "Explicação detalhada dos motivos principais (2-3 frases)",
  "pontos_fortes": ["Motivo 1", "Motivo 2", "Motivo 3"],
  "pontos_atencao": ["Ponto 1 se houver", "Ponto 2 se houver"],
  "confianca": "Alta/Média/Baixa",
  "recomendacao": "Ação recomendada (1 frase)"
}}

Seja objetivo, profissional e foque nos FATOS que justificam o match."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=500
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
                explicacao = json.loads(texto[inicio:fim])

                # Adicionar metadados
                explicacao['score'] = score
                explicacao['diff_valor'] = diff_valor
                explicacao['diff_valor_pct'] = diff_valor_pct

                return explicacao
            else:
                return self._explicacao_fallback(match)

        except Exception as e:
            print(f"⚠️ Erro ao gerar explicação: {str(e)}")
            return self._explicacao_fallback(match)

    def explicar_lote(self, matches: List[Dict]) -> List[Dict]:
        """
        Gera explicações para um lote de matches

        Args:
            matches: Lista de matches

        Returns:
            Lista de matches com explicações adicionadas
        """

        print(f"\n🧠 Gerando explicações inteligentes para {len(matches)} matches...")

        matches_explicados = []

        for i, match in enumerate(matches, 1):
            print(f"   📝 Explicando match {i}/{len(matches)}...", end=' ')

            try:
                explicacao = self.explicar_match(match)
                match['explicacao_ia'] = explicacao
                matches_explicados.append(match)
                print("✅")

            except Exception as e:
                print(f"❌ Erro: {str(e)}")
                match['explicacao_ia'] = self._explicacao_fallback(match)
                matches_explicados.append(match)

        print(f"✅ {len(matches_explicados)} explicações geradas!\n")

        return matches_explicados

    def _explicacao_fallback(self, match: Dict) -> Dict:
        """Gera explicação básica em caso de erro"""

        nfe = match['nfe']
        trans = match['transacao']
        score = match.get('score', 0)

        diff_valor = abs(nfe.get('valor_total', 0) - abs(trans.get('valor', 0)))

        if diff_valor < 10:
            confianca = "Alta"
            motivo = "Valores praticamente idênticos"
        elif diff_valor < 100:
            confianca = "Média"
            motivo = "Valores muito próximos (pequena diferença)"
        else:
            confianca = "Baixa"
            motivo = "Valores apresentam diferença significativa"

        return {
            "titulo": f"Match por proximidade de valores (Score: {score:.0f}%)",
            "resumo": f"{motivo} entre NFe e transação",
            "porque_match": f"A NFe #{nfe.get('numero')} e a transação {trans.get('id')} foram relacionadas principalmente devido à proximidade dos valores (diferença de R$ {diff_valor:.2f}).",
            "pontos_fortes": [
                "Valores compatíveis",
                f"Score de confiança: {score:.1f}%"
            ],
            "pontos_atencao": [
                "Explicação gerada automaticamente (modo básico)"
            ],
            "confianca": confianca,
            "recomendacao": "Verificar contexto adicional para confirmar o match",
            "score": score,
            "diff_valor": diff_valor,
            "diff_valor_pct": (diff_valor / nfe.get('valor_total', 1)) * 100
        }

    def gerar_resumo_geral(self, matches_explicados: List[Dict]) -> Dict:
        """
        Gera resumo geral sobre todos os matches explicados

        Args:
            matches_explicados: Lista de matches com explicações

        Returns:
            Dict com resumo geral
        """

        if not matches_explicados:
            return {
                "qualidade_geral": "N/A",
                "principais_padroes": ["Nenhum match para analisar"],
                "alertas": ["Sem dados suficientes"]
            }

        # Preparar dados para análise
        scores = [m.get('score', 0) for m in matches_explicados]
        score_medio = sum(scores) / len(scores) if scores else 0

        alta_confianca = sum(1 for m in matches_explicados
                             if m.get('explicacao_ia', {}).get('confianca') == 'Alta')

        media_confianca = sum(1 for m in matches_explicados
                              if m.get('explicacao_ia', {}).get('confianca') == 'Média')

        prompt = f"""Analise estes resultados de conciliação e gere um resumo executivo:

**Estatísticas:**
- Total de matches: {len(matches_explicados)}
- Score médio: {score_medio:.1f}%
- Alta confiança: {alta_confianca}
- Média confiança: {media_confianca}
- Baixa confiança: {len(matches_explicados) - alta_confianca - media_confianca}

Gere JSON com:
{{
  "qualidade_geral": "Excelente/Boa/Regular/Ruim",
  "principais_padroes": ["Padrão 1", "Padrão 2", "Padrão 3"],
  "alertas": ["Alerta 1 se necessário", "Alerta 2 se necessário"],
  "recomendacao_final": "Recomendação geral"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=300
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
            print(f"⚠️ Erro ao gerar resumo: {str(e)}")

        # Fallback
        if score_medio >= 80:
            qualidade = "Excelente"
        elif score_medio >= 60:
            qualidade = "Boa"
        elif score_medio >= 40:
            qualidade = "Regular"
        else:
            qualidade = "Ruim"

        return {
            "qualidade_geral": qualidade,
            "principais_padroes": [
                f"{alta_confianca} matches de alta confiança",
                f"Score médio de {score_medio:.1f}%"
            ],
            "alertas": [] if alta_confianca > media_confianca else ["Revisar matches de média confiança"],
            "recomendacao_final": "Validar matches antes de finalizar"
        }


def criar_explicador(api_key: str = None):
    """Cria instância do explicador"""
    return ExplicadorIA(api_key=api_key)


# ============================================================================
# TESTE DO EXPLICADOR
# ============================================================================

if __name__ == "__main__":
    print("🧪 Testando Explicador IA...\n")

    # Dados de teste
    match_teste = {
        'nfe': {
            'numero': '12345',
            'valor_total': 2500.00,
            'data_emissao': '2024-01-10',
            'tipo_operacao': 'ENTRADA',
            'nome_emitente': 'Fornecedor Tech LTDA',
            'descricao': 'Compra de equipamentos'
        },
        'transacao': {
            'id': 'TRANS_001',
            'valor': -2500.00,
            'data': '2024-01-11',
            'tipo': 'DEBITO',
            'descricao': 'TED - Fornecedor Tech'
        },
        'score': 95.5
    }

    try:
        # Criar explicador
        explicador = criar_explicador()

        # Gerar explicação
        explicacao = explicador.explicar_match(match_teste)

        print("✅ Explicação gerada:")
        print(json.dumps(explicacao, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")