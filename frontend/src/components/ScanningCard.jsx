export function ScanningCard() {
  return (
    <section className="card scanning-card" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <p className="scanning-title">
        Scanning recent receipts &amp; stripping PII in memory…
      </p>
      <p className="scanning-subtitle">
        Checking up to 50 billing emails from the last 90 days. Nothing is saved
        to disk.
      </p>
    </section>
  );
}

