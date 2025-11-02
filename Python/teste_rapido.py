"""
Teste Rápido - Diagnóstico do Sistema
Execute este arquivo para verificar se tudo está funcionando
"""

import os
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

print("=" * 60)
print("🧪 TESTE DE DIAGNÓSTICO DO SISTEMA")
print("=" * 60)

# 1. Verificar API Key
print("\n1️⃣ Verificando API Key...")
api_key = os.getenv('GROQ_API_KEY')
if api_key:
    print(f"   ✅ API Key encontrada: {api_key[:20]}...")
else:
    print("   ❌ API Key NÃO encontrada!")
    print("   → Crie arquivo .env com: GROQ_API_KEY=sua_chave")

# 2. Testar imports
print("\n2️⃣ Testando imports...")

try:
    from agente_llm_groq import criar_agente

    print("   ✅ agente_llm_groq importado")
except Exception as e:
    print(f"   ❌ Erro ao importar agente: {str(e)}")

try:
    from explicador_ia import criar_explicador

    print("   ✅ explicador_ia importado")
except Exception as e:
    print(f"   ❌ Erro ao importar explicador: {str(e)}")

try:
    from detector_anomalias import criar_detector

    print("   ✅ detector_anomalias importado")
except Exception as e:
    print(f"   ❌ Erro ao importar detector: {str(e)}")

try:
    from chatbot_assistente import criar_chatbot

    print("   ✅ chatbot_assistente importado")
except Exception as e:
    print(f"   ❌ Erro ao importar chatbot: {str(e)}")

# 3. Testar Groq
print("\n3️⃣ Testando conexão com Groq...")
if api_key:
    try:
        from groq import Groq

        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Responda apenas: OK"}],
            max_tokens=10
        )

        print(f"   ✅ Groq funcionando! Resposta: {response.choices[0].message.content}")
    except Exception as e:
        print(f"   ❌ Erro ao conectar com Groq: {str(e)}")
else:
    print("   ⏭️ Pulando (sem API key)")

# 4. Testar agente com dados de exemplo
print("\n4️⃣ Testando agente com dados de exemplo...")
if api_key:
    try:
        from agente_llm_groq import criar_agente

        # Dados de teste
        nfes_teste = [
            {
                'numero': '12345',
                'valor_total': 1000.00,
                'data_emissao': '2024-01-10',
                'tipo_operacao': 'ENTRADA',
                'nome_emitente': 'Fornecedor Teste'
            }
        ]

        transacoes_teste = [
            {
                'id': 'TRANS_001',
                'valor': -1000.00,
                'data': '2024-01-11',
                'tipo': 'DEBITO',
                'descricao': 'Pagamento Teste'
            }
        ]

        agente = criar_agente()
        resultados = agente.fazer_conciliacao(nfes_teste, transacoes_teste)

        print(f"   ✅ Agente funcionando!")
        print(f"   → Matches: {len(resultados.get('matches_confirmados', []))}")
        print(f"   → Sugestões: {len(resultados.get('sugestoes', []))}")
        print(f"   → Sem match: {len(resultados.get('sem_match', []))}")

    except Exception as e:
        print(f"   ❌ Erro ao testar agente: {str(e)}")
else:
    print("   ⏭️ Pulando (sem API key)")

# Resultado final
print("\n" + "=" * 60)
print("📊 RESULTADO DO DIAGNÓSTICO")
print("=" * 60)

if api_key:
    print("✅ Sistema pronto para uso!")
    print("\n💡 Próximos passos:")
    print("   1. Execute: streamlit run app_v1_com_llm.py")
    print("   2. Faça upload de NFes e Extrato")
    print("   3. Clique em 'Processar com IA Avançada'")
else:
    print("❌ Configure a API Key primeiro!")
    print("\n💡 Como configurar:")
    print("   1. Acesse: https://console.groq.com/keys")
    print("   2. Crie uma conta (grátis)")
    print("   3. Gere uma API Key")
    print("   4. Crie arquivo .env na raiz do projeto")
    print("   5. Adicione: GROQ_API_KEY=sua_chave_aqui")
    print("   6. Execute este teste novamente")

print("=" * 60)