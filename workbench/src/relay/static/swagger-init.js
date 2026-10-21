/* Swagger assets and API calls stay on the same origin, including in offline class setups. */
async function relayRequest(request) {
  const url = new URL(request.url, window.location.origin);
  if (
    url.origin !== window.location.origin ||
    !(url.pathname === '/openapi.json' || url.pathname.startsWith('/api/'))
  ) {
    throw new Error('Swagger UI can only call this Relay instance.');
  }
  request.credentials = 'same-origin';
  const method = (request.method || 'GET').toUpperCase();
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    // Fetch each time: changing demo persona rotates both the cookie and CSRF token.
    const response = await fetch('/api/v1/session', { credentials: 'same-origin' });
    if (response.ok) {
      const session = await response.json();
      request.headers['X-CSRF-Token'] = session.csrf_token;
    } else if (response.status !== 401 || url.pathname !== '/api/v1/demo/session') {
      throw new Error('Create a demo session before sending this request.');
    }
    if (/\/proposals(?:\/[^/]+\/decision)?$/.test(url.pathname)) {
      const existingKey = Object.keys(request.headers).find(
        (key) => key.toLowerCase() === 'idempotency-key',
      );
      if (!existingKey || !request.headers[existingKey]) {
        request.headers['Idempotency-Key'] = crypto.randomUUID();
      }
    }
  }
  return request;
}

window.ui = SwaggerUIBundle({
  url: '/openapi.json',
  dom_id: '#swagger-ui',
  layout: 'BaseLayout',
  deepLinking: true,
  filter: true,
  displayRequestDuration: true,
  defaultModelsExpandDepth: 0,
  validatorUrl: null,
  queryConfigEnabled: false,
  persistAuthorization: false,
  requestInterceptor: relayRequest,
  presets: [SwaggerUIBundle.presets.apis],
});
