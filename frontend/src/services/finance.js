/**
 * Deterministic future value of reallocating a monthly recurring amount
 * into a compounding vehicle (ordinary monthly annuity).
 *
 * FV = PMT * (((1 + r/12)^(12 * years) - 1) / (r/12))
 */
export function calculateCompoundedValue(
  monthlyAmount,
  years,
  annualRate = 0.07
) {
  if (monthlyAmount <= 0 || years <= 0) {
    return 0;
  }
  const months = years * 12;
  if (annualRate <= 0) {
    return monthlyAmount * months;
  }
  const monthlyRate = annualRate / 12;
  const futureValue =
    monthlyAmount * ((Math.pow(1 + monthlyRate, months) - 1) / monthlyRate);
  return Math.round(futureValue * 100) / 100;
}

export function formatCurrency(amount, { wholeDollars = false } = {}) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: wholeDollars ? 0 : 2,
    maximumFractionDigits: wholeDollars ? 0 : 2,
  }).format(amount);
}

export function formatFrequency(freq) {
  switch (freq) {
    case 'monthly':
      return 'Monthly';
    case 'annual':
      return 'Annual';
    case 'quarterly':
      return 'Quarterly';
    case 'weekly':
      return 'Weekly';
    default:
      return 'One-time';
  }
}

