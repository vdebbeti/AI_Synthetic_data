/* Auto-generated SAS program from CompilerIR */
/* Spec Type: ADaM */

/* Dataset: ADSL */
data adsl;
  set dm;
  STUDYID = STUDYID;
  USUBJID = USUBJID;
  SUBJID = SUBJID;
  TRT01A = ARM;
  SAFFL = 'Y';
run;

/* Dataset: ADAE */
data adae;
  set adsl;
  STUDYID = STUDYID;
  USUBJID = USUBJID;
  AESEQ = AESEQ;
  AETERM = AETERM;
  TRTA = TRT01A;
  SAFFL = SAFFL;
  ASTDT = AESTDTC;
  AENDT = AEENDTC;
run;