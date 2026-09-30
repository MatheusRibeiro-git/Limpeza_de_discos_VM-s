## Como Usar

### Execução Manual
Para executar os scripts manualmente:

1. Abra o Prompt de Comando ou PowerShell como Administrador (recomendado para evitar erros de permissão).
2. Execute o script desejado passando o caminho:
   - Para limpeza do Portal (mantém pastas): `py D:\Caminho\deletar_portal.py`
   - Para limpeza do ETL (remove pastas vazias): `py D:\Caminho\deletar_etl.py`

### Arquivos .bat
O projeto inclui arquivos batch (.bat) para facilitar o agendamento da execução:

- `executar_deletar_portal.bat`: Executa o script `deletar_portal.py`
- `executar_deletar_prefect.bat`: Executa o script `deletar_etl.py` (nota: "prefect" refere-se a VM do ETL Prefect)

Estes arquivos contêm o comando `python <caminho_do_script>` e um `pause` para manter a janela aberta após a execução.

### Agendamento Automático
Para automatizar a limpeza mensalmente:

1. Abra o **Agendador de Tarefas (Task Scheduler)** do Windows.
2. Crie uma nova tarefa básica ou avançada.
3. Configure o gatilho para executar mensalmente no primeiro sábado do mês.
4. Na ação, selecione "Iniciar um programa" e aponte para o arquivo .bat correspondente (ex.: `executar_deletar_portal.bat`).
5. Execute como usuário com permissões administrativas para evitar erros de acesso.

### Diferenças entre os Scripts
- **deletar_portal.py**: Exclui apenas arquivos antigos, preservando a estrutura de pastas (mesmo vazias). Feito assim pois na vm do portal excluimos os arquivos no caminho de usuarios do portal, não excluindo as pastas pois cada uma é um usuario. 
- **deletar_etl.py**: Além de excluir arquivos, remove subpastas que ficarem vazias após a limpeza (exceto a pasta raiz). Como na VM do prefect as pastas são repostas recorrentemente devido a execução do ETL elas podem ser excluidas.

Ambos scripts respeitam as configurações de pastas protegidas e registram todas as ações no log.

## Requisitos
- Python 3.x instalado
- Biblioteca `loguru` (instale via `pip install loguru`)
- Permissões de administrador para acessar diretórios protegidos

## Logs
Os scripts geram logs detalhados durante a execução. Verifique a saída no console ou redirecione para um arquivo se necessário (ex.: `python deletar_portal.py > log.txt`).
