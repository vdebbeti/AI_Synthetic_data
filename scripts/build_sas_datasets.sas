/* Build synthetic RAW, SDTM, and ADaM SAS datasets from CSV golden files */

options validvarname=upcase;

%let root=C:\Users\Varun\Desktop\for_tools\AI_synthetic_data;

libname raw "&root.\\sasdata\\raw";
libname sdtm "&root.\\sasdata\\sdtm";
libname adam "&root.\\sasdata\\adam";

/* Import raw CSV */
proc import datafile="&root.\\data\\raw\\raw_dm.csv"
  out=raw.raw_dm dbms=csv replace;
  guessingrows=max;
run;

proc import datafile="&root.\\data\\raw\\raw_ae.csv"
  out=raw.raw_ae dbms=csv replace;
  guessingrows=max;
run;

/* Build SDTM DM */
data sdtm.dm;
  length DOMAIN $2 RFSTDTC $20;
  set raw.raw_dm;
  DOMAIN='DM';
  RFSTDTC=RANDDTC;
  keep STUDYID DOMAIN USUBJID SUBJID SITEID SEX RACE BRTHDTC ARM RFSTDTC;
run;

/* Build SDTM AE */
data sdtm.ae;
  length DOMAIN $2;
  set raw.raw_ae;
  DOMAIN='AE';
  keep STUDYID DOMAIN USUBJID AESEQ AETERM AESTDTC AEENDTC AESEV AESER;
run;

/* Build ADaM ADSL */
data adam.adsl;
  length TRT01A $20 SAFFL $1;
  set sdtm.dm;
  TRT01A=ARM;
  SAFFL='Y';
  keep STUDYID USUBJID SUBJID TRT01A SAFFL;
run;

/* Build ADaM ADAE */
proc sql;
  create table adam.adae as
  select
    a.STUDYID,
    a.USUBJID,
    a.AESEQ,
    a.AETERM,
    b.TRT01A as TRTA,
    b.SAFFL,
    a.AESTDTC as ASTDT,
    a.AEENDTC as AENDT
  from sdtm.ae as a
  left join adam.adsl as b
    on a.USUBJID=b.USUBJID
  ;
quit;

/* Export generated outputs for comparison */
proc export data=sdtm.dm outfile="&root.\\sasdata\\DM_generated.csv" dbms=csv replace; run;
proc export data=sdtm.ae outfile="&root.\\sasdata\\AE_generated.csv" dbms=csv replace; run;
proc export data=adam.adsl outfile="&root.\\sasdata\\ADSL_generated.csv" dbms=csv replace; run;
proc export data=adam.adae outfile="&root.\\sasdata\\ADAE_generated.csv" dbms=csv replace; run;
