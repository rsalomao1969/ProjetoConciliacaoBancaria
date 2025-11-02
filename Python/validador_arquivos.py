"""
Módulo de Validação de Arquivos
Valida NFes (XML) e Extratos antes de processar
"""
import xml.etree.ElementTree as ET
import pandas as pd
from typing import Tuple, List


class ValidadorArquivos:
    """Valida arquivos antes do processamento"""

    @staticmethod
    def validar_xml_nfe(arquivo) -> Tuple[bool, str]:
        """
        Valida se XML é uma NFe válida

        Returns:
            (bool, str): (é_valido, mensagem)
        """
        try:
            # Tentar fazer parse do XML
            conteudo = arquivo.read()
            arquivo.seek(0)  # Resetar para processar depois

            root = ET.fromstring(conteudo)

            # Verificar se tem tag NFe
            if 'NFe' not in root.tag and 'nfeProc' not in root.tag:
                return False, "❌ Arquivo não é uma NFe válida"

            # Verificar campos essenciais
            namespaces = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

            # Buscar número da nota
            numero = root.find('.//nfe:nNF', namespaces)
            if numero is None:
                return False, "❌ NFe sem número"

            # Buscar valor
            valor = root.find('.//nfe:vNF', namespaces)
            if valor is None:
                return False, "❌ NFe sem valor"

            return True, "✅ NFe válida"

        except ET.ParseError:
            return False, "❌ XML inválido ou corrompido"
        except Exception as e:
            return False, f"❌ Erro ao validar: {str(e)}"

    @staticmethod
    def validar_extrato_csv(arquivo) -> Tuple[bool, str]:
        """
        Valida se CSV é um extrato válido

        Returns:
            (bool, str): (é_valido, mensagem)
        """
        try:
            # Tentar ler CSV
            df = pd.read_csv(arquivo, encoding='utf-8', sep=None, engine='python')
            arquivo.seek(0)  # Resetar

            # Verificar se tem linhas
            if len(df) == 0:
                return False, "❌ Extrato vazio"

            # Verificar colunas essenciais (flexível)
            colunas = [col.lower() for col in df.columns]

            tem_data = any('data' in col for col in colunas)
            tem_valor = any('valor' in col or 'vlr' in col for col in colunas)
            tem_descricao = any('descr' in col or 'hist' in col for col in colunas)

            if not tem_data:
                return False, "❌ Extrato sem coluna de data"

            if not tem_valor:
                return False, "❌ Extrato sem coluna de valor"

            return True, f"✅ Extrato válido ({len(df)} transações)"

        except pd.errors.EmptyDataError:
            return False, "❌ Arquivo vazio"
        except Exception as e:
            return False, f"❌ Erro ao validar: {str(e)}"

    @staticmethod
    def validar_lote_nfes(arquivos) -> Tuple[List, List]:
        """
        Valida lote de NFes

        Returns:
            (validos, invalidos): listas de arquivos
        """
        validos = []
        invalidos = []

        for arquivo in arquivos:
            eh_valido, msg = ValidadorArquivos.validar_xml_nfe(arquivo)

            if eh_valido:
                validos.append((arquivo, msg))
            else:
                invalidos.append((arquivo.name, msg))

        return validos, invalidos