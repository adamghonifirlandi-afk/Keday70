<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import VueApexCharts from "vue3-apexcharts";
import { ShoppingBag, Settings, DollarSign } from 'lucide-vue-next';
import api from '../api';
import { formatCurrency, formatCompactRupiah, formatCompactNumber, formatCategory } from '../utils/formatters';

const props = defineProps({ mode: String, filterValue: String, year: String });
const data = ref(null);
const loading = ref(true);
const expenseTypeColors = {
  Belanja: '#F59E0B',
  Operasional: '#A78BFA'
};
const expenseColorByType = (type) => expenseTypeColors[type] || '#64748B';

const fetchExpenses = async () => {
    loading.value = true;
    try {
        const params = {};
        if (props.mode) params.mode = props.mode;
        if (props.filterValue) params.value = props.filterValue;
        if (props.year) params.year = props.year;
        const res = await api.get('/dashboard/expenses', { params });
        data.value = res.data;
    } catch(e) { console.error(e); }
    finally { loading.value = false; }
};

onMounted(fetchExpenses);
watch([() => props.mode, () => props.filterValue, () => props.year], fetchExpenses);

// Chart 1: Pengeluaran per Kategori (Horizontal Bar)
const barOptions = computed(() => ({
  chart: { type: 'bar', background: 'transparent', toolbar: { show: false } },
  theme: { mode: 'dark' },
  colors: data.value?.breakdown?.map(d => expenseColorByType(d.Tipe)) || [],
  plotOptions: { bar: { borderRadius: 4, horizontal: true, distributed: true, barHeight: '65%' } },
  dataLabels: { enabled: false },
  xaxis: {
    categories: data.value?.breakdown?.map(d => formatCategory(d.Kategori)) || [],
    axisBorder: { show: false }, axisTicks: { show: false },
    labels: { formatter: (val) => formatCompactNumber(val), style: { colors: '#888' } }
  },
  yaxis: { labels: { style: { colors: '#bbb', fontSize: '12px' } } },
  grid: { borderColor: 'rgba(255,255,255,0.05)', strokeDashArray: 4 },
  legend: { show: false },
  tooltip: { theme: 'dark', y: { formatter: (val) => formatCurrency(val) } }
}));

const barSeries = computed(() => [{
  name: 'Jumlah',
  data: data.value?.breakdown?.map(d => d.Jumlah) || []
}]);

// Chart 2: Komposisi Biaya (Donut)
const donutOptions = computed(() => ({
  chart: { type: 'donut', background: 'transparent', fontFamily: 'Inter, sans-serif' },
  theme: { mode: 'dark' },
  colors: data.value?.composition?.map(d => expenseColorByType(d.Tipe || d.Label)) || [],
  labels: data.value?.composition?.map(d => d.Label) || [],
  legend: { position: 'bottom', labels: { colors: '#bbb' } },
  dataLabels: { enabled: false },
  plotOptions: { pie: { donut: { size: '65%', labels: { show: true,
    value: { formatter: (val) => formatCompactRupiah(Number(val)), color: '#fff', fontSize: '18px', fontWeight: 'bold' },
    total: { show: true, label: 'Total', formatter: () => formatCompactRupiah(data.value?.kpi?.total_pengeluaran || 0), color: '#fff' }
  } } } },
  tooltip: { theme: 'dark', y: { formatter: (val) => formatCurrency(val) } }
}));

const donutSeries = computed(() => data.value?.composition?.map(d => d.Jumlah) || []);
</script>

<template>
  <div class="flex flex-col gap-6 w-full pb-10">
    <div v-if="loading" class="flex justify-center p-10"><div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-warning"></div></div>

    <template v-else-if="data">
      <!-- KPI Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
        <!-- Total Pengeluaran -->
        <div class="glass-card p-6 flex items-center justify-between group overflow-hidden relative">
          <div class="absolute -right-6 -top-6 w-24 h-24 bg-red-500/10 rounded-full blur-2xl group-hover:bg-red-500/20 transition-all duration-500"></div>
          <div class="flex flex-col gap-1 z-10 pr-10 min-w-0">
            <span class="text-[11px] font-semibold uppercase tracking-widest text-white/40">Total Pengeluaran</span>
            <span class="text-base md:text-lg font-bold text-white tabular-nums whitespace-nowrap tracking-tight">{{ formatCurrency(data.kpi.total_pengeluaran) }}</span>
          </div>
          <div class="absolute top-4 right-4 w-8 h-8 md:w-9 md:h-9 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 group-hover:scale-110 transition-transform">
            <DollarSign class="w-4 h-4" />
          </div>
        </div>

        <!-- Total Bahan Baku -->
        <div class="glass-card p-6 flex items-center justify-between group overflow-hidden relative">
          <div class="absolute -right-6 -top-6 w-24 h-24 bg-warning/10 rounded-full blur-2xl group-hover:bg-warning/20 transition-all duration-500"></div>
          <div class="flex flex-col gap-1 z-10 pr-10 min-w-0">
            <span class="text-[11px] font-semibold uppercase tracking-widest text-white/40">Total Bahan Baku</span>
            <span class="text-base md:text-lg font-bold text-white tabular-nums whitespace-nowrap tracking-tight">{{ formatCurrency(data.kpi.total_belanja) }}</span>
          </div>
          <div class="absolute top-4 right-4 w-8 h-8 md:w-9 md:h-9 rounded-2xl bg-warning/10 border border-warning/20 flex items-center justify-center text-warning group-hover:scale-110 transition-transform">
            <ShoppingBag class="w-4 h-4" />
          </div>
        </div>

        <!-- Total Operasional -->
        <div class="glass-card p-6 flex items-center justify-between group overflow-hidden relative">
          <div class="absolute -right-6 -top-6 w-24 h-24 bg-violet-400/10 rounded-full blur-2xl group-hover:bg-violet-400/20 transition-all duration-500"></div>
          <div class="flex flex-col gap-1 z-10 pr-10 min-w-0">
            <span class="text-[11px] font-semibold uppercase tracking-widest text-white/40">Total Operasional</span>
            <span class="text-base md:text-lg font-bold text-white tabular-nums whitespace-nowrap tracking-tight">{{ formatCurrency(data.kpi.total_ops) }}</span>
          </div>
          <div class="absolute top-4 right-4 w-8 h-8 md:w-9 md:h-9 rounded-2xl bg-violet-400/10 border border-violet-400/20 flex items-center justify-center text-violet-400 group-hover:scale-110 transition-transform">
            <Settings class="w-4 h-4" />
          </div>
        </div>
      </div>

      <!-- Charts Row: Bar + Donut -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Pengeluaran per Kategori -->
        <div class="glass-card p-6 lg:col-span-2">
          <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50 mb-4">Pengeluaran per Kategori</h3>
          <div class="h-[360px] w-full">
            <VueApexCharts type="bar" height="100%" :options="barOptions" :series="barSeries" />
          </div>
        </div>

        <!-- Komposisi Biaya -->
        <div class="glass-card p-6">
          <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50 mb-4">Komposisi Biaya</h3>
          <div class="h-[360px] flex items-center justify-center">
            <VueApexCharts type="donut" height="100%" width="100%" :options="donutOptions" :series="donutSeries" />
          </div>
        </div>
      </div>

      <!-- Rincian Pengeluaran Terbesar -->
      <div class="glass-card p-6 w-full">
        <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50 mb-4">Rincian Pengeluaran Terbesar</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-white/80">
            <thead class="text-xs uppercase bg-white/5 text-white/50">
              <tr>
                <th class="px-4 py-3 rounded-tl-lg font-medium">Kategori</th>
                <th class="px-4 py-3 font-medium">Tipe</th>
                <th class="px-4 py-3 font-medium text-right">Jumlah</th>
                <th class="px-4 py-3 rounded-tr-lg font-medium text-right">% Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, i) in data.top_items" :key="i" class="border-b border-white/5 hover:bg-white/5 transition-colors">
                <td class="px-4 py-3 font-medium">{{ formatCategory(item.Kategori) }}</td>
                <td class="px-4 py-3">
                  <span :class="item.Tipe === 'Belanja' ? 'bg-warning/20 text-warning' : 'bg-violet-400/20 text-violet-300'" class="px-2 py-1 rounded-md text-[10px] font-semibold">{{ item.Tipe }}</span>
                </td>
                <td class="px-4 py-3 text-right font-semibold text-red-400">{{ formatCurrency(item.Jumlah) }}</td>
                <td class="px-4 py-3 text-right text-white/60">{{ item.Pct }}%</td>
              </tr>
              <tr v-if="!data.top_items?.length">
                <td colspan="4" class="px-4 py-10 text-center text-white/40">Tidak ada data pengeluaran.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
