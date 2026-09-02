<script setup>
import { ref } from 'vue';
import { Bot, Send, X } from 'lucide-vue-next';
import api from '../../api';

const props = defineProps({ isOpen: Boolean });
const emit = defineEmits(['close']);

// Unique session per page load — agar n8n memory tidak bocor antar sesi
const sessionId = `web-${Date.now()}`;

const messages = ref([{ sender: 'bot', text: 'Halo! Saya Keday70 AI Assistant. Ada yang bisa dibantu mengenai data kita hari ini?' }]);
const input = ref('');
const isTyping = ref(false);

const sendMessage = async () => {
  if (!input.value.trim()) return;
  const userMsg = input.value;
  input.value = '';
  isTyping.value = true;
  
  try {
    // Build history SEBELUM push pesan baru agar tidak duplikasi
    // (pesan saat ini sudah dikirim via chatInput, tidak perlu di history)
    const historyMessages = messages.value
      .filter((m, i) => !(i === 0 && m.sender === 'bot'))  // skip greeting
      .slice(-6)
      .map(m => ({
        role: m.sender === 'user' ? 'user' : 'assistant',
        content: m.text
      }));

    // Push pesan user ke UI SETELAH build history
    messages.value.push({ sender: 'user', text: userMsg });

    const res = await api.post('/chat/message', {
      sessionId: sessionId,
      chatInput: userMsg,
      history: historyMessages
    });

    const botReply = res.data?.output || 'Maaf, gagal memproses respons.';
    messages.value.push({ sender: 'bot', text: botReply });
  } catch (err) {
    const backendMessage = err?.response?.data?.detail;
    const safeMessage = typeof backendMessage === 'string' && backendMessage.trim()
      ? backendMessage
      : 'Layanan AI sedang tidak tersedia. Silakan coba lagi nanti.';

    messages.value.push({ sender: 'bot', text: safeMessage });
  } finally {
    isTyping.value = false;
  }
};
</script>

<template>
  <transition name="slide">
    <div v-if="isOpen" class="fixed right-0 top-0 h-screen w-full sm:w-[400px] glass-panel z-[60] flex flex-col shadow-2xl backdrop-blur-2xl bg-surface/90 border-l border-white/10">
      <!-- Header -->
      <div class="h-20 border-b border-white/5 flex items-center justify-between px-6 bg-gradient-to-r from-accent/10 to-transparent">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center text-accent shadow-lg shadow-accent/20">
            <Bot class="w-6 h-6 animate-pulse" />
          </div>
          <div class="flex flex-col">
            <h3 class="font-bold text-white text-lg">Asisten AI</h3>
            <p class="text-[11px] font-medium tracking-wide text-white/50 uppercase">AI Data Assistant</p>
          </div>
        </div>
        <button @click="emit('close')" class="text-white/50 hover:text-white rounded-xl p-2 hover:bg-white/10 transition-all border border-transparent hover:border-white/10">
          <X class="w-5 h-5" />
        </button>
      </div>
      
      <!-- Messages -->
      <div class="flex-1 overflow-y-auto p-6 flex flex-col gap-5">
        <div v-for="(msg, i) in messages" :key="i" :class="['max-w-[85%] px-5 py-3 rounded-2xl text-sm leading-relaxed shadow-lg', msg.sender === 'user' ? 'bg-gradient-to-br from-primary to-[#38a685] text-bg self-end rounded-br-sm' : 'bg-surface2/80 backdrop-blur-sm border border-white/10 text-white/90 self-start rounded-bl-sm']">
          <span v-html="msg.text.replace(/\n/g, '<br>')"></span>
        </div>
        <div v-if="isTyping" class="bg-surface2/80 border border-white/10 text-white/50 self-start rounded-2xl rounded-bl-sm px-5 py-3.5 text-sm flex gap-1 items-center shadow-lg">
          <span class="w-1.5 h-1.5 rounded-full bg-white/50 animate-bounce"></span>
          <span class="w-1.5 h-1.5 rounded-full bg-white/50 animate-bounce" style="animation-delay: 0.1s"></span>
          <span class="w-1.5 h-1.5 rounded-full bg-white/50 animate-bounce" style="animation-delay: 0.2s"></span>
        </div>
      </div>
      
      <!-- Input -->
      <div class="p-4 border-t border-white/5 bg-black/40">
        <form @submit.prevent="sendMessage" class="flex items-center gap-2 relative">
          <input 
            v-model="input" 
            placeholder="Ketik pesan..." 
            class="w-full bg-surface border border-white/10 text-white text-sm rounded-xl py-4 pl-5 pr-14 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all shadow-inner"
          />
          <button type="submit" :disabled="!input.trim()" class="absolute right-2 w-10 h-10 rounded-lg bg-primary text-bg flex items-center justify-center disabled:opacity-50 disabled:bg-white/10 disabled:text-white/30 transition-all hover:scale-105 shadow-lg shadow-primary/20">
            <Send class="w-5 h-5 ml-1" />
          </button>
        </form>
      </div>
    </div>
  </transition>
  
  <!-- Backdrop -->
  <transition name="fade">
    <div v-if="isOpen" @click="emit('close')" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[55]"></div>
  </transition>
</template>

<style>
.slide-enter-active, .slide-leave-active { transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1); }
.slide-enter-from, .slide-leave-to { transform: translateX(100%); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.4s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>