# %% [markdown]
# # T3 - Etapa 2: Análise exploratória e processamento de dados com Pandas
# ## SIASUS: produção ambulatorial dos estabelecimentos de Ijuí
#
# **Fonte de dados (Estratégia A):** a VIEW `pa_ijui` (`sql/07_view_pa_ijui.sql`). Ela faz as ligações com as
# tabelas descritivas e reduz a base aos estabelecimentos de Ijuí (`pa_ufmun = '431020'`).
#
# **Período:** arquivos PARS de junho, julho e agosto de 2026. Na VIEW, `Ano` e `Mes` vêm da tabela
# DIMTEMPO ligada pelo **mês de processamento** (`pa_mvm`), ou seja, o mês do arquivo em que o registro chegou.
#
# Os resultados de cada análise ficam em DataFrames e também são gravados em `resultados/etapa2/`
# para a Etapa 3 (visualização).

# %% [markdown]
# ## 1. Conexão com o MySQL e carga da VIEW
# Conexão com `mysql-connector-python` ao banco `dbsia`, no servidor local, com o usuário `root`. Se o
# usuário tiver senha, ela deve ser informada em `SENHA`.

# %%
from pathlib import Path

import pandas as pd
from mysql.connector import connect

pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 200)
pd.set_option("display.float_format", lambda v: f"{v:,.2f}")

SENHA = ""
REMOVER_DUPLICADOS = False  # ver a seção 3.2 antes de mudar
SAIDA = Path(__file__).resolve().parents[1] / "resultados" / "etapa2" if "__file__" in globals() else Path("../resultados/etapa2")
SAIDA.mkdir(parents=True, exist_ok=True)


def consultar(sql):
    """Executa uma consulta no MySQL e devolve um DataFrame."""
    with connect(host="localhost", user="root", password=SENHA, database="dbsia") as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            return pd.DataFrame(cursor.fetchall(), columns=cursor.column_names)


def salvar(df, nome):
    """Grava o resultado em CSV (abre direto no Excel) e devolve o próprio DataFrame."""
    df.to_csv(SAIDA / f"{nome}.csv", encoding="utf-8-sig")
    return df


tabela = consultar("SELECT * FROM pa_ijui")
display(tabela.head(10)) if "display" in globals() else print(tabela.head(10))

# %% [markdown]
# ## 2. Análise exploratória
# ### 2.1 Dimensão: quantos registros e variáveis existem?

# %%
print("Quantidade de linhas:", len(tabela))
print("Quantidade de colunas:", tabela.shape[1])
print("Colunas disponíveis:", list(tabela.columns))

# %% [markdown]
# ### 2.2 Tipos de variáveis
# Quantidades e valores chegam do MySQL como `Decimal` e precisam ser convertidos para número.
# A idade chega como texto (`'086'`).

# %%
colunas_numericas = ["pa_qtdpro", "pa_qtdapr", "pa_valpro", "pa_valapr"]
for coluna in colunas_numericas:
    tabela[coluna] = pd.to_numeric(tabela[coluna])
tabela["IdadeOriginal"] = tabela["pa_idade"]
tabela["IdadeNumerica"] = pd.to_numeric(tabela["pa_idade"], errors="coerce")

tipos = pd.DataFrame({"tipo_pandas": tabela.dtypes.astype(str), "valores_distintos": tabela.nunique()})
tipos["classificacao"] = "textual"
tipos.loc[tipos.valores_distintos <= 50, "classificacao"] = "categórica"
tipos.loc[colunas_numericas + ["IdadeNumerica", "Ano", "Mes"], "classificacao"] = "numérica"
salvar(tipos, "01_tipos_variaveis")
tipos

# %% [markdown]
# ### 2.3 Estatísticas descritivas e distribuições de frequência

# %%
descritivas = tabela[colunas_numericas + ["IdadeNumerica"]].describe().T
descritivas["mediana"] = tabela[colunas_numericas + ["IdadeNumerica"]].median()
salvar(descritivas, "02_estatisticas_descritivas")
descritivas

