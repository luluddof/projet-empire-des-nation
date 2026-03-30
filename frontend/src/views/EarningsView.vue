<script setup>
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import {
  FLORINS_NOM,
  formatCompactNombre,
  formatFlorin,
  formatFlorinExact,
  formatQuantiteRessource,
  useApi,
} from "../composables/useApi.js";

const props = defineProps({
  authState: { type: Object, required: true },
});

const { get } = useApi();
const route = useRoute();
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
  const uid =
    isMj.value && selectedUid.value
      ? `&uid=${encodeURIComponent(String(selectedUid.value))}`
      : "";
  try {
    data.value = await get(`/api/transactions?page=${page.value}&per_page=50${uid}`);
  } catch (e) {
    erreur.value = e.message;
  }
}

function syncMjUidFromRoute() {
  if (!isMj.value) return;
  const list = utilisateurs.value;
  if (!list?.length) return;
  const ids = new Set(list.map((u) => String(u.id)));
  const raw = route.query.uid;
  if (raw != null && raw !== "" && ids.has(String(raw))) {
    selectedUid.value = String(raw);
  }
}

watch([selectedUid, page], chargerTransactions);
watch([() => utilisateurs.value, () => route.query.uid], syncMjUidFromRoute, { immediate: true });
chargerUtilisateurs();
chargerTransactions();

const stats = computed(() => {
  const txs = data.value.transactions;
  // On classe gain / perte par le signe de la quantité (et non par la valeur_florins),
  // car valeur_florins peut être arrondi à 0 pour de petites variations.
  const gains = txs.filter((t) => t.quantite > 0).reduce((s, t) => s + t.valeur_florins, 0);
  const pertes = txs.filter((t) => t.quantite < 0).reduce((s, t) => s + t.valeur_florins, 0);
  return { gains, pertes, net: gains + pertes };
});

