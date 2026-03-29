<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const user = ref(null);

const logout = async () => {
  await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
  router.replace("/");
};

onMounted(async () => {
  try {
    const response = await fetch("/api/auth/me", { credentials: "include" });
    const data = await response.json();
    if (!data.authenticated) {
      router.replace("/");
      return;
    }
    user.value = data.user;
  } catch (_error) {
    router.replace("/");
  }
});
</script>

<template>
  <main class="container">
    <header v-if="user" class="topbar">
      <span>Connecte en tant que <strong>{{ user.username }}</strong></span>
      <button class="button secondary" @click="logout">Se deconnecter</button>
    </header>
  </main>
</template>
