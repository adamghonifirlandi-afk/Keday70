<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import Sidebar from './components/layout/Sidebar.vue';
import Topbar from './components/layout/Topbar.vue';
import DashboardView from './views/DashboardView.vue';
import TransaksiView from './views/TransaksiView.vue';
import PengeluaranView from './views/PengeluaranView.vue';
import LabaRugiView from './views/LabaRugiView.vue';
import ProdukView from './views/ProdukView.vue';
import ChatPanel from './components/chat/ChatPanel.vue';
import api from './api';

const isChatOpen = ref(false);
const currentPage = ref('overview');

const currentYear = ref(String(new Date().getFullYear()));
const currentMode = ref('Bulan');
const currentValue = ref('');
const dashboardData = ref(null);
const isLoading = ref(true);
const filterOptions = ref({});

const fetchOptions = async () => {
  try {
    const params = { mode: currentMode.value };
    if (currentYear.value && currentYear.value !== 'Semua') {
      params.year = currentYear.value;
    } else {
      params.year = 'Semua';
    }
    const res = await api.get('/dashboard/filter-options', { params });
    filterOptions.value = res.data;
    
    // Set proper default value based on mode if empty
    if (!currentValue.value) {
        if (currentMode.value === 'Hari') currentValue.value = filterOptions.value?.max_date || '';
        else if (currentMode.value === 'Minggu') currentValue.value = filterOptions.value?.max_week || '';
        else Object.keys(filterOptions.value).length > 0 ? currentValue.value = 'Semua' : ''; // default bulan to Semua
    }
  } catch(e) {
    console.error(e);
  }
}

const fetchData = async () => {
  isLoading.value = true;
  try {
    const params = new URLSearchParams({ mode: currentMode.value });
    if(currentValue.value) params.append('value', currentValue.value);
    // Always include year param
    params.append('year', currentYear.value || 'Semua');
    
    const res = await api.get('/dashboard/data', { params });
    dashboardData.value = res.data;
  } catch (e) {
    console.error("Error fetching data:", e);
  } finally {
    isLoading.value = false;
  }
};

onMounted(async () => {
  // Sync Excel → SQLite setiap kali halaman di-reload/refresh
  try {
    await api.post('/reload');
  } catch (e) {
    console.error('Auto-sync error:', e);
  }
  await fetchOptions();
  fetchData();
});

// When year changes → reset value and refetch options
watch(currentYear, async (newYear, oldYear) => {
  if (newYear !== oldYear) {
    currentValue.value = null;
    await fetchOptions();
  }
});

watch(currentMode, async (newMode, oldMode) => {
  if (newMode !== oldMode) {
    currentValue.value = null; // reset value before fetch so it defaults to first valid option
    await fetchOptions();
  }
});

watch([currentMode, currentValue, currentYear], () => {
  if (currentValue.value) {
    fetchData();
  }
});

const pageTitleMap = {
  'overview': 'Ringkasan',
  'transaksi': 'Transaksi',
  'pengeluaran': 'Pengeluaran',
  'labarugi': 'Laba Rugi',
  'produk': 'Produk'
};
const currentTitle = computed(() => pageTitleMap[currentPage.value] || 'Ringkasan');

const availableFilterModes = computed(() => {
    return ['Hari', 'Minggu', 'Bulan']; // All modes enabled for all pages
});

// Remove watcher locking mode
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-bg text-white font-sans selection:bg-primary/30">
    <Sidebar :currentPage="currentPage" @navigate="(pg) => currentPage = pg" @openChat="isChatOpen = true" />

    <div class="flex-1 flex flex-col overflow-hidden relative">
      <Topbar 
        :title="currentTitle"
        :availableModes="availableFilterModes"
        v-model:mode="currentMode" 
        v-model:value="currentValue"
        v-model:year="currentYear"
        :options="filterOptions" 
      />
      
      <main class="flex-1 overflow-x-hidden overflow-y-auto bg-bg/50 px-4 md:px-8 py-6">
        <div v-if="isLoading && !dashboardData" class="flex h-full w-full items-center justify-center">
            <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
        </div>
        
        <template v-else-if="dashboardData">
          <div v-if="isLoading" class="absolute inset-0 bg-bg/50 backdrop-blur-sm z-30 flex items-center justify-center rounded-xl">
             <div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
          </div>
          <DashboardView v-if="currentPage === 'overview'" :data="dashboardData" :mode="currentMode" :year="currentYear"/>
          <TransaksiView v-else-if="currentPage === 'transaksi'" :mode="currentMode" :filterValue="currentValue" :year="currentYear" />
          <PengeluaranView v-else-if="currentPage === 'pengeluaran'" :mode="currentMode" :filterValue="currentValue" :year="currentYear" />
          <LabaRugiView v-else-if="currentPage === 'labarugi'" :mode="currentMode" :filterValue="currentValue" :year="currentYear" />
          <ProdukView v-else-if="currentPage === 'produk'" :data="dashboardData" :mode="currentMode" :filterValue="currentValue" :year="currentYear" />
        </template>
      </main>
      
      <ChatPanel :isOpen="isChatOpen" @close="isChatOpen = false" :year="currentYear" />
    </div>
  </div>
</template>

<style>
/* Basic animations can go here or index.css */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
