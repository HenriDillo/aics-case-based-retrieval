# Synthetic case base

`study_intake.csv` is a byte-for-byte copy of the supplied v25 bundle's
`data/synthetic/v1_intake.csv`: 1,000 events, 844 applicant IDs and 57 columns.
The source bundle in Downloads remains unchanged. The app no longer reads
`mock_cases.csv`; that older demonstration fixture remains for historical reference.

The CSV uses `case_id` as applicant ID and `event_id` as an event number within
that applicant. The composite identifies an event. `control_no` is also preserved.
Blank values remain unknown. Granted amounts are blank and documented costs are
absent in that preserved intake-only file.

`study_complete.csv` is the current application default: the reconciled p=.50
synthetic case base with generated grants and costs. It is a copy of
research/generated/reconciled-primary/case_base_p50.csv. The research generator
produces these values offline; the application only displays recorded fields.
Food and cash relief have no documented cost under the rule. The app never
calculates a recommended amount, and experimental learned weights never configure it.

Only generated records belong here. Keep the repository private. Do not place
real DSWD records in the repository or use them with this prototype.

Set `AICS_CSV_PATH` only to another compatible synthetic study CSV and restart
the backend to load it. The old mock CSV schema is no longer supported by the app.