# %%
for coluna in ["Mes", "pa_sexo", "Estabelecimento", "MunicipioPaciente"]:
    print(f"\n{coluna} (10 mais frequentes):")
    print(tabela[coluna].value_counts(dropna=False).head(10).to_string())

# %% [markdown]
# ### 2.4 Valores ausentes e inválidos
# No SIASUS a falta de informação quase nunca aparece como `NULL`: ela vem codificada
# (`0000` no CID, `999` na idade, `0` no sexo, município `INVALIDO`).

# %%
nulos = tabela.isna().sum()
problemas = pd.DataFrame({
    "registros": {
        "Diagnostico nulo (CID inexistente na tabela CID-10)": int(nulos["Diagnostico"]),
        "Procedimento nulo (código fora da tabela)": int(nulos["Procedimento"]),
        "pa_cidpri = '0000' (CID não informado)": int((tabela.pa_cidpri == "0000").sum()),
        "idade > 120 (idade inválida, geralmente 999)": int((tabela.IdadeNumerica > 120).sum()),
        "pa_sexo diferente de M/F": int((~tabela.pa_sexo.isin(["M", "F"])).sum()),
        "MunicipioPaciente = 'INVALIDO' (residência ignorada)": int((tabela.MunicipioPaciente == "INVALIDO").sum()),
        "valor aprovado maior que o apresentado": int((tabela.pa_valapr > tabela.pa_valpro).sum()),
    }
})
problemas["percentual"] = 100 * problemas.registros / len(tabela)
salvar(problemas, "03_ausentes_invalidos")
problemas

# %% [markdown]
# Sexo, idade e residência ignorados aparecem juntos: são registros do **BPA consolidado**, que não trazem
# dados do paciente. A VIEW não tem a coluna do tipo de registro (`pa_docorig`), mas o padrão aparece
# cruzando as colunas:

# %%
pd.crosstab(tabela.pa_sexo, tabela.MunicipioPaciente == "INVALIDO", margins=True).rename(
    columns={True: "residência INVALIDO", False: "residência informada"})

# %% [markdown]
# ## 3. Limpeza e preparação
# ### 3.1 Estratégia para valores nulos
# * **Nenhuma linha é apagada**: registros sem dados do paciente têm quantidade e valor válidos, e apagá-los
#   subestimaria a produção.
# * Códigos de "ignorado" viram **"Não informado"** nas colunas de texto e `NA` na idade.

# %%
df = tabela.copy()
df.loc[df.IdadeNumerica > 120, "IdadeNumerica"] = pd.NA
df["Sexo"] = df.pa_sexo.map({"M": "Masculino", "F": "Feminino"}).fillna("Não informado")
df["Diagnostico"] = df.Diagnostico.where(df.pa_cidpri != "0000", "Não informado").fillna("CID inexistente")
df["MunicipioPaciente"] = df.MunicipioPaciente.replace("INVALIDO", "Não informado")
df["Procedimento"] = df.Procedimento.fillna("Não informado")
df["FaixaEtaria"] = pd.cut(df.IdadeNumerica, bins=[-1, 14, 29, 44, 59, 200],
                           labels=["0–14", "15–29", "30–44", "45–59", "60+"])
df["Periodo"] = df.Ano.astype(str) + "-" + df.Mes.astype(str).str.zfill(2)

# %% [markdown]
# ### 3.2 Registros duplicados
# A VIEW tem só 17 das 62 colunas do PARS, e o PARS não identifica o paciente nem a data do atendimento.
# Por isso há muitas linhas iguais que são atendimentos diferentes (por exemplo, várias sessões do mesmo
# procedimento no mesmo mês). A remoção fica desligada (`REMOVER_DUPLICADOS = False`); a tabela mostra o
# efeito que ela teria.

