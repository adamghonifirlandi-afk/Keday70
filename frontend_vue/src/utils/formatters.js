const nfNumber = new Intl.NumberFormat('id-ID');
const nfCurrency = new Intl.NumberFormat('id-ID', {
  style: 'currency',
  currency: 'IDR',
  minimumFractionDigits: 0,
});

export function formatNumber(value) {
  return nfNumber.format(Number(value || 0));
}

export function formatCurrency(value) {
  return nfCurrency.format(Number(value || 0));
}

function compactSuffix(n) {
  const abs = Math.abs(Number(n || 0));
  if (abs >= 1_000_000_000) return { div: 1_000_000_000, suffix: ' M' };
  if (abs >= 1_000_000) return { div: 1_000_000, suffix: ' jt' };
  if (abs >= 1_000) return { div: 1_000, suffix: ' rb' };
  return { div: 1, suffix: '' };
}

export function formatCompactNumber(value, { maximumFractionDigits = 1 } = {}) {
  const num = Number(value || 0);
  const { div, suffix } = compactSuffix(num);
  if (div === 1) return formatNumber(num);

  const scaled = num / div;
  // Indonesia uses comma for decimals; thousands are dots via formatNumber elsewhere.
  const fixed = scaled.toFixed(maximumFractionDigits);
  const trimmed = fixed.replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1');
  return `${trimmed.replace('.', ',')}${suffix}`;
}

export function formatCompactRupiah(value, { maximumFractionDigits = 1 } = {}) {
  const num = Number(value || 0);
  // If < 1jt, show full number with dots for readability.
  if (Math.abs(num) < 1_000_000) return `Rp ${formatNumber(num)}`;
  return `Rp ${formatCompactNumber(num, { maximumFractionDigits })}`;
}

export function formatPercent(value, { maximumFractionDigits = 1 } = {}) {
  const num = Number(value || 0);
  return `${num.toFixed(maximumFractionDigits).replace('.', ',')}%`;
}

export function formatCategory(cat) {
  if (!cat) return cat;
  if (cat === 'Sewa & Tempat') return 'Sewa Tempat';
  if (cat === 'Operasional') return 'Administrasi & Perawatan';
  return cat;
}

