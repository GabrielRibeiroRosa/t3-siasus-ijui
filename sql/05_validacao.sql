-- Validacao da carga e consultas que demonstram o funcionamento do banco.
USE dbsia;

-- Registros por competencia
SELECT pa_cmp, COUNT(*) AS registros FROM pars GROUP BY pa_cmp ORDER BY pa_cmp;

-- Valores numericos ausentes
SELECT SUM(pa_qtdpro IS NULL) AS qtdpro_nulo, SUM(pa_qtdapr IS NULL) AS qtdapr_nulo,
       SUM(pa_valpro IS NULL) AS valpro_nulo, SUM(pa_valapr IS NULL) AS valapr_nulo FROM pars;

-- Registros do PARS sem correspondencia nas tabelas auxiliares
SELECT 'cadgerrs' AS relacao, COUNT(*) AS orfaos FROM pars p LEFT JOIN cadgerrs x ON p.pa_coduni = x.cnes WHERE x.cnes IS NULL
UNION ALL SELECT 'tb_municip (ufmun)', COUNT(*) FROM pars p LEFT JOIN tb_municip x ON p.pa_ufmun = x.co_municip WHERE x.co_municip IS NULL
UNION ALL SELECT 'procedimentos', COUNT(*) FROM pars p LEFT JOIN procedimentos x ON p.pa_proc_id = x.ip_cod WHERE x.ip_cod IS NULL
UNION ALL SELECT 'cbo', COUNT(*) FROM pars p LEFT JOIN cbo x ON p.pa_cbocod = x.cbo WHERE x.cbo IS NULL
UNION ALL SELECT 'cid', COUNT(*) FROM pars p LEFT JOIN cid x ON p.pa_cidpri = x.cd_cod WHERE x.cd_cod IS NULL;

-- Ijui: producao por competencia
SELECT p.pa_cmp, m.ds_nome, COUNT(*) AS registros, SUM(p.pa_qtdpro) AS qtd_produzida, SUM(p.pa_qtdapr) AS qtd_aprovada,
       SUM(p.pa_valpro) AS valor_produzido, SUM(p.pa_valapr) AS valor_aprovado
FROM pars p JOIN tb_municip m ON p.pa_ufmun = m.co_municip
WHERE p.pa_ufmun = '431020'
GROUP BY p.pa_cmp, m.ds_nome ORDER BY p.pa_cmp;

-- Ijui: estabelecimentos com maior producao
SELECT c.fantasia, SUM(p.pa_qtdpro) AS qtd_produzida
FROM pars p JOIN cadgerrs c ON p.pa_coduni = c.cnes
WHERE p.pa_ufmun = '431020'
GROUP BY c.fantasia ORDER BY qtd_produzida DESC LIMIT 10;

-- Problema da fonte: rl_municip_micibge liga todos os 497 municipios do RS ao codigo 43900,
-- que nao existe em tb_micibge (a microrregiao de Ijui e 43008). Ocorre nas bases fev/2025 e jun/2026.
SELECT COUNT(*) AS rl_sem_micro FROM rl LEFT JOIN micro mi ON rl.co_micibge = mi.co_micibge WHERE mi.co_micibge IS NULL;
SELECT rl.co_municip, rl.co_micibge, mi.ds_nome AS microrregiao
FROM rl LEFT JOIN micro mi ON rl.co_micibge = mi.co_micibge
WHERE rl.co_municip = '431020';
