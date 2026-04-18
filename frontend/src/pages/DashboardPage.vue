<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { clearMjViewLocalStorage } from "../authState.js";
import { formatFlorinExact, useApi } from "../composables/useApi.js";

const router = useRouter();
const user = ref(null);
const { get } = useApi();

const erreur = ref("");
const evenementsActifs = ref([]);
const alertes = ref([]);

const isMj = computed(() => !!user.value?.is_mj);

const logout = async () => {
  await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
  clearMjViewLocalStorage();
  router.replace("/");
};

function computeDiff(oldMap, newMap) {
  const out = [];
  for (const [k, v] of Object.entries(newMap)) {
    const prev = oldMap?.[k];
    if (prev == null) continue;
    if (String(prev) !== String(v)) out.push({ key: k, from: prev, to: v });
  }
  return out;
}

async function chargerDashboard() {
  erreur.value = "";
  alertes.value = [];
  try {
    const [ev, ressources, prods] = await Promise.all([
      get("/api/evenements?actifs=1"),
      get("/api/ressources"),
      get("/api/gains-passifs"),
    ]);

    evenementsActifs.value = ev?.evenements || [];

    // Alertes "prix évolués" (comparaison locale, sans serveur push)
    const prixKey = `dashboard_last_prices_${user.value?.id ?? "me"}`;
    const prodKey = `dashboard_last_prods_${user.value?.id ?? "me"}`;
    const evKey = `dashboard_last_events_${user.value?.id ?? "me"}`;

    const prixNow = {};
    for (const r of ressources || []) {
      prixNow[String(r.id)] = r.prix_achat;
    }
    const prodsNow = {};
    for (const g of prods || []) {
      // inclut les productions "evenement" grâce à evenement_id
      prodsNow[String(g.id)] = `${g.ressource_id}:${g.quantite_par_tour}:${g.actif}:${g.tours_restants ?? ""}:${g.delai_tours ?? 0}:${g.evenement_id ?? ""}`;
    }
    const evNow = {};
    for (const e of evenementsActifs.value || []) {
      evNow[String(e.id)] = `${e.titre}:${e.updated_at ?? ""}`;
    }

    const prixPrev = JSON.parse(localStorage.getItem(prixKey) || "{}");
    const prodPrev = JSON.parse(localStorage.getItem(prodKey) || "{}");
    const evPrev = JSON.parse(localStorage.getItem(evKey) || "{}");

    const dPrix = computeDiff(prixPrev, prixNow);
    const dProd = computeDiff(prodPrev, prodsNow);
    const dEv = computeDiff(evPrev, evNow);

    if (dPrix.length > 0) {
      alertes.value.push({
        titre: "Des prix ont évolué",
        details: dPrix.slice(0, 8).map((x) => {
          const rr = (ressources || []).find((r) => String(r.id) === String(x.key));
          const name = rr?.nom ?? `Ressource #${x.key}`;
          return `${name} : ${formatFlorinExact(x.from)} → ${formatFlorinExact(x.to)}`;
        }),
      });
    }
    if (dEv.length > 0) {
      alertes.value.push({
        titre: "Évènements mis à jour",
        details: dEv.slice(0, 8).map((x) => {
          const name = (evenementsActifs.value || []).find((e) => String(e.id) === String(x.key))?.titre ?? `#${x.key}`;
          return `${name}`;
        }),
      });
    }
    if (dProd.length > 0) {
      alertes.value.push({
        titre: "Productions modifiées",
        details: dProd.slice(0, 8).map((x) => `Production #${x.key} modifiée`),
      });
    }

    localStorage.setItem(prixKey, JSON.stringify(prixNow));
    localStorage.setItem(prodKey, JSON.stringify(prodsNow));
    localStorage.setItem(evKey, JSON.stringify(evNow));
  } catch (e) {
    erreur.value = e.message;
  }
}

onMounted(async () => {
  try {
    const response = await fetch("/api/auth/me", { credentials: "include" });
    const data = await response.json();
    if (!data.authenticated) {
      router.replace("/");
      return;
    }
    user.value = data.user;
    await chargerDashboard();
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

    <p v-if="erreur" class="error">{{ erreur }}</p>

    <section v-if="user" class="card">
      <h2 style="margin-top: 0">Tableau de bord</h2>

      <div v-if="alertes.length > 0" class="alerts">
        <div v-for="(a, i) in alertes" :key="i" class="alert">
          <div class="alert-title"><strong>{{ a.titre }}</strong></div>
          <ul v-if="a.details?.length" class="alert-list">
            <li v-for="(d, j) in a.details" :key="j">{{ d }}</li>
          </ul>
        </div>
      </div>
      <div v-else class="muted">Aucune alerte récente.</div>
    </section>

    <section v-if="user" class="card">
      <h3 style="margin-top: 0">Évènements en cours</h3>
      <div v-if="evenementsActifs.length === 0" class="muted">Aucun évènement actif.</div>
      <div v-else class="events">
        <div v-for="e in evenementsActifs" :key="e.id" class="event">
          <div class="event-header">
            <strong>{{ e.titre }}</strong>
            <span v-if="isMj" class="muted">#{{ e.id }}</span>
          </div>
          <div v-if="e.description" class="event-desc">{{ e.description }}</div>
          <div class="event-actions">
            <button
              v-if="isMj"
              type="button"
              class="button secondary small"
              @click="router.push({ path: '/mj/evenements', query: { edit: String(e.id) } })"
            >
              Modifier
            </button>
            <button
              v-else
              type="button"
              class="button secondary small"
              @click="router.push(`/evenements/${e.id}`)"
            >
              Détails
            </button>
          </div>
        </div>
      </div>
      <div v-if="isMj" class="muted" style="margin-top: 10px">
        Liste limitée aux évènements qui vous concernent aussi ; la gestion complète est dans « Évènements (MJ) ».
      </div>
    </section>

    <section v-if="user" class="grid-4">
      <div class="card placeholder">
        <h3 style="margin-top: 0">Commerce</h3>
        <div class="muted">À venir.</div>
      </div>
      <div class="card placeholder">
        <h3 style="margin-top: 0">Recherche</h3>
        <div class="muted">À venir.</div>
      </div>
      <div class="card placeholder">
        <h3 style="margin-top: 0">Déficits</h3>
        <div class="muted">À venir.</div>
      </div>
      <div v-if="isMj" class="card placeholder">
        <h3 style="margin-top: 0">Craft</h3>
        <div class="muted">À venir.</div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.muted {
  color: #94a3b8;
}
.alerts {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.alert {
  border: 1px solid rgba(56, 189, 248, 0.35);
  background: rgba(56, 189, 248, 0.1);
  border-radius: 12px;
  padding: 12px;
}
.alert-title {
  color: #e0f2fe;
}
.alert-list {
  margin: 8px 0 0;
  padding-left: 1.2em;
  color: #cbd5e1;
}
.events {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.event {
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 12px;
  background: rgba(15, 23, 42, 0.2);
}
.event-header {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: baseline;
  color: #e2e8f0;
}
.event-desc {
  margin-top: 8px;
  color: #cbd5e1;
  white-space: pre-wrap;
}
.event-actions {
  margin-top: 10px;
}
.grid-4 {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 12px;
}
@media (min-width: 900px) {
  .grid-4 {
    grid-template-columns: repeat(2, 1fr);
  }
}
.placeholder {
  min-height: 120px;
}
</style>
