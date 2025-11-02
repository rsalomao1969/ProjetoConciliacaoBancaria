"""
Processador de Notas Fiscais Eletrônicas (NFe)
Suporta formato XML padrão SEFAZ (NFe 4.0)
"""

import xml.etree.ElementTree as ET
from typing import List, Dict
import io


class NFEProcessor:
    """Processador de NFes em formato XML"""

    def __init__(self):
        self.namespace = {
            'nfe': 'http://www.portalfiscal.inf.br/nfe'
        }

    def processar_xml(self, arquivo) -> List[Dict]:
        """
        Processa arquivo XML e extrai dados das NFes

        Args:
            arquivo: Arquivo XML (file-like object ou bytes)

        Returns:
            Lista de dicionários com dados das NFes
        """
        nfes = []

        try:
            # Ler conteúdo do arquivo
            if hasattr(arquivo, 'read'):
                conteudo = arquivo.read()
            else:
                conteudo = arquivo

            # Converter para string se for bytes
            if isinstance(conteudo, bytes):
                conteudo = conteudo.decode('utf-8')

            # Parsear XML
            root = ET.fromstring(conteudo)

            # Verificar se é um lote ou NFe única
            if 'loteNFe' in root.tag:
                # É um lote - processar múltiplas NFes
                nfe_procs = root.findall('.//nfe:nfeProc', self.namespace)
                for nfe_proc in nfe_procs:
                    nfe_data = self._extrair_dados_nfe(nfe_proc)
                    if nfe_data:
                        nfes.append(nfe_data)

            elif 'nfeProc' in root.tag:
                # É uma NFe única
                nfe_data = self._extrair_dados_nfe(root)
                if nfe_data:
                    nfes.append(nfe_data)

            elif 'NFe' in root.tag:
                # É NFe sem protocolo
                nfe_data = self._extrair_dados_nfe_simples(root)
                if nfe_data:
                    nfes.append(nfe_data)

            else:
                # Tentar encontrar NFe no XML
                nfe_elem = root.find('.//nfe:NFe', self.namespace)
                if nfe_elem is not None:
                    nfe_data = self._extrair_dados_nfe_simples(nfe_elem)
                    if nfe_data:
                        nfes.append(nfe_data)

        except Exception as e:
            print(f"Erro ao processar XML: {str(e)}")
            raise

        return nfes

    def _extrair_dados_nfe(self, nfe_proc) -> Dict:
        """Extrai dados de uma NFe completa (com protocolo)"""
        try:
            # Encontrar NFe
            nfe = nfe_proc.find('.//nfe:NFe', self.namespace)
            if nfe is None:
                nfe = nfe_proc.find('.//NFe')

            if nfe is None:
                return None

            # Encontrar infNfe
            inf_nfe = nfe.find('.//nfe:infNfe', self.namespace)
            if inf_nfe is None:
                inf_nfe = nfe.find('.//infNfe')

            if inf_nfe is None:
                return None

            # Extrair chave (do atributo Id)
            chave = inf_nfe.get('Id', '')
            if chave.startswith('NFe'):
                chave = chave[3:]  # Remove "NFe" do início

            # Extrair dados básicos
            ide = inf_nfe.find('.//nfe:ide', self.namespace) or inf_nfe.find('.//ide')
            emit = inf_nfe.find('.//nfe:emit', self.namespace) or inf_nfe.find('.//emit')
            dest = inf_nfe.find('.//nfe:dest', self.namespace) or inf_nfe.find('.//dest')
            total = inf_nfe.find('.//nfe:total', self.namespace) or inf_nfe.find('.//total')

            # Número e série
            numero = self._get_text(ide, 'nNF')
            serie = self._get_text(ide, 'serie', '1')

            # Data de emissão
            data_emissao = self._get_text(ide, 'dhEmi')
            if 'T' in data_emissao:
                data_emissao = data_emissao.split('T')[0]  # Pegar só a data

            # Tipo de operação (0=Entrada, 1=Saída)
            tpnf = self._get_text(ide, 'tpNF', '0')
            tipo_operacao = 'ENTRADA' if tpnf == '0' else 'SAIDA' # CORREÇÃO: Mapeamento de 0 para ENTRADA e 1 para SAIDA

            # Valor total
            icms_tot = total.find('.//nfe:ICMSTot', self.namespace) or total.find('.//ICMSTot')
            valor_total = float(self._get_text(icms_tot, 'vNF', '0'))

            # Emitente
            nome_emitente = self._get_text(emit, 'xNome')
            cnpj_emitente = self._get_text(emit, 'CNPJ')

            # Destinatário
            nome_destinatario = self._get_text(dest, 'xNome')
            cnpj_destinatario = self._get_text(dest, 'CNPJ')

            # Natureza da operação
            nat_op = self._get_text(ide, 'natOp', '')

            return {
                'chave': chave,
                'numero': numero,
                'serie': serie,
                'data_emissao': data_emissao,
                'tipo_operacao': tipo_operacao,
                'valor_total': valor_total,
                'nome_emitente': nome_emitente,
                'cnpj_emitente': cnpj_emitente,
                'nome_destinatario': nome_destinatario,
                'cnpj_destinatario': cnpj_destinatario,
                'descricao': nat_op,
                'tipo': tipo_operacao  # Compatibilidade
            }

        except Exception as e:
            print(f"Erro ao extrair dados da NFe: {str(e)}")
            return None

    def _extrair_dados_nfe_simples(self, nfe_elem) -> Dict:
        """Extrai dados de NFe sem protocolo"""
        try:
            inf_nfe = nfe_elem.find('.//nfe:infNfe', self.namespace) or nfe_elem.find('.//infNfe')

            if inf_nfe is None:
                return None

            # Extrair chave
            chave = inf_nfe.get('Id', '')
            if chave.startswith('NFe'):
                chave = chave[3:]

            # Dados básicos
            ide = inf_nfe.find('.//nfe:ide', self.namespace) or inf_nfe.find('.//ide')
            emit = inf_nfe.find('.//nfe:emit', self.namespace) or inf_nfe.find('.//emit')
            dest = inf_nfe.find('.//nfe:dest', self.namespace) or inf_nfe.find('.//dest')
            total = inf_nfe.find('.//nfe:total', self.namespace) or inf_nfe.find('.//total')

            numero = self._get_text(ide, 'nNF')
            serie = self._get_text(ide, 'serie', '1')

            data_emissao = self._get_text(ide, 'dhEmi')
            if 'T' in data_emissao:
                data_emissao = data_emissao.split('T')[0]

            # Tipo de operação (0=Entrada, 1=Saída)
            tpnf = self._get_text(ide, 'tpNF', '0')
            tipo_operacao = 'ENTRADA' if tpnf == '0' else 'SAIDA'

            icms_tot = total.find('.//nfe:ICMSTot', self.namespace) or total.find('.//ICMSTot')
            valor_total = float(self._get_text(icms_tot, 'vNF', '0'))

            nome_emitente = self._get_text(emit, 'xNome')
            cnpj_emitente = self._get_text(emit, 'CNPJ')

            nome_destinatario = self._get_text(dest, 'xNome')
            cnpj_destinatario = self._get_text(dest, 'CNPJ')

            nat_op = self._get_text(ide, 'natOp', '')

            return {
                'chave': chave,
                'numero': numero,
                'serie': serie,
                'data_emissao': data_emissao,
                'tipo_operacao': tipo_operacao,
                'valor_total': valor_total,
                'nome_emitente': nome_emitente,
                'cnpj_emitente': cnpj_emitente,
                'nome_destinatario': nome_destinatario,
                'cnpj_destinatario': cnpj_destinatario,
                'descricao': nat_op,
                'tipo': tipo_operacao
            }

        except Exception as e:
            print(f"Erro ao extrair NFe simples: {str(e)}")
            return None

    def _get_text(self, parent, tag, default=''):
        """Extrai texto de um elemento XML"""
        if parent is None:
            return default

        # Tentar com namespace
        elem = parent.find(f'.//nfe:{tag}', self.namespace)
        if elem is None:
            # Tentar sem namespace
            elem = parent.find(f'.//{tag}')

        if elem is not None and elem.text:
            return elem.text.strip()

        return default


# ============================================================================
# TESTE DO PROCESSADOR
# ============================================================================

if __name__ == "__main__":
    # Teste básico
    xml_test = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
  <NFe>
    <infNfe Id="NFe35240123456789000198550010000000011234567890" versao="4.00">
      <ide>
        <nNF>1</nNF>
        <serie>1</serie>
        <dhEmi>2024-01-10T10:00:00-03:00</dhEmi>
        <tpNF>0</tpNF>
        <natOp>COMPRA</natOp>
      </ide>
      <emit>
        <CNPJ>12345678000190</CNPJ>
        <xNome>Fornecedor Teste</xNome>
      </emit>
      <dest>
        <CNPJ>98765432000110</CNPJ>
        <xNome>Minha Empresa</xNome>
      </dest>
      <total>
        <ICMSTot>
          <vNF>2500.00</vNF>
        </ICMSTot>
      </total>
    </infNfe>
  </NFe>
</nfeProc>"""

    processor = NFEProcessor()
    nfes = processor.processar_xml(xml_test)

    if nfes:
        print("✅ Teste passou!")
        print(f"NFe processada: {nfes[0]}")
    else:
        print("❌ Teste falhou!")