<script setup>
import { computed, ref, watch } from "vue";
import { useApi } from "../composables/useApi.js";

const props = defineProps({
  authState: { type: Object, required: true },
});

const { get, patch } = useApi();

const isMj = computed(() => props.authState.user?.is_mj);
const utilisateurs = ref([]);
const erreur = ref("");
const chargement = ref(true);
const majMj = ref({});

async function charger() {
  if (!isMj.value) {
    chargement.value = false;
    return;
  }
  erreur.value = "";
  chargement.value = true;
  try {
    utilisateurs.value = await get("/api/utilisateurs");
  } catch (e) {
    erreur.value = e.message;
  } finally {
    chargement.value = false;
  }
}

watch(isMj, (v) => {
  if (v) charger();
});

charger();

function formatDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

async function basculerMj(u, event) {
  const checked = event.target.checked;
  majMj.value[u.id] = true;
  erreur.value = "";
  try {
    const updated = await patch(`/api/utilisateurs/${encodeURIComponent(u.id)}`, {
      is_mj: checked,
    });
    const i = utilisateurs.value.findIndex((x) => x.id === u.id);
    if (i >= 0) utilisateurs.value[i] = updated;
  } catch (e) {
    erreur.value = e.message;
    event.target.checked = !checked;
  } finally {
    delete majMj.value[u.id];
  }
}

function lienStocks(uid) {
  return { path: "/stocks", query: { uid: String(uid) } };
}
function lienProductions(uid) {
  return { path: "/productions", query: { uid: String(uid) } };
}
function lienGains(uid) {
  return { path: "/gains", query: { uid: String(uid) } };
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">Joueurs (MJ)</h2>
        <p class="page-subtitle">
          Consulter n’importe quel compte (joueur ou MJ), ouvrir ses stocks / productions / historique, et
          attribuer ou retirer le rôle MJ.
        </p>
      </div>
    </div>

    <p v-if="!authState.authenticated" class="error">Connexion requise.</p>
    <p v-else-if="!isMj" class="error">Cette page est réservée aux Maîtres du Jeu.</p>
    <p v-else-if="chargement" class="muted">Chargement…</p>
    <p v-else-if="erreur" class="error">{{ erreur }}</p>

    <div v-else class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Pseudo</th>
            <th>ID Discord</th>
            <th>Inscription</th>
            <th>MJ</th>
            <th>Ouvrir</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in utilisateurs" :key="u.id">
            <td class="nom">
              {{ u.username }}
              <span v-if="u.is_mj" class="badge badge-mj">MJ</span>
            </td>
            <td class="mono muted">{{ u.id }}</td>
            <td>{{ formatDate(u.created_at) }}</td>
            <td>
              <label class="mj-toggle">
                <input
                  type="checkbox"
                  :checked="u.is_mj"
                  :disabled="majMj[u.id]"
                  @change="basculerMj(u, $event)"
                />
                <span class="sr-only">Rôle MJ</span>
              </label>
            </td>
            <td class="actions-cell">
              <router-link class="button small secondary" :to="lienStocks(u.id)">Stocks</router-link>
              <router-link class="button small secondary" :to="lienProductions(u.id)">Productions</router-link>
              <router-link class="button small secondary" :to="lienGains(u.id)">Gains</router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.mono {
  font-family: ui-monospace, monospace;
  font-size: 0.85rem;
}
.actions-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.mj-toggle {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
.muted {
  color: var(--color-muted, #8b949e);
}
</style>
