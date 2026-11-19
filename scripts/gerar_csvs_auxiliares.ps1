# Gera os CSVs das tabelas auxiliares em D:\T3\uploads a partir dos DBFs do DATASUS.
$py = "D:\T3\.venv\Scripts\python.exe"
$s = "D:\T3\repo\scripts\dbf_to_csv.py"
$a = "D:\T3\auxiliares"
$arquivos = @{
    cadgerrs     = "$a\TAB_SIA\DBF\CADGERRS.dbf"
    cbo          = "$a\TAB_SIA\DBF\CBO.dbf"
    cid10        = "$a\TAB_SIA\DBF\S_CID.DBF"
    procedimento = "$a\TAB_SIA\DBF\TB_SIGTAW.dbf"
    municipio    = "$a\base_territorial\tb_municip.dbf"
    micro        = "$a\base_territorial\tb_micibge.dbf"
    rl           = "$a\base_territorial\rl_municip_micibge.dbf"
}
foreach ($t in $arquivos.Keys) { & $py $s $arquivos[$t] --csv "D:\T3\uploads\$t.csv" }
