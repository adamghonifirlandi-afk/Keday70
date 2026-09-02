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
const isSidebarOpen = ref(false);
const currentPage = ref('overview');

const currentYear = ref('2024');
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

    if (!currentValue.value) {
      if (currentMode.value === 'Hari') currentValue.value = filterOptions.value?.max_date || '';
      else if (currentMode.value === 'Minggu') currentValue.value = filterOptions.value?.max_week || '';
      else Object.keys(filterOptions.value).length > 0 ? currentValue.value = 'Semua' : '';
    }
  } catch (e) {
    console.error(e);
  }
};

const fetchData = async () => {
  isLoading.value = true;
  try {
    const params = new URLSearchParams({ mode: currentMode.value });
    if (currentValue.value) params.append('value', currentValue.value);
    params.append('year', currentYear.value || 'Semua');

    const res = await api.get('/dashboard/data', { params });
    dashboardData.value = res.data;
  } catch (e) {
    console.error('Error fetching data:', e);
  } finally {
    isLoading.value = false;
  }
};

onMounted(async () => {
  if (import.meta.env.DEV) {
    try {
      await api.post('/reload');
    } catch (e) {
      console.error('Auto-sync error:', e);
    }
  }
  await fetchOptions();
  fetchData();
});

watch(currentYear, async (newYear, oldYear) => {
  if (newYear !== oldYear) {
    currentValue.value = null;
    await fetchOptions();
  }
});

watch(currentMode, async (newMode, oldMode) => {
  if (newMode !== oldMode) {
    currentValue.value = null;
    await fetchOptions();
  }
});

watch([currentMode, currentValue, currentYear], () => {
  if (currentValue.value) {
    fetchData();
  }
});

watch(currentPage, () => {
  isSidebarOpen.value = false;
});

const pageTitleMap = {
  overview: 'Ringkasan',
  transaksi: 'Transaksi',
  pengeluaran: 'Pengeluaran',
  labarugi: 'Laba Rugi',
  produk: 'Produk'
};
const currentTitle = computed(() => pageTitleMap[currentPage.value] || 'Ringkasan');
const availableFilterModes = computed(() => ['Hari', 'Minggu', 'Bulan']);
</script>

<template>
  <div class="dashboard-shell flex h-screen overflow-hidden bg-bg text-white antialiased selection:bg-primary/30">
    <div
      v-if="isSidebarOpen"
      class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
      @click="isSidebarOpen = false"
    ></div>

    <Sidebar
      :currentPage="currentPage"
      :isMobileOpen="isSidebarOpen"
      @navigate="(pg) => currentPage = pg"
      @openChat="isChatOpen = true"
      @closeSidebar="isSidebarOpen = false"
    />

    <div class="relative flex min-w-0 flex-1 flex-col overflow-hidden">
      <Topbar
        :title="currentTitle"
        :availableModes="availableFilterModes"
        v-model:mode="currentMode"
        v-model:value="currentValue"
        v-model:year="currentYear"
        :options="filterOptions"
        @toggleSidebar="isSidebarOpen = !isSidebarOpen"
      />

      <main class="flex-1 overflow-x-hidden overflow-y-auto px-4 py-5 sm:px-6 lg:px-8">
        <div v-if="isLoading && !dashboardData" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <div v-for="n in 4" :key="n" class="h-28 animate-pulse rounded-2xl border border-white/10 bg-surface/80"></div>
        </div>

        <template v-else-if="dashboardData">
          <div v-if="isLoading" class="pointer-events-none absolute inset-0 z-30 flex items-center justify-center bg-bg/30 backdrop-blur-[1px]">
            <div class="h-10 w-10 animate-spin rounded-full border-2 border-primary/30 border-t-primary"></div>
          </div>
          <div class="space-y-5 lg:space-y-6">
            <DashboardView v-if="currentPage === 'overview'" :data="dashboardData" :mode="currentMode" :year="currentYear" />
            <TransaksiView v-else-if="currentPage === 'transaksi'" :mode="currentMode" :filterValue="currentValue" :year="currentYear" />
            <PengeluaranView v-else-if="currentPage === 'pengeluaran'" :mode="currentMode" :filterValue="currentValue" :year="currentYear" />
            <LabaRugiView v-else-if="currentPage === 'labarugi'" :mode="currentMode" :filterValue="currentValue" :year="currentYear" />
            <ProdukView v-else-if="currentPage === 'produk'" :data="dashboardData" :mode="currentMode" :filterValue="currentValue" :year="currentYear" />
          </div>
        </template>
      </main>

      <ChatPanel :isOpen="isChatOpen" @close="isChatOpen = false" :year="currentYear" />
    </div>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
