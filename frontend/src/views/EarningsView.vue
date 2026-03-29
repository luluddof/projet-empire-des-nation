<script setup>
import { computed, ref, watch } from "vue";
import { formatFlorin, useApi } from "../composables/useApi.js";

const props = defineProps({
  authState: { type: Object, required: true },
});

const { get } = useApi();
const isMj = computed(() => props.authState.user?.is_mj);

const utilisateurs = ref([]);
const selectedUid = ref(props.authState.user?.id ?? "");
const data = ref({ transactions: [], total: 0, pages: 1, page: 1 });
const erreur = ref("");
const page = ref(1);

async function chargerUtilisateurs() {
  if (!isMj.value) return;
  try {
    utilisateurs.value = await get("/api/utilisateurs");
  } catch (e) {
    erreur.value = e.message;
  }
}

async function chargerTransactions() {
  erreur.value = "";
  const uid = isMj.value && selectedUid.value ? `&uid=${selectedUid.value}` : "";
  try {
    data.value = await get(`/api/transactions?page=${page.value}&per_page=50${uid}`);
  } catch (e) {
    erreur.value = e.message;
  }
}

watch([selectedUid, page], chargerTransactions);
chargerUtilisateurs();
chargerTransactions();

const stats = computed(() => {
  const txs = data.value.transactions;
  const gains = txs.filter((t) => t.valeur_florins > 0).reduce((s, t) => s + t.valeur_florins, 0);
  const pertes = txs.filter((t) => t.valeur_florins < 0).reduce((s, t) => s + t.valeur_florins, 0);
  return { gains, pertes, net: gains + pertes };
});

function formatDate(iso) {
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

const MOTIFS = {
  gain_passif: "Gain passif",
  ajustement_manuel: "Ajustement",
  ajustement_mj: "Ajustement MJ",
};
function labelMotif(motif) {
  return MOTIFS[motif] ?? motif ?? "—";
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">Gains & Pertes</h2>
        <p class="page-subtitle">Historique des mouvements de stock</p>
      </div>
      <select v-if="isMj" v-model="selectedUid" class="select">
        <option v-for="u in utilisateurs" :key="u.id" :value="u.id">
          {{ u.username }}{{ u.is_mj ? " (MJ)" : "" }}
        </option>
      </select>
    </div>

    <p v-if="erreur" class="error">{{ erreur }}</p>

    <div class="stats-grid">
      <div class="stat-card stat-gain">
        <div class="stat-label">Gains totaux (page)</div>
        <div class="stat-value">{{ formatFlorin(stats.gains) }}</div>
      </div>
      <div class="stat-card stat-perte">
        <div class="stat-label">Pertes totales (page)</div>
        <div class="stat-value">{{ formatFlorin(stats.pertes) }}</div>
      </div>
      <div class="stat-card" :class="stats.net >= 0 ? 'stat-gain' : 'stat-perte'">
        <div class="stat-label">Solde net (page)</div>
        <div class="stat-value">{{ formatFlorin(stats.net) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Transactions totales</div>
        <div class="stat-value">{{ data.total }}</div>
      </div>
    </div>

    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Ressource</th>
            <th>Quantité</th>
            <th>Valeur (ƒ)</th>
            <th>Motif</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in data.transactions" :key="t.id">
            <td class="date">{{ formatDate(t.created_at) }}</td>
            <td class="nom">{{ t.ressource.nom }}</td>
            <td :class="['prix', t.quantite >= 0 ? 'text-gain' : 'text-perte']">
              {{ t.quantite > 0 ? "+" : "" }}{{ t.quantite }}
            </td>
            <td :class="['prix', t.valeur_florins >= 0 ? 'text-gain' : 'text-perte']">
              {{ t.valeur_florins > 0 ? "+" : "" }}{{ formatFlorin(t.valeur_florins) }}
            </td>
            <td>
              <span class="tag">{{ labelMotif(t.motif) }}</span>
            </td>
          </tr>
          <tr v-if="data.transactions.length === 0">
            <td colspan="5" class="empty">Aucune transaction pour le moment.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="data.pages > 1" class="pagination">
      <button class="button secondary" :disabled="page === 1" @click="page--">← Précédent</button>
      <span>Page {{ page }} / {{ data.pages }}</span>
      <button class="button secondary" :disabled="page >= data.pages" @click="page++">Suivant →</button>
    </div>
  </div>
</template>