# %%
duplicadas = tabela.duplicated()
impacto_duplicados = pd.DataFrame({
    "com_duplicados": [len(df), df.pa_qtdpro.sum(), df.pa_valapr.sum()],
    "sem_duplicados": [(~duplicadas).sum(), df.loc[~duplicadas, "pa_qtdpro"].sum(),
                       df.loc[~duplicadas, "pa_valapr"].sum()],
}, index=["registros", "quantidade apresentada", "valor aprovado (R$)"])
impacto_duplicados["variacao_%"] = 100 * (impacto_duplicados.sem_duplicados / impacto_duplicados.com_duplicados - 1)
salvar(impacto_duplicados, "04_impacto_duplicados")
if REMOVER_DUPLICADOS:
    df = df[~duplicadas].copy()
impacto_duplicados

# %% [markdown]
# ### 3.3 Classificação dos procedimentos por área
# A VIEW traz o **nome** do procedimento, não o código. A área é identificada por palavras no nome
# (`str.contains`), na ocupação e no estabelecimento. É uma aproximação: nomes que não seguem o padrão
# ficam em "Outros".

# %%
AREAS = [  # a primeira regra que combinar define a área
    ("Oncologia", "Procedimento", r"QUIMIOTERAPIA|RADIOTERAPIA|HORMONIOTERAPIA|BRAQUITERAPIA|BETATERAPIA|ONCOLOG"),
    ("Saúde mental", "Ocupacao", r"(?i)psiquiatr|psicolog"),
    ("Saúde mental", "Estabelecimento", r"CAPS|PSICOSSOCIAL"),
    ("Medicamentos", "Procedimento", r"\(POR (?:COMPRIMIDO|CAPSULA|FRASCO|AMPOLA|SERINGA|ADESIVO|DRAGEA|SACHE|TUBO|BISNAGA|FRASCO-AMPOLA)|\d+ ?(?:MG|MCG|UI)\b"),
    ("Exames de imagem", "Procedimento", r"RADIOGRAFIA|ULTRASSONOGRAFIA|TOMOGRAFIA|RESSONANCIA|CINTILOGRAFIA|MAMOGRAFIA|ECOCARDIOGRAFIA|DENSITOMETRIA"),
    ("Exames laboratoriais", "Procedimento", r"^DOSAGEM|^HEMOGRAMA|^PESQUISA DE|^DETERMINACAO|^CONTAGEM|^ANALISE|^CULTURA|^EXAME|^ANTIBIOGRAMA|^TESTE"),
    ("Consultas e atendimentos", "Procedimento", r"^CONSULTA|^ATENDIMENTO|^ACOMPANHAMENTO|^ADMINISTRACAO"),
]
df["Area"] = "Outros"
for area, coluna, padrao in reversed(AREAS):  # de trás para frente: a primeira regra da lista prevalece
    df.loc[df[coluna].fillna("").str.contains(padrao, regex=True), "Area"] = area
df.Area.value_counts()

# %% [markdown]
# ### 3.4 Granularidade temporal
# Mês, bimestre e trimestre vêm da DIMTEMPO (script `04-gera-dimtempo-mysql.sql`), ligada pelo mês de
# processamento. **Atenção:** o arquivo de agosto também traz atendimentos de junho e julho processados com
# atraso, que a VIEW conta como agosto.

# %%
tempo = df.groupby(["Ano", "Mes", "AnoBimestre", "AnoTrimestre"], as_index=False).size()
tempo

# %% [markdown]
# ## 4. Análises estratégicas para o gestor
# ### 4.1 Volume e perfil dos procedimentos
# Último mês, bimestre e trimestre disponíveis. Os bimestres e trimestres são os do calendário (DIMTEMPO);
# como só há dados de junho a agosto, o 2º trimestre tem só junho e o 3º só julho e agosto.

