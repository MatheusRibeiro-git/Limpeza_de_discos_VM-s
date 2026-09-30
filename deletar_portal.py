import os
from datetime import datetime, timedelta
from time import sleep
from typing import Optional, Tuple
from loguru import logger

# ==============================
# CONFIGURAÇÕES DO SCRIPT
# ==============================

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
    """
    # Normaliza o caminho e deixa em minúsculo pra não ter problema de barra ou caixa
    caminho_completo_norm = os.path.normpath(caminho_completo).lower()
    for protegida in ARQUIVOS_PROTEGIDOS:
        protegida_norm = os.path.normpath(protegida).lower()
        # Se o caminho começa com o caminho protegido, ele tá protegido
        if caminho_completo_norm.startswith(protegida_norm):
            return True
    return False


def excluir_antigos(
    caminho: str,
    data_corte: Optional[datetime] = None,
    data_dinamica: Optional[int] = None
) -> Tuple[int, int]:
    """
    Exclui arquivos criados ANTES da data_corte, de forma recursiva.
    Retorna: (deletados, pulados)
    """
    # Se não passou data_corte, calcula pela quantidade de dias
    if data_corte is None:
        if data_dinamica is None:
            raise ValueError("É necessário fornecer 'data_corte' ou 'data_dinamica'.")
        data_corte = datetime.now() - timedelta(days=data_dinamica)

    # Contadores
    deletados = 0
    pulados = 0

    logger.info(f"Analisando pasta: {caminho}")

    try:
        # Pega a lista de tudo que tem na pasta
        itens = os.listdir(caminho)
    except PermissionError:
        logger.info(f"✗ Sem permissão para acessar a pasta: {caminho}\n")
        return 0, 0
    except FileNotFoundError:
        logger.info(f"✗ Pasta não encontrada: {caminho}\n")
        return 0, 0
    except Exception as e:
        logger.info(f"✗ Erro ao listar itens da pasta '{caminho}': {e}\n")
        return 0, 0

    for item in itens:
        caminho_completo = os.path.join(caminho, item)

        # Se estiver na lista de protegidos, pula
        if caminho_esta_protegido(caminho_completo):
            logger.info(f"- Protegida → mantida intacta: {caminho_completo}")
            pulados += 1
            continue

        if os.path.isfile(caminho_completo):
            try:
                # Pega a data de criação do arquivo (no Windows é getctime)
                data_criacao = datetime.fromtimestamp(os.path.getctime(caminho_completo))

                # Se o arquivo é mais velho que a data de corte, deleta
                if data_criacao < data_corte:
                    os.remove(caminho_completo)
                    logger.info(f"✓ Excluído arquivo: {caminho_completo}")
                    deletados += 1
                    sleep(0.2)
                else:
                    # Arquivo ainda tá novo, deixa quieto
                    logger.info(f"- Muito novo, mantido: {caminho_completo} ({data_criacao.strftime('%Y-%m-%d')})")
                    sleep(0.2)

            except PermissionError:
                logger.info(f"✗ ACESSO NEGADO (travado): {caminho_completo}")
                pulados += 1
                sleep(0.2)
            except Exception as e:
                logger.info(f"✗ Erro ao excluir: {caminho_completo} → {e}")
                pulados += 1
                sleep(0.2)

        elif os.path.isdir(caminho_completo):
            # Se for pasta, chama a função de novo (recursão)
            logger.info(f"- Entrando na subpasta: {caminho_completo}")
            sub_deletados, sub_pulados = excluir_antigos(
                caminho_completo,
                data_corte=data_corte,
                data_dinamica=data_dinamica
            )
            deletados += sub_deletados
            pulados += sub_pulados

    # Resumo do que rolou nessa pasta
    logger.info(f"\nResumo da pasta {caminho} (incluindo subpastas):")
    logger.info(f"   Arquivos deletados: {deletados}")
    logger.info(f"   Arquivos pulados/protegidos: {pulados}\n")

    return deletados, pulados


if __name__ == "__main__":
    logger.info("=== INICIANDO LIMPEZA AUTOMÁTICA ===\n")

    total_deletados = 0
    total_pulados = 0

    # Passa por todas as pastas que foram configuradas
    for pasta in PASTAS_PARA_LIMPAR:
        data_str = pasta.get('data_corte', None)
        data_corte = None

        if data_str is not None:
            try:
                # Converte a string YYYY/MM/DD pra datetime
                ano, mes, dia = map(int, data_str.split('/'))
                data_corte = datetime(ano, mes, dia)
                logger.info(
                    f"   Data de corte: {data_corte.strftime('%Y-%m-%d')} → "
                    "exclui arquivos criados ANTES dessa data\n"
                )
            except ValueError:
                logger.info(f"✗ Formato de data inválido: '{data_str}'. Use YYYY/MM/DD\n")
                continue

        pasta_alvo = pasta['caminho']
        data_dinamica = pasta.get('data_dinamica', None)

        if os.path.exists(pasta_alvo):
            logger.info(f"Processando pasta principal: {pasta_alvo}")

            # Chama a função principal de limpeza
            del_count, skip_count = excluir_antigos(
                pasta_alvo,
                data_corte=data_corte,
                data_dinamica=data_dinamica
            )
            total_deletados += del_count
            total_pulados += skip_count
        else:
            logger.info(f"Pasta NÃO ENCONTRADA: {pasta_alvo}\n")

    # Resumo final
    logger.info("=== LIMPEZA CONCLUÍDA ===")
    logger.info(f"Total geral → Arquivos deletados: {total_deletados} | Pulados/protegidos: {total_pulados}")
    logger.info("\nDica: se aparecer muitos 'ACESSO NEGADO', rode como Administrador ou verifique locks.")