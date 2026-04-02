<script setup>
import { computed, nextTick, reactive, ref, watch, proxyRefs } from "vue";
import { useRoute } from "vue-router";
import PrixSparkline from "../components/PrixSparkline.vue";
import MjViewSelect from "../components/MjViewSelect.vue";
import { useMjView } from "../composables/useMjView.js";
import {
  FLORINS_NOM,
  formatFlorin,
  formatFlorinExact,
  formatQuantiteRessource,
  useApi,
} from "../composables/useApi.js";
import { deltaNetProchainTour } from "../utils/gainPassif.js";

const props = defineProps({
  authState: { type: Object, required: true },
});

const { get, put, post } = useApi();
const route = useRoute();

const isMj = computed(() => props.authState.user?.is_mj);
const currentUserIdStr = computed(() => String(props.authState.user?.id ?? ""));

const utilisateurs = ref([]);
const mjRaw = useMjView({
  authState: props.authState,
  utilisateursListeRef: utilisateurs,
  isMjRef: isMj,
  currentUserIdStrRef: currentUserIdStr,
  allowGlobal: false,
  storageKey: "mj_view_choice_uid",
});
// Pour le template : évite de passer des Ref en props (Vue ne dé-référence pas
// automatiquement les refs imbriquées dans un objet normal).
const mj = proxyRefs(mjRaw);
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
  const uid =
    isMj.value && mjRaw.mjVueChoix.value
      ? `?uid=${encodeURIComponent(String(mjRaw.mjVueChoix.value))}`
      : "";
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

function syncMjUidFromRoute() {
  if (!isMj.value) return;
  const list = utilisateurs.value;
  if (!list?.length) return;
  const ids = new Set(list.map((u) => String(u.id)));
  const raw = route.query.uid;
  if (raw != null && raw !== "" && ids.has(String(raw))) {
    mjRaw.mjVueSetChoix(String(raw));
  }
}

watch(() => mjRaw.mjVueChoix.value, chargerStocks);
watch([() => utilisateurs.value, () => route.query.uid], syncMjUidFromRoute, { immediate: true });
chargerUtilisateurs();
chargerStocks();

