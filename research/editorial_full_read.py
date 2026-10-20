"""Four editorial changes from the 20 October full-read brief; no experiments."""

VERSION='2026-10-20-v01'
REVISION_TIMESTAMP='20 October 2026, 16:13 PHT (UTC+08:00)'

def revise_full_read(md):
    title='Draft for research-team review · revised from the 19 October 2026 brief; existing results only'
    assert md.count(title)==1
    md=md.replace(title,f'Draft for research-team review · version {VERSION} · revision timestamp {REVISION_TIMESTAMP} · incorporates the dose-response, scaled-error contribution, exact-completeness and full-read editorial updates; existing experimental results only')
    anchor='The separate weight-learning experiment improved over equal weights under its'
    assert md.count(anchor)==1
    overview='Separately, all four non-medical assistance types show steadily increasing reductions in case-base retrieval error relative to their condition-specific purpose baselines as planted household signal increases; this ordered pattern is descriptive and does not change the fixed reviewed-case failure.\n\n'
    md=md.replace(anchor,overview+anchor)
    old='divide by the 794 applicants with a defined scaled error.'
    assert md.count(old)==1
    md=md.replace(old,'divide by the 794 applicants with a defined scaled error (844 total applicant IDs minus 50 transportation-only applicants, whose events have no scaled width).')
    old='Six-type browser checks covered retrieval,'
    assert md.count(old)==1
    md=md.replace(old,'Browser checks across all six assistance types covered retrieval,')
    return md
