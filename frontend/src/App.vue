<script setup>
import { onMounted, ref } from "vue";

const apiBase = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:5000";
const authState = ref({ authenticated: false });
const loading = ref(true);
const errorMessage = ref("");

const readErrorFromUrl = () => {
  const params = new URLSearchParams(window.location.search);
  const error = params.get("error");
  if (error) {
    errorMessage.value = "La connexion Discord a echoue. Reessaie.";
  }
};

const fetchMe = async () => {
  loading.value = true;
  try {
    const response = await fetch(`${apiBase}/api/auth/me`, {
      credentials: "include",
    });
    authState.value = await response.json();
  } catch (_error) {
    errorMessage.value = "Impossible de contacter le serveur.";
  } finally {
    loading.value = false;
  }
};

const loginWithDiscord = () => {
  window.location.href = `${apiBase}/api/auth/discord/login`;
};

const logout = async () => {
  await fetch(`${apiBase}/api/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
  await fetchMe();
};

onMounted(async () => {
  readErrorFromUrl();
  await fetchMe();
});
</script>

<template>
  <main class="container">
    <section class="card">
      <h1>Bienvenue sur Empire des Nation</h1>
      <p class="subtitle">Connecte-toi avec Discord pour acceder a ton espace.</p>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="loading">Chargement...</p>

      <template v-else>
        <div v-if="authState.authenticated" class="state">
          <p>
            Connecte en tant que
            <strong>{{ authState.user.username }}</strong>
          </p>
          <button class="button secondary" @click="logout">Se deconnecter</button>
        </div>
        <div v-else class="state">
          <p>Tu n'es pas connecte.</p>
          <button class="button" @click="loginWithDiscord">
            Se connecter avec Discord
          </button>
        </div>
      </template>
    </section>
  </main>
</template>
