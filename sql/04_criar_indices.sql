-- Indices criados depois da carga, nos campos do modelo conceitual e na competencia.
USE dbsia;
ALTER TABLE pars
  ADD INDEX ix_pars_ufmun (pa_ufmun),
  ADD INDEX ix_pars_coduni (pa_coduni),
  ADD INDEX ix_pars_proc (pa_proc_id),
  ADD INDEX ix_pars_cbo (pa_cbocod),
  ADD INDEX ix_pars_cid (pa_cidpri),
  ADD INDEX ix_pars_cmp (pa_cmp);
