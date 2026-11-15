export function AlertsList({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return null;
  }

  return (
    <section className="alerts-section" aria-label="Detected billing alerts">
      {alerts.map((alert, idx) => (
        <div
          key={`${alert.type}-${idx}`}
          className={`alert-row alert-${alert.type}`}
        >
          <span className="alert-badge">
            {alert.type === 'price_creep' ? '▲ Price Creep' : '● Overlap'}
          </span>
          <span className="alert-text">{alert.message}</span>
        </div>
      ))}
    </section>
  );
}

