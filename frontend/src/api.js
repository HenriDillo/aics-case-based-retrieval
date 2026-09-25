export async function request(path, options = {}) {
  const response = await fetch(`/api/${path}`, { cache: 'no-store', ...options });
  if (!response.ok) {
    let body;
    try { body = await response.json(); } catch { /* Proxy may return plain text. */ }
    const error = new Error(response.status === 422
      ? 'Please check the intake details below.'
      : 'The case service could not complete this request. Check that the backend is running, then try again.');
    error.details = Array.isArray(body?.detail) ? body.detail : [];
    throw error;
  }
  return response.json();
}

export const currency = new Intl.NumberFormat('en-PH', {
  style: 'currency', currency: 'PHP', minimumFractionDigits: 2, maximumFractionDigits: 2,
});

export function money(value) {
  return value === null || value === undefined ? 'Not recorded' : currency.format(value);
}
