<script setup>
import KpiCards from '../components/charts/KpiCards.vue';
import VueApexCharts from "vue3-apexcharts";
import { computed } from 'vue';
import { formatCurrency, formatCompactNumber, formatCompactRupiah } from '../utils/formatters';

const props = defineProps({
  data: Object,
  mode: String,
  year: String
});

const kpi = computed(() => props.data?.kpi);
const charts = computed(() => props.data?.charts);

// Revenue Chart
const revenueChartOptions = computed(() => ({
  chart: { type: 'area', fontFamily: 'Inter, sans-serif', background: 'transparent', toolbar: { show: false } },
  theme: { mode: 'dark', palette: 'palette1'},
  colors: ['#4ECCA3'],
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.0, stops: [0, 100] } },
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 3 },
  markers: { size: charts.value?.revenue?.length === 1 ? 6 : 0, colors: ['#4ECCA3'], strokeColors: '#161B22', strokeWidth: 2 },
  xaxis: { categories: charts.value?.revenue?.map(d => d.Label) || [], axisBorder: { show: false }, axisTicks: { show: false }, labels: { style: { colors: '#888' } } },
  yaxis: { labels: { formatter: (val) => formatCompactNumber(val), style: { colors: '#888' } } },
  grid: { borderColor: 'rgba(255,255,255,0.05)', strokeDashArray: 4 },
  tooltip: { theme: 'dark', y: { formatter: (val) => formatCompactRupiah(val) } }
}));
const revenueChartSeries = computed(() => [{ name: 'Pendapatan', data: charts.value?.revenue?.map(d => d.Revenue) || [] }]);

// Category Pie Chart
const catChartOptions = computed(() => ({
  chart: { type: 'donut', background: 'transparent', fontFamily: 'Inter, sans-serif' },
  labels: charts.value?.category?.map(d => d.Kategori) || [],
  theme: { mode: 'dark' },
  colors: ['#4ECCA3', '#7F77DD', '#00B8D9', '#EF9F27', '#E24B4A', '#97C459'],
  stroke: { show: true, colors: ['#161B22'], width: 2 },
  legend: { position: 'bottom', fontSize: '13px', labels: { colors: '#A0AEC0' } },
  dataLabels: { enabled: false },
  plotOptions: {
    pie: {
      donut: {
        size: '75%',
        labels: {
          show: true,
          value: {
            formatter: (val) => formatCompactRupiah(Number(val)),
            color: '#fff',
            fontSize: '18px',
            fontWeight: 800,
          },
          total: {
            show: true,
            label: 'Total',
            formatter: (w) => {
              const total = w?.globals?.seriesTotals?.reduce((a, b) => a + b, 0) ?? 0;
              return formatCompactRupiah(total);
            },
            color: '#fff',
            fontSize: '13px',
            fontWeight: 700,
          },
        },
      },
    },
  },
  tooltip: { theme: 'dark', y: { formatter: (val) => formatCurrency(val) } }
}));
const catChartSeries = computed(() => charts.value?.category?.map(d => d.Revenue) || []);

// Payment Chart
const paymentChartOptions = computed(() => ({
  chart: { type: 'donut', background: 'transparent', fontFamily: 'Inter, sans-serif' },
  labels: charts.value?.payment?.map(d => d.Metode) || [],
  theme: { mode: 'dark' },
  colors: ['#7F77DD', '#4ECCA3', '#EF9F27'],
  stroke: { show: true, colors: ['#161B22'], width: 2 },
  legend: { position: 'bottom', fontSize: '13px', labels: { colors: '#A0AEC0' } },
  dataLabels: { enabled: false },
  plotOptions: {
    pie: {
      donut: {
        size: '75%',
        labels: {
          show: true,
          value: {
            formatter: (val) => formatCompactNumber(Number(val)),
            color: '#fff',
            fontSize: '16px',
            fontWeight: 800,
          },
          total: {
            show: true,
            label: 'Total',
            formatter: (w) => {
              const total = w?.globals?.seriesTotals?.reduce((a, b) => a + b, 0) ?? 0;
              return formatCompactNumber(total);
            },
            color: '#fff',
            fontSize: '12px',
            fontWeight: 700,
          },
        },
      },
    },
  },
  tooltip: { theme: 'dark', y: { formatter: (val) => formatCompactNumber(val) } }
}));
const paymentChartSeries = computed(() => charts.value?.payment?.map(d => d.Jumlah) || []);

