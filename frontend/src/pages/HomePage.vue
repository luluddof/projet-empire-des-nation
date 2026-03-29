<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const loading = ref(true);
const errorMessage = ref("");

const readErrorFromUrl = () => {
  const params = new URLSearchParams(window.location.search);
  const error = params.get("error");
  if (error) {
    errorMessage.value = "La connexion Discord a echoue. Reessaie.";
  }
};

const checkAuth = async () => {
  loading.value = true;
  try {
    const response = await fetch("/api/auth/me", { credentials: "include" });
    const data = await response.json();
    if (data.authenticated) {
      router.replace("/dashboard");
      return;
    }
  } catch (_error) {
    errorMessage.value = "Impossible de contacter le serveur.";
  } finally {
    loading.value = false;
  }
};

const loginWithDiscord = () => {
  window.location.href = "/api/auth/discord/login";
};

onMounted(async () => {
  readErrorFromUrl();
  await checkAuth();
});
</script>

<template>
  <main class="container">
    <section class="card">
      <h1>Bienvenue sur Empire des Nation</h1>
      <p class="subtitle">Connecte-toi avec Discord pour acceder a ton espace.</p>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="loading">Chargement...</p>

      <div v-else class="state">
        <p>Tu n'es pas connecte.</p>
        <button class="button" @click="loginWithDiscord">
          Se connecter avec Discord
        </button>
      </div>
    </section>
  </main>
</template>
