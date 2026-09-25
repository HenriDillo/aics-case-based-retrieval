import { useState } from 'react';
import { money } from '../api.js';

function MoneyInput({ id, value, onChange, describedBy }) {
  const [focused, setFocused] = useState(false);
  const raw = value ?? '';
  // Formatting only: no rounding, ceiling, aggregation, or amount suggestions.
  const shown = focused || raw === '' || !Number.isFinite(Number(raw)) ? raw : money(raw).replace('₱', '');
  return <div className="money-input"><span aria-hidden="true">₱</span>
    <input id={id} type="text" inputMode="decimal" value={shown}
      aria-describedby={describedBy} autoComplete="off"
      onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
      onChange={event => onChange(event.target.value.replaceAll(',', '').replaceAll('₱', ''))} />
  </div>;
}

export default function Field({ field, value, onChange }) {
  const id = `field-${field.key}`;
  const hintId = field.hint ? `${id}-hint` : undefined;
  if (field.kind === 'multi') {
    return <fieldset className="multi-field">
      <legend>{field.label}</legend>
      <p className="field-hint">Select all that apply. Leave unchecked if none are reported.</p>
      <div className="checkbox-grid">{field.options.map(option => <label key={option} className="check-label">
        <input type="checkbox" checked={(value ?? []).includes(option)}
          onChange={event => onChange(event.target.checked ? [...(value ?? []), option] : value.filter(item => item !== option))} />
        <span>{option}</span>
      </label>)}</div>
    </fieldset>;
  }
  return <div className="field">
    <label htmlFor={id}>{field.label}{field.kind === 'money' ? ' (₱)' : ''}{field.optional ? <span className="optional"> · optional</span> : null}</label>
    {field.kind === 'money' ? <MoneyInput id={id} value={value} onChange={onChange} describedBy={hintId} />
      : field.kind === 'select' || field.kind === 'boolean' ? <select id={id} value={value ?? ''} aria-describedby={hintId}
        onChange={event => onChange(field.kind === 'boolean' ? (event.target.value === '' ? null : event.target.value === 'true') : event.target.value)}>
        <option value="">Select an option</option>
        {field.kind === 'boolean' ? <><option value="true">Yes</option><option value="false">No</option></>
          : field.options.map(option => <option key={option} value={option}>{option}</option>)}
      </select>
      : <input id={id} type={['count', 'year'].includes(field.kind) ? 'number' : 'text'}
        step={['count', 'year'].includes(field.kind) ? '1' : undefined}
        value={value ?? ''} onChange={event => onChange(event.target.value)} aria-describedby={hintId} autoComplete="off" />}
    {field.hint ? <p id={hintId} className="field-hint">{field.hint}</p> : null}
  </div>;
}
