import { calculateCompoundedValue, formatCurrency } from '../services/finance';

export function SummaryStrip({
  totalMonthlyRecurring,
  totalAnnualRecurring,
  selectedMonthlySavings,
  selectedCount,
  annualReturnRate,
}) {
  const fiveYearValue = calculateCompoundedValue(
    selectedMonthlySavings,
    5,
    annualReturnRate
  );
  const tenYearValue = calculateCompoundedValue(
    selectedMonthlySavings,
    10,
    annualReturnRate
  );
  const ratePct = Math.round(annualReturnRate * 100);

  return (
    <section className="summary-strip" aria-label="Audit summary">
      <div className="summary-cell">
        <span className="summary-label">Recurring Spend</span>
        <strong className="summary-value">
          {formatCurrency(totalMonthlyRecurring)}
          <span className="summary-unit"> / mo</span>
        </strong>
        <span className="summary-sub">
          {formatCurrency(totalAnnualRecurring, { wholeDollars: true })} / yr
        </span>
      </div>

      <div className="summary-cell">
        <span className="summary-label">Selected to Cut</span>
        <strong className="summary-value">
          {formatCurrency(selectedMonthlySavings)}
          <span className="summary-unit"> / mo</span>
        </strong>
        <span className="summary-sub">
          {selectedCount} {selectedCount === 1 ? 'item' : 'items'} checked
        </span>
      </div>

      <div className="summary-cell summary-cell-highlight">
        <span className="summary-label">10-Yr Value (@ {ratePct}%)</span>
        <strong className="summary-value summary-value-accent">
          {formatCurrency(tenYearValue, { wholeDollars: true })}
        </strong>
        <span className="summary-sub">
          5-Yr: {formatCurrency(fiveYearValue, { wholeDollars: true })}
        </span>
      </div>
    </section>
  );
}

