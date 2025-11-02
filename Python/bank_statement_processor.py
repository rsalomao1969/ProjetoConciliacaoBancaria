"""
Processador de Extratos Bancários
Suporta formatos: CSV, TXT, OFX
"""

import csv
import io
from typing import List, Dict


class BankStatementProcessor:
    """Processador de extratos bancários"""

    def processar_csv(self, arquivo) -> List[Dict]:
        """
        Processa arquivo CSV de extrato bancário
        """
        transacoes = []

        try:
            # Ler conteúdo
            if hasattr(arquivo, 'read'):
                conteudo = arquivo.read()
            else:
                conteudo = arquivo

            # Converter para string se for bytes
            if isinstance(conteudo, bytes):
                conteudo = conteudo.decode('utf-8')

            # Criar StringIO
            arquivo_io = io.StringIO(conteudo)

            # Ler CSV
            reader = csv.DictReader(arquivo_io)

            for i, row in enumerate(reader, 1):
                try:
                    transacao = self._processar_linha_csv(row, i)
                    if transacao:
                        transacoes.append(transacao)
                except Exception as e:
                    print(f"⚠️  Erro na linha {i}: {str(e)}")
                    continue

        except Exception as e:
            print(f"Erro ao processar CSV: {str(e)}")
            raise

        return transacoes

    def _processar_linha_csv(self, row: Dict, linha: int) -> Dict:
        """Processa uma linha do CSV"""

        # Tentar diferentes formatos de campos
        trans_id = (
                row.get('id') or
                row.get('ID') or
                row.get('trans_id') or
                row.get('transacao_id') or
                f"TRANS_{linha:04d}"
        )

        data = (
                row.get('data') or
                row.get('Data') or
                row.get('data_trans') or
                row.get('date') or
                ''
        )

        # CAPTURA DO RÓTULO BRUTO
        rotulo_bruto = (
                row.get('tipo') or
                row.get('Tipo') or
                row.get('tipo_trans') or
                row.get('type') or
                'N/A'  # Usamos N/A como fallback de rótulo
        ).strip().upper()

        valor_str = (
                row.get('valor') or
                row.get('Valor') or
                row.get('value') or
                row.get('amount') or
                '0'
        )

        # Limpar e converter valor
        valor_str = str(valor_str).replace('R$', '').strip()

        # Detectar formato: se tem vírgula, é formato brasileiro (1.234,56)
        if ',' in valor_str:
            valor_str = valor_str.replace('.', '').replace(',', '.')

        try:
            valor = float(valor_str)
        except:
            valor = 0.0

        # Lógica de normalização do TIPO baseada no sinal do VALOR (Para o LLM)
        if valor < 0:
            tipo_normalizado = 'DEBITO'
        elif valor > 0:
            tipo_normalizado = 'CREDITO'
        else:
            tipo_normalizado = 'INDEFINIDO'

        tipo_final = tipo_normalizado

        descricao = (
                row.get('descricao') or
                row.get('Descricao') or
                row.get('description') or
                row.get('memo') or
                ''
        )

        documento = (
                row.get('documento') or
                row.get('Documento') or
                row.get('cnpj') or
                row.get('cpf') or
                ''
        )

        saldo_str = row.get('saldo', '0')
        try:
            saldo = float(saldo_str)
        except:
            saldo = 0.0

        return {
            'id': trans_id.strip(),
            'data': data.strip(),
            'tipo': tipo_final,
            'rotulo_extrato_original': rotulo_bruto,  # NOVO CAMPO: Para verificação de anomalia
            'valor': valor,
            'descricao': descricao.strip(),
            'documento': documento.strip(),
            'saldo': saldo
        }

    def processar_ofx(self, arquivo) -> List[Dict]:
        """
        Processa arquivo OFX de extrato bancário
        """
        transacoes = []

        try:
            # Ler conteúdo
            if hasattr(arquivo, 'read'):
                conteudo = arquivo.read()
            else:
                conteudo = arquivo

            if isinstance(conteudo, bytes):
                conteudo = conteudo.decode('utf-8', errors='ignore')

            # Parsear OFX (formato simplificado)
            linhas = conteudo.split('\n')

            transacao_atual = {}
            dentro_transacao = False

            for linha in linhas:
                linha = linha.strip()

                if '<STMTTRN>' in linha:
                    dentro_transacao = True
                    transacao_atual = {}

                elif '</STMTTRN>' in linha:
                    dentro_transacao = False
                    if transacao_atual:
                        transacoes.append(self._normalizar_transacao_ofx(transacao_atual))
                    transacao_atual = {}

                elif dentro_transacao:
                    # Extrair tags
                    if '<TRNTYPE>' in linha:
                        transacao_atual['tipo'] = linha.replace('<TRNTYPE>', '').strip()
                    elif '<DTPOSTED>' in linha:
                        transacao_atual['data'] = linha.replace('<DTPOSTED>', '').strip()
                    elif '<TRNAMT>' in linha:
                        transacao_atual['valor'] = linha.replace('<TRNAMT>', '').strip()
                    elif '<FITID>' in linha:
                        transacao_atual['id'] = linha.replace('<FITID>', '').strip()
                    elif '<MEMO>' in linha:
                        transacao_atual['descricao'] = linha.replace('<MEMO>', '').strip()

        except Exception as e:
            print(f"Erro ao processar OFX: {str(e)}")
            raise

        return transacoes

    def _normalizar_transacao_ofx(self, trans_ofx: Dict) -> Dict:
        """Normaliza transação do formato OFX"""

        # Converter data (YYYYMMDD → YYYY-MM-DD)
        data = trans_ofx.get('data', '')
        if len(data) >= 8:
            data_formatada = f"{data[0:4]}-{data[4:6]}-{data[6:8]}"
        else:
            data_formatada = data

        # Converter valor
        try:
            valor = float(trans_ofx.get('valor', '0'))
        except:
            valor = 0.0

        # Rótulo Bruto do OFX (TRNTYPE)
        rotulo_bruto = trans_ofx.get('tipo', '').upper()

        # NORMALIZAÇÃO: O tipo é determinado pelo sinal do valor
        if valor < 0:
            tipo_normalizado = 'DEBITO'
        elif valor > 0:
            tipo_normalizado = 'CREDITO'
        else:
            tipo_normalizado = 'INDEFINIDO'

        return {
            'id': trans_ofx.get('id', ''),
            'data': data_formatada,
            'tipo': tipo_normalizado,
            'rotulo_extrato_original': rotulo_bruto,  # NOVO CAMPO: Para verificação de anomalia
            'valor': valor,
            'descricao': trans_ofx.get('descricao', ''),
            'documento': '',
            'saldo': 0.0
        }


# ============================================================================
# TESTE DO PROCESSADOR
# ============================================================================

if __name__ == "__main__":
    # Teste com CSV
    csv_test = """id,data,tipo,valor,descricao,documento,saldo
TRANS_001,2024-01-11,DEBITO,-2500.00,TED Fornecedor Tech,12.345.678/0001-90,45000.00
TRANS_002,2024-01-13,CREDITO,3805.50,PIX Cliente Premium,11.222.333/0001-45,48805.50"""

    processor = BankStatementProcessor()
    transacoes = processor.processar_csv(csv_test)

    if transacoes and len(transacoes) == 2:
        print("✅ Teste CSV passou!")
        print(f"Transações processadas: {len(transacoes)}")
        for t in transacoes:
            print(f"  - {t['id']}: R$ {t['valor']} ({t['tipo']}) [Original: {t['rotulo_extrato_original']}]")
    else:
        print("❌ Teste CSV falhou!")