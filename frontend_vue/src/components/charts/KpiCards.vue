<script setup>
import { computed } from 'vue';
import { TrendingUp, TrendingDown, DollarSign, Activity } from 'lucide-vue-next';
import { formatNumber, formatCurrency } from '../../utils/formatters';

const props = defineProps({
  kpi: Object
});

const colorStyleOptions = {
    primary: {
        glow: 'bg-primary/10 group-hover:bg-primary/20',
        iconBox: 'bg-primary/10 border-primary/20 text-primary shadow-[0_0_15px_rgba(78,204,163,0.15)]'
    },
    secondary: {
        glow: 'bg-secondary/10 group-hover:bg-secondary/20',
        iconBox: 'bg-secondary/10 border-secondary/20 text-secondary shadow-[0_0_15px_rgba(0,184,217,0.15)]'
    },
    success: {
        glow: 'bg-success/10 group-hover:bg-success/20',
        iconBox: 'bg-success/10 border-success/20 text-success shadow-[0_0_15px_rgba(151,196,89,0.15)]'
    },
    danger: {
        glow: 'bg-danger/10 group-hover:bg-danger/20',
        iconBox: 'bg-danger/10 border-danger/20 text-danger shadow-[0_0_15px_rgba(226,75,74,0.15)]'
    }
};

const cards = computed(() => {
  if(!props.kpi) return [];
  return [
    { title: 'Total Pendapatan', value: formatCurrency(props.kpi.total_revenue), icon: DollarSign, theme: 'primary' },
    { title: 'Total Transaksi', value: formatNumber(props.kpi.total_tx), icon: Activity, theme: 'secondary' },
    { title: 'Laba Bersih', value: formatCurrency(props.kpi.estimasi_laba), icon: TrendingUp, theme: 'success' },
    { title: 'Total Pengeluaran', value: formatCurrency(props.kpi.total_expense), icon: TrendingDown, theme: 'danger' },
  ];
});
</script>
<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 w-full">
    <div v-for="(card, i) in cards" :key="i" class="glass-card p-6 relative overflow-hidden group cursor-default">
      <div :class="`absolute -right-6 -top-6 w-32 h-32 rounded-full blur-3xl transition-colors duration-500 ${colorStyleOptions[card.theme].glow}`"></div>
      
      <div class="z-10 relative pr-10">
        <div class="flex flex-col gap-1 min-w-0">
          <span class="text-[11px] font-semibold uppercase tracking-widest text-white/40">{{ card.title }}</span>
          <span class="text-base md:text-lg font-bold text-white drop-shadow-sm tabular-nums whitespace-nowrap tracking-tight">
            {{ card.value }}
          </span>
        </div>
      </div>

      <div
        :class="`absolute top-4 right-4 w-8 h-8 md:w-9 md:h-9 rounded-2xl border flex items-center justify-center transition-all duration-300 group-hover:-translate-y-0.5 group-hover:scale-110 ${colorStyleOptions[card.theme].iconBox}`"
      >
        <component :is="card.icon" class="w-4 h-4" />
      </div>
    </div>
  </div>
</template>
