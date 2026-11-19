# T3 - Análise de Dados do SIASUS para a Gestão Municipal de Saúde de Ijuí/RS

Trabalho da disciplina Programação para Ciência de Dados. Etapas concluídas: Etapa 1 (construção e carga
do banco de dados MySQL) e Etapa 2 (exploração, limpeza e análises com Pandas a partir da VIEW `pa_ijui`).

## Fontes e período

| Dados | Arquivos | Origem (DATASUS) |
|---|---|---|
| Produção ambulatorial do RS (jun a ago/2026) | `PARS2606a`, `PARS2606b`, `PARS2607a`, `PARS2607b`, `PARS2608` | `ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/` |
| `cadgerrs`, `cbo`, `cid`, `procedimentos` | `TAB_SIA.zip` (`CADGERRS`, `CBO`, `S_CID`, `TB_SIGTAW`) | `ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Auxiliar/` |
| `tb_municip`, `micro`, `rl` | `02-base_territorial_fev25.zip` (`tb_municip`, `tb_micibge`, `rl_municip_micibge`) | `ftp://ftp.datasus.gov.br/territorio/tabelas/2025/` |

Arquivos baixados em 05/11/2026. O DATASUS pode republicá-los.

## Requisitos

- MySQL Server 8.4 (com MySQL Workbench, opcional). No `my.ini`, `secure-file-priv` aponta para a pasta dos
  CSVs (`D:/T3/uploads`).
- Python 3.13 e as bibliotecas de `requirements.txt`:

  ```
  pip install -r requirements.txt
  ```

- TABWIN (pacote `TAB415.zip` do DATASUS), para converter `.dbc` em `.dbf`.

## Estrutura

```
sql/        scripts do banco dbsia, na ordem de execução
scripts/    conversão dos DBF em CSV e geração do notebook
analise/    código da Etapa 2 (lê a VIEW pa_ijui)
notebooks/  notebook da Etapa 2 com as saídas
resultados/ tabelas geradas pela Etapa 2 (CSV) e base preparada para a Etapa 3 (Parquet)
```

## Como executar

### Etapa 1 - banco de dados

1. Baixe os arquivos da tabela de fontes.
2. Converta cada `.dbc` em `.dbf` arrastando-o sobre o `dbf2dbc.exe` do TABWIN.
3. Gere os CSVs na pasta de importação do MySQL. Para cada arquivo PARS:

   ```
   python scripts/dbf_to_csv.py PARS2608.dbf --csv D:/T3/uploads/PARS2608.csv
   ```

   Para as tabelas auxiliares: `powershell -File scripts/gerar_csvs_auxiliares.ps1`.
4. Abra o cliente do MySQL na linha de comando (como administrador) e rode os scripts na ordem:

   ```
   mysql -u root -p
   source D:/T3/repo/sql/01_criar_banco.sql
   source D:/T3/repo/sql/02_carregar_auxiliares.sql
   source D:/T3/repo/sql/03_carregar_pars.sql
   source D:/T3/repo/sql/04_criar_indices.sql
   source D:/T3/repo/sql/05_validacao.sql
   source D:/T3/repo/sql/06_dimtempo.sql
   source D:/T3/repo/sql/07_view_pa_ijui.sql
   ```

   `06_dimtempo.sql` corresponde ao script `04-gera-dimtempo-mysql.sql` e `07_view_pa_ijui.sql` ao
   `view.sql`, ambos disponibilizados na disciplina. Na primeira execução, a linha `drop view pa_ijui;`
   mostra o erro "Unknown table", porque a VIEW ainda não existe; o `CREATE OR REPLACE VIEW` seguinte a cria.

### Etapa 2 - análise com Pandas

Com o MySQL ligado, abra `notebooks/etapa2_analise.ipynb` no VS Code (extensão Jupyter) ou no Jupyter:

```
jupyter notebook
```

O mesmo código está em `analise/etapa2_analise.py`, que pode ser executado direto
(`python analise/etapa2_analise.py`) e grava as tabelas em `resultados/etapa2/`.

## Resultado da carga

| Arquivo | Registros |
|---|---|
| `PARS2606a` | 4.798.458 |
| `PARS2606b` | 85.543 |
| `PARS2607a` | 4.799.781 |
| `PARS2607b` | 84.808 |
| `PARS2608` | 4.040.363 |
| **Total em `pars`** | **13.808.953** |

Os totais conferem com o cabeçalho de cada DBF, e a carga não gerou avisos. A VIEW `pa_ijui` tem
204.301 registros (60.282 em junho, 68.827 em julho e 75.192 em agosto).

## Etapa 2 - decisões

- Fonte: VIEW `pa_ijui` (estabelecimentos de Ijuí, `pa_ufmun = '431020'`).
- O tempo (mês, bimestre, trimestre) vem da DIMTEMPO ligada pelo **mês de processamento** (`pa_mvm`), como
  na VIEW. O arquivo de agosto traz 14.594 atendimentos de junho e 1.666 de julho processados com atraso,
  que aparecem como agosto.
- A VIEW traz o nome do procedimento, não o código. As áreas (oncologia, imagem, laboratório, saúde mental,
  medicamentos, consultas) são identificadas por palavras no nome, na ocupação e no estabelecimento; é uma
  aproximação.
- Nenhuma linha é apagada por valor ausente. Códigos de "ignorado" (`0000` no CID, `999` na idade, `0` no
  sexo, município `INVALIDO`) viram "Não informado" ou `NA`.
- Linhas duplicadas **não** são removidas: o PARS não identifica o paciente nem a data, e a VIEW tem só 17
  colunas, então linhas iguais podem ser atendimentos diferentes. Removê-las cortaria 39% dos registros
  (ver `resultados/etapa2/04_impacto_duplicados.csv`). A constante `REMOVER_DUPLICADOS` muda isso.

## Limitações dos dados

- **Agosto/2026 incompleto:** CAPS, laboratórios, UPA, SAMU e Hemovita não enviaram produção de agosto.
- **Atenção básica:** as UBS registram sua produção no e-SUS APS/SISAB, não no SIASUS, e a VIEW não tem o
  tipo de estabelecimento.
- **Medicamentos:** a 17ª Coordenadoria Regional de Saúde dispensa medicamentos para a região, contados por
  comprimido ou cápsula (57% da quantidade apresentada). Os rankings também aparecem sem eles.
- **Municípios:** a VIEW traz o nome sem o estado; alguns nomes existem em mais de um estado.
- **CID:** 67% dos registros não têm CID principal informado.
- `rl_municip_micibge` liga todos os municípios do RS ao código `43900`, que não existe em `tb_micibge`; a
  ligação `rl` → `micro` não funciona para o RS.
- `micro` está em cp850; os demais textos, em latin1. `S_CID` e `TB_SIGTAW` têm alguns caracteres com
  codificação inconsistente.
- O banco usa `latin1_bin` porque o `S_CID.DBF` tem códigos que diferem só por maiúsculas e minúsculas
  (`J450` e `j450`).
