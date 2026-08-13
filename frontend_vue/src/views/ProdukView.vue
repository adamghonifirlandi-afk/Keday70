<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import VueApexCharts from 'vue3-apexcharts';
import { Package, BadgePercent, TrendingUp, Award } from 'lucide-vue-next';
import api from '../api';
import { formatCurrency as fmtCurrencyUtil, formatCompactRupiah, formatNumber as fmtNumberUtil, formatPercent as fmtPercentUtil, formatCompactNumber } from '../utils/formatters';

const props = defineProps({
  data: Object,
  mode: String,
  filterValue: String,
  year: String
});

const viewData = ref(null);
const loading = ref(true);

const normalizeProductRows = (rows = []) => rows.map((item) => ({
  'Product Name': item['Product Name'],
  Category: item.Category ?? '-',
  Price: item.Price ?? 0,
  Cost: item.Cost ?? 0,
  MarginPct: item.MarginPct ?? 0,
  Revenue: Number(item.Revenue || 0),
  Qty: Number(item.Qty || 0),
  Transactions: Number(item.Transactions ?? item.Transaksi ?? 0)
}));

const buildFallbackFromDashboard = () => {
  const charts = props.data?.charts || {};
  const productAnalysis = normalizeProductRows(charts.product_analysis || []);
  const fallbackTop = normalizeProductRows(charts.product_revenue_top || charts.top_products || []);

  const soldProducts = (productAnalysis.length ? productAnalysis : fallbackTop)
    .filter((item) => Number(item.Revenue || 0) > 0)
    .sort((a, b) => Number(b.Revenue || 0) - Number(a.Revenue || 0));

  const categoryQtyRows = (charts.category_qty || []).map((item) => ({
    Kategori: item.Kategori,
    Qty: Number(item.Qty || 0)
  }));

  const avgMargin = soldProducts.length
    ? soldProducts.reduce((sum, item) => sum + Number(item.MarginPct || 0), 0) / soldProducts.length
    : 0;

  return {
    kpi: {
      sold_products: soldProducts.length,
      total_qty: soldProducts.reduce((sum, item) => sum + Number(item.Qty || 0), 0),
      avg_margin: Number(avgMargin.toFixed(1)),
      best_seller: soldProducts.length
        ? [...soldProducts].sort((a, b) => Number(b.Qty || 0) - Number(a.Qty || 0))[0]
        : null,
      highest_margin: soldProducts.length
        ? [...soldProducts].sort((a, b) => Number(b.MarginPct || 0) - Number(a.MarginPct || 0))[0]
        : null
    },
    top_products: soldProducts.slice(0, 8),
    category_qty: categoryQtyRows,
    products: soldProducts
  };
};

const fetchProducts = async () => {
  loading.value = true;
  try {
    const params = new URLSearchParams({ mode: props.mode });
    if (props.filterValue) params.append('value', props.filterValue);
    if (props.year) params.append('year', props.year);
    const res = await api.get('/dashboard/products', { params });
    viewData.value = res.data;
  } catch (error) {
    console.error(error);
    viewData.value = buildFallbackFromDashboard();
  } finally {
    loading.value = false;
  }
};

onMounted(fetchProducts);
watch([() => props.mode, () => props.filterValue, () => props.year, () => props.data], fetchProducts);

const productRows = computed(() => normalizeProductRows(viewData.value?.products || []));
const topRevenueProducts = computed(() => normalizeProductRows(viewData.value?.top_products || []));
const categoryQtyRows = computed(() => (viewData.value?.category_qty || []).map((item) => ({
  Kategori: item.Kategori,
  Qty: Number(item.Qty || 0)
})));

const hasSales = computed(() => topRevenueProducts.value.length > 0);
const totalQty = computed(() => Number(viewData.value?.kpi?.total_qty || 0));
const donutQtyTotal = computed(() => donutSeries.value.reduce((sum, n) => sum + Number(n || 0), 0));

const formatCurrency = (val) => fmtCurrencyUtil(Number(val || 0));
const formatCompactCurrency = (val) => formatCompactRupiah(Number(val || 0));
const formatNumber = (val) => fmtNumberUtil(Number(val || 0));
const formatPercent = (val) => fmtPercentUtil(Number(val || 0));