# %%
ultimo_mes = df.Periodo.max()
ultimo_bi = df.AnoBimestre.max()
ultimo_tri = df.AnoTrimestre.max()
volume_periodos = pd.DataFrame({
    nome: {
        "registros": int(filtro.sum()),
        "quantidade apresentada": df.loc[filtro, "pa_qtdpro"].sum(),
        "quantidade aprovada": df.loc[filtro, "pa_qtdapr"].sum(),
        "meses com dados": ", ".join(sorted(df.loc[filtro, "Periodo"].unique())),
    }
    for nome, filtro in [(f"último mês ({ultimo_mes})", df.Periodo == ultimo_mes),
                         (f"último bimestre ({ultimo_bi})", df.AnoBimestre == ultimo_bi),
                         (f"último trimestre ({ultimo_tri})", df.AnoTrimestre == ultimo_tri)]
}).T
salvar(volume_periodos, "05_volume_periodos")
volume_periodos

# %%
por_area = df.groupby("Area")[["pa_qtdpro", "pa_qtdapr", "pa_valapr"]].sum().sort_values("pa_qtdpro", ascending=False)
por_area["participacao_%"] = 100 * por_area.pa_qtdpro / por_area.pa_qtdpro.sum()
salvar(por_area, "06_volume_por_area")
por_area

# %%
top_procedimentos = (df.groupby("Procedimento")[["pa_qtdpro", "pa_qtdapr"]].sum()
                       .sort_values("pa_qtdpro", ascending=False).head(15))
salvar(top_procedimentos, "07_top_procedimentos")
top_procedimentos

# %% [markdown]
# **Evolução temporal:** produção mensal por área e variação em relação ao mês anterior (`pct_change`).

# %%
evolucao_area = df.pivot_table(index="Area", columns="Periodo", values="pa_qtdpro", aggfunc="sum", fill_value=0)
variacao = evolucao_area.pct_change(axis=1).iloc[:, 1:].mul(100).add_prefix("var_%_")
evolucao_area = evolucao_area.join(variacao)
salvar(evolucao_area, "08_evolucao_por_area")
evolucao_area

# %% [markdown]
# ### 4.2 Produção por estabelecimento de saúde
# Ranking pela quantidade apresentada, com a taxa de aprovação. A 17ª Coordenadoria Regional de Saúde
# dispensa medicamentos para toda a região, contados por comprimido; por isso também há um ranking sem ela.

# %%
ranking = (df.groupby("Estabelecimento")
             .agg(Registros=("Procedimento", "size"),
                  QuantidadeApresentada=("pa_qtdpro", "sum"), QuantidadeAprovada=("pa_qtdapr", "sum"),
                  ValorApresentado=("pa_valpro", "sum"), ValorAprovado=("pa_valapr", "sum"))
             .sort_values("QuantidadeApresentada", ascending=False))
ranking["Aprovacao_qtd_%"] = 100 * ranking.QuantidadeAprovada / ranking.QuantidadeApresentada
ranking["Glosa_qtd"] = ranking.QuantidadeApresentada - ranking.QuantidadeAprovada
salvar(ranking, "09_ranking_estabelecimentos")
ranking

# %%
ranking_sem_medicamentos = (df[df.Area != "Medicamentos"].groupby("Estabelecimento")["pa_qtdpro"].sum()
                              .sort_values(ascending=False).head(10).to_frame())
salvar(ranking_sem_medicamentos, "10_ranking_sem_medicamentos")
ranking_sem_medicamentos

# %% [markdown]
# ### 4.3 Perfil demográfico e epidemiológico

# %%
sexo_faixa = df.pivot_table(index="FaixaEtaria", columns="Sexo", values="pa_qtdpro",
                            aggfunc="sum", fill_value=0, observed=False)
sexo_faixa.loc["Não informado"] = df[df.FaixaEtaria.isna()].groupby("Sexo")["pa_qtdpro"].sum()
sexo_faixa = sexo_faixa.fillna(0)
salvar(sexo_faixa, "11_sexo_faixa_etaria")
sexo_faixa

