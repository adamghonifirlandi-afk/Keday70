<script setup>
import { Home, ListOrdered, DollarSign, WalletCards, Package, Bot } from 'lucide-vue-next';

const props = defineProps({ currentPage: String });
const emit = defineEmits(['navigate', 'openChat']);
</script>

<template>
  <aside class="w-20 lg:w-64 glass-panel border-r border-white/5 flex flex-col items-center lg:items-stretch py-6 transition-all duration-300 z-50">
    <div class="mb-10 w-full flex justify-center lg:justify-start px-0 lg:px-6 items-center gap-3 cursor-pointer group">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary to-secondary flex items-center justify-center shadow-lg shadow-primary/20 group-hover:scale-105 transition-transform">
        <span class="text-xl font-bold text-bg">K</span>
      </div>
      <div class="hidden lg:flex flex-col">
          <h1 class="font-bold text-xl tracking-tight text-white">Keday70</h1>
          <span class="text-[10px] text-white/40 font-medium uppercase tracking-widest">Dashboard</span>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 px-3 space-y-2 w-full">
      <button @click="emit('navigate', 'overview')" :class="['w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group relative overflow-hidden', currentPage === 'overview' ? 'bg-primary/10 text-primary border border-primary/20 shadow-[0_0_15px_rgba(78,204,163,0.15)]' : 'text-white/50 hover:text-white/90 hover:bg-white/5']">
        <div v-if="currentPage === 'overview'" class="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/10 to-primary/0 opacity-0 group-hover:opacity-100 transition-opacity translate-x-[-100%] group-hover:translate-x-[100%] duration-1000"></div>
        <Home class="w-5 h-5 shrink-0" />
        <span class="hidden lg:block font-medium">Ringkasan</span>
      </button>

      <button @click="emit('navigate', 'transaksi')" :class="['w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group', currentPage === 'transaksi' ? 'bg-primary/10 text-primary border border-primary/20' : 'text-white/50 hover:text-white/90 hover:bg-white/5']">
        <ListOrdered class="w-5 h-5 shrink-0" />
        <span class="hidden lg:block font-medium">Transaksi</span>
      </button>
      
      <button @click="emit('navigate', 'pengeluaran')" :class="['w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group', currentPage === 'pengeluaran' ? 'bg-primary/10 text-primary border border-primary/20' : 'text-white/50 hover:text-white/90 hover:bg-white/5']">
        <WalletCards class="w-5 h-5 shrink-0" />
        <span class="hidden lg:block font-medium">Pengeluaran</span>
      </button>
      
      <button @click="emit('navigate', 'labarugi')" :class="['w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group', currentPage === 'labarugi' ? 'bg-primary/10 text-primary border border-primary/20' : 'text-white/50 hover:text-white/90 hover:bg-white/5']">
        <DollarSign class="w-5 h-5 shrink-0" />
        <span class="hidden lg:block font-medium">Laba Rugi</span>
      </button>

      <button @click="emit('navigate', 'produk')" :class="['w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group', currentPage === 'produk' ? 'bg-primary/10 text-primary border border-primary/20' : 'text-white/50 hover:text-white/90 hover:bg-white/5']">
        <Package class="w-5 h-5 shrink-0" />
        <span class="hidden lg:block font-medium">Produk</span>
      </button>
    </nav>
    
    <div class="mt-auto px-4 w-full">
       <button @click="emit('openChat')" class="w-full flex items-center justify-center lg:justify-start gap-3 px-4 py-3 rounded-xl bg-accent/20 text-accent hover:bg-accent/30 border border-accent/20 transition-all shadow-lg group">
        <Bot class="w-5 h-5 shrink-0 group-hover:scale-110 transition-transform" />
        <span class="hidden lg:block font-medium">Tanya AI</span>
      </button>
    </div>
  </aside>
</template>