const highestMarginDisplay = computed(() => {
  const value = viewData.value?.kpi?.highest_margin;
  if (!value) return null;
  return value;
});

const kpiCards = computed(() => ([
  {
    id: 'sold-products',
    label: 'Produk Terjual',
    value: formatNumber(viewData.value?.kpi?.sold_products || 0),
    glow: 'bg-primary/10',
    iconWrap: 'bg-primary/10 border border-primary/20 text-primary',
    icon: Package
  },
  {
    id: 'avg-margin',
    label: 'Avg Margin Kotor Produk',
    value: formatPercent(viewData.value?.kpi?.avg_margin || 0),
    glow: 'bg-accent/10',
    iconWrap: 'bg-accent/10 border border-accent/20 text-accent',
    icon: BadgePercent
  },
  {
    id: 'best-seller',
    label: 'Produk Terlaris',
    value: viewData.value?.kpi?.best_seller?.['Product Name'] || '-',
    glow: 'bg-warning/10',
    iconWrap: 'bg-warning/10 border border-warning/20 text-warning',
    icon: TrendingUp
  },
  {
    id: 'highest-margin',
    label: 'Margin Kotor Produk Tertinggi',
    value: highestMarginDisplay.value?.['Product Name'] || '-',
    glow: 'bg-success/10',
    iconWrap: 'bg-success/10 border border-success/20 text-success',
    icon: Award
  }
]));

const chartColors = ['#4ECCA3', '#7F77DD', '#00B8D9', '#EF9F27', '#E24B4A', '#97C459', '#8B7CF5', '#C68B3C'];

const topRevenueMax = computed(() => {
  const maxRevenue = Math.max(...topRevenueProducts.value.map((item) => Number(item.Revenue || 0)), 0);
  if (!maxRevenue) return 100;
  return Math.ceil(maxRevenue * 1.15);
});

const revenueChartOptions = computed(() => ({
  chart: { type: 'bar', background: 'transparent', toolbar: { show: false } },
  theme: { mode: 'dark' },
  colors: chartColors,
  plotOptions: {
    bar: {
      horizontal: false,
      distributed: true,
      borderRadius: 4,
      columnWidth: '56%'
    }
  },
  dataLabels: { enabled: false },
  legend: { show: false },
  stroke: { show: false },
  grid: { borderColor: 'rgba(255,255,255,0.05)', strokeDashArray: 4 },
  xaxis: {
    categories: topRevenueProducts.value.map((item) => item['Product Name']),
    axisBorder: { show: false },
    axisTicks: { show: false },
    labels: {
      formatter: (value) => value.length > 12 ? `${value.slice(0, 12)}...` : value,
      style: { colors: '#888', fontSize: '11px' },
      trim: false,
      hideOverlappingLabels: false
    }
  },
  yaxis: {
    min: 0,
    max: topRevenueMax.value,
    tickAmount: 5,
    labels: {
      formatter: (value) => formatCompactNumber(value),
      style: { colors: '#888' }
    }
  },
  tooltip: { theme: 'dark', y: { formatter: (value) => formatCurrency(value) } }
}));

const revenueChartSeries = computed(() => [{
  name: 'Pendapatan',
  data: topRevenueProducts.value.map((item) => Number(item.Revenue || 0))
}]);

const donutOptions = computed(() => ({
  chart: { type: 'donut', background: 'transparent' },
  theme: { mode: 'dark' },
  colors: ['#4ECCA3', '#7F77DD', '#00B8D9', '#EF9F27', '#E24B4A', '#97C459'],
  labels: categoryQtyRows.value.map((item) => item.Kategori),
  stroke: { show: true, colors: ['#161B22'], width: 2 },
  legend: { position: 'bottom', labels: { colors: '#bbb' } },
  dataLabels: {
    enabled: false
  },
  plotOptions: {
    pie: {
      donut: {
        size: '68%',
        labels: {
          show: true,
          value: {
            formatter: (value) => `${formatNumber(Number(value))} item`,
            color: '#fff',
            fontSize: '18px',
            fontWeight: '700'
          },
          total: {
            show: true,
            label: 'Total Terjual',
            formatter: () => `${formatNumber(donutQtyTotal.value)} item`,
            color: '#fff',
            style: { fontSize: '13px', fontWeight: 700 }
          }
        }
      }
    }
  },
  tooltip: {
    theme: 'dark',
    y: { formatter: (value) => `${formatNumber(value)} item` }
  }
}));

