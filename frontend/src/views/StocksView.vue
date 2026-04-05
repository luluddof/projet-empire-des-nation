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
import { playCashSound } from "../utils/playCashSound.js";

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
const VOIR_TOUTES_KEY = "stocks_voir_toutes_ressources";

function readVoirToutesPref() {
  try {
    return typeof localStorage !== "undefined" && localStorage.getItem(VOIR_TOUTES_KEY) === "1";
  } catch {
    return false;
  }
}

const stocks = ref([]);
const gainsPassifs = ref([]);
const erreur = ref("");
/** Faux : vue réduite (possédé, achetable au moins ×1 au prix local, ou production / gain passif). */
const voirToutesLesRessources = ref(readVoirToutesPref());
const modifEnCours = ref({});
const sauvegarde = ref(false);

const isMjOtherView = computed(() => isMj.value && mjRaw.mjVueChoix.value && String(mjRaw.mjVueChoix.value) !== currentUserIdStr.value);

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
watch(voirToutesLesRessources, (v) => {
  try {
    localStorage.setItem(VOIR_TOUTES_KEY, v ? "1" : "0");
  } catch {
    /* ignore */
  }
});
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
  const promesses = stocks.value
    .filter((s) => hasModif(s))
    .map((s) =>
      put(`/api/stocks/${s.ressource_id}${uidParam}`, {
        quantite: Number(modifEnCours.value[s.ressource_id]),
        motif: "ajustement_manuel",
      })
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

const nbModifications = computed(() => stocks.value.filter((s) => hasModif(s)).length);

const sort = reactive({ key: "nom", dir: "asc" });

const colonnesTri = computed(() => [
  ["nom", "Ressource"],
  ["type", "Type"],
  ["quantite", "Stock actuel"],
  ...(isMj.value ? [["nouvelle_qte", "Nouvelle quantité"]] : []),
  ["gain_tour", "Prod. prochain tour"],
  ["commerce", "Achat / vente"],
  ["valeur", "Valeur stock (ƒ)"],
]);

function gainTourPourTri(stock) {
  const list = gainsParRid.value[stock.ressource_id] || [];
  return deltaNetProchainTour(qteAffichee(stock), list);
}

const stocksTries = computed(() => {
  const key = sort.key;
  const dir = sort.dir === "asc" ? 1 : -1;
  const sorted = [...stocksFiltresRecherche.value].sort((a, b) => {
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

/**
 * Vue réduite : monnaie toujours affichée ; autres ressources uniquement si quantité en stock > 0
 * (pas les lignes « achetables » sans possession).
 */
function ressourceVisibleDansVueStocks(stock) {
  if (stock.ressource.nom === FLORINS_NOM) return true;
  return qteAffichee(stock) > 0;
}

const stocksFiltres = computed(() => {
  if (voirToutesLesRessources.value) return stocks.value;
  return stocks.value.filter(ressourceVisibleDansVueStocks);
});

const nbStocksTotal = computed(() => stocks.value.length);
const nbStocksFiltres = computed(() => stocksFiltres.value.length);

const rechercheStocks = ref("");

function texteRechercheNormalise() {
  return String(rechercheStocks.value ?? "").trim().toLowerCase();
}

const stocksFiltresRecherche = computed(() => {
  const q = texteRechercheNormalise();
  if (!q) return stocksFiltres.value;
  return stocksFiltres.value.filter((s) => {
    const nom = (s.ressource.nom || "").toLowerCase();
    const type = (s.ressource.type || "").toLowerCase();
    return nom.includes(q) || type.includes(q);
  });
});

const nbStocksRecherche = computed(() => stocksFiltresRecherche.value.length);

const aUneRechercheStock = computed(() => texteRechercheNormalise().length > 0);

// --- Commerce (ressources ↔ florins) ---
const commerceModal = ref(null);
const commerceQte = ref(1);
const commerceAchatMode = ref("local"); // local | lointain
const commerceQteInputRef = ref(null);
const commerceErr = ref("");
const commerceLoading = ref(false);
const historiquePrix = ref([]);

function ouvrirCommerce(stock, sens) {
  commerceModal.value = { stock, sens };
  commerceQte.value = 1;
  commerceAchatMode.value = "local";
  commerceErr.value = "";
}

const commercePrixUnitaire = computed(() => {
  if (!commerceModal.value) return 0;
  const r = commerceModal.value.stock.ressource;
  if (commerceModal.value.sens === "vente") return r.prix_modifie;
  return commerceAchatMode.value === "lointain" ? r.prix_lointain : r.prix_achat;
});

const commerceTotal = computed(() => {
  if (!commerceModal.value) return 0;
  const q = Math.max(0, Math.floor(Number(commerceQte.value) || 0));
  return q * (Number(commercePrixUnitaire.value) || 0);
});

async function executerCommerce() {
  if (!commerceModal.value) return;
  if (isMjOtherView.value) {
    commerceErr.value = "Achat / vente indisponible pour un autre joueur : utilisez la colonne des quantités et Sauvegarder.";
    return;
  }
  commerceErr.value = "";
  const q = Math.floor(Number(commerceQte.value) || 0);
  if (q <= 0) {
    commerceErr.value = "Indiquez une quantité entière positive.";
    return;
  }
  const uidParam =
    isMj.value && mjRaw.mjVueChoix.value
      ? `?uid=${encodeURIComponent(String(mjRaw.mjVueChoix.value))}`
      : "";
  commerceLoading.value = true;
  try {
    const payload = {
      ressource_id: commerceModal.value.stock.ressource_id,
      quantite: q,
      sens: commerceModal.value.sens,
    };
    if (commerceModal.value.sens === "achat") {
      payload.achat_mode = commerceAchatMode.value;
    }
    await post(`/api/stocks/commerce${uidParam}`, payload);
    playCashSound();
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

/** MJ sur les stocks d’un autre joueur : pas de commerce, ajustement manuel (+/− ou saisie). */
function ajusterQuantiteMj(stock, delta) {
  const cur = Number(qteAffichee(stock)) || 0;
  const next = Math.max(0, cur + delta);
  setModif(stock.ressource_id, String(next));
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
          <template v-if="isMj && isMjOtherView">
            Vue stocks de <strong>{{ mj.mjVueLabel }}</strong> : l’achat et la vente automatiques sont désactivés.
            Utilisez la colonne « Nouvelle quantité » (saisie ou boutons +/−) puis
            <strong>Sauvegarder</strong> pour ajouter ou retirer des unités (y compris les florins).
          </template>
          <template v-else-if="isMj">Modifiez les quantités puis sauvegardez, ou utilisez Acheter / Vendre.</template>
          <template v-else>Consultez vos stocks et effectuez des achats/ventes.</template>
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
          v-if="isMj"
          class="button"
          :disabled="nbModifications === 0 || sauvegarde"
          @click="sauvegarderTout"
        >
          {{ sauvegarde ? "Sauvegarde…" : `Sauvegarder (${nbModifications})` }}
        </button>
      </div>
    </div>

    <p v-if="erreur" class="error">{{ erreur }}</p>

    <div class="stocks-toolbar">
      <div class="stocks-toolbar-row stocks-mode-row" role="group" aria-label="Mode d'affichage des stocks">
        <span class="stocks-mode-label" :class="{ 'is-active': !voirToutesLesRessources }">Mes stocks</span>
        <button
          type="button"
          class="stocks-switch"
          role="switch"
          :aria-checked="voirToutesLesRessources"
          :aria-label="
            voirToutesLesRessources
              ? 'Afficher tout le catalogue : activé'
              : 'Afficher uniquement les ressources possédées'
          "
          @click="voirToutesLesRessources = !voirToutesLesRessources"
        >
          <span class="stocks-switch-track" :class="{ 'is-on': voirToutesLesRessources }">
            <span class="stocks-switch-thumb" />
          </span>
        </button>
        <span class="stocks-mode-label" :class="{ 'is-active': voirToutesLesRessources }">Tout le catalogue</span>
      </div>
      <div class="stocks-toolbar-row">
        <label class="stocks-search-label">
          <span class="stocks-search-title">Rechercher une ressource</span>
          <input
            v-model.trim="rechercheStocks"
            type="search"
            class="input stocks-search-input"
            placeholder="Nom ou type…"
            autocomplete="off"
            spellcheck="false"
          />
        </label>
      </div>
      <p class="stocks-filter-meta">
        <template v-if="aUneRechercheStock">
          {{ nbStocksRecherche }} résultat{{ nbStocksRecherche !== 1 ? "s" : "" }} sur {{ nbStocksFiltres }}
          ressource{{ nbStocksFiltres !== 1 ? "s" : "" }} affichée{{ nbStocksFiltres !== 1 ? "s" : "" }}.
        </template>
        <template v-else-if="voirToutesLesRessources">
          Catalogue complet : {{ nbStocksFiltres }} ressources.
        </template>
        <template v-else>
          {{ nbStocksFiltres }} ressource{{ nbStocksFiltres !== 1 ? "s" : "" }} en possession sur
          {{ nbStocksTotal }} au catalogue (activez « Tout le catalogue » pour tout voir).
        </template>
      </p>
    </div>

    <p
      v-if="aUneRechercheStock && nbStocksRecherche === 0 && stocksFiltres.length > 0"
      class="stocks-empty-search"
    >
      Aucune ressource ne correspond à « {{ rechercheStocks }} ».
    </p>

    <div class="table-wrap">
      <table v-show="nbStocksRecherche > 0" class="data-table">
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
            <td v-if="isMj">
              <div class="mj-qty-cell">
                <input
                  type="number"
                  class="input-qty"
                  :value="getModif(s.ressource_id)"
                  :placeholder="s.quantite"
                  min="0"
                  step="any"
                  @input="setModif(s.ressource_id, $event.target.value)"
                />
                <div v-if="isMjOtherView" class="mj-qty-delta" :title="'Ajouter ou retirer une unité (puis Sauvegarder)'">
                  <button type="button" class="button secondary tiny" @click="ajusterQuantiteMj(s, -1)">−</button>
                  <button type="button" class="button secondary tiny" @click="ajusterQuantiteMj(s, 1)">+</button>
                </div>
              </div>
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
                  :disabled="isMjOtherView"
                  @click="ouvrirCommerce(s, 'achat')"
                >
                  Acheter
                </button>
                <button
                  type="button"
                  class="button small secondary"
                  :disabled="isMjOtherView"
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
            Prix unitaire :
            <strong>{{ formatFlorin(commercePrixUnitaire) }}</strong>.
            Le montant est débité de votre stock « Florins ».
          </template>
          <template v-else>
            Prix unitaire (revente) : <strong>{{ formatFlorin(commercePrixUnitaire) }}</strong>.
            Les florins sont ajoutés à votre stock « Florins ».
          </template>
        </p>
        <p v-if="isMjOtherView" class="error">
          En tant que MJ, vous ne pouvez pas acheter/vendre pour un autre joueur. Utilisez uniquement l’ajustement manuel des stocks.
        </p>
        <div v-if="commerceModal.sens === 'achat'" class="commerce-mode">
          <button
            type="button"
            :class="['button', 'secondary', 'small', commerceAchatMode === 'local' ? 'is-active' : '']"
            @click="commerceAchatMode = 'local'"
          >
            Achat local
          </button>
          <button
            type="button"
            :class="['button', 'secondary', 'small', commerceAchatMode === 'lointain' ? 'is-active' : '']"
            @click="commerceAchatMode = 'lointain'"
          >
            Achat lointain
          </button>
        </div>
        <div v-if="!estFlorins(commerceModal.stock) && historiquePrix.length < 2" class="sparkline-single">
          Historique insuffisant ({{ historiquePrix.length }} point) — achat/vente possible.
        </div>
        <PrixSparkline
          v-else-if="!estFlorins(commerceModal.stock)"
          :points="historiquePrix"
          :value-key="commerceModal.sens === 'vente' ? 'prix_modifie' : 'prix_achat'"
          :label="commerceModal.sens === 'vente'
            ? 'Évolution du prix de revente catalogue (ƒ)'
            : 'Évolution du prix d’achat catalogue (ƒ)'"
        />
        <p v-if="commerceErr" class="error">{{ commerceErr }}</p>
        <label class="form-label">
          Quantité
          <input
            ref="commerceQteInputRef"
            v-model.number="commerceQte"
            type="number"
            min="1"
            class="input"
            @focus="(e) => e.target.select()"
            @click="(e) => e.target.select()"
          />
        </label>
        <div class="modal-total" :title="formatFlorinExact(commerceTotal)">
          <span class="modal-total-label">Total</span>
          <strong class="modal-total-value">{{ formatFlorin(commerceTotal) }}</strong>
        </div>
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
            :disabled="commerceLoading || isMjOtherView"
            @click="executerCommerce"
          >
            {{ commerceLoading ? "…" : "Confirmer" }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.stocks-toolbar {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 14px;
  padding: 14px 16px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 10px;
  max-width: 100%;
}

.stocks-toolbar-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.stocks-mode-row {
  gap: 14px;
  padding: 4px 0;
}

.stocks-mode-label {
  font-size: 15px;
  font-weight: 600;
  color: #64748b;
  transition: color 0.15s ease;
  user-select: none;
}

.stocks-mode-label.is-active {
  color: #e2e8f0;
}

.stocks-switch {
  border: none;
  background: transparent;
  padding: 6px 10px;
  cursor: pointer;
  flex-shrink: 0;
  border-radius: 8px;
}

.stocks-switch:focus-visible {
  outline: 2px solid #38bdf8;
  outline-offset: 3px;
}

.stocks-switch-track {
  display: block;
  width: 56px;
  height: 30px;
  border-radius: 999px;
  background: #334155;
  position: relative;
  transition: background 0.2s ease;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.35);
}

.stocks-switch-track.is-on {
  background: #0284c7;
}

.stocks-switch-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #f8fafc;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
  transition: transform 0.2s ease;
}

.stocks-switch-track.is-on .stocks-switch-thumb {
  transform: translateX(26px);
}

.stocks-search-label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  max-width: 420px;
  margin: 0;
}

.stocks-search-title {
  font-size: 13px;
  font-weight: 600;
  color: #cbd5e1;
}

.stocks-search-input {
  width: 100%;
  min-height: 42px;
  font-size: 15px;
}

.stocks-filter-meta {
  margin: 0;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.5;
}

.stocks-empty-search {
  margin: 0 0 12px;
  padding: 12px 14px;
  border-radius: 8px;
  background: rgba(251, 191, 36, 0.08);
  border: 1px solid rgba(251, 191, 36, 0.35);
  color: #fcd34d;
  font-size: 14px;
}

.mj-qty-cell {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.mj-qty-delta {
  display: inline-flex;
  gap: 4px;
}

.button.tiny {
  min-width: 2rem;
  padding: 2px 8px;
  font-size: 14px;
  line-height: 1.2;
}
</style>
