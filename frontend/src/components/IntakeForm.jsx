import { useEffect, useRef, useState } from 'react';
import Field from './Field.jsx';

export default function IntakeForm({ sections, samples, draft, onChange, onLoad, onSubmit, busy, error, notice }) {
  const [sampleId, setSampleId] = useState('');
  const formRef = useRef(null);
  const errorRef = useRef(null);
  useEffect(() => { errorRef.current?.focus(); }, [error]);

  function focusField(key) {
    const element = formRef.current?.querySelector(`#field-${key}`);
    const section = sections.find(item => item.fields.some(field => field.key === key));
    const details = formRef.current?.querySelector(`#section-${section?.id}`);
    if (details) details.open = true;
    if (element) element.focus();
    else details?.querySelector('summary')?.focus();
  }

  return <>
    <div className="page-heading"><div><h1>New case</h1><p>Enter the intake details to review past assistance cases.</p></div></div>
    <div className="sample-bar">
      <div><strong>Try a saved sample</strong><p>Load a synthetic study intake. Missing answers stay not recorded.</p></div>
      <div className="sample-controls"><label className="sr-only" htmlFor="sample">Saved sample case</label>
        <select id="sample" value={sampleId} onChange={event => setSampleId(event.target.value)}>
          <option value="">Choose a sample case</option>
          {samples.map(sample => <option key={sample.id} value={sample.id}>{sample.label}</option>)}
        </select>
        <button type="button" disabled={!sampleId || busy} onClick={() => onLoad(samples.find(sample => sample.id === sampleId))}>Load sample</button>
      </div>
    </div>
    <p className="status-line" role="status">{notice || 'Choose an assistance type. Leave unknown answers blank; use No or recorded none only when known.'}</p>
    <form ref={formRef} noValidate onSubmit={event => { event.preventDefault(); onSubmit(); }}>
      {error ? <div className="error-box" role="alert" tabIndex="-1" ref={errorRef}>
        <strong>{error.message}</strong>
        {error.details?.length ? <ul>{error.details.map((detail, index) => {
          const key = detail.loc?.[1];
          const field = sections.flatMap(section => section.fields).find(item => item.key === key);
          return <li key={`${key}-${index}`}>{field ? <button type="button" className="text-button" onClick={() => focusField(key)}>{field.label}: {detail.msg}</button> : detail.msg}</li>;
        })}</ul> : null}
      </div> : null}
      <fieldset disabled={busy} className="form-fields" aria-label="GIS intake fields">
      {sections.map((section, index) => <details className="form-section" key={section.id} id={`section-${section.id}`} open={index === 0 ? true : undefined}>
        <summary><span>{section.title}</span><span className="section-toggle" aria-hidden="true">+</span></summary>
        <div className="section-body">
          {section.description ? <p className="section-description">{section.description}</p> : null}
          {section.id === 'sector' ? <p className="section-description">Enter income sources as recorded on the intake. Record the six-month total separately.</p> : null}
          <div className="fields-grid">{section.fields.map(field => <Field key={field.key} field={field} value={draft[field.key]} onChange={value => onChange(field.key, value)} />)}</div>
        </div>
      </details>)}
      </fieldset>
      <div className="form-actions"><p>Past cases provide context. The assistance decision remains with the social worker.</p>
        <button type="submit" className="primary" disabled={busy}>{busy ? 'Finding cases…' : 'Find similar cases'}<span aria-hidden="true"> →</span></button>
      </div>
    </form>
  </>;
}
