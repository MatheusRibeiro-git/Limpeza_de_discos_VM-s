from __future__ import annotations  # Adicione esta linha para compatibilidade com Python 3.9

import os
from datetime import datetime, timedelta
from time import sleep
from loguru import logger

# ==============================
# CONFIGURAÇÕES DO SCRIPT
# ==============================

# Lista de pastas a serem limpas.
# Cada item contém:
#   - "caminho": pasta alvo
#   - "data_corte": data limite (YYYY/MM/DD). Arquivos criados ANTES desta data serão excluídos.
# Lista de pastas a serem limpas.
PASTAS_PARA_LIMPAR = [
    {
        "caminho": r"D:/Pasta/Arquivos", # Defina o caminho da pasta que deseja limpar
        "data_dinamica": 30  # Excluir arquivos com mais de 30 dias
    }
]

# Lista de caminhos protegidos (adicione caminhos reais se necessário)
ARQUIVOS_PROTEGIDOS = [
    # Exemplo:
    # r"D:\Pasta\Arquivos\Importante",
]

def caminho_esta_protegido(caminho_completo: str) -> bool:
    """
    Verifica se o caminho informado está dentro de algum caminho protegido.
    A comparação é feita com caminhos normalizados e em minúsculas para evitar diferenças de barra/caixa.
    """
    # Normaliza o caminho completo e deixa tudo em minúsculo pra comparação ficar justa
    caminho_completo_norm = os.path.normpath(caminho_completo).lower()
    for protegida in ARQUIVOS_PROTEGIDOS:
        # Normaliza também o caminho protegido
        protegida_norm = os.path.normpath(protegida).lower()
        # Se o caminho completo começa com o caminho protegido, ele é considerado protegido.
        if caminho_completo_norm.startswith(protegida_norm):
            return True
    return False

def excluir_antigos(caminho: str, data_corte: datetime | None = None, data_dinamica: int | None = None, is_root: bool = True):
    """
    Exclui arquivos criados ANTES da data_corte, de forma recursiva (entra em subpastas).
    - Após excluir arquivos em uma pasta, verifica se ela ficou vazia e a exclui (exceto a pasta raiz).
    - Respeita a lista de caminhos protegidos.
    - Em caso de erro de permissão/lock, contabiliza como 'pulado'.
    Retorna: (deletados, pulados, pastas_deletadas)
    """
    
    # Se não passou data_corte, tenta calcular pela data_dinamica
    if data_corte is None: 
        if data_dinamica is None:
            raise ValueError("É necessário fornecer 'data_corte' ou 'data_dinamica'.")
        else:
            # Calcula a data de corte com base na data dinâmica (dias atrás)
            data_corte = datetime.now() - timedelta(days=data_dinamica)
 
    # Contadores de quantos arquivos/pastas foram deletados ou pulados
    deletados = 0
    pulados = 0
    pastas_deletadas = 0

    print(f"Analisando pasta: {caminho}")

    try:
        # Lista tudo que tem dentro da pasta
        itens = os.listdir(caminho)
    except PermissionError:
        logger.info(f"✗ Sem permissão para acessar a pasta: {caminho}\n")
        return 0, 0, 0
    except FileNotFoundError:
        logger.info(f"✗ Pasta não encontrada (pode ter sido movida/removida): {caminho}\n")
        return 0, 0, 0
    except Exception as e:
        logger.info(f"✗ Erro ao listar itens da pasta '{caminho}': {e}\n")
        return 0, 0, 0

    # Itera sobre os itens na pasta
    for item in itens:
        caminho_completo = os.path.join(caminho, item)

        # Se o caminho estiver em área protegida, pula
        if caminho_esta_protegido(caminho_completo):
            logger.info(f"- Protegida → mantida intacta: {caminho_completo}")
            pulados += 1
            continue

        if os.path.isfile(caminho_completo):
            try:
                # Em Windows, getctime retorna a data de criação.
                data_criacao = datetime.fromtimestamp(os.path.getctime(caminho_completo))

                # Se criado ANTES da data de corte, excluir
                if data_criacao < data_corte:
                    os.remove(caminho_completo)
                    logger.info(f"✓ Excluído arquivo: {caminho_completo}")
                    deletados += 1
                    sleep(0.2)  # pequena espera para não saturar o disco
                else:
                    # Arquivo novo o suficiente → manter
                    logger.info(f"- Muito novo, mantido: {caminho_completo} ({data_criacao.strftime('%Y-%m-%d')})")
                    sleep(0.2)

            except PermissionError:
                # Arquivo em uso/travado ou sem permissão
                logger.info(f"✗ ACESSO NEGADO (travado): {caminho_completo}")
                pulados += 1
                sleep(0.2)
            except Exception as e:
                # Qualquer outra falha inesperada ao tentar remover
                logger.info(f"✗ Erro ao excluir: {caminho_completo} → {e}")
                pulados += 1
                sleep(0.2)

        elif os.path.isdir(caminho_completo):
            # Se for subpasta, entra recursivamente
            logger.info(f"- Entrando na subpasta: {caminho_completo}")
            sub_deletados, sub_pulados, sub_pastas_deletadas = excluir_antigos(caminho_completo, data_corte=data_corte, data_dinamica=data_dinamica, is_root=False)
            deletados += sub_deletados
            pulados += sub_pulados
            pastas_deletadas += sub_pastas_deletadas

    # Após processar todos os itens, verifica se a pasta atual ficou vazia
    # Só exclui se NÃO for a pasta raiz e NÃO estiver protegida
    if not is_root and not caminho_esta_protegido(caminho):
        try:
            itens_restantes = os.listdir(caminho)
            if not itens_restantes:  # Pasta vazia
                os.rmdir(caminho)
                logger.info(f"✓ Excluída pasta vazia: {caminho}")
                pastas_deletadas += 1
                sleep(0.2)
            else:
                logger.info(f"- Pasta não vazia, mantida: {caminho}")
        except PermissionError:
            logger.info(f"✗ ACESSO NEGADO ao excluir pasta: {caminho}")
            pulados += 1
        except Exception as e:
            logger.info(f"✗ Erro ao excluir pasta: {caminho} → {e}")
            pulados += 1

    # Resumo desta pasta (incluindo subpastas)
    logger.info(f"\nResumo da pasta {caminho} (incluindo subpastas):")
    logger.info(f"   Arquivos deletados: {deletados}")
    logger.info(f"   Pastas deletadas: {pastas_deletadas}")
    logger.info(f"   Arquivos/pastas pulados/protegidos: {pulados}\n")

    return deletados, pulados, pastas_deletadas