// Session Chart
const sessionChartOptions = computed(() => ({
  chart: { type: 'bar', background: 'transparent', toolbar: { show: false } },
  theme: { mode: 'dark' },
  colors: ['#00B8D9'],
  plotOptions: { bar: { borderRadius: 4, horizontal: false, columnWidth: '50%' } },
  dataLabels: { enabled: false },
  xaxis: { categories: charts.value?.session?.map(d => d.Sesi) || [], axisBorder: { show: false }, axisTicks: { show: false }, labels: { style: { colors: '#888' } } },
  yaxis: { labels: { formatter: (val) => formatCompactNumber(val), style: { colors: '#888' } } },
  grid: { borderColor: 'rgba(255,255,255,0.05)', strokeDashArray: 4 },
  tooltip: { theme: 'dark', y: { formatter: (val) => formatCompactRupiah(val) } }
}));
const sessionChartSeries = computed(() => [{ name: 'Pendapatan', data: charts.value?.session?.map(d => d.Revenue) || [] }]);

const topProducts = computed(() => charts.value?.top_products || []);

</script>

<template>
  <div class="flex flex-col gap-6 w-full pb-10">
    <KpiCards v-if="kpi" :kpi="kpi" />
    
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Revenue Chart -->
      <div class="lg:col-span-2 glass-card p-6">
         <div class="mb-4">
            <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50">Tren Pendapatan</h3>
         </div>
         <div class="h-80 w-full" v-if="charts?.revenue">
             <VueApexCharts :key="`rev-${props.mode}-${charts?.revenue?.length}`" type="area" height="100%" :options="revenueChartOptions" :series="revenueChartSeries" />
         </div>
      </div>

      <!-- Category Chart -->
      <div class="glass-card p-6">
         <div class="mb-4">
            <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50">Pendapatan per Kategori</h3>
         </div>
         <div class="h-80 w-full flex items-center justify-center" v-if="charts?.category">
             <VueApexCharts :key="`cat-${props.mode}-${charts?.category?.length}`" type="donut" height="100%" width="100%" :options="catChartOptions" :series="catChartSeries" />
         </div>
      </div>

      <!-- Session Chart -->
      <div class="lg:col-span-1 glass-card p-6">
         <div class="mb-4">
            <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50">Pendapatan per Sesi</h3>
         </div>
         <div class="h-80 w-full" v-if="charts?.session">
             <VueApexCharts :key="`ses-${props.mode}-${charts?.session?.length}`" type="bar" height="100%" :options="sessionChartOptions" :series="sessionChartSeries" />
         </div>
      </div>

      <!-- Payment Chart -->
      <div class="glass-card p-6">
         <div class="mb-4">
            <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50">Metode Pembayaran (Jumlah Transaksi)</h3>
         </div>
         <div class="h-80 w-full flex items-center justify-center" v-if="charts?.payment">
             <VueApexCharts :key="`pay-${props.mode}-${charts?.payment?.length}`" type="donut" height="100%" width="100%" :options="paymentChartOptions" :series="paymentChartSeries" />
         </div>
      </div>

      <!-- Top Products Table -->
      <div class="glass-card p-6">
         <div class="mb-4">
            <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50">5 Produk Teratas</h3>
         </div>
         <div class="overflow-x-auto">
            <table class="w-full text-left text-sm text-white/80">
                <thead class="text-xs uppercase bg-white/5 text-white/50">
                    <tr>
                        <th class="px-4 py-3 rounded-tl-lg font-medium">Produk</th>
                        <th class="px-4 py-3 font-medium text-right">Pendapatan</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="item in topProducts" :key="item['Product Name']" class="border-b border-white/5 hover:bg-white/5 transition-colors">
                        <td class="px-4 py-3">{{ item['Product Name'] }}</td>
                        <td class="px-4 py-3 text-right font-semibold text-primary">{{ formatCurrency(item.Revenue) }}</td>
                    </tr>
                </tbody>
            </table>
         </div>
      </div>
    </div>
  </div>
</template>
