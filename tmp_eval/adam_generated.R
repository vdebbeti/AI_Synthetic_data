# Auto-generated R program from CompilerIR
# Spec Type: ADaM
library(dplyr)

adsl <- dm %>%
  mutate(
    STUDYID = STUDYID,
    USUBJID = USUBJID,
    SUBJID = SUBJID,
    TRT01A = ARM,
    SAFFL = 'Y'
  )

adae <- adsl %>%
  mutate(
    STUDYID = STUDYID,
    USUBJID = USUBJID,
    AESEQ = AESEQ,
    AETERM = AETERM,
    TRTA = TRT01A,
    SAFFL = SAFFL,
    ASTDT = AESTDTC,
    AENDT = AEENDTC
  )