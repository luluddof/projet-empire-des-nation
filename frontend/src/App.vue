<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import NavBar from "./components/NavBar.vue";

/** Vide = requêtes relatives via proxy Vite (cookie de session sur :5173). */
const apiBase = import.meta.env.VITE_API_BASE ?? "";
const router = useRouter();

const authState = ref({ authenticated: false, user: null });
const loading = ref(true);
const errorMessage = ref("");

const readErrorFromUrl = () => {
  const params = new URLSearchParams(window.location.search);
  if (params.get("error")) {
    errorMessage.value = "La connexion Discord a échoué. Réessaie.";
    history.replaceState({}, "", window.location.pathname);
  }
};

const fetchMe = async () => {
  loading.value = true;
  try {
    const res = await fetch(`${apiBase}/api/auth/me`, { credentials: "include" });
    authState.value = await res.json();
  } catch {
    errorMessage.value = "Impossible de contacter le serveur.";
  } finally {
    loading.value = false;
  }
};

const loginWithDiscord = () => {
  window.location.href = `${apiBase}/api/auth/discord/login`;
};

const logout = async () => {
  await fetch(`${apiBase}/api/auth/logout`, { method: "POST", credentials: "include" });
  authState.value = { authenticated: false, user: null };
  router.push("/");
};

onMounted(async () => {
  readErrorFromUrl();
  await fetchMe();
  if (authState.value.authenticated && router.currentRoute.value.path === "/") {
    router.push("/stocks");
  }
});
</script>

<template>
  <div v-if="loading" class="loading-screen">Chargement…</div>

  <template v-else>
    <NavBar
      v-if="authState.authenticated"
      :user="authState.user"
      @logout="logout"
    />

    <router-view
      :auth-state="authState"
      :error-message="errorMessage"
      @login="loginWithDiscord"
    />
  </template>
</template>
