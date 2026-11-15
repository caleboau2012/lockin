export function ConnectCard({
  onConnectGmail,
  onConnectOutlook,
  onRunSample,
  errorMessage,
}) {
  return (
    <section className="card connect-card">
      <h1 className="brand-title">LockIn</h1>
      <p className="brand-subtitle">
        Audit recurring bills &amp; see what you could be earning — without linking
        your bank.
      </p>

      {errorMessage && (
        <div className="error-banner" role="alert">
          {errorMessage}
        </div>
      )}

      <div className="connect-actions">
        <button
          type="button"
          className="btn btn-primary"
          onClick={onConnectGmail}
        >
          Connect Gmail
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onConnectOutlook}
        >
          Connect Outlook
        </button>
      </div>

      {import.meta.env.DEV && (
        <div className="sample-trigger-wrap">
          <button type="button" className="btn-link" onClick={onRunSample}>
            Try sample receipts (local dev)
          </button>
        </div>
      )}

      <p className="trust-note">
        Read-only last 90 days · Redacted in RAM · Nothing stored ·{' '}
        <a href="/privacy.html" className="subtle-link">
          Privacy
        </a>
      </p>
    </section>
  );
}

