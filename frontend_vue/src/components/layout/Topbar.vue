<script setup>
import { computed } from 'vue';

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

const emit = defineEmits(['update:mode', 'update:value', 'update:year']);

const onValueChange = (e) => {
   emit('update:value', e.target.value);
};

// Generate year list from backend options
const yearOptions = computed(() => {
  return props.options?.years || [];
});
</script>

<template>
  <header class="glass-panel border-b border-white/5 min-h-20 flex items-center px-4 md:px-8 z-40 sticky top-0">
    <div class="w-full flex items-center justify-between gap-4 md:gap-6 py-3">
      <div class="flex items-center gap-4 min-w-0">
        <h2 class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary hidden sm:block">{{ title }}</h2>
      </div>

      <!-- Filter Bar (right aligned) -->
      <div class="flex items-center gap-2 bg-black/30 p-1.5 rounded-2xl border border-white/10 shadow-inner ml-auto backdrop-blur-md">
        
        <!-- ═══ Mode Selector (Hari/Minggu/Bulan) ═══ -->
        <div v-if="availableModes.length > 1" class="flex rounded-xl bg-surface2/60 p-1 gap-1">
        <button 
          v-for="m in availableModes" :key="m"
          @click="emit('update:mode', m)"
          :class="[
            'px-3 md:px-4 py-1.5 text-xs md:text-sm font-semibold tracking-wide transition-all rounded-lg min-w-[60px] md:min-w-[72px]',
            mode === m
              ? 'bg-gradient-to-r from-primary/25 to-secondary/20 text-primary border border-primary/30 shadow-[0_0_10px_rgba(78,204,163,0.15)]'
              : 'text-white/45 hover:bg-white/5 hover:text-white/85 border border-transparent'
          ]"
        >
          {{ m }}
        </button>
        </div>

        <div class="w-px h-7 bg-white/10 mx-0.5"></div>

        <div class="flex items-center gap-1.5 md:gap-2">
          <!-- Input Option 1: Dropdown Bulan -->
          <select
            v-if="mode === 'Bulan'"
            :value="value"
            @change="onValueChange"
            class="h-9 md:h-10 bg-surface2/80 text-white/90 text-xs md:text-sm rounded-xl focus:ring-2 focus:ring-primary/50 focus:border-primary block px-3 md:px-4 outline-none cursor-pointer border border-white/10 shadow-sm transition-all w-32 md:w-40"
          >
            <option value="Semua">Semua Bulan</option>
            <option v-for="opt in options?.months" :key="opt" :value="opt">{{ opt }}</option>
            <option v-if="!options?.months?.length" value="">---</option>
          </select>

          <!-- Input Option 2: Native HTML5 Date Calendar (Mode Hari) -->
          <input 
            v-else-if="mode === 'Hari'" 
            type="date" 
            :value="value"
            :min="options?.min_date"
            :max="options?.max_date" 
            @change="onValueChange" 
            class="h-9 md:h-10 bg-surface2/80 text-white/90 text-xs md:text-sm rounded-xl focus:ring-2 focus:ring-primary/50 border border-white/10 px-3 md:px-4 outline-none cursor-pointer w-32 md:w-40 calendar-input-dark" 
          />

          <!-- Input Option 3: Native HTML5 Week Picker (Mode Minggu) -->
          <input 
            v-else-if="mode === 'Minggu'" 
            type="week" 
            :value="value"
            :min="options?.min_week"
            :max="options?.max_week" 
            @change="onValueChange" 
            class="h-9 md:h-10 bg-surface2/80 text-white/90 text-xs md:text-sm rounded-xl focus:ring-2 focus:ring-primary/50 border border-white/10 px-3 md:px-4 outline-none cursor-pointer w-32 md:w-40 calendar-input-dark" 
          />
        </div>

        <div class="w-px h-7 bg-white/10 mx-0.5"></div>

        <!-- ═══ Year Dropdown Selector ═══ -->
        <select
          :value="year"
          @change="(e) => emit('update:year', e.target.value)"
          class="h-9 md:h-10 bg-surface2/80 text-white/90 text-xs md:text-sm rounded-xl focus:ring-2 focus:ring-primary/50 focus:border-primary block px-3 md:px-4 outline-none cursor-pointer border border-white/10 shadow-sm transition-all w-28 md:w-32"
        >
          <option value="Semua">Semua Tahun</option>
          <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>
    </div>
  </header>
</template>

<style scoped>
/* Inject CSS to style Webkit calendar picker icon to look white/dark-mode compatible */
::-webkit-calendar-picker-indicator {
    filter: invert(1);
    cursor: pointer;
    opacity: 0.6;
}
::-webkit-calendar-picker-indicator:hover {
    opacity: 1;
}
</style>
