export function ConnectCard({
  onConnectGmail,
  onConnectOutlook,
  showOutlook = false,
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
        {showOutlook && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onConnectOutlook}
          >
            Connect Outlook
          </button>
        )}
      </div>

      <div className="sample-trigger-wrap">
        <button type="button" className="btn-link" onClick={onRunSample}>
          View sample report
        </button>
      </div>

      <p className="trust-note">
        Read-only last 365 days · Redacted in RAM · Nothing stored ·{' '}
        <a href="/privacy.html" className="subtle-link">
          Privacy
        </a>
      </p>
    </section>
  );
}
