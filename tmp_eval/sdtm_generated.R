# Auto-generated R program from CompilerIR
# Spec Type: SDTM
library(dplyr)

dm <- raw_dm %>%
  mutate(
    STUDYID = STUDYID,
    DOMAIN = 'DM',
    USUBJID = USUBJID,
    SUBJID = SUBJID,
    SITEID = SITEID,
    SEX = SEX,
    RACE = RACE,
    BRTHDTC = BRTHDTC,
    ARM = ARM,
    RFSTDTC = RANDDTC
  )

ae <- raw_ae %>%
  mutate(
    STUDYID = STUDYID,
    DOMAIN = 'AE',
    USUBJID = USUBJID,
    AESEQ = AESEQ,
    AETERM = AETERM,
    AESTDTC = AESTDTC,
    AEENDTC = AEENDTC,
    AESEV = AESEV,
    AESER = AESER
  )