# %%
com_cid = df[~df.Diagnostico.isin(["Não informado", "CID inexistente"])]
print(f"Registros com CID informado: {len(com_cid):,} de {len(df):,} ({100 * len(com_cid) / len(df):.1f}%)")
top_cid = com_cid.groupby("Diagnostico")["pa_qtdpro"].sum().sort_values(ascending=False).head(15).to_frame()
salvar(top_cid, "12_top_diagnosticos")
top_cid

# %%
GRUPOS_CID = {
    "Hipertensão (I10-I15)": r"^I1[0-5]", "Diabetes (E10-E14)": r"^E1[0-4]",
    "Neoplasias (C00-D48)": r"^(?:C|D[0-3]|D4[0-8])", "Transtornos mentais (F00-F99)": r"^F",
    "Doenças do olho (H00-H59)": r"^H[0-5]", "Doenças do ouvido (H60-H95)": r"^H[6-9]",
    "Doença renal crônica (N18)": r"^N18",
}
grupos_cid = pd.DataFrame({
    nome: {"registros": int(com_cid.pa_cidpri.str.contains(rx).sum()),
           "quantidade apresentada": com_cid.loc[com_cid.pa_cidpri.str.contains(rx), "pa_qtdpro"].sum()}
    for nome, rx in GRUPOS_CID.items()
}).T.sort_values("quantidade apresentada", ascending=False)
salvar(grupos_cid, "13_grupos_diagnosticos")
grupos_cid

# %% [markdown]
# ### 4.4 Fluxos regionais e acesso
# Residente é quem tem `MunicipioPaciente` igual ao município do estabelecimento (Ijuí). A VIEW traz só o
# nome do município, sem o estado; alguns nomes existem em mais de um estado.

# %%
df["Origem"] = "Outro município"
df.loc[df.MunicipioPaciente == df.MunicipioEstabelecimento, "Origem"] = "Ijuí"
df.loc[df.MunicipioPaciente == "Não informado", "Origem"] = "Não informado"
origem = df.groupby("Origem").agg(Registros=("Procedimento", "size"), QuantidadeApresentada=("pa_qtdpro", "sum"))
origem["participacao_qtd_%"] = 100 * origem.QuantidadeApresentada / origem.QuantidadeApresentada.sum()
salvar(origem, "14_residentes_x_outros")
origem

# %%
municipios_origem = (df[df.Origem == "Outro município"].groupby("MunicipioPaciente")["pa_qtdpro"].sum()
                       .sort_values(ascending=False).to_frame())
municipios_origem["participacao_%"] = 100 * municipios_origem.pa_qtdpro / municipios_origem.pa_qtdpro.sum()
print("Municípios de origem diferentes:", len(municipios_origem))
salvar(municipios_origem, "15_municipios_origem")
municipios_origem.head(15)

# %%
origem_por_area = df.pivot_table(index="Area", columns="Origem", values="pa_qtdpro", aggfunc="sum", fill_value=0)
origem_por_area["outros_municipios_%"] = 100 * origem_por_area["Outro município"] / origem_por_area.sum(axis=1)
origem_por_area = origem_por_area.sort_values("outros_municipios_%", ascending=False)
salvar(origem_por_area, "16_origem_por_area")
origem_por_area

# %% [markdown]
# ### 4.5 Recursos financeiros

# %%
financeiro = df.groupby("Periodo")[["pa_valpro", "pa_valapr", "pa_qtdpro", "pa_qtdapr"]].sum()
financeiro.loc["Total"] = financeiro.sum()
financeiro["Diferenca_valor"] = financeiro.pa_valpro - financeiro.pa_valapr
financeiro["Aprovado_%"] = 100 * financeiro.pa_valapr / financeiro.pa_valpro
financeiro["Gasto_medio_por_procedimento"] = financeiro.pa_valapr / financeiro.pa_qtdapr
salvar(financeiro, "17_financeiro_mensal")
financeiro