const donutSeries = computed(() => categoryQtyRows.value.map((item) => Number(item.Qty || 0)));

const categoryClass = (category) => {
  const value = String(category || '').toLowerCase();
  if (value.includes('coffee')) return 'bg-success/20 text-success';
  if (value.includes('non')) return 'bg-secondary/20 text-secondary';
  return 'bg-warning/20 text-warning';
};
</script>

<template>
  <div class="flex flex-col gap-6 w-full pb-10">
    <div v-if="loading" class="flex justify-center p-10">
      <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
    </div>

    <template v-else-if="viewData">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        <div
          v-for="card in kpiCards"
          :key="card.id"
          class="glass-card p-6 flex items-center justify-between group overflow-hidden relative"
        >
          <div :class="['absolute -right-6 -top-6 w-24 h-24 rounded-full blur-2xl transition-all duration-500 group-hover:opacity-100 opacity-80', card.glow]"></div>
          <div class="flex flex-col gap-1 z-10 pr-10 min-w-0">
            <span class="text-[11px] font-semibold uppercase tracking-widest text-white/40">{{ card.label }}</span>
            <span class="text-base md:text-lg font-bold text-white tabular-nums whitespace-nowrap tracking-tight">{{ card.value }}</span>
          </div>
          <div :class="['absolute top-4 right-4 w-8 h-8 md:w-9 md:h-9 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform', card.iconWrap]">
            <component :is="card.icon" class="w-4 h-4" />
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="glass-card p-6 lg:col-span-2">
          <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50 mb-4">Top 8 Produk per Pendapatan</h3>
          <div v-if="hasSales" class="h-[360px] w-full">
            <VueApexCharts type="bar" height="100%" :options="revenueChartOptions" :series="revenueChartSeries" />
          </div>
          <div v-else class="h-[360px] flex items-center justify-center text-sm text-white/40">
            Tidak ada data produk pada filter ini.
          </div>
        </div>

        <div class="glass-card p-6">
          <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50 mb-4">Kategori Terjual</h3>
          <div v-if="categoryQtyRows.length" class="h-[360px] flex items-center justify-center">
            <VueApexCharts type="donut" height="100%" width="100%" :options="donutOptions" :series="donutSeries" />
          </div>
          <div v-else class="h-[360px] flex items-center justify-center px-8 text-center text-sm text-white/40">
            Data jumlah terjual per kategori belum tersedia. Restart backend sekali agar data produk terbaru terbaca.
          </div>
        </div>
      </div>

      <div class="glass-card p-6 w-full">
        <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50 mb-4">Rincian Produk</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-white/80">
            <thead class="text-xs uppercase bg-white/5 text-white/50">
              <tr>
                <th class="px-4 py-3 rounded-tl-lg font-medium">Produk</th>
                <th class="px-4 py-3 font-medium">Kategori</th>
                <th class="px-4 py-3 font-medium text-center">Qty</th>
                <th class="px-4 py-3 font-medium text-right">Harga</th>
                <th class="px-4 py-3 font-medium text-right">Modal</th>
                <th class="px-4 py-3 rounded-tr-lg font-medium text-right">Revenue</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in productRows"
                :key="item['Product Name']"
                class="border-b border-white/5 hover:bg-white/5 transition-colors"
              >
                <td class="px-4 py-3 font-medium">{{ item['Product Name'] }}</td>
                <td class="px-4 py-3">
                  <span :class="categoryClass(item.Category)" class="px-2 py-1 rounded-md text-[10px] font-semibold">
                    {{ item.Category }}
                  </span>
                </td>
                <td class="px-4 py-3 text-center text-white/60">{{ formatNumber(item.Qty) }}</td>
                <td class="px-4 py-3 text-right">{{ item.Price ? formatCurrency(item.Price) : '-' }}</td>
                <td class="px-4 py-3 text-right">{{ item.Cost ? formatCurrency(item.Cost) : '-' }}</td>
                <td class="px-4 py-3 text-right font-semibold text-primary">{{ formatCurrency(item.Revenue) }}</td>
              </tr>
              <tr v-if="!productRows.length">
                <td colspan="6" class="px-4 py-10 text-center text-white/40">Tidak ada data produk pada filter ini.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
