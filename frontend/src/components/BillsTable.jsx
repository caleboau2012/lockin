import { formatCurrency, formatFrequency } from '../services/finance';

export function BillsTable({ items, selectedIds, onToggleItem }) {
  return (
    <section className="card bills-section">
      <div className="bills-header">
        <h2 className="section-title">Detected Recurring Bills</h2>
        <span className="section-hint">
          Check items to simulate reallocating them
        </span>
      </div>

      {items.length === 0 ? (
        <p className="empty-state">
          No recurring bills were detected in the last 365 days.
        </p>
      ) : (
        <div className="table-wrap">
          <table className="bills-table">
            <thead>
              <tr>
                <th className="col-check" aria-label="Select to cut" />
                <th>Merchant</th>
                <th>Category</th>
                <th>Cycle</th>
                <th className="col-amount">Monthly</th>
                <th className="col-flag">Note</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const checked = selectedIds.has(item.id);
                return (
                  <tr
                    key={item.id}
                    className={checked ? 'row-selected' : ''}
                    onClick={() => onToggleItem(item.id)}
                  >
                    <td
                      className="col-check"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => onToggleItem(item.id)}
                        aria-label={`Select ${item.merchant}`}
                      />
                    </td>
                    <td className="merchant-cell">{item.merchant}</td>
                    <td className="muted-cell">{item.category}</td>
                    <td className="muted-cell">
                      {formatFrequency(item.billing_frequency)}
                    </td>
                    <td className="col-amount">
                      {formatCurrency(item.monthly_equivalent)}
                    </td>
                    <td className="col-flag">
                      {item.flags.includes('price_creep') &&
                        item.price_change_amount ? (
                        <span className="tag tag-warn">
                          +{formatCurrency(item.price_change_amount)} ↑
                        </span>
                      ) : item.flags.includes('duplicate_category') ? (
                        <span className="tag tag-neutral">Overlap</span>
                      ) : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

