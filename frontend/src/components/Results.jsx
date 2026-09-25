import { money } from '../api.js';

export default function Results({ cases, intake, onEdit, onCompare }) {
  return <>
    <div className="page-heading"><div><h1>Retrieved cases</h1><p>Review the circumstances and assistance recorded in each past case.</p></div>
      <button onClick={onEdit}>Edit intake</button>
    </div>
    <div className="intake-context"><span>Current intake</span><strong>{intake.control_number}</strong><span className="capitalize">{intake.assistance_type}</span><span>{intake.purpose}</span></div>
    {cases.length ? <div className="notice"><strong>About these references</strong><p>{cases[0].explanation_context} Open a comparison to see the fields side by side for your actual intake.</p></div> : null}
    <div className="results-label"><h2>Past case records</h2><span>Amounts are recorded outcomes, not recommendations.</span></div>
    {cases.length ? <div className="case-list">{cases.map((item, index) => <article className="case-record" key={item.control_number}>
      <div className="record-top">
        <div className="intake-date"><span className="small-label">Month of intake</span><strong>{item.intake_month}</strong><span>{item.intake_year}</span></div>
        <div className="record-description"><h3 className="capitalize">{item.provided_type} assistance</h3><p>{item.provided_purpose}</p><span className="record-id">{item.control_number}</span></div>
        <dl className="record-amounts"><div><dt>Amount requested</dt><dd>{money(item.amount_requested)}</dd></div><div><dt>Amount granted</dt><dd>{money(item.amount_granted)}</dd></div></dl>
        <button onClick={() => onCompare(index)} aria-label={`Compare case ${item.control_number}`}>Compare case <span aria-hidden="true">→</span></button>
      </div>
      <div className="record-explanation"><strong>Why this case was retrieved</strong><ul>{item.matched_fields.map(text => <li key={text}>{text}</li>)}</ul></div>
    </article>)}</div> : <div className="empty-state"><h2>No past cases returned</h2><p>You can review the intake and try again.</p><button onClick={onEdit}>Edit intake</button></div>}
  </>;
}