/** Clé jour local YYYY-MM-DD pour regrouper l’historique. */
function cleJourLocal(iso) {
  const d = new Date(iso);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/**
 * Regroupe la page courante par jour (ordre décroissant : jour le plus récent d’abord),
 * puis sépare gains / pertes / neutre (valeur 0) par jour.
 */
const blocsParJour = computed(() => {
  const txs = data.value.transactions;
  const ordreJours = [];
  const parJour = new Map();

  for (const t of txs) {
    const key = cleJourLocal(t.created_at);
    if (!parJour.has(key)) {
      parJour.set(key, {
        key,
        date: new Date(t.created_at),
        gains: [],
        pertes: [],
        neutre: [],
      });
      ordreJours.push(key);
    }
    const b = parJour.get(key);
    const q = t.quantite;
    if (q > 0) b.gains.push(t);
    else if (q < 0) b.pertes.push(t);
    else b.neutre.push(t);
  }

  return ordreJours.map((k) => parJour.get(k));
});

function formatDate(iso) {
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function titreJourBloc(bloc) {
  const s = new Date(bloc.date).toLocaleDateString("fr-FR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  return s.charAt(0).toUpperCase() + s.slice(1);
}

const MOTIFS = {
  gain_passif: "Gain passif",
  ajustement_manuel: "Ajustement",
  ajustement_mj: "Ajustement MJ",
  achat_marche: "Achat (marché)",
  vente_marche: "Vente (marché)",
};
function labelMotif(motif) {
  return MOTIFS[motif] ?? motif ?? "—";
}

function formatQuantiteMouvement(t) {
  const n = t.quantite;
  const abs = Math.abs(n);
  if (t.ressource.nom === FLORINS_NOM) {
    return (n < 0 ? "−" : n > 0 ? "+" : "") + formatCompactNombre(abs);
  }
  return (n < 0 ? "−" : n > 0 ? "+" : "") + formatQuantiteRessource(abs);
}

function titleQuantiteMouvement(t) {
  if (t.ressource.nom !== FLORINS_NOM) return undefined;
  return (t.quantite > 0 ? "+" : "") + new Intl.NumberFormat("fr-FR").format(t.quantite);
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
        <div class="stat-value" :title="formatFlorinExact(stats.gains)">
          {{ formatFlorin(stats.gains) }}
        </div>
      </div>
      <div class="stat-card stat-perte">
        <div class="stat-label">Pertes totales (page)</div>
        <div class="stat-value" :title="formatFlorinExact(stats.pertes)">
          {{ formatFlorin(stats.pertes) }}
        </div>
      </div>
      <div class="stat-card" :class="stats.net >= 0 ? 'stat-gain' : 'stat-perte'">
        <div class="stat-label">Solde net (page)</div>
        <div class="stat-value" :title="formatFlorinExact(stats.net)">
          {{ formatFlorin(stats.net) }}
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Transactions totales</div>
        <div class="stat-value">{{ data.total }}</div>
      </div>
    </div>

    <div class="table-wrap">
      <table class="data-table earnings-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Ressource</th>
            <th>Quantité</th>
            <th>Valeur (ƒ)</th>
            <th>Motif</th>
          </tr>
        </thead>
        <tbody v-if="data.transactions.length === 0">
          <tr>
            <td colspan="5" class="empty">Aucune transaction pour le moment.</td>
          </tr>
        </tbody>
        <tbody
          v-for="bloc in blocsParJour"
          v-else
          :key="bloc.key"
          class="earnings-day-block"
        >
          <tr class="earnings-day-header">
            <td colspan="5">{{ titreJourBloc(bloc) }}</td>
          </tr>
          <template v-if="bloc.gains.length">
            <tr class="earnings-subhead earnings-subhead-gain">
              <td colspan="5">Gains</td>
            </tr>
            <tr v-for="t in bloc.gains" :key="t.id">
              <td class="date">{{ formatDate(t.created_at) }}</td>
              <td class="nom">{{ t.ressource.nom }}</td>
              <td
                :class="['prix', t.quantite >= 0 ? 'text-gain' : 'text-perte']"
                :title="titleQuantiteMouvement(t)"
              >
                {{ formatQuantiteMouvement(t) }}
              </td>
              <td
                :class="['prix', t.valeur_florins >= 0 ? 'text-gain' : 'text-perte']"
                :title="formatFlorinExact(t.valeur_florins)"
              >
                {{ t.valeur_florins > 0 ? "+" : "" }}{{ formatFlorin(t.valeur_florins) }}
              </td>
              <td>
                <span class="tag">{{ labelMotif(t.motif) }}</span>
              </td>
            </tr>
          </template>
          <template v-if="bloc.pertes.length">
            <tr class="earnings-subhead earnings-subhead-perte">
              <td colspan="5">Pertes</td>
            </tr>
            <tr v-for="t in bloc.pertes" :key="t.id">
              <td class="date">{{ formatDate(t.created_at) }}</td>
              <td class="nom">{{ t.ressource.nom }}</td>
              <td
                :class="['prix', t.quantite >= 0 ? 'text-gain' : 'text-perte']"
                :title="titleQuantiteMouvement(t)"
              >
                {{ formatQuantiteMouvement(t) }}
              </td>
              <td
                :class="['prix', t.valeur_florins >= 0 ? 'text-gain' : 'text-perte']"
                :title="formatFlorinExact(t.valeur_florins)"
              >
                {{ t.valeur_florins > 0 ? "+" : "" }}{{ formatFlorin(t.valeur_florins) }}
              </td>
              <td>
                <span class="tag">{{ labelMotif(t.motif) }}</span>
              </td>
            </tr>
          </template>
          <template v-if="bloc.neutre.length">
            <tr class="earnings-subhead earnings-subhead-neutral">
              <td colspan="5">Sans effet sur la valeur (0 ƒ)</td>
            </tr>
            <tr v-for="t in bloc.neutre" :key="t.id">
              <td class="date">{{ formatDate(t.created_at) }}</td>
              <td class="nom">{{ t.ressource.nom }}</td>
              <td
                :class="['prix', t.quantite >= 0 ? 'text-gain' : 'text-perte']"
                :title="titleQuantiteMouvement(t)"
              >
                {{ formatQuantiteMouvement(t) }}
              </td>
              <td
                class="prix"
                :title="formatFlorinExact(t.valeur_florins)"
              >
                {{ formatFlorin(t.valeur_florins) }}
              </td>
              <td>
                <span class="tag">{{ labelMotif(t.motif) }}</span>
              </td>
            </tr>
          </template>
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
