"""
Gerador de Relatório de Conciliação
Versão Corrigida
"""

from datetime import datetime
from typing import List, Dict


class ReportGenerator:
    """Gerador de relatórios de conciliação"""

    def gerar_relatorio_completo(
            self,
            matches_confirmados: List[Dict],
            sugestoes: List[Dict],
            sem_match: List[Dict],
            nfes: List[Dict],
            transacoes: List[Dict]
    ) -> str:
        """
        Gera relatório completo de conciliação

        Args:
            matches_confirmados: Lista de matches confirmados
            sugestoes: Lista de sugestões
            sem_match: Lista de NFes sem match
            nfes: Lista de todas as NFes
            transacoes: Lista de todas as transações

        Returns:
            String com o relatório formatado
        """

        linhas = []

        # Cabeçalho
        linhas.append("=" * 80)
        linhas.append("RELATÓRIO DE CONCILIAÇÃO BANCÁRIA - SISTEMA CORRIGIDO")
        linhas.append("=" * 80)
        linhas.append(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        linhas.append(f"Status: CONCLUÍDO")
        linhas.append("")

        # Estatísticas Gerais (CORRIGIDO!)
        linhas.append("ESTATÍSTICAS GERAIS")
        linhas.append("-" * 80)
        linhas.append(f"Total de NFes: {len(nfes)}")
        linhas.append(f"Total de Transações: {len(transacoes)}")
        linhas.append("")

        # Categorização (CORRIGIDO!)
        total_nfes = len(nfes)
        pct_confirmados = (len(matches_confirmados) / total_nfes * 100) if total_nfes else 0
        pct_sugestoes = (len(sugestoes) / total_nfes * 100) if total_nfes else 0
        pct_sem_match = (len(sem_match) / total_nfes * 100) if total_nfes else 0

        linhas.append("CATEGORIZAÇÃO:")
        linhas.append(f"✅ Confirmados: {len(matches_confirmados)} ({pct_confirmados:.1f}%)")
        linhas.append(f"🤔 Sugestões: {len(sugestoes)} ({pct_sugestoes:.1f}%)")
        linhas.append(f"❌ Sem Match: {len(sem_match)} ({pct_sem_match:.1f}%)")
        linhas.append("")

        # Matches Confirmados
        if matches_confirmados:
            linhas.append("=" * 80)
            linhas.append("✅ MATCHES CONFIRMADOS")
            linhas.append("=" * 80)
            linhas.append("")

            for i, match in enumerate(matches_confirmados, 1):
                nfe = match['nfe']
                trans = match['transacao']
                score = match['score']
                detalhes = match.get('detalhes', {})

                linhas.append(f"{i}. NFe: {nfe.get('numero', 'N/A')} - R$ {nfe.get('valor_total', 0):.2f} "
                              f"↔ {trans.get('id', 'N/A')} - R$ {trans.get('valor', 0):.2f}")
                linhas.append(f"   Score: {score:.1f}%")
                linhas.append(f"   Data NFe: {nfe.get('data_emissao', 'N/A')} | "
                              f"Data Trans: {trans.get('data', 'N/A')}")
                linhas.append(f"   Tipo NFe: {nfe.get('tipo_operacao', 'N/A')} | "
                              f"Tipo Trans: {trans.get('tipo', 'N/A')}")
                linhas.append(f"   Emitente: {nfe.get('nome_emitente', 'N/A')}")
                linhas.append(f"   Descrição Trans: {trans.get('descricao', 'N/A')}")

                # Detalhes dos scores
                if detalhes:
                    linhas.append(f"   Detalhes: Valor={detalhes.get('score_valor', 0):.1f}% | "
                                  f"Data={detalhes.get('score_data', 0):.1f}% | "
                                  f"Tipo={detalhes.get('score_tipo', 0):.1f}% | "
                                  f"Texto={detalhes.get('score_texto', 0):.1f}%")

                linhas.append("")

        # Sugestões
        if sugestoes:
            linhas.append("=" * 80)
            linhas.append("🤔 SUGESTÕES (Requer Revisão Manual)")
            linhas.append("=" * 80)
            linhas.append("")

            for i, match in enumerate(sugestoes, 1):
                nfe = match['nfe']
                trans = match['transacao']
                score = match['score']

                linhas.append(f"{i}. NFe: {nfe.get('numero', 'N/A')} - R$ {nfe.get('valor_total', 0):.2f} "
                              f"↔ {trans.get('id', 'N/A')} - R$ {trans.get('valor', 0):.2f}")
                linhas.append(f"   Score: {score:.1f}%")
                linhas.append(f"   Data NFe: {nfe.get('data_emissao', 'N/A')} | "
                              f"Data Trans: {trans.get('data', 'N/A')}")
                linhas.append("")

        # Sem Match
        if sem_match:
            linhas.append("=" * 80)
            linhas.append("❌ SEM MATCH")
            linhas.append("=" * 80)
            linhas.append("")

            for i, item in enumerate(sem_match, 1):
                nfe = item['nfe']
                motivo = item.get('motivo', 'Score insuficiente')

                linhas.append(f"{i}. NFe: {nfe.get('numero', 'N/A')} - R$ {nfe.get('valor_total', 0):.2f}")
                linhas.append(f"   Data: {nfe.get('data_emissao', 'N/A')} | "
                              f"Tipo: {nfe.get('tipo_operacao', 'N/A')}")
                linhas.append(f"   Emitente: {nfe.get('nome_emitente', 'N/A')}")
                linhas.append(f"   Motivo: {motivo}")
                linhas.append("")

        # Transações Não Conciliadas (CORRIGIDO!)
        linhas.append("=" * 80)
        linhas.append("⚠️ TRANSAÇÕES NÃO CONCILIADAS")
        linhas.append("=" * 80)
        linhas.append("")

        # Coletar IDs das transações usadas
        trans_usadas = set()
        for match in matches_confirmados:
            trans_usadas.add(match['transacao']['id'])
        for match in sugestoes:
            trans_usadas.add(match['transacao']['id'])

        # Filtrar transações não usadas
        trans_nao_conciliadas = [
            t for t in transacoes
            if t['id'] not in trans_usadas
        ]

        if trans_nao_conciliadas:
            linhas.append(f"{len(trans_nao_conciliadas)} transação(ões) sem NFe correspondente:")
            linhas.append("")

            for i, trans in enumerate(trans_nao_conciliadas, 1):
                linhas.append(f"{i}. {trans.get('id', 'N/A')} - R$ {trans.get('valor', 0):.2f}")
                linhas.append(f"   Data: {trans.get('data', 'N/A')} | Tipo: {trans.get('tipo', 'N/A')}")
                linhas.append(f"   Descrição: {trans.get('descricao', 'N/A')}")
                linhas.append("")
        else:
            linhas.append("✅ Todas as transações foram conciliadas!")
            linhas.append("")

        # Análise Geral
        linhas.append("=" * 80)
        linhas.append("🎯 ANÁLISE GERAL E CONCLUSÕES")
        linhas.append("=" * 80)
        linhas.append("")

        linhas.append("1. 📊 RESUMO EXECUTIVO")

        # Qualidade da conciliação
        if pct_confirmados >= 80:
            qualidade = "EXCELENTE ✅"
            mensagem = "Alta taxa de conciliação automática."
        elif pct_confirmados >= 60:
            qualidade = "BOA ✅"
            mensagem = "Boa taxa de conciliação, mas há espaço para melhoria."
        elif pct_confirmados >= 40:
            qualidade = "REGULAR ⚠️"
            mensagem = "Taxa de conciliação mediana. Requer atenção."
        else:
            qualidade = "BAIXA ⚠️"
            mensagem = "Baixa taxa de conciliação automática. Requer atenção urgente."

        linhas.append(f"   Qualidade da Conciliação: {qualidade}")
        linhas.append(f"   {mensagem}")
        linhas.append(f"   Taxa de Sucesso: {pct_confirmados:.1f}% de conciliação automática")
        linhas.append(f"   Taxa de Revisão: {pct_sugestoes:.1f}% necessitam análise")
        linhas.append(f"   Pendências: {pct_sem_match:.1f}% sem correspondência")
        linhas.append("")

        # Recomendações
        linhas.append("2. 🎯 RECOMENDAÇÕES")
        linhas.append("")

        if sugestoes:
            linhas.append(f"   ► Revisar manualmente as {len(sugestoes)} sugestões")

        if sem_match:
            linhas.append(f"   ► Investigar os {len(sem_match)} itens sem match")

        if trans_nao_conciliadas:
            linhas.append(f"   ► Verificar {len(trans_nao_conciliadas)} transações sem NFe")

        if pct_confirmados < 80:
            linhas.append("   ► Considerar ajustes nas regras de matching")
            linhas.append("   ► Validar qualidade dos dados de entrada")

        if not sugestoes and not sem_match:
            linhas.append("   ✅ Nenhuma ação necessária - 100% de conciliação!")

        linhas.append("")

        # Rodapé
        linhas.append("=" * 80)
        linhas.append(f"📌 FIM DO RELATÓRIO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        linhas.append("=" * 80)

        return '\n'.join(linhas)


# ============================================================================
# TESTE DO GERADOR
# ============================================================================

if __name__ == "__main__":
    # Dados de teste
    matches = [
        {
            'nfe': {'numero': '001', 'valor_total': 2500.00, 'data_emissao': '2024-01-10',
                    'tipo_operacao': 'ENTRADA', 'nome_emitente': 'Fornecedor'},
            'transacao': {'id': 'TRANS_001', 'valor': -2500.00, 'data': '2024-01-11',
                          'tipo': 'DEBITO', 'descricao': 'Pagamento'},
            'score': 95.5,
            'detalhes': {'score_valor': 100, 'score_data': 95, 'score_tipo': 100, 'score_texto': 80}
        }
    ]

    nfes = [{'numero': '001', 'valor_total': 2500.00}]
    transacoes = [{'id': 'TRANS_001', 'valor': -2500.00}, {'id': 'TRANS_002', 'valor': -100.00}]

    generator = ReportGenerator()
    relatorio = generator.gerar_relatorio_completo(
        matches_confirmados=matches,
        sugestoes=[],
        sem_match=[],
        nfes=nfes,
        transacoes=transacoes
    )

    print("✅ Relatório gerado:")
    print(relatorio[:500])
    print("...")