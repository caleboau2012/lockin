import { calculateCompoundedValue } from './finance';

function escapeCsvCell(value) {
  const str = String(value);
  if (/[",\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

export function exportAuditToCsv(audit, selectedIds) {
  const headers = [
    'Merchant',
    'Category',
    'Frequency',
    'Latest Bill ($)',
    'Monthly Equivalent ($)',
    'Selected to Cut',
    'Flags',
    '5-Yr Value @ 7% ($)',
    '10-Yr Value @ 7% ($)',
    'Last Billed Date',
  ];

  const rows = audit.items.map((item) => {
    const isSelected = selectedIds.has(item.id);
    const fiveYr = calculateCompoundedValue(
      item.monthly_equivalent,
      5,
      audit.annual_return_rate
    );
    const tenYr = calculateCompoundedValue(
      item.monthly_equivalent,
      10,
      audit.annual_return_rate
    );

    return [
      item.merchant,
      item.category,
      item.billing_frequency,
      item.latest_amount.toFixed(2),
      item.monthly_equivalent.toFixed(2),
      isSelected ? 'Yes' : 'No',
      item.flags.join('; '),
      fiveYr.toFixed(2),
      tenYr.toFixed(2),
      item.last_billed_date,
    ].map(escapeCsvCell);
  });

  const csvContent = [
    headers.map(escapeCsvCell).join(','),
    ...rows.map((row) => row.join(',')),
  ].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const today = new Date().toISOString().slice(0, 10);
  link.href = url;
  link.download = `lockin-audit-${today}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