# %%
gasto_area = df.pivot_table(index="Area", columns="Periodo", values=["pa_valapr", "pa_qtdapr"], aggfunc="sum")
gasto_medio_area = (gasto_area["pa_valapr"] / gasto_area["pa_qtdapr"]).round(2)
salvar(gasto_medio_area, "18_gasto_medio_por_area")
gasto_medio_area

# %% [markdown]
# ### 4.6 Áreas críticas
# #### Oncologia: quimioterapia x radioterapia (apresentado x aprovado)

# %%
onco = df[df.Area == "Oncologia"].copy()
onco["Modalidade"] = "Quimioterapia/hormonioterapia"
onco.loc[onco.Procedimento.str.contains("RADIOTERAPIA|BRAQUITERAPIA|BETATERAPIA"), "Modalidade"] = "Radioterapia"
oncologia = onco.groupby(["Modalidade", "Periodo"])[["pa_qtdpro", "pa_qtdapr", "pa_valpro", "pa_valapr"]].sum()
oncologia["Aprovacao_qtd_%"] = 100 * oncologia.pa_qtdapr / oncologia.pa_qtdpro
salvar(oncologia, "19_oncologia")
print("Estabelecimentos com produção oncológica:", onco.Estabelecimento.unique().tolist())
oncologia

# %% [markdown]
# #### Saúde mental: atendimentos psiquiátricos e psicológicos

# %%
sm = df[df.Area == "Saúde mental"].copy()
sm["Profissional"] = "Outros profissionais (CAPS)"
sm.loc[sm.Ocupacao.str.contains("(?i)psiquiatr"), "Profissional"] = "Psiquiatra"
sm.loc[sm.Ocupacao.str.contains("(?i)psicolog"), "Profissional"] = "Psicólogo"
saude_mental = sm.pivot_table(index=["Estabelecimento", "Profissional"], columns="Periodo",
                              values="pa_qtdpro", aggfunc="sum", fill_value=0)
saude_mental["Total"] = saude_mental.sum(axis=1)
saude_mental = saude_mental.sort_values("Total", ascending=False)
salvar(saude_mental, "20_saude_mental")
saude_mental

# %% [markdown]
# #### Atenção básica
# **Limitação:** as UBS registram sua produção no e-SUS APS / SISAB, não no SIASUS, e a VIEW não traz o tipo
# de estabelecimento. Ficam a produção do Posto Central (unidade municipal) e o acompanhamento de doenças
# crônicas (hipertensão e diabetes) em qualquer estabelecimento.

# %%
posto = df[df.Estabelecimento.str.contains("POSTO|UBS|UNIDADE BASICA|ESF", na=False)]
atencao_basica = posto.pivot_table(index="Area", columns="Periodo", values="pa_qtdpro", aggfunc="sum", fill_value=0)
salvar(atencao_basica, "21_atencao_basica")
print("Estabelecimentos considerados:", posto.Estabelecimento.unique().tolist())
atencao_basica

# %%
cronicas = com_cid[com_cid.pa_cidpri.str.contains(r"^(?:I1[0-5]|E1[0-4])")].copy()
cronicas["Condicao"] = cronicas.pa_cidpri.str.startswith("I").map({True: "Hipertensão", False: "Diabetes"})
doencas_cronicas = cronicas.pivot_table(index=["Condicao", "Estabelecimento"], columns="Periodo",
                                        values="pa_qtdpro", aggfunc="sum", fill_value=0)
salvar(doencas_cronicas, "22_doencas_cronicas")
doencas_cronicas

# %% [markdown]
# ## 5. Base preparada para a Etapa 3
# O DataFrame tratado é gravado em formato Parquet para a etapa de visualização.

# %%
df.to_parquet(SAIDA / "pa_ijui_preparado.parquet", index=False)
print(f"Base preparada: {len(df):,} registros, {df.shape[1]} colunas -> {SAIDA / 'pa_ijui_preparado.parquet'}")