/** Plusieurs gains passifs possibles par ressource */
const gainsParRid = computed(() => {
  const m = {};
  gainsPassifs.value.forEach((g) => {
    if (!m[g.ressource_id]) m[g.ressource_id] = [];
    m[g.ressource_id].push(g);
  });
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
  const uidParam =
    isMj.value && mjRaw.mjVueChoix.value
      ? `?uid=${encodeURIComponent(String(mjRaw.mjVueChoix.value))}`
      : "";
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

function texteProchainTour(stock) {
  const n = gainTourPourTri(stock);
  if (n === 0) return "0";
  return (n > 0 ? "+" : "") + String(n);
}

const nbModifications = computed(
  () => Object.values(modifEnCours.value).filter((v) => v !== "").length
);

const sort = reactive({ key: "nom", dir: "asc" });

const colonnesTri = [
  ["nom", "Ressource"],
  ["type", "Type"],
  ["quantite", "Stock actuel"],
  ["nouvelle_qte", "Nouvelle quantité"],
  ["gain_tour", "Prod. prochain tour"],
  ["commerce", "Achat / vente"],
  ["valeur", "Valeur stock (ƒ)"],
];

function gainTourPourTri(stock) {
  const list = gainsParRid.value[stock.ressource_id] || [];
  return deltaNetProchainTour(qteAffichee(stock), list);
}

const stocksTries = computed(() => {
  const key = sort.key;
  const dir = sort.dir === "asc" ? 1 : -1;
  const sorted = [...stocks.value].sort((a, b) => {
    let va;
    let vb;
    switch (key) {
      case "nom":
        va = a.ressource.nom.toLowerCase();
        vb = b.ressource.nom.toLowerCase();
        break;
      case "type":
        va = a.ressource.type;
        vb = b.ressource.type;
        break;
      case "quantite":
        va = a.quantite;
        vb = b.quantite;
        break;
      case "nouvelle_qte":
        va = qteAffichee(a);
        vb = qteAffichee(b);
        break;
      case "gain_tour":
        va = gainTourPourTri(a);
        vb = gainTourPourTri(b);
        break;
      case "commerce":
        va = a.ressource.nom.toLowerCase();
        vb = b.ressource.nom.toLowerCase();
        break;
      case "valeur":
        va = qteAffichee(a) * a.ressource.prix_achat;
        vb = qteAffichee(b) * b.ressource.prix_achat;
        break;
      default:
        va = a.ressource.nom.toLowerCase();
        vb = b.ressource.nom.toLowerCase();
    }
    return va === vb ? 0 : va < vb ? -dir : dir;
  });
  const fi = sorted.findIndex((s) => s.ressource.nom === FLORINS_NOM);
  if (fi > 0) {
    const [row] = sorted.splice(fi, 1);
    sorted.unshift(row);
  }
  return sorted;
});

const stockFlorins = computed(() =>
  stocks.value.find((s) => s.ressource.nom === FLORINS_NOM)
);

// --- Commerce (ressources ↔ florins) ---
const commerceModal = ref(null);
const commerceQte = ref(1);
const commerceQteInputRef = ref(null);
const commerceErr = ref("");
const commerceLoading = ref(false);
const historiquePrix = ref([]);

function ouvrirCommerce(stock, sens) {
  commerceModal.value = { stock, sens };
  commerceQte.value = 1;
  commerceErr.value = "";
}

const commerceTotal = computed(() => {
  if (!commerceModal.value) return 0;
  const r = commerceModal.value.stock.ressource;
  const q = Math.max(0, Math.floor(Number(commerceQte.value) || 0));
  return commerceModal.value.sens === "achat"
    ? q * r.prix_achat
    : q * r.prix_modifie;
});

async function executerCommerce() {
  if (!commerceModal.value) return;
  commerceErr.value = "";
  const q = Math.floor(Number(commerceQte.value) || 0);
  if (q <= 0) {
    commerceErr.value = "Indiquez une quantité entière positive.";
    return;
  }
  const uidParam =
    isMj.value && selectedUid.value
      ? `?uid=${encodeURIComponent(String(selectedUid.value))}`
      : "";
  commerceLoading.value = true;
  try {
    await post(`/api/stocks/commerce${uidParam}`, {
      ressource_id: commerceModal.value.stock.ressource_id,
      quantite: q,
      sens: commerceModal.value.sens,
    });
    commerceModal.value = null;
    await chargerStocks();
  } catch (e) {
    commerceErr.value = e.message;
  } finally {
    commerceLoading.value = false;
  }
}

function estFlorins(stock) {
  return stock.ressource.nom === FLORINS_NOM;
}

watch(commerceModal, async (m) => {
  if (!m || estFlorins(m.stock)) {
    historiquePrix.value = [];
  } else {
    try {
      historiquePrix.value = await get(
        `/api/ressources/${m.stock.ressource_id}/historique-prix?limit=80`
      );
    } catch {
      historiquePrix.value = [];
    }
  }
  if (m) {
    await nextTick();
    commerceQteInputRef.value?.select?.();
  }
});

function affichageStockQuantite(stock) {
  const q = qteAffichee(stock);
  if (estFlorins(stock)) return formatFlorin(q);
  return formatQuantiteRessource(q);
}

function titleStockQuantite(stock) {
  if (!estFlorins(stock)) return undefined;
  return formatFlorinExact(qteAffichee(stock)) || undefined;
}

function titleValeurStock(stock) {
  const v = qteAffichee(stock) * stock.ressource.prix_achat;
  return formatFlorinExact(v) || undefined;
}

function toggleSort(k) {
  if (sort.key === k) {
    sort.dir = sort.dir === "asc" ? "desc" : "asc";
  } else {
    sort.key = k;
    sort.dir = "asc";
  }
}

function sortLabel(k) {
  if (sort.key !== k) return "";
  return sort.dir === "asc" ? " ▲" : " ▼";
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">Gestion des Stocks</h2>
        <p class="page-subtitle">
          Modifiez les quantités puis sauvegardez.
          <span
            v-if="stockFlorins"
            class="solde-florins"
            :title="formatFlorinExact(qteAffichee(stockFlorins))"
          >
            Solde monnaie : {{ formatFlorin(qteAffichee(stockFlorins)) }}
          </span>
          <span class="stocks-sub-hint">
            Détail et historique des productions :
            <router-link to="/productions">Mes productions</router-link>.
          </span>
        </p>
      </div>
      <div class="header-actions">
        <MjViewSelect
          v-if="isMj"
          :open="mj.mjVueOpen"
          :label="mj.mjVueLabel"
          :search="mj.mjVueSearch"
          :options="mj.mjVueAutres"
          :current-choice="mj.mjVueChoix"
          :current-user-id-str="currentUserIdStr"
          :show-global="false"
          @update:open="(v) => (mj.mjVueOpen = v)"
          @update:search="(v) => (mj.mjVueSearch = v)"
          @select="mj.mjVueSetChoix"
        />
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
            <th
              v-for="[k, lab] in colonnesTri"
              :key="k"
              class="th-sort"
              @click="toggleSort(k)"
            >
              {{ lab }}{{ sortLabel(k) }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="s in stocksTries"
            :key="s.ressource_id"
            :class="{ modified: hasModif(s) }"
          >
            <td class="nom">{{ s.ressource.nom }}</td>
            <td>
              <span :class="['badge', s.ressource.type === 'Manufacturé' ? 'badge-manuf' : 'badge-prem']">
                {{ s.ressource.type }}
              </span>
            </td>
            <td class="prix" :title="titleStockQuantite(s)">
              {{ affichageStockQuantite(s) }}
            </td>
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
            <td class="gain-cell">
              <span
                v-if="!estFlorins(s)"
                class="prod-next-tour"
                :title="'Somme des règles actives pour le prochain tour (mercredi ou samedi 00h00)'"
              >
                {{ texteProchainTour(s) }}
              </span>
              <router-link
                class="button secondary small link-as-button"
                :to="{
                  path: '/productions',
                  query: {
                    ressource: String(s.ressource_id),
                    ...(isMj && mj.mjVueChoix ? { uid: String(mj.mjVueChoix) } : {}),
                  },
                }"
              >
                Voir la production
              </router-link>
            </td>
            <td class="commerce-actions">
              <template v-if="!estFlorins(s)">
                <button
                  type="button"
                  class="button small secondary"
                  @click="ouvrirCommerce(s, 'achat')"
                >
                  Acheter
                </button>
                <button
                  type="button"
                  class="button small secondary"
                  @click="ouvrirCommerce(s, 'vente')"
                >
                  Vendre
                </button>
              </template>
              <span v-else class="commerce-na">—</span>
            </td>
            <td class="prix accent" :title="titleValeurStock(s)">
              {{ formatFlorin(qteAffichee(s) * s.ressource.prix_achat) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal achat / vente contre florins -->
    <div
      v-if="commerceModal"
      class="modal-overlay"
      @click.self="commerceModal = null"
    >
      <div class="modal modal-wide commerce-modal">
        <h3 class="modal-title">
          {{
            commerceModal.sens === "achat"
              ? "Acheter contre des florins"
              : "Vendre pour des florins"
          }}
          — {{ commerceModal.stock.ressource.nom }}
        </h3>
        <p class="modal-hint">
          <template v-if="commerceModal.sens === 'achat'">
            Prix unitaire (achat) : {{ formatFlorin(commerceModal.stock.ressource.prix_achat) }}.
            Le montant est débité de votre stock « Florins ».
          </template>
          <template v-else>
            Prix unitaire (revente) : {{ formatFlorin(commerceModal.stock.ressource.prix_modifie) }}.
            Les florins sont ajoutés à votre stock « Florins ».
          </template>
        </p>
        <PrixSparkline v-if="!estFlorins(commerceModal.stock)" :points="historiquePrix" />
        <p v-if="commerceErr" class="error">{{ commerceErr }}</p>
        <label class="form-label">
          Quantité
          <input
            ref="commerceQteInputRef"
            v-model.number="commerceQte"
            type="number"
            min="1"
            class="input"
          />
        </label>
        <p class="modal-total">
          Total :
          <strong :title="formatFlorinExact(commerceTotal)">{{ formatFlorin(commerceTotal) }}</strong>
        </p>
        <div class="modal-footer">
          <button
            class="button secondary"
            :disabled="commerceLoading"
            @click="commerceModal = null"
          >
            Annuler
          </button>
          <button
            class="button"
            :disabled="commerceLoading"
            @click="executerCommerce"
          >
            {{ commerceLoading ? "…" : "Confirmer" }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>
