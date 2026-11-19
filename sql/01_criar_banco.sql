-- T3 - Banco SIASUS. Estrutura baseada nos campos dos DBFs do DATASUS.
DROP DATABASE IF EXISTS dbsia;
-- latin1_bin diferencia maiusculas de minusculas: o S_CID.DBF tem codigos como J450 e j450.
CREATE DATABASE dbsia CHARACTER SET latin1 COLLATE latin1_bin;
USE dbsia;

CREATE TABLE micro (
  co_micibge CHAR(5) PRIMARY KEY,
  co_status CHAR(8),
  ds_nome CHAR(41),
  ds_nomepad CHAR(21),
  ds_abrev CHAR(21),
  ordem DECIMAL(1,0)
);

CREATE TABLE tb_municip (
  co_municip CHAR(6) PRIMARY KEY,
  co_municdv CHAR(1),
  co_status CHAR(1),
  ds_nome CHAR(41),
  sg_uf CHAR(2),
  in_capital CHAR(1),
  in_amazleg CHAR(1),
  in_semiar CHAR(1),
  in_frontzn CHAR(1),
  dt_instal CHAR(4),
  dt_extin CHAR(4),
  co_sucess CHAR(6),
  nu_latitud CHAR(19),
  nu_longit CHAR(17),
  nu_altitud CHAR(4),
  nu_area CHAR(10)
);

CREATE TABLE rl (
  co_municip CHAR(6),
  co_micibge CHAR(5),
  PRIMARY KEY (co_municip, co_micibge)
);

CREATE TABLE cadgerrs (
  cnes CHAR(7) PRIMARY KEY,
  cpf_cnpj CHAR(14),
  fantasia CHAR(60),
  raz_soci CHAR(85),
  rsoc_man CHAR(60),
  logradou CHAR(40),
  num_end CHAR(10),
  compleme CHAR(20),
  bairro CHAR(20),
  cod_cep CHAR(8),
  telefone CHAR(13),
  fax CHAR(13),
  email CHAR(30),
  regsaude CHAR(4),
  micr_reg CHAR(6),
  distrsan CHAR(4),
  distradm CHAR(4),
  codufmun CHAR(6),
  excluido CHAR(1),
  dataincl DATE,
  dataexcl DATE,
  natureza CHAR(2)
);

CREATE TABLE cbo (
  cbo CHAR(6) PRIMARY KEY,
  ds_cbo CHAR(150)
);

CREATE TABLE cid (
  cd_cod CHAR(4) PRIMARY KEY,
  opc CHAR(1),
  cat CHAR(1),
  subcat CHAR(1),
  cd_descr CHAR(50),
  restrsexo CHAR(1),
  campos_rad CHAR(3),
  estadio CHAR(1),
  repete_rad CHAR(1)
);

CREATE TABLE procedimentos (
  ip_cod CHAR(10) PRIMARY KEY,
  ip_dscr CHAR(150)
);

CREATE TABLE pars (
  pa_coduni CHAR(7),
  pa_gestao CHAR(6),
  pa_condic CHAR(2),
  pa_ufmun CHAR(6),
  pa_regct CHAR(4),
  pa_incout CHAR(4),
  pa_incurg CHAR(4),
  pa_tpups CHAR(2),
  pa_tippre CHAR(2),
  pa_mn_ind CHAR(1),
  pa_cnpjcpf CHAR(14),
  pa_cnpjmnt CHAR(14),
  pa_cnpj_cc CHAR(14),
  pa_mvm CHAR(6),
  pa_cmp CHAR(6),
  pa_proc_id CHAR(10),
  pa_tpfin CHAR(2),
  pa_subfin CHAR(4),
  pa_nivcpl CHAR(1),
  pa_docorig CHAR(1),
  pa_autoriz CHAR(13),
  pa_cnsmed CHAR(15),
  pa_cbocod CHAR(6),
  pa_motsai CHAR(2),
  pa_obito CHAR(1),
  pa_encerr CHAR(1),
  pa_perman CHAR(1),
  pa_alta CHAR(1),
  pa_transf CHAR(1),
  pa_cidpri CHAR(4),
  pa_cidsec CHAR(4),
  pa_cidcas CHAR(4),
  pa_catend CHAR(2),
  pa_idade CHAR(3),
  idademin CHAR(3),
  idademax CHAR(3),
  pa_flidade CHAR(1),
  pa_sexo CHAR(1),
  pa_racacor CHAR(2),
  pa_munpcn CHAR(6),
  pa_qtdpro DECIMAL(11,0),
  pa_qtdapr DECIMAL(11,0),
  pa_valpro DECIMAL(20,2),
  pa_valapr DECIMAL(20,2),
  pa_ufdif CHAR(1),
  pa_mndif CHAR(1),
  pa_dif_val DECIMAL(20,2),
  nu_vpa_tot DECIMAL(20,2),
  nu_pa_tot DECIMAL(20,2),
  pa_indica CHAR(1),
  pa_codoco CHAR(1),
  pa_flqt CHAR(1),
  pa_fler CHAR(1),
  pa_etnia CHAR(4),
  pa_vl_cf DECIMAL(20,2),
  pa_vl_cl DECIMAL(20,2),
  pa_vl_inc DECIMAL(20,2),
  pa_srv_c CHAR(6),
  pa_ine CHAR(10),
  pa_nat_jur CHAR(4),
  pa_fntorc CHAR(2),
  pa_vl_crd DECIMAL(20,2)
);
