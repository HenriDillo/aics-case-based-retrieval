export default function Comparison({ cases, active, intake, onBack, onMove }) {
  const past = cases[active];
  return <>
    <button className="text-button back-link" onClick={onBack}>← Back to retrieved cases</button>
    <div className="page-heading"><div><h1>Case comparison</h1><p>Compare the intake and the closed record, field by field.</p></div>
      <div className="comparison-navigation"><button disabled={active === 0} onClick={() => onMove(active - 1)}>← Previous case</button><button disabled={active === cases.length - 1} onClick={() => onMove(active + 1)}>Next case →</button></div>
    </div>
    <div className="comparison-note"><span className="same-key">Same</span><span>marks equal field values. Differences remain visible. Missing values are shown as “Not recorded”.</span></div>
    <div className="comparison-scroll" tabIndex="0" aria-label="Field by field case comparison">
      <table className="comparison-table">
        <caption className="sr-only">Current intake {intake.control_number} compared with past case {past.control_number}</caption>
        <thead><tr><th scope="col">GIS field</th><th scope="col"><span>New case</span><strong>{intake.control_number}</strong><span>{intake.intake_month} {intake.intake_year}</span></th><th scope="col"><span>Past case</span><strong>{past.control_number}</strong><span className="past-date">{past.intake_month} {past.intake_year}</span></th></tr></thead>
        {past.comparison.map(section => <tbody key={section.id}>
          <tr className="table-section"><th colSpan="3" scope="rowgroup">{section.title}</th></tr>
          {section.rows.map(row => <tr key={row.key} className={row.status === 'same' ? 'matching-row' : ''}>
            <th scope="row">{row.label}</th><td>{row.current}</td><td><div className="compared-value"><span>{row.past}</span>{row.status === 'same' ? <span className="same-key">Same</span> : null}</div></td>
          </tr>)}
        </tbody>)}
      </table>
    </div>
  </>;
}
