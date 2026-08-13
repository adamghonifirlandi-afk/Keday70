<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import VueApexCharts from "vue3-apexcharts";
import { TrendingUp, TrendingDown, ShoppingCart, Settings2, Percent } from 'lucide-vue-next';
import api from '../api';
import { formatCurrency, formatCompactRupiah, formatCompactNumber, formatPercent, formatCategory } from '../utils/formatters';

const props = defineProps({ mode: String, filterValue: String, year: String });

const data = ref(null);
const expenseData = ref(null);
const loading = ref(true);

// ── Format helpers ─────────────────────────────────────────────────────────────
const fmtCurrency = (v) => formatCurrency(Math.abs(v ?? 0));
const fmtCompact = (v) => formatCompactNumber(v ?? 0);
const expenseColors = ['#EF9F27', '#7F77DD', '#00B8D9', '#E24B4A', '#97C459', '#8B7CF5', '#F59E0B', '#34D399', '#60A5FA', '#F472B6'];
const expenseColor = (index) => expenseColors[index % expenseColors.length];

// ── Fetch ───────────────────────────────────────────────────────────────────────
const fetchAll = async () => {
  loading.value = true;
  try {
    const params = {};
    if (props.mode) params.mode = props.mode;
    if (props.filterValue) params.value = props.filterValue;
    if (props.year) params.year = props.year;

    const [profitRes, expenseRes] = await Promise.all([
      api.get('/dashboard/profit', { params }),
      api.get('/dashboard/expenses', { params }),
    ]);
    data.value = profitRes.data;
    expenseData.value = expenseRes.data;
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchAll);
watch([() => props.mode, () => props.filterValue, () => props.year], () => {
  if (props.filterValue) {
    fetchAll();
  }
});

// ── KPI Cards ──────────────────────────────────────────────────────────────────
const kpi = computed(() => data.value?.kpi ?? {});

const cards = computed(() => [
  {
    id: 'revenue',
    label: 'PENDAPATAN',
    value: kpi.value.total_revenue ?? 0,
    color: '#4ECCA3',
    borderColor: 'border-b-[#4ECCA3]',
    glowClass: 'bg-[#4ECCA3]/10',
    icon: TrendingUp,
    iconColor: 'text-[#4ECCA3]',
  },
  {
    id: 'hpp',
    label: 'BAHAN BAKU',
    value: kpi.value.total_belanja ?? 0,
    color: '#EF9F27',
    borderColor: 'border-b-[#EF9F27]',
    glowClass: 'bg-[#EF9F27]/10',
    icon: ShoppingCart,
    iconColor: 'text-[#EF9F27]',
    negative: true,
  },
  {
    id: 'ops',
    label: 'BIAYA OPERASIONAL',
    value: kpi.value.total_ops ?? 0,
    color: '#7F77DD',
    borderColor: 'border-b-[#7F77DD]',
    glowClass: 'bg-[#7F77DD]/10',
    icon: Settings2,
    iconColor: 'text-[#7F77DD]',
    negative: true,
  },
  {
    id: 'margin',
    label: 'MARGIN LABA BERSIH',
    value: kpi.value.margin_pct ?? 0,
    isPercent: true,
    color: '#97C459',
    borderColor: 'border-b-[#97C459]',
    glowClass: 'bg-[#97C459]/10',
    icon: Percent,
    iconColor: 'text-[#97C459]',
  },
]);

// ── Waterfall Chart ────────────────────────────────────────────────────────────
// Build 5 bars: Pendapatan, Bahan Baku, Biaya Ops, Laba Kotor, Laba Bersih
const waterfallBars = computed(() => {
  const r = kpi.value.total_revenue ?? 0;
  const b = kpi.value.total_belanja ?? 0;
  const o = kpi.value.total_ops ?? 0;
  const gp = r - b;
  const laba = kpi.value.estimasi_laba ?? 0;
  return [
    { label: 'Pendapatan', value: r,    color: '#4ECCA3' },
    { label: 'Bahan Baku', value: -b,   color: '#EF9F27' },
    { label: 'Biaya Ops',  value: -o,   color: '#7F77DD' },
    { label: 'Laba Kotor', value: gp, color: gp >= 0 ? '#97C459' : '#E24B4A' },
    { label: 'Laba Bersih', value: laba, color: laba >= 0 ? '#97C459' : '#E24B4A' },
  ];
});

const waterfallOptions = computed(() => ({
  chart: {
    type: 'bar',
    background: 'transparent',
    toolbar: { show: false },
    fontFamily: 'Inter, sans-serif',
    animations: { enabled: true, speed: 600 },
  },
  theme: { mode: 'dark' },
  colors: waterfallBars.value.map(b => b.color),
  plotOptions: {
    bar: {
      borderRadius: 5,
      columnWidth: '55%',
      distributed: true,
      dataLabels: { position: 'top' },
    },
  },
  dataLabels: {
    enabled: true,
    formatter: (val) => {
      const sign = val < 0 ? '-' : '';
      return sign + formatCompactRupiah(Math.abs(val));
    },
    style: { colors: ['rgba(255,255,255,0.85)'], fontSize: '11px', fontWeight: '600' },
    offsetY: -22,
  },
  xaxis: {
    categories: waterfallBars.value.map(b => b.label),
    axisBorder: { show: false },
    axisTicks: { show: false },
    labels: { style: { colors: '#888', fontSize: '12px' } },
  },
  yaxis: {
    labels: {
      formatter: (val) => fmtCompact(val),
      style: { colors: '#888' },
    },
  },
  grid: { borderColor: 'rgba(255,255,255,0.05)', strokeDashArray: 4 },
  legend: { show: false },
  tooltip: {
    theme: 'dark',
    y: { formatter: (val) => (val < 0 ? '-' : '') + fmtCurrency(Math.abs(val)) },
  },
}));

const waterfallSeries = computed(() => [{
  name: 'Nilai',
  data: waterfallBars.value.map(b => b.value),
}]);

// ── Margin Trend Chart ──────────────────────────────────────────────────────────
const marginTrend = computed(() => data.value?.margin_trend ?? []);

const marginChartOptions = computed(() => ({
  chart: {
    type: 'line',
    background: 'transparent',
    toolbar: { show: false },
    fontFamily: 'Inter, sans-serif',
  },
  theme: { mode: 'dark' },
  colors: ['#97C459'],
  stroke: { curve: 'smooth', width: 3 },
  markers: { size: 5, colors: ['#97C459'], strokeColors: '#161B22', strokeWidth: 2, hover: { size: 7 } },
  dataLabels: { enabled: false },
  xaxis: {
    categories: marginTrend.value.map(d => d.Label),
    axisBorder: { show: false },
    axisTicks: { show: false },
    labels: { style: { colors: '#888', fontSize: '11px' } },
  },
  yaxis: {
    labels: {
      formatter: (v) => formatPercent(v, { maximumFractionDigits: 1 }),
      style: { colors: '#888' },
    },
  },
  grid: { borderColor: 'rgba(255,255,255,0.05)', strokeDashArray: 4 },
  tooltip: { theme: 'dark', y: { formatter: (v) => formatPercent(v, { maximumFractionDigits: 1 }) } },
}));

const marginSeries = computed(() => [{
  name: 'Margin',
  data: marginTrend.value.map(d => d.Margin),
}]);

// ── Donut (Komposisi) ──────────────────────────────────────────────────────────
const composition = computed(() => expenseData.value?.composition ?? []);

const donutOptions = computed(() => ({
  chart: { type: 'donut', background: 'transparent', fontFamily: 'Inter, sans-serif' },
  theme: { mode: 'dark' },
  colors: composition.value.map((_, i) => expenseColor(i)),
  labels: composition.value.map(d => d.Label),
  stroke: { show: true, colors: ['#161B22'], width: 2 },
  legend: { show: false },
  dataLabels: {
    enabled: false,
  },
  plotOptions: {
    pie: {
      donut: {
        size: '75%',
        labels: {
          show: false,
        },
      },
    },
  },
  tooltip: { theme: 'dark', y: { formatter: (v) => fmtCurrency(v) } },
}));

const donutSeries = computed(() => composition.value.map(d => d.Jumlah));

// ── Summary table ──────────────────────────────────────────────────────────────
const summary = computed(() => data.value?.summary ?? []);

// ── Top items ──────────────────────────────────────────────────────────────────
const topItems = computed(() => expenseData.value?.top_items?.slice(0, 5) ?? []);
</script>

<template>
  <div class="flex flex-col gap-6 w-full pb-10">

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="relative">
        <div class="w-12 h-12 rounded-full border-2 border-primary/20 animate-spin border-t-primary"></div>
        <div class="absolute inset-0 flex items-center justify-center">
          <div class="w-4 h-4 rounded-full bg-primary/40 animate-pulse"></div>
        </div>
      </div>
    </div>

    <template v-else-if="data">

      <!-- ══ 4 KPI Cards (Gambar 1 style) ══════════════════════════════════════ -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="card in cards" :key="card.id"
          class="glass-card p-6 flex items-center justify-between group overflow-hidden relative"
        >
          <div class="flex flex-col gap-1 z-10 pr-10 min-w-0">
            <span class="text-[11px] font-semibold uppercase tracking-widest text-white/40">{{ card.label }}</span>
            <span v-if="card.isPercent" class="text-base md:text-lg font-bold text-white tabular-nums whitespace-nowrap tracking-tight">
              {{ formatPercent(card.value, { maximumFractionDigits: 1 }) }}
            </span>
            <span v-else class="text-base md:text-lg font-bold text-white tabular-nums whitespace-nowrap tracking-tight">
              {{ formatCurrency(card.value) }}
            </span>
          </div>
          <div class="absolute top-4 right-4 w-8 h-8 md:w-9 md:h-9 rounded-2xl border border-white/5 flex items-center justify-center"
               :style="{ backgroundColor: card.color + '1A' }">
            <component :is="card.icon" class="w-4 h-4" :class="card.iconColor" />
          </div>
        </div>
      </div>

      <!-- ══ Row 2: Waterfall + Ringkasan ══════════════════════════════════════ -->
      <div class="grid grid-cols-1 lg:grid-cols-5 gap-5">

        <!-- Waterfall Chart (gambar 1 style: batang warna berbeda) -->
        <div class="lg:col-span-3 glass-card p-6">
          <div class="mb-4">
            <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50">Breakdown Laba Rugi</h3>
          </div>
          <div class="h-72 w-full mt-2">
            <VueApexCharts type="bar" height="100%" :options="waterfallOptions" :series="waterfallSeries" />
          </div>
        </div>

        <!-- Ringkasan Komponen (gambar 2) -->
        <div class="lg:col-span-2 glass-card p-6 flex flex-col">
          <div class="mb-4">
            <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50">Ringkasan Komponen</h3>
          </div>
          <div class="flex flex-col gap-0 flex-1">
            <div
              v-for="(item, i) in summary" :key="i"
              class="flex items-center justify-between py-3 border-b border-white/5 last:border-0"
            >
              <span
                class="text-sm"
                :class="{
                  'text-white font-semibold': item.Komponen === 'Laba Kotor' || item.Komponen === 'Laba Bersih',
                  'text-white/60': item.Komponen !== 'Laba Kotor' && item.Komponen !== 'Laba Bersih'
                }"
              >{{ item.Komponen === 'HPP / Bahan Baku' ? 'Bahan Baku' : item.Komponen }}</span>
              <span
                class="text-sm font-bold tabular-nums"
                :class="{
                  'text-[#4ECCA3]': item.Sign === 1 && item.Nilai >= 0,
                  'text-[#E24B4A]': item.Sign === -1 || item.Nilai < 0,
                  'text-[#EF9F27]': item.Format === 'percent',
                }"
              >
                <span v-if="item.Format === 'percent'">{{ item.Nilai }}%</span>
                <span v-else>
                  {{ item.Nilai < 0 ? '–' : (item.Sign === -1 ? '–' : '+') }}
                  Rp {{ fmtCompact(Math.abs(item.Nilai)) }}
                </span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- ══ Row 3: Margin Trend + Komposisi ══════════════════════════════════ -->
      <div class="grid grid-cols-1 lg:grid-cols-5 gap-5">

        <!-- Tren Margin Bersih (gambar 3) -->
        <div class="lg:col-span-3 glass-card p-6">
          <div class="flex items-start justify-between mb-4">
            <div>
              <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50">Tren Margin Laba Bersih</h3>
            </div>
            <div class="flex items-center gap-4 text-[11px] text-white/50">
              <span class="flex items-center gap-1.5">
                <span class="inline-block w-3 h-0.5 bg-[#97C459] rounded"></span>Margin aktual
              </span>
            </div>
          </div>
          <div class="h-64 w-full mt-2">
            <VueApexCharts type="line" height="100%" :options="marginChartOptions" :series="marginSeries" />
          </div>
        </div>

        <!-- Komposisi Pengeluaran + Top Kategori (gambar 3) -->
        <div class="lg:col-span-2 glass-card p-6 flex flex-col gap-4">
          <div class="mb-4">
            <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50">Komposisi Pengeluaran</h3>
          </div>

          <!-- Donut + legend inline -->
          <div class="flex items-center gap-4">
            <div class="w-[130px] h-[130px] shrink-0">
              <VueApexCharts v-if="donutSeries.length" type="donut" height="130" width="130" :options="donutOptions" :series="donutSeries" />
            </div>
            <div class="flex flex-col gap-2 text-sm min-w-0 max-h-[130px] overflow-y-auto pr-1">
              <div v-for="(c, i) in composition" :key="i" class="flex items-center gap-2 min-w-0">
                <span class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ background: expenseColor(i) }"></span>
                <div class="min-w-0">
                  <div class="text-white/70 text-xs font-medium truncate">{{ c.Label }}</div>
                  <div class="text-white font-bold text-xs">Rp {{ fmtCompact(c.Jumlah) }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Divider -->
          <div class="border-t border-white/5"></div>

          <!-- Top kategori pengeluaran -->
          <div>
            <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50 mb-4">Kategori Teratas</h3>
            <div class="flex flex-col gap-2">
              <div v-for="(item, i) in topItems" :key="i" class="flex items-center justify-between gap-2 group">
                <div class="flex items-center gap-2 min-w-0 flex-1">
                  <span class="text-[11px] font-bold text-white/30 w-4 shrink-0">{{ i + 1 }}</span>
                  <div class="flex-1 min-w-0">
                    <p class="text-xs text-white/80 font-medium truncate">{{ formatCategory(item.Kategori) }}</p>
                    <!-- progress bar -->
                    <div class="mt-0.5 h-1 rounded-full bg-white/5 overflow-hidden">
                      <div
                        class="h-full rounded-full transition-all duration-700"
                        :style="{
                          width: item.Pct + '%',
                          background: item.Tipe === 'Belanja' ? '#EF9F27' : '#7F77DD'
                        }"
                      ></div>
                    </div>
                  </div>
                </div>
                <span class="text-xs font-bold text-white/70 shrink-0 tabular-nums">Rp {{ fmtCompact(item.Jumlah) }}</span>
              </div>
            </div>
          </div>
        </div>

      </div>

    </template>

    <!-- Empty state -->
    <div v-else class="flex flex-col items-center justify-center py-20 text-white/30 gap-3">
      <TrendingDown class="w-10 h-10 opacity-30" />
      <p class="text-sm">Tidak ada data untuk periode ini.</p>
    </div>

  </div>
</template>
