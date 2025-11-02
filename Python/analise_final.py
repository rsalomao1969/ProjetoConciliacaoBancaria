"""
Módulo de Análise Final com LLM e Gráficos
"""
import json
from groq import Groq
import os
import plotly.graph_objects as go
import plotly.express as px


def gerar_analise_final_llm(resultados: dict, api_key: str = None) -> dict:
    """Gera análise final usando LLM"""

    client = Groq(api_key=api_key or os.getenv('GROQ_API_KEY'))

    # Estatísticas
    stats = {
        'total_nfes': len(resultados.get('matches_confirmados', [])) + len(resultados.get('sem_match', [])),
        'matches': len(resultados.get('matches_confirmados', [])),
        'taxa': 0
    }
    stats['taxa'] = round((stats['matches'] / stats['total_nfes'] * 100) if stats['total_nfes'] > 0 else 0, 1)

    prompt = f"""Analise a conciliação:

Matches: {stats['matches']}/{stats['total_nfes']} ({stats['taxa']}%)

Responda JSON:
{{
  "diagnostico": "texto curto",
  "insights": ["insight 1", "insight 2"],
  "recomendacoes": ["ação 1", "ação 2"]
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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
            analise = json.loads(texto[inicio:fim])
            analise['estatisticas'] = stats
            return analise
    except:
        pass

    return {
        'diagnostico': f"Taxa de {stats['taxa']}%",
        'insights': [f"{stats['matches']} matches encontrados"],
        'recomendacoes': ["Revisar pendências"],
        'estatisticas': stats
    }


def gerar_dados_graficos(resultados: dict) -> dict:
    """Prepara dados para gráficos"""

    matches = resultados.get('matches_confirmados', [])
    sem_match = resultados.get('sem_match', [])
    sugestoes = resultados.get('sugestoes', [])

    return {
        'pizza': {
            'labels': ['Conciliados', 'Sugestões', 'Pendentes'],
            'values': [len(matches), len(sugestoes), len(sem_match)]
        },
        'scores': [m.get('score', 0) for m in matches]
    }


def criar_grafico_pizza(resultados: dict):
    """Cria gráfico de pizza da distribuição"""

    matches = len(resultados.get('matches_confirmados', []))
    sugestoes = len(resultados.get('sugestoes', []))
    sem_match = len(resultados.get('sem_match', []))

    fig = go.Figure(data=[go.Pie(
        labels=['✅ Conciliados', '🤔 Sugestões', '❌ Pendentes'],
        values=[matches, sugestoes, sem_match],
        hole=.3,
        marker_colors=['#00cc66', '#ffaa00', '#ff4444']
    )])

    fig.update_layout(
        title_text="Distribuição dos Resultados",
        height=400
    )

    return fig


def criar_grafico_scores(resultados: dict):
    """Cria gráfico de barras dos scores"""

    matches = resultados.get('matches_confirmados', [])

    if not matches:
        return None

    nfes = [f"NFe {m['nfe'].get('numero', 'N/A')}" for m in matches]
    scores = [m.get('score', 0) for m in matches]

    fig = go.Figure(data=[go.Bar(
        x=nfes,
        y=scores,
        marker_color='#00cc66',
        text=[f"{s:.0f}%" for s in scores],
        textposition='auto'
    )])

    fig.update_layout(
        title_text="Scores de Confiança por Match",
        xaxis_title="NFe",
        yaxis_title="Score (%)",
        height=400,
        yaxis_range=[0, 100]
    )

    return fig


def criar_grafico_valores(resultados: dict, nfes: list):
    """Cria gráfico de valores conciliados vs pendentes"""

    matches = resultados.get('matches_confirmados', [])

    valor_total = sum(n.get('valor_total', 0) for n in nfes)
    valor_conciliado = sum(m['nfe'].get('valor_total', 0) for m in matches)
    valor_pendente = valor_total - valor_conciliado

    fig = go.Figure(data=[go.Bar(
        x=['Total NFes', 'Conciliado', 'Pendente'],
        y=[valor_total, valor_conciliado, valor_pendente],
        marker_color=['#3366cc', '#00cc66', '#ff4444'],
        text=[f"R$ {v:,.2f}" for v in [valor_total, valor_conciliado, valor_pendente]],
        textposition='auto'
    )])

    fig.update_layout(
        title_text="Valores: Total vs Conciliado",
        yaxis_title="Valor (R$)",
        height=400
    )

    return fig