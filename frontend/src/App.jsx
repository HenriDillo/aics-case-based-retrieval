import { useEffect, useRef, useState } from 'react';
import { request } from './api.js';
import IntakeForm from './components/IntakeForm.jsx';
import Results from './components/Results.jsx';
import Comparison from './components/Comparison.jsx';

export default function App() {
  const [setup, setSetup] = useState(null);
  const [setupError, setSetupError] = useState(null);
  const [retry, setRetry] = useState(0);
  const [draft, setDraft] = useState({});
  const [submitted, setSubmitted] = useState(null);
  const [cases, setCases] = useState(null);
  const [screen, setScreen] = useState('intake');
  const [active, setActive] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState('');
  const mainRef = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    setSetupError(null);
    Promise.all([request('form-schema', { signal: controller.signal }), request('sample-cases', { signal: controller.signal })])
      .then(([schema, samples]) => { setSetup({ ...schema, samples }); setDraft(schema.empty_case); })
      .catch(problem => { if (problem.name !== 'AbortError') setSetupError(problem); });
    return () => controller.abort();
  }, [retry]);

  useEffect(() => {
    mainRef.current?.focus();
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [screen, active]);

  function changeField(key, value) {
    setDraft(current => ({ ...current, [key]: value }));
    setCases(null);
    setSubmitted(null);
    setNotice('Intake updated. Find similar cases again to refresh the comparison.');
  }

  function loadSample(sample) {
    setDraft(sample.case);
    setCases(null);
    setSubmitted(null);
    setError(null);
    setNotice(`${sample.label} sample loaded. You can edit any field before continuing.`);
  }

  async function retrieve() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const found = await request('similar-cases', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(draft) });
      setSubmitted(draft);
      setCases(found);
      setActive(0);
      setScreen('results');
    } catch (problem) { setError(problem); }
    finally { setBusy(false); }
  }

  return <>
    <a href="#main" className="skip-link">Skip to content</a>
    <header className="site-header"><div className="header-inner"><div className="brand"><strong>AICS <span>/</span> Case Reference</strong><span>Research prototype · Davao City</span></div>
      <nav aria-label="Main navigation"><button aria-current={screen === 'intake' ? 'page' : undefined} onClick={() => setScreen('intake')}>New case</button><button disabled={!cases} aria-current={screen !== 'intake' ? 'page' : undefined} onClick={() => setScreen('results')}>Retrieved cases</button></nav>
    </div></header>
    <div className="prototype-strip">Synthetic records only. No real client information is included.</div>
    <main id="main" tabIndex="-1" ref={mainRef}>
      {setupError ? <div className="error-box" role="alert"><h1>Case service unavailable</h1><p>Start the FastAPI backend on port 8000, then try again.</p><button onClick={() => setRetry(value => value + 1)}>Try again</button></div>
        : !setup ? <p role="status">Loading the intake form…</p>
          : screen === 'intake' ? <IntakeForm sections={setup.sections} samples={setup.samples} draft={draft} onChange={changeField} onLoad={loadSample} onSubmit={retrieve} busy={busy} error={error} notice={notice} />
            : screen === 'results' ? <Results cases={cases} intake={submitted} onEdit={() => setScreen('intake')} onCompare={index => { setActive(index); setScreen('comparison'); }} />
              : <Comparison cases={cases} active={active} intake={submitted} onBack={() => setScreen('results')} onMove={setActive} />}
    </main>
    <footer><span>AICS Case Reference</span><span>Thesis prototype · Ateneo de Davao University</span></footer>
  </>;
}
