/* Auto-generated SAS program from CompilerIR */
/* Spec Type: SDTM */

/* Dataset: DM */
data dm;
  set raw_dm;
  STUDYID = STUDYID;
  DOMAIN = 'DM';
  USUBJID = USUBJID;
  SUBJID = SUBJID;
  SITEID = SITEID;
  SEX = SEX;
  RACE = RACE;
  BRTHDTC = BRTHDTC;
  ARM = ARM;
  RFSTDTC = RANDDTC;
run;

/* Dataset: AE */
data ae;
  set raw_ae;
  STUDYID = STUDYID;
  DOMAIN = 'AE';
  USUBJID = USUBJID;
  AESEQ = AESEQ;
  AETERM = AETERM;
  AESTDTC = AESTDTC;
  AEENDTC = AEENDTC;
  AESEV = AESEV;
  AESER = AESER;
run;