if __name__ == "__main__": 
    logger.info("=== INICIANDO LIMPEZA AUTOMÁTICA ===\n")

    total_deletados = 0
    total_pulados = 0
    total_pastas_deletadas = 0

    # Percorre todas as pastas configuradas
    for pasta in PASTAS_PARA_LIMPAR:
        data_str = pasta.get('data_corte', None)
        if data_str is not None:
            try:
                # Quebra a string de data no formato YYYY/MM/DD
                ano, mes, dia = map(int, data_str.split('/'))
                data_str = datetime(ano, mes, dia)
                logger.info(f"   Data de corte: {data_str.strftime('%Y-%m-%d')} → exclui arquivos criados ANTES dessa data\n")
            except ValueError:
                # Caso o formato não esteja correto
                logger.info(f"✗ Formato de data inválido: '{data_str}'. Use YYYY/MM/DD\n")
                continue
            
        pasta_alvo = pasta['caminho']

        data_dinamica_2 = pasta.get('data_dinamica', None)

        if os.path.exists(pasta_alvo):
            logger.info(f"Processando pasta principal: {pasta_alvo}")
            
            # Executa a limpeza na pasta alvo (agora recursiva)
            del_count, skip_count, pastas_del_count = excluir_antigos(pasta_alvo, data_corte=data_str, data_dinamica=data_dinamica_2, is_root=True)
            total_deletados += del_count
            total_pulados += skip_count
            total_pastas_deletadas += pastas_del_count

        else:
            logger.info(f"Pasta NÃO ENCONTRADA: {pasta_alvo}\n")

    # Resumo geral
    logger.info("=== LIMPEZA CONCLUÍDA ===")
    logger.info(f"Total geral → Arquivos deletados: {total_deletados} | Pastas deletadas: {total_pastas_deletadas} | Pulados/protegidos: {total_pulados}")
    logger.info("\nDica: se aparecer muitos 'ACESSO NEGADO', pause o OneDrive e rode como Administrador.")

    input("\nPressione Enter para fechar...")