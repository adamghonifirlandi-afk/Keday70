<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import VueApexCharts from "vue3-apexcharts";
import { Activity, DollarSign, Package } from 'lucide-vue-next';
import api from '../api';
import { formatCurrency, formatCompactNumber, formatNumber } from '../utils/formatters';

const props = defineProps({ mode: String, filterValue: String, year: String });
const data = ref(null);
const loading = ref(true);
const selectedCategory = ref('Semua');

const fetchTx = async () => {
    loading.value = true;
    try {
        const params = new URLSearchParams({ mode: props.mode });
        if(props.filterValue) params.append('value', props.filterValue);
        if(props.year) params.append('year', props.year);
        if(selectedCategory.value !== 'Semua') params.append('category', selectedCategory.value);
        
        const res = await api.get('/dashboard/transactions', { params });
        data.value = res.data;
    } catch(e) { console.error(e); }
    finally { loading.value = false; }
};

onMounted(fetchTx);
watch([() => props.mode, () => props.filterValue, () => props.year, selectedCategory], fetchTx);

// Chart 1: Top 10 Produk
const productChartOptions = computed(() => ({
  chart: { type: 'bar', toolbar: { show: false }, background: 'transparent' },
  theme: { mode: 'dark' },
  colors: ['#4ECCA3'],
  plotOptions: { bar: { horizontal: true, borderRadius: 4, barHeight: '70%' } },
  dataLabels: { enabled: false },
  xaxis: { 
     categories: data.value?.chart_products?.map(d => d['Product Name']) || [],
     labels: { formatter: (val) => formatCompactNumber(val), style: { colors: '#888' } },
     axisBorder: { show: false }, axisTicks: { show: false }
  },
  yaxis: { labels: { style: { colors: '#eee' }, maxWidth: 150 } },
  grid: { borderColor: 'rgba(255,255,255,0.05)', strokeDashArray: 4 },
  tooltip: { theme: 'dark', y: { formatter: (val) => formatCurrency(val) } }
}));

const productSeries = computed(() => [{
  name: 'Pendapatan',
  data: data.value?.chart_products?.map(d => d.Revenue) || []
}]);

// Chart 2: Pendapatan Periodik
const periodChartOptions = computed(() => ({
  chart: { type: 'bar', background: 'transparent', toolbar: { show: false } },
  theme: { mode: 'dark' },
  colors: ['#00B8D9'],
  plotOptions: { bar: { borderRadius: 4, horizontal: false, columnWidth: '40%' } },
  dataLabels: { enabled: false },
  xaxis: {
    categories: data.value?.chart_period?.map(d => d.Label) || [],
    axisBorder: { show: false }, axisTicks: { show: false },
    labels: { style: { colors: '#888' } }
  },
  yaxis: { labels: { formatter: (val) => formatCompactNumber(val), style: { colors: '#888' } } },
  grid: { borderColor: 'rgba(255,255,255,0.05)', strokeDashArray: 4 },
  tooltip: { theme: 'dark', y: { formatter: (val) => formatCurrency(val) } }
}));

const periodSeries = computed(() => [{
  name: 'Pendapatan',
  data: data.value?.chart_period?.map(d => d.Revenue) || []
}]);

// Chart 3: Jumlah Transaksi Periodik
const txCountChartOptions = computed(() => ({
  chart: { type: 'bar', background: 'transparent', toolbar: { show: false } },
  theme: { mode: 'dark' },
  colors: ['#A78BFA'],
  plotOptions: { bar: { borderRadius: 4, columnWidth: '40%' } },
  dataLabels: { enabled: false },
  xaxis: {
    categories: data.value?.chart_period?.map(d => d.Label) || [],
    axisBorder: { show: false }, axisTicks: { show: false },
    labels: { style: { colors: '#888' } }
  },
  yaxis: { labels: { formatter: (val) => formatNumber(val), style: { colors: '#888' } } },
  grid: { borderColor: 'rgba(255,255,255,0.05)', strokeDashArray: 4 },
  tooltip: { theme: 'dark', y: { formatter: (val) => `${formatNumber(val)} transaksi` } }
}));

const txCountSeries = computed(() => [{
  name: 'Transaksi',
  data: data.value?.chart_period?.map(d => d.Count) || []
}]);
</script>

<template>
  <div class="flex flex-col gap-6 w-full pb-10">
    <div v-if="loading" class="flex justify-center p-10"><div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div></div>
    
    <template v-else-if="data">
      <!-- Category Filter Dropdown -->
      <div class="flex justify-end -mt-4 mb-2 z-10 relative">
         <div class="relative group">
            <select v-model="selectedCategory" class="appearance-none bg-black/40 text-white/90 text-sm font-medium tracking-wide rounded-full px-5 py-2.5 pr-10 border border-white/10 hover:border-primary/50 outline-none cursor-pointer transition-all shadow-lg backdrop-blur-md focus:ring-2 focus:ring-primary/50">
                <option value="Semua">Semua Kategori</option>
                <option v-for="cat in data.categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
            <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-white/50 group-hover:text-primary transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
            </div>
         </div>
      </div>

      <!-- KPIs -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
         <!-- Card 1 -->
         <div class="glass-card p-6 flex items-center justify-between group overflow-hidden relative">
            <div class="absolute -right-6 -top-6 w-24 h-24 bg-primary/10 rounded-full blur-2xl group-hover:bg-primary/20 transition-all duration-500"></div>
            <div class="flex flex-col gap-1 z-10 pr-10 min-w-0">
               <span class="text-[11px] font-semibold uppercase tracking-widest text-white/40">Total Pendapatan</span>
               <span class="text-base md:text-lg font-bold text-white tabular-nums whitespace-nowrap tracking-tight">{{ formatCurrency(data.kpi.total_revenue) }}</span>
            </div>
            <div class="absolute top-4 right-4 w-8 h-8 md:w-9 md:h-9 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
              <DollarSign class="w-4 h-4" />
            </div>
         </div>
         
         <!-- Card 2 -->
         <div class="glass-card p-6 flex items-center justify-between group overflow-hidden relative">
            <div class="absolute -right-6 -top-6 w-24 h-24 bg-secondary/10 rounded-full blur-2xl group-hover:bg-secondary/20 transition-all duration-500"></div>
            <div class="flex flex-col gap-1 z-10 pr-10 min-w-0">
               <span class="text-[11px] font-semibold uppercase tracking-widest text-white/40">Total Transaksi</span>
               <span class="text-base md:text-lg font-bold text-white tabular-nums whitespace-nowrap tracking-tight">{{ formatNumber(data.kpi.total_tx) }}</span>
            </div>
            <div class="absolute top-4 right-4 w-8 h-8 md:w-9 md:h-9 rounded-2xl bg-secondary/10 border border-secondary/20 flex items-center justify-center text-secondary group-hover:scale-110 transition-transform">
              <Activity class="w-4 h-4" />
            </div>
         </div>

         <!-- Card 3 -->
         <div class="glass-card p-6 flex items-center justify-between group overflow-hidden relative">
            <div class="absolute -right-6 -top-6 w-24 h-24 bg-accent/10 rounded-full blur-2xl group-hover:bg-accent/20 transition-all duration-500"></div>
            <div class="flex flex-col gap-1 z-10 pr-10 min-w-0">
               <span class="text-[11px] font-semibold uppercase tracking-widest text-white/40">Rata-rata Nilai Order</span>
               <span class="text-base md:text-lg font-bold text-white tabular-nums whitespace-nowrap tracking-tight">{{ formatCurrency(data.kpi.avg_order) }}</span>
            </div>
            <div class="absolute top-4 right-4 w-8 h-8 md:w-9 md:h-9 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent group-hover:scale-110 transition-transform">
              <DollarSign class="w-4 h-4" />
            </div>
         </div>

         <!-- Card 4 -->
         <div class="glass-card p-6 flex items-center justify-between group overflow-hidden relative">
            <div class="absolute -right-6 -top-6 w-24 h-24 bg-success/10 rounded-full blur-2xl group-hover:bg-success/20 transition-all duration-500"></div>
            <div class="flex flex-col gap-1 z-10 pr-10 min-w-0">
               <span class="text-[11px] font-semibold uppercase tracking-widest text-white/40">Produk Terjual</span>
               <span class="text-base md:text-lg font-bold text-white tabular-nums whitespace-nowrap tracking-tight">{{ formatNumber(data.kpi.total_qty) }}</span>
            </div>
            <div class="absolute top-4 right-4 w-8 h-8 md:w-9 md:h-9 rounded-2xl bg-success/10 border border-success/20 flex items-center justify-center text-success group-hover:scale-110 transition-transform">
              <Package class="w-4 h-4" />
            </div>
         </div>
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
         <!-- Chart 1: Top 10 Produk -->
         <div class="glass-card p-6 w-full">
            <div class="mb-4">
               <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50">10 Produk Teratas — Pendapatan</h3>
            </div>
            <div class="h-80 w-full" v-if="data?.chart_products">
                <VueApexCharts type="bar" height="100%" :options="productChartOptions" :series="productSeries" />
            </div>
         </div>

         <!-- Chart 2: Pendapatan -->
         <div class="glass-card p-6 w-full">
            <div class="mb-4">
               <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50">
                  Pendapatan {{ props.mode === 'Bulan' ? 'Bulanan' : (props.mode === 'Minggu' ? 'Mingguan' : 'Harian') }}
               </h3>
            </div>
            <div class="h-80 w-full" v-if="data?.chart_period">
                <VueApexCharts type="bar" height="100%" :options="periodChartOptions" :series="periodSeries" />
            </div>
         </div>
      </div>

      <!-- Chart 3: Jumlah Transaksi -->
      <div class="glass-card p-6 w-full">
         <div class="mb-4">
            <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50">
               Transaksi {{ props.mode === 'Bulan' ? 'Bulanan' : (props.mode === 'Minggu' ? 'Mingguan' : 'Harian') }}
            </h3>
         </div>
         <div class="h-64 w-full" v-if="data?.chart_period">
             <VueApexCharts type="bar" height="100%" :options="txCountChartOptions" :series="txCountSeries" />
         </div>
      </div>

      <!-- Table Section -->
      <div class="glass-card p-6 w-full flex flex-col gap-4">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50">Daftar Transaksi ({{ data.transactions.length }} TERAKHIR)</h3>
        </div>
        
        <div class="overflow-x-auto w-full">
            <table class="w-full text-left text-sm text-white/80">
                <thead class="text-xs uppercase bg-white/5 text-white/50 whitespace-nowrap">
                    <tr>
                        <th class="px-4 py-3 rounded-tl-lg font-medium">Tanggal</th>
                        <th class="px-4 py-3 font-medium">Waktu</th>
                        <th class="px-4 py-3 font-medium">Produk</th>
                        <th class="px-4 py-3 font-medium">Kategori</th>
                        <th class="px-4 py-3 font-medium text-center">Qty</th>
                        <th class="px-4 py-3 font-medium text-right">Harga</th>
                        <th class="px-4 py-3 font-medium">Metode</th>
                        <th class="px-4 py-3 rounded-tr-lg font-medium">Sesi</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(tx, i) in data.transactions" :key="i" class="border-b border-white/5 hover:bg-white/5 transition-colors">
                        <td class="px-4 py-3 whitespace-nowrap text-xs">{{ new Date(tx['Transaction Date']).toLocaleString('id-ID', { year: 'numeric', month: 'short', day: 'numeric'}) }}</td>
                        <td class="px-4 py-3 text-xs text-white/50">{{ tx['Transaction Time'] ?? '-' }}</td>
                        <td class="px-4 py-3 font-medium">{{ tx['Product Name'] }}</td>
                        <td class="px-4 py-3"><span class="px-2 py-1 bg-surface2 rounded-md text-[10px]">{{ tx['Category'] }}</span></td>
                        <td class="px-4 py-3 text-center text-xs">{{ tx['Quantity'] }}</td>
                        <td class="px-4 py-3 text-right font-semibold text-primary text-xs">{{ formatCurrency(tx['Total Price Idr']) }}</td>
                        <td class="px-4 py-3 text-xs">{{ tx['Payment Method'] }}</td>
                        <td class="px-4 py-3 text-xs">{{ tx['Session'] }}</td>
                    </tr>
                    <tr v-if="!data.transactions.length">
                        <td colspan="8" class="px-4 py-10 text-center text-white/40">Tidak ada data transaksi.</td>
                    </tr>
                </tbody>
            </table>
        </div>
      </div>
    </template>
  </div>
</template>
