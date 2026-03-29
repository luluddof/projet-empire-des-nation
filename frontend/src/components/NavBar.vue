<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";

const props = defineProps({
  user: { type: Object, required: true },
});
const emit = defineEmits(["logout"]);

const route = useRoute();
const avatarUrl = computed(() => {
  if (!props.user?.avatar) return null;
  return `https://cdn.discordapp.com/avatars/${props.user.id}/${props.user.avatar}.png?size=32`;
});
</script>

<template>
  <nav class="navbar">
    <div class="navbar-brand">
      <span class="brand-icon">⚔</span>
      <span class="brand-text">Empire des Nations</span>
    </div>

    <div class="navbar-links">
      <router-link to="/ressources" :class="{ active: route.path === '/ressources' }">
        Ressources
      </router-link>
      <router-link to="/stocks" :class="{ active: route.path === '/stocks' }">
        Mes Stocks
      </router-link>
      <router-link to="/productions" :class="{ active: route.path === '/productions' }">
        Mes productions
      </router-link>
      <router-link to="/gains" :class="{ active: route.path === '/gains' }">
        Gains & Pertes
      </router-link>
      <router-link
        v-if="user?.is_mj"
        to="/mj/joueurs"
        :class="{ active: route.path === '/mj/joueurs' }"
      >
        Joueurs (MJ)
      </router-link>
    </div>

    <div class="navbar-user">
      <span v-if="user?.is_mj" class="badge badge-mj">MJ</span>
      <img v-if="avatarUrl" :src="avatarUrl" :alt="user.username" class="avatar" />
      <span class="username">{{ user?.username }}</span>
      <button class="btn-logout" @click="emit('logout')">Déconnexion</button>
    </div>
  </nav>
</template>
