<script setup>
import { Home, ListOrdered, DollarSign, WalletCards, Package, Bot, X } from 'lucide-vue-next';

const props = defineProps({ currentPage: String, isMobileOpen: Boolean });
const emit = defineEmits(['navigate', 'openChat', 'closeSidebar']);

const navItems = [
  { key: 'overview', label: 'Ringkasan', icon: Home },
  { key: 'transaksi', label: 'Transaksi', icon: ListOrdered },
  { key: 'pengeluaran', label: 'Pengeluaran', icon: WalletCards },
  { key: 'labarugi', label: 'Laba Rugi', icon: DollarSign },
  { key: 'produk', label: 'Produk', icon: Package },
];
</script>

<template>
  <aside
    :class="[
      'fixed inset-y-0 left-0 z-50 flex flex-col border-r border-white/10 bg-surface/90 backdrop-blur-xl transition-transform duration-300 ease-out lg:static lg:w-64',
      isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
      'w-[82%] max-w-[280px] sm:w-[260px] lg:w-64'
    ]"
  >
    <div class="flex items-center justify-between border-b border-white/10 px-4 py-4 lg:px-5">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-secondary font-bold text-bg shadow-[0_10px_24px_rgba(78,204,163,0.25)]">
          K
        </div>
        <div class="hidden lg:block">
          <h1 class="text-lg font-bold tracking-tight text-white">Keday70</h1>
          <span class="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/40">Dashboard</span>
        </div>
      </div>

      <button
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 text-white/60 transition hover:border-white/20 hover:text-white lg:hidden"
        aria-label="Tutup menu"
        @click="emit('closeSidebar')"
      >
        <X class="h-4 w-4" />
      </button>
    </div>

    <nav class="flex-1 space-y-2 px-3 py-4">
      <button
        v-for="item in navItems"
        :key="item.key"
        type="button"
        @click="emit('navigate', item.key)"
        :class="[
          'flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left transition-all duration-200',
          currentPage === item.key
            ? 'border border-primary/20 bg-primary/10 text-primary shadow-[0_0_18px_rgba(78,204,163,0.12)]'
            : 'text-white/60 hover:bg-white/5 hover:text-white'
        ]"
      >
        <component :is="item.icon" class="h-5 w-5 shrink-0" />
        <span class="text-sm font-medium">{{ item.label }}</span>
      </button>
    </nav>

    <div class="border-t border-white/10 p-3">
      <button
        type="button"
        @click="emit('openChat')"
        class="flex w-full items-center justify-center gap-3 rounded-2xl border border-accent/20 bg-accent/10 px-4 py-3 text-sm font-medium text-accent transition hover:bg-accent/15 lg:justify-start"
      >
        <Bot class="h-5 w-5" />
        <span>Tanya AI</span>
      </button>
    </div>
  </aside>
</template>
