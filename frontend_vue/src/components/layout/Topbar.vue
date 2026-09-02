<script setup>
import { computed } from 'vue';
import { Menu } from 'lucide-vue-next';

const props = defineProps({
  mode: String,
  value: String,
  options: Object,
  title: String,
  year: {
    type: String,
    default: 'Semua'
  },
  availableModes: {
    type: Array,
    default: () => ['Hari', 'Minggu', 'Bulan']
  }
});

const emit = defineEmits(['update:mode', 'update:value', 'update:year', 'toggleSidebar']);

const onValueChange = (e) => {
  emit('update:value', e.target.value);
};

const yearOptions = computed(() => {
  return props.options?.years || [];
});
</script>

<template>
  <header class="sticky top-0 z-40 border-b border-white/10 bg-bg/80 backdrop-blur-xl">
    <div class="mx-auto flex w-full items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
      <div class="flex min-w-0 items-center gap-3">
        <button
          type="button"
          class="flex h-11 w-11 items-center justify-center rounded-xl border border-white/10 bg-surface/80 text-white/80 transition hover:border-primary/30 hover:text-primary lg:hidden"
          @click="emit('toggleSidebar')"
          aria-label="Buka menu navigasi"
        >
          <Menu class="h-5 w-5" />
        </button>

        <div class="min-w-0">
          <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/40">Overview</p>
          <h2 class="truncate text-lg font-semibold text-white sm:text-xl">{{ title }}</h2>
        </div>
      </div>

      <div class="ml-auto flex max-w-full flex-col gap-3 sm:flex-row sm:items-center sm:justify-end">
        <div class="flex items-center gap-2 rounded-2xl border border-white/10 bg-surface/80 p-1.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] backdrop-blur">
          <div v-if="availableModes.length > 1" class="flex items-center gap-1 rounded-xl bg-surface2/80 p-1">
            <button
              v-for="m in availableModes"
              :key="m"
              @click="emit('update:mode', m)"
              :class="[
                'min-w-[62px] rounded-lg px-3 py-2 text-[11px] font-semibold tracking-wide transition sm:min-w-[72px] sm:text-xs',
                mode === m
                  ? 'bg-primary/12 text-primary shadow-[0_0_18px_rgba(78,204,163,0.15)]'
                  : 'text-white/50 hover:bg-white/5 hover:text-white/80'
              ]"
            >
              {{ m }}
            </button>
          </div>

          <div class="hidden h-7 w-px bg-white/10 sm:block"></div>

          <div class="flex items-center gap-2">
            <select
              v-if="mode === 'Bulan'"
              :value="value"
              @change="onValueChange"
              class="h-10 w-[110px] rounded-xl border border-white/10 bg-surface2/70 px-3 text-[11px] text-white/90 outline-none transition focus:border-primary/40 focus:ring-2 focus:ring-primary/20 sm:w-[140px] sm:text-xs"
            >
              <option value="Semua">Semua Bulan</option>
              <option v-for="opt in options?.months" :key="opt" :value="opt">{{ opt }}</option>
              <option v-if="!options?.months?.length" value="">---</option>
            </select>

            <input
              v-else-if="mode === 'Hari'"
              type="date"
              :value="value"
              :min="options?.min_date"
              :max="options?.max_date"
              @change="onValueChange"
              class="h-10 w-[120px] rounded-xl border border-white/10 bg-surface2/70 px-3 text-[11px] text-white/90 outline-none transition focus:border-primary/40 focus:ring-2 focus:ring-primary/20 sm:w-[150px] sm:text-xs calendar-input-dark"
            />

            <input
              v-else-if="mode === 'Minggu'"
              type="week"
              :value="value"
              :min="options?.min_week"
              :max="options?.max_week"
              @change="onValueChange"
              class="h-10 w-[120px] rounded-xl border border-white/10 bg-surface2/70 px-3 text-[11px] text-white/90 outline-none transition focus:border-primary/40 focus:ring-2 focus:ring-primary/20 sm:w-[150px] sm:text-xs calendar-input-dark"
            />
          </div>

          <div class="hidden h-7 w-px bg-white/10 sm:block"></div>

          <select
            :value="year"
            @change="(e) => emit('update:year', e.target.value)"
            class="h-10 w-[110px] rounded-xl border border-white/10 bg-surface2/70 px-3 text-[11px] text-white/90 outline-none transition focus:border-primary/40 focus:ring-2 focus:ring-primary/20 sm:w-[130px] sm:text-xs"
          >
            <option value="Semua">Semua Tahun</option>
            <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
::-webkit-calendar-picker-indicator {
  filter: invert(1);
  cursor: pointer;
  opacity: 0.7;
}
::-webkit-calendar-picker-indicator:hover {
  opacity: 1;
}
</style>
