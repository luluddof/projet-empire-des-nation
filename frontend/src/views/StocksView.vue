<script setup>
import { computed, ref, watch } from "vue";
import { formatFlorin, useApi } from "../composables/useApi.js";

const props = defineProps({
  authState: { type: Object, required: true },
});

const { get, put, patch } = useApi();
const isMj = computed(() => props.authState.user?.is_mj);

const utilisateurs = ref([]);
const selectedUid = ref(props.authState.user?.id ?? "");
const stocks = ref([]);
const gainsPassifs = ref([]);
const erreur = ref("");
const modifEnCours = ref({});
const sauvegarde = ref(false);

async function chargerUtilisateurs() {
  if (!isMj.value) return;
  try {
    utilisateurs.value = await get("/api/utilisateurs");
  } catch (e) {
    erreur.value = e.message;
  }
}

async function chargerStocks() {
  erreur.value = "";
  const uid = isMj.value && selectedUid.value ? `?uid=${selectedUid.value}` : "";
  try {
    const [s, g] = await Promise.all([
      get(`/api/stocks${uid}`),
      get(`/api/gains-passifs${uid}`),
    ]);
    stocks.value = s;
    gainsPassifs.value = g;
    modifEnCours.value = {};
  } catch (e) {
    erreur.value = e.message;
  }
}

watch(selectedUid, chargerStocks);
chargerUtilisateurs();
chargerStocks();

const gainParRid = computed(() => {
  const m = {};
  gainsPassifs.value.forEach((g) => (m[g.ressource_id] = g));
  return m;
});

function getModif(rid) {
  return modifEnCours.value[rid] ?? "";
}

function setModif(rid, val) {
  modifEnCours.value[rid] = val;
}

function qteAffichee(stock) {
  const m = modifEnCours.value[stock.ressource_id];
  return m !== undefined && m !== "" ? Number(m) : stock.quantite;
}

function hasModif(stock) {
  const m = modifEnCours.value[stock.ressource_id];
  return m !== undefined && m !== "" && Number(m) !== stock.quantite;
}

async function sauvegarderTout() {
  erreur.value = "";
  sauvegarde.value = true;
  const uidParam = isMj.value && selectedUid.value ? `?uid=${selectedUid.value}` : "";
  const promesses = Object.entries(modifEnCours.value)
    .filter(([, v]) => v !== "")
    .map(([rid, qte]) =>
      put(`/api/stocks/${rid}${uidParam}`, { quantite: Number(qte), motif: "ajustement_manuel" })
    );
  try {
    await Promise.all(promesses);
    await chargerStocks();
  } catch (e) {
    erreur.value = e.message;
  } finally {
    sauvegarde.value = false;
  }
}

// --- Gain passif modal ---
const gainModal = ref(null);
const gainForm = ref({ quantite_par_tick: 0, actif: true });

function ouvrirGainModal(stock) {
  const gain = gainParRid.value[stock.ressource_id];
  gainForm.value = {
    quantite_par_tick: gain?.quantite_par_tick ?? 0,
    actif: gain?.actif ?? true,
  };
  gainModal.value = stock;
}

const { put: apiPut, del: apiDel } = useApi();

async function sauvegarderGain() {
  const uidParam = isMj.value && selectedUid.value ? `?uid=${selectedUid.value}` : "";
  try {
    if (gainForm.value.quantite_par_tick === 0) {
      if (gainParRid.value[gainModal.value.ressource_id]) {
        const { del } = useApi();
        await del(`/api/gains-passifs/${gainModal.value.ressource_id}${uidParam}`);
      }
    } else {
      await put(
        `/api/gains-passifs/${gainModal.value.ressource_id}${uidParam}`,
        gainForm.value
      );
    }
    await chargerStocks();
    gainModal.value = null;
  } catch (e) {
    erreur.value = e.message;
  }
}

const nbModifications = computed(
  () => Object.values(modifEnCours.value).filter((v) => v !== "").length
);
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">Gestion des Stocks</h2>
        <p class="page-subtitle">Modifiez les quantités puis sauvegardez</p>
      </div>
      <div class="header-actions">
        <select v-if="isMj" v-model="selectedUid" class="select">
          <option v-for="u in utilisateurs" :key="u.id" :value="u.id">
            {{ u.username }}{{ u.is_mj ? " (MJ)" : "" }}
          </option>
        </select>
        <button
          class="button"
          :disabled="nbModifications === 0 || sauvegarde"
          @click="sauvegarderTout"
        >
          {{ sauvegarde ? "Sauvegarde…" : `Sauvegarder (${nbModifications})` }}
        </button>
      </div>
    </div>

    <p v-if="erreur" class="error">{{ erreur }}</p>

    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Ressource</th>
            <th>Type</th>
            <th>Stock actuel</th>
            <th>Nouvelle quantité</th>
            <th>Gain passif / tick</th>
            <th>Valeur stock (ƒ)</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="s in stocks"
            :key="s.ressource_id"
            :class="{ modified: hasModif(s) }"
          >
            <td class="nom">{{ s.ressource.nom }}</td>
            <td>
              <span :class="['badge', s.ressource.type === 'Manufacturé' ? 'badge-manuf' : 'badge-prem']">
                {{ s.ressource.type }}
              </span>
            </td>
            <td class="prix">{{ s.quantite }}</td>
            <td>
              <input
                type="number"
                class="input-qty"
                :value="getModif(s.ressource_id)"
                :placeholder="s.quantite"
                min="0"
                @input="setModif(s.ressource_id, $event.target.value)"
              />
            </td>
            <td>
              <button
                class="gain-btn"
                :class="{
                  'gain-positif': gainParRid[s.ressource_id]?.quantite_par_tick > 0,
                  'gain-negatif': gainParRid[s.ressource_id]?.quantite_par_tick < 0,
                }"
                @click="ouvrirGainModal(s)"
              >
                <template v-if="gainParRid[s.ressource_id]">
                  {{ gainParRid[s.ressource_id].quantite_par_tick > 0 ? "+" : "" }}
                  {{ gainParRid[s.ressource_id].quantite_par_tick }}
                  <span v-if="!gainParRid[s.ressource_id].actif" class="inactive">(inactif)</span>
                </template>
                <template v-else>
                  <span class="add-gain">+ configurer</span>
                </template>
              </button>
            </td>
            <td class="prix accent">
              {{ formatFlorin(qteAffichee(s) * s.ressource.prix_achat) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal gain passif -->
    <div v-if="gainModal" class="modal-overlay" @click.self="gainModal = null">
      <div class="modal modal-sm">
        <h3 class="modal-title">
          Gain passif — {{ gainModal.ressource.nom }}
        </h3>
        <p class="modal-hint">
          Valeur positive = gain, négative = perte.<br />
          Appliqué chaque <strong>mercredi et samedi à 00h00</strong>.
        </p>
        <label class="form-label">
          Quantité par tick
          <input v-model.number="gainForm.quantite_par_tick" type="number" class="input" />
        </label>
        <label class="form-label checkbox-label">
          <input v-model="gainForm.actif" type="checkbox" />
          Actif
        </label>
        <div class="modal-footer">
          <button class="button secondary" @click="gainModal = null">Annuler</button>
          <button class="button" @click="sauvegarderGain">Sauvegarder</button>
        </div>
      </div>
    </div>
  </div>
</template>
