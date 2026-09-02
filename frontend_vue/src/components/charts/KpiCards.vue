<script setup>
import { computed } from 'vue';
import { TrendingUp, TrendingDown, DollarSign, Activity } from 'lucide-vue-next';
import { formatNumber, formatCurrency } from '../../utils/formatters';

const props = defineProps({
  kpi: Object
});

const colorStyleOptions = {
  primary: {
    glow: 'bg-primary/12',
    iconBox: 'bg-primary/10 border-primary/20 text-primary shadow-[0_0_18px_rgba(78,204,163,0.18)]'
  },
  secondary: {
    glow: 'bg-secondary/12',
    iconBox: 'bg-secondary/10 border-secondary/20 text-secondary shadow-[0_0_18px_rgba(0,184,217,0.18)]'
  },
  success: {
    glow: 'bg-success/12',
    iconBox: 'bg-success/10 border-success/20 text-success shadow-[0_0_18px_rgba(151,196,89,0.18)]'
  },
  danger: {
    glow: 'bg-danger/12',
    iconBox: 'bg-danger/10 border-danger/20 text-danger shadow-[0_0_18px_rgba(226,75,74,0.18)]'
  }
};

const cards = computed(() => {
  if (!props.kpi) return [];
  return [
    { title: 'Total Pendapatan', value: formatCurrency(props.kpi.total_revenue), icon: DollarSign, theme: 'primary' },
    { title: 'Total Transaksi', value: formatNumber(props.kpi.total_tx), icon: Activity, theme: 'secondary' },
    { title: 'Laba Bersih', value: formatCurrency(props.kpi.estimasi_laba), icon: TrendingUp, theme: 'success' },
    { title: 'Total Pengeluaran', value: formatCurrency(props.kpi.total_expense), icon: TrendingDown, theme: 'danger' },
  ];
});
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 md:gap-5 w-full">
    <div
      v-for="(card, i) in cards"
      :key="i"
      class="group relative overflow-hidden rounded-2xl border border-white/10 bg-surface/80 p-4 sm:p-5 shadow-[0_12px_30px_rgba(15,17,23,0.28)] transition-all duration-300 ease-out hover:-translate-y-1 hover:border-white/20 hover:shadow-[0_18px_40px_rgba(15,17,23,0.35)]"
    >
      <div :class="`absolute -right-8 -top-8 h-28 w-28 rounded-full blur-3xl transition-duration-300 ${colorStyleOptions[card.theme].glow}`"></div>

      <div class="relative z-10 flex items-start justify-between gap-3">
        <div class="min-w-0 flex-1">
          <p class="text-[11px] font-semibold uppercase tracking-[0.14em] text-white/40">{{ card.title }}</p>
          <p class="mt-3 text-xl font-bold tracking-[-0.04em] text-white tabular-nums sm:text-[1.7rem]">
            {{ card.value }}
          </p>
        </div>

        <div
          :class="`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border ${colorStyleOptions[card.theme].iconBox}`"
        >
          <component :is="card.icon" class="h-5 w-5" />
        </div>
      </div>
    </div>
  </div>
</template>
