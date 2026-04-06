<script setup>
import { computed, nextTick, reactive, ref, watch, proxyRefs } from "vue";
import { useRoute, useRouter } from "vue-router";
import ProductionChronologieChart from "../components/ProductionChronologieChart.vue";
import MjViewSelect from "../components/MjViewSelect.vue";
import { useMjView } from "../composables/useMjView.js";
import { FLORINS_NOM, useApi } from "../composables/useApi.js";
import { formatEffetProduction } from "../utils/gainPassif.js";

const props = defineProps({
  authState: { type: Object, required: true },
});

const { get, post, put, del } = useApi();
const route = useRoute();
const router = useRouter();

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
const mj = proxyRefs(mjRaw);
const gainsPassifs = ref([]);
const ressourcesListe = ref([]);
const balisesDisponibles = ref([]);
const chronologie = ref(null);
const erreur = ref("");
const gainQteInputRef = ref(null);

/** Sélectionne toute la valeur ; rAF aide certains navigateurs sur `type="number"`. */
function selectAllInputText(e) {
  const el = e.target;
  requestAnimationFrame(() => {
    if (typeof el.select === "function") el.select();
  });
}

const sort = reactive({ key: "nom", dir: "asc" });

const ressourceIdFiltre = computed(() => {
  const q = route.query.ressource;
  if (q == null || q === "") return null;
  const n = Number(q);
  return Number.isNaN(n) ? null : n;
});

const nomRessourceFiltre = computed(() => {
  if (!ressourceIdFiltre.value) return "";
  const r = ressourcesListe.value.find((x) => x.id === ressourceIdFiltre.value);
  return r?.nom ?? chronologie.value?.ressource?.nom ?? "";
});

/** Query route /productions en conservant le joueur MJ (uid) ; `ressource` omis = vue globale. */
function buildProductionsQuery({ ressource } = {}) {
  const q = {};
  if (ressource != null && ressource !== "") q.ressource = String(ressource);
  if (isMj.value && mjRaw.mjVueChoix.value) {
    q.uid = String(mjRaw.mjVueChoix.value);
  }
  return q;
}

const productionsQueryAll = computed(() => buildProductionsQuery({}));

async function chargerUtilisateurs() {
  if (!isMj.value) return;
  try {
    utilisateurs.value = await get("/api/utilisateurs");
  } catch (e) {
    erreur.value = e.message;
  }
}

async function charger() {
  erreur.value = "";
  const uid =
    isMj.value && mjRaw.mjVueChoix.value
      ? `?uid=${encodeURIComponent(String(mjRaw.mjVueChoix.value))}`
      : "";
  const qRes = isMj.value ? "?global=1" : "";
  try {
    const [g, r, balises] = await Promise.all([
      get(`/api/gains-passifs${uid}`),
      get(`/api/ressources${qRes}`),
      get("/api/gains-passifs/balises"),
    ]);
    gainsPassifs.value = g;
    ressourcesListe.value = r || [];
    balisesDisponibles.value = balises || [];
  } catch (e) {
    erreur.value = e.message;
  }
  await chargerChronologie();
}

function libelleBalise(b) {
  const map = new Map((balisesDisponibles.value || []).map((x) => [x.id, x.label]));
  return map.get(b) ?? map.get("autre") ?? b ?? "—";
}

/** Justifications choisissables à la main (la récolte fructueuse est réservée au tirage automatique). */
const balisesFormulaireProduction = computed(() =>
  (balisesDisponibles.value || []).filter((b) => b.id !== "recolte_fructueuse"),
);

async function chargerChronologie() {
  const rid = ressourceIdFiltre.value;
  if (!rid) {
    chronologie.value = null;
    return;
  }
  const uidParam =
    isMj.value && mjRaw.mjVueChoix.value
      ? `&uid=${encodeURIComponent(String(mjRaw.mjVueChoix.value))}`
      : "";
  try {
    chronologie.value = await get(`/api/gains-passifs/chronologie?ressource_id=${rid}${uidParam}`);
  } catch (e) {
    erreur.value = e.message;
    chronologie.value = null;
  }
}

watch(() => mjRaw.mjVueChoix.value, charger);
watch(
  () => route.query.ressource,
  () => charger()
);

watch(utilisateurs, (list) => {
  if (!isMj.value || !list?.length) return;
  const ids = new Set(list.map((u) => String(u.id)));
  const fromRoute =
    route.query.uid != null && route.query.uid !== "" ? String(route.query.uid) : null;
  if (fromRoute && ids.has(fromRoute)) {
    mjRaw.mjVueSetChoix(fromRoute);
    return;
  }
  const cur = String(mjRaw.mjVueChoix.value ?? "");
  if (!cur || !ids.has(cur)) {
    const me = props.authState.user?.id;
    if (me != null && ids.has(String(me))) {
      mjRaw.mjVueSetChoix(String(me));
    } else {
      mjRaw.mjVueSetChoix(String(list[0].id));
    }
  }
});

watch(
  () => route.query.uid,
  () => {
    const list = utilisateurs.value;
    if (!isMj.value || !list?.length) return;
    const ids = new Set(list.map((u) => String(u.id)));
    const fromRoute =
      route.query.uid != null && route.query.uid !== "" ? String(route.query.uid) : null;
    if (fromRoute && ids.has(fromRoute)) {
      mjRaw.mjVueSetChoix(fromRoute);
    }
  }
);

chargerUtilisateurs();
charger();

const gainsFiltres = computed(() => {
  const id = ressourceIdFiltre.value;
  if (id == null) return gainsPassifs.value;
  return gainsPassifs.value.filter((g) => Number(g.ressource_id) === Number(id));
});

const gainsTries = computed(() => {
  const dir = sort.dir === "asc" ? 1 : -1;
  const list = [...gainsFiltres.value];
  return list.sort((a, b) => {
    let va;
    let vb;
    switch (sort.key) {
      case "nom":
        va = (a.ressource?.nom ?? "").toLowerCase();
        vb = (b.ressource?.nom ?? "").toLowerCase();
        break;
      case "qte":
        va = a.quantite_par_tour;
        vb = b.quantite_par_tour;
        break;
      case "balise":
        va = (a.balise || "autre").toLowerCase();
        vb = (b.balise || "autre").toLowerCase();
        break;
      case "actif":
        va = a.actif ? 1 : 0;
        vb = b.actif ? 1 : 0;
        break;
      case "duree":
        va = a.definitif ? 1e9 : a.tours_restants ?? 0;
        vb = b.definitif ? 1e9 : b.tours_restants ?? 0;
        break;
      default:
        va = (a.ressource?.nom ?? "").toLowerCase();
        vb = (b.ressource?.nom ?? "").toLowerCase();
    }
    return va === vb ? 0 : va < vb ? -dir : dir;
  });
});

const productionsParRessource = computed(() => {
  const m = new Map();
  for (const g of gainsPassifs.value || []) {
    const rid = Number(g.ressource_id);
    if (!m.has(rid)) {
      m.set(rid, { ressource_id: rid, ressource: g.ressource, gains: [] });
    }
    m.get(rid).gains.push(g);
  }
  const out = Array.from(m.values());
  out.sort((a, b) => (a.ressource?.nom ?? "").localeCompare(b.ressource?.nom ?? "", "fr"));
  for (const x of out) {
    x.gains.sort((a, b) => (a.id ?? 0) - (b.id ?? 0));
  }
  return out;
});

function ouvrirDetailRessource(rid) {
  if (!rid) return;
  router.push({ path: "/productions", query: buildProductionsQuery({ ressource: rid }) });
}

function ouvrirCreationSelonContexte() {
  if (ressourceIdFiltre.value) {
    ouvrirCreation(ressourceIdFiltre.value);
  } else {
    ouvrirCreationVide();
  }
}

function ouvrirAjoutProductionPourRessource(ressourceId, nom = "") {
  ouvrirCreation(ressourceId, nom);
}

function toggleSort(k) {
  if (sort.key === k) sort.dir = sort.dir === "asc" ? "desc" : "asc";
  else {
    sort.key = k;
    sort.dir = "asc";
  }
}

function sortLabel(k) {
  if (sort.key !== k) return "";
  return sort.dir === "asc" ? " ▲" : " ▼";
}

// --- Modal gain ---
const gainFormModal = ref(null);
const gainForm = reactive({
  ressource_id: null,
  quantite_par_tour: 1,
  balise: "autre",
  mode_production: "fixe",
  actif: true,
  /** null = illimité (comme tours_restants NULL côté API). */
  tours_restants: null,
  delai_tours: 0,
});

/** Affichage du champ « tours restants » : ∞ = illimité (gainForm.tours_restants === null). */
const toursRestantsInput = ref("∞");
/** Panneau d’aide « ? » pour la durée (masqué par défaut). */
const toursRestantsAideOuverte = ref(false);
/** Panneau d’aide « ? » pour le mode pourcentage (masqué par défaut). */
const pourcentageAideOuverte = ref(false);

/** Création depuis la fiche graphe (ressource dans l’URL) : pas de changement de ressource dans la modale. */
const ressourceVerrouilleeEnCreation = computed(
  () =>
    gainFormModal.value?.mode === "create" &&
    ressourceIdFiltre.value != null &&
    gainForm.ressource_id != null &&
    Number(gainForm.ressource_id) === Number(ressourceIdFiltre.value),
);

function syncToursRestantsInputFromForm() {
  if (gainForm.tours_restants == null) toursRestantsInput.value = "∞";
  else toursRestantsInput.value = String(gainForm.tours_restants);
}

/** Minuscules, sans accents, espaces normalisés (pour reconnaître « infini », « l’infini », etc.). */
function normalizeInfinityText(s) {
  return String(s)
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .replace(/['']/g, "")
    .replace(/\s+/g, " ");
}

/**
 * Texte interprété comme « illimité » : vide, symbole ∞, ou formulations proches de infini / synonymes.
 */
function textMeansInfinity(raw) {
  const t = String(raw ?? "").trim();
  if (t === "") return true;
  if (t === "∞" || t === "\u221e") return true;

  const n = normalizeInfinityText(t);

  // Codes courts (claviers sans ∞)
  if (n === "inf" || n === "infinity") return true;

  // Synonymes et expressions usuelles
  const patterns = [
    /^infini$/,
    /^infinie$/,
    /^infinis$/,
    /^infinit$/,
    /^l infini$/,
    /^linfini$/,
    /infini/,
    /infin\b/,
    /illimit/,
    /sans limite/,
    /sans fin/,
    /pour toujours/,
    /a vie$/,
    /etern/,
    /toujours/,
    /unlimited/,
    /unendlich/,
    /jamais fin/,
  ];
  if (patterns.some((re) => re.test(n))) return true;

  // Fautes fréquentes proches de « infini » (distance simple)
  if (n.length >= 4 && n.length <= 12 && levenshtein1ToInfini(n)) return true;

  return false;
}

/** True si la chaîne ressemble à « infini » (distance ≤ 2, longueur raisonnable). */
function levenshtein1ToInfini(s) {
  const target = "infini";
  if (s === target) return true;
  if (s.includes("infini")) return true;
  if (s.length < 4 || s.length > 9) return false;
  const a = target;
  const b = s;
  const rows = a.length + 1;
  const cols = b.length + 1;
  const dp = Array.from({ length: rows }, () => Array.from({ length: cols }, () => 0));
  for (let i = 0; i < rows; i++) dp[i][0] = i;
  for (let j = 0; j < cols; j++) dp[0][j] = j;
  for (let i = 1; i < rows; i++) {
    for (let j = 1; j < cols; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost);
    }
  }
  return dp[a.length][b.length] <= 2;
}

/** Interprète le texte : entier > 0 → limité, sinon illimité (affiche ∞). */
function parseToursRestantsFromInput() {
  const raw = toursRestantsInput.value;
  if (textMeansInfinity(raw)) {
    gainForm.tours_restants = null;
    syncToursRestantsInputFromForm();
    return;
  }
  const t = raw.trim();
  const n = Number(t);
  if (Number.isInteger(n) && n > 0) {
    gainForm.tours_restants = n;
    toursRestantsInput.value = String(n);
    return;
  }
  gainForm.tours_restants = null;
  syncToursRestantsInputFromForm();
}

function onToursRestantsBlur() {
  parseToursRestantsFromInput();
}

function setToursRestantsRapide(n) {
  gainForm.tours_restants = n;
  toursRestantsInput.value = String(n);
}

function setToursRestantsIllimite() {
  gainForm.tours_restants = null;
  toursRestantsInput.value = "∞";
}

function resetGainForm() {
  gainForm.ressource_id = null;
  gainForm.quantite_par_tour = 1;
  gainForm.balise = "autre";
  gainForm.mode_production = "fixe";
  gainForm.actif = true;
  gainForm.tours_restants = null;
  gainForm.delai_tours = 0;
  syncToursRestantsInputFromForm();
}

function ouvrirCreation(ressourceId = null, nom = "") {
  resetGainForm();
  if (ressourceId) {
    gainForm.ressource_id = ressourceId;
  }
  gainFormModal.value = {
    mode: "create",
    gain: null,
    nomHint: nom,
  };
}

watch(gainFormModal, async (m) => {
  if (m) {
    toursRestantsAideOuverte.value = false;
    pourcentageAideOuverte.value = false;
    await nextTick();
    gainQteInputRef.value?.select?.();
  }
});

watch(
  () => gainForm.mode_production,
  (mode) => {
    if (mode !== "pourcentage") pourcentageAideOuverte.value = false;
  },
);

function ouvrirCreationVide() {
  ouvrirCreation();
}

function ouvrirEditionGain(g) {
  resetGainForm();
  gainForm.ressource_id = g.ressource_id;
  gainForm.quantite_par_tour = g.quantite_par_tour;
  gainForm.balise = g.balise || "autre";
  gainForm.mode_production = g.mode_production || "fixe";
  gainForm.actif = g.actif;
  gainForm.tours_restants = g.definitif ? null : g.tours_restants != null ? Number(g.tours_restants) : null;
  gainForm.delai_tours = g.delai_tours ?? 0;
  syncToursRestantsInputFromForm();
  gainFormModal.value = {
    mode: "edit",
    gain: g,
    nomHint: g.ressource?.nom ?? "",
  };
}

async function sauvegarderGainForm(etAjouterAutre = false) {
  const uidParam =
    isMj.value && mjRaw.mjVueChoix.value ? `?uid=${encodeURIComponent(String(mjRaw.mjVueChoix.value))}` : "";
  const m = gainFormModal.value;
  if (!m) return;
  if (m.mode === "create" && !gainForm.ressource_id) {
    erreur.value = "Choisissez une ressource.";
    return;
  }
  parseToursRestantsFromInput();
  const illimite = gainForm.tours_restants == null;
  try {
    if (m.mode === "create") {
      await post(`/api/gains-passifs${uidParam}`, {
        ressource_id: Number(gainForm.ressource_id),
        quantite_par_tour: Number(gainForm.quantite_par_tour),
        balise: gainForm.balise,
        mode_production: gainForm.mode_production,
        actif: gainForm.actif,
        definitif: illimite,
        tours_restants: illimite ? undefined : Number(gainForm.tours_restants),
        delai_tours: Number(gainForm.delai_tours),
      });
    } else {
      await put(`/api/gains-passifs/${m.gain.id}${uidParam}`, {
        quantite_par_tour: Number(gainForm.quantite_par_tour),
        balise: gainForm.balise,
        mode_production: gainForm.mode_production,
        actif: gainForm.actif,
        definitif: illimite,
        tours_restants: illimite ? null : Number(gainForm.tours_restants),
        delai_tours: Number(gainForm.delai_tours),
      });
    }
    await charger();
    // Navigation vers la fiche ressource uniquement après « Enregistrer » (pas « & ajouter une autre »).
    if (m.mode === "create" && !etAjouterAutre) {
      const rid = Number(gainForm.ressource_id);
      if (!Number.isNaN(rid)) {
        const filtre = ressourceIdFiltre.value;
        if (filtre == null || Number(filtre) !== rid) {
          await router.replace({
            path: "/productions",
            query: buildProductionsQuery({ ressource: rid }),
          });
        }
      }
    }
    if (etAjouterAutre && m.mode === "create") {
      const rid = gainForm.ressource_id;
      const nom =
        ressourcesListe.value.find((x) => x.id === rid)?.nom ?? m.nomHint ?? "";
      resetGainForm();
      gainForm.ressource_id = rid;
      gainForm.quantite_par_tour = 1;
      gainFormModal.value = {
        mode: "create",
        gain: null,
        nomHint: nom,
      };
    } else {
      gainFormModal.value = null;
    }
  } catch (e) {
    erreur.value = e.message;
  }
}

async function supprimerGain(g) {
  if (!confirm(`Supprimer cette production pour « ${g.ressource?.nom ?? "?" } » ?`)) return;
  const uidParam =
    isMj.value && mjRaw.mjVueChoix.value ? `?uid=${encodeURIComponent(String(mjRaw.mjVueChoix.value))}` : "";
  try {
    await del(`/api/gains-passifs/${g.id}${uidParam}`);
    await charger();
  } catch (e) {
    erreur.value = e.message;
  }
}

const colonnes = [
  ["nom", "Ressource"],
  ["balise", "Justification"],
  ["qte", "Effet"],
  ["duree", "Durée"],
  ["actif", "Actif"],
];

const nomRessourceForm = computed(() => {
  const id = gainForm.ressource_id;
  if (id == null) return "";
  const r = ressourcesListe.value.find((x) => Number(x.id) === Number(id));
  return r?.nom ?? `Ressource #${id}`;
});
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">Mes productions</h2>
        <p v-if="!ressourceIdFiltre" class="page-subtitle">
          Gains et pertes passifs par <strong>tour</strong> (mercredi & samedi 00h00). Vous pouvez définir
          <strong>plusieurs règles distinctes</strong> pour la même ressource (ex. +10 et −2 par tour).
        </p>
        <p v-else class="page-subtitle page-subtitle-filtre">
          <span class="page-subtitle-filtre-text">
            Vue actuelle : <strong class="page-ressource-courante">{{ nomRessourceFiltre }}</strong>
            — une seule ressource à la fois.
          </span>
          <router-link class="button secondary small productions-back-all" :to="{ path: '/productions', query: productionsQueryAll }">
            ← Toutes les productions
          </router-link>
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
        <button type="button" class="button" @click="ouvrirCreationSelonContexte">
          + Nouvelle production
        </button>
      </div>
    </div>

    <p v-if="erreur" class="error">{{ erreur }}</p>

    <div v-if="productionsParRessource.length > 0" class="productions-header">
      <div class="productions-header-title">Aperçu</div>
      <div class="productions-header-list">
        <button
          v-for="p in productionsParRessource"
          :key="p.ressource_id"
          type="button"
          class="productions-header-item"
          :class="{ active: Number(ressourceIdFiltre) === Number(p.ressource_id) }"
          @click="ouvrirDetailRessource(p.ressource_id)"
        >
          <span class="productions-header-nom">{{ p.ressource?.nom ?? "—" }}</span>
          <span class="productions-header-count">{{ p.gains.length }}</span>
        </button>
      </div>
    </div>

    <div v-if="ressourceIdFiltre" class="banner-salon banner-vue-ressource">
      <div class="banner-vue-ressource-title">Production — {{ nomRessourceFiltre }}</div>
    </div>

    <ProductionChronologieChart
      v-if="ressourceIdFiltre && chronologie"
      :passe="chronologie.passe"
      :futur="chronologie.futur"
      :futur-breakdown="chronologie.futur_breakdown || []"
      :ressource-nom="nomRessourceFiltre"
    />

    <!-- Vue d'ensemble : tableau par ressource -->
    <div v-if="!ressourceIdFiltre">
      <div v-if="productionsParRessource.length === 0" class="productions-empty">
        Aucune production passive pour l’instant. Cliquez sur « Nouvelle production » pour choisir une ressource
        et ajouter une ou plusieurs règles.
      </div>

      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Ressource</th>
              <th>Règles</th>
              <th>Détail (menu)</th>
              <th class="actions"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in productionsParRessource" :key="p.ressource_id">
              <td class="nom">{{ p.ressource?.nom ?? "—" }}</td>
              <td>{{ p.gains.length }}</td>
              <td>
                <details>
                  <summary class="details-summary">Détails</summary>
                  <div class="productions-dropdown">
                    <div
                      v-for="g in p.gains"
                      :key="g.id"
                      class="prod-dropdown-row"
                    >
                      <span :class="['tag-balise', 'tag-balise-' + (g.balise || 'autre')]">
                        {{ libelleBalise(g.balise || 'autre') }}
                      </span>
                      <span class="prix effet-cell">{{ formatEffetProduction(g) }}</span>
                      <span v-if="g.definitif" class="tag tag-durable">Sans limite</span>
                      <span v-else class="tag tag-temp">{{ g.tours_restants }} tour(s) restant(s)</span>
                      <span v-if="(g.delai_tours ?? 0) > 0" class="muted">
                        Démarre dans {{ g.delai_tours }} tour(s)
                      </span>
                      <span class="muted">{{ g.actif ? "Actif" : "Inactif" }}</span>
                    </div>
                  </div>
                </details>
              </td>
              <td class="actions">
                <button
                  type="button"
                  class="button secondary table-row-action"
                  @click="ouvrirDetailRessource(p.ressource_id)"
                >
                  Ouvrir le graphe
                </button>
                <button
                  type="button"
                  class="button secondary table-row-action"
                  @click="ouvrirAjoutProductionPourRessource(p.ressource_id, p.ressource?.nom ?? '')"
                >
                  Ajouter
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Vue détaillée : une ressource -->
    <div v-else>
      <div v-if="gainsFiltres.length === 0" class="productions-empty">
        Aucune règle de production pour « {{ nomRessourceFiltre }} ». Utilisez « Nouvelle production » en choisissant
        cette ressource, ou revenez à
        <router-link class="inline-link" :to="{ path: '/productions', query: productionsQueryAll }">toutes les productions</router-link>.
      </div>

      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th
                v-for="[k, lab] in colonnes"
                :key="k"
                class="th-sort"
                @click="toggleSort(k)"
              >
                {{ lab }}{{ sortLabel(k) }}
              </th>
              <th class="actions"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="g in gainsTries" :key="g.id">
              <td class="nom">{{ g.ressource?.nom ?? "—" }}</td>
              <td>
                <span :class="['tag-balise', 'tag-balise-' + (g.balise || 'autre')]">
                  {{ libelleBalise(g.balise || 'autre') }}
                </span>
              </td>
              <td class="prix effet-cell">{{ formatEffetProduction(g) }}</td>
              <td>
                <span v-if="g.definitif" class="tag tag-durable">Sans limite</span>
                <span v-else class="tag tag-temp">{{ g.tours_restants }} tour(s) restant(s)</span>
                <span v-if="(g.delai_tours ?? 0) > 0" class="muted">
                  Démarre dans {{ g.delai_tours }} tour(s)
                </span>
              </td>
              <td>{{ g.actif ? "Oui" : "Non" }}</td>
              <td class="actions">
                <button
                  type="button"
                  class="button secondary table-row-action"
                  @click="ouvrirEditionGain(g)"
                >
                  Modifier
                </button>
                <button
                  type="button"
                  class="button secondary table-row-action danger"
                  @click="supprimerGain(g)"
                >
                  Supprimer
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="gainFormModal" class="modal-overlay modal-overlay-gain" @click.self="gainFormModal = null">
      <div class="modal modal-sm modal-gain-form">
        <h3 class="modal-title">
          {{
            gainFormModal.mode === "create" ? "Nouvelle production" : "Modifier la production"
          }}
        </h3>
        <div v-if="gainForm.ressource_id" class="modal-resource-banner">
          <span class="modal-resource-banner-label">Ressource</span>
          <span class="modal-resource-banner-nom">{{ nomRessourceForm }}</span>
        </div>
        <p v-else-if="gainFormModal.mode === 'create' && !ressourceVerrouilleeEnCreation" class="modal-resource-missing">
          Choisissez une ressource ci-dessous pour cette règle.
        </p>
        <label
          v-if="gainFormModal.mode === 'create' && !ressourceVerrouilleeEnCreation"
          class="form-label"
        >
          Ressource
          <select v-model.number="gainForm.ressource_id" class="select full-width">
            <option :value="null" disabled>Choisir une ressource…</option>
            <option v-for="r in ressourcesListe" :key="r.id" :value="r.id">
              {{ r.nom }} ({{ r.type }})
            </option>
          </select>
        </label>
        <label class="form-label">
          Justification (balise)
          <select v-model="gainForm.balise" class="select full-width">
            <option v-if="balisesFormulaireProduction.length === 0" value="autre">Chargement…</option>
            <option v-for="b in balisesFormulaireProduction" :key="b.id" :value="b.id">
              {{ b.label }}
            </option>
          </select>
        </label>
        <div class="form-label">Mode</div>
        <div class="mode-row">
          <label class="radio-label">
            <input v-model="gainForm.mode_production" type="radio" value="fixe" />
            unités fixes (par tour)
          </label>
          <div class="mode-pct-line">
            <label class="radio-label mode-pct-label">
              <input v-model="gainForm.mode_production" type="radio" value="pourcentage" />
              <span>% de la production du tour (après les règles précédentes)</span>
            </label>
            <button
              type="button"
              class="tours-help-btn mode-pct-help"
              :aria-expanded="pourcentageAideOuverte"
              aria-controls="hint-mode-pourcentage"
              title="Aide : mode pourcentage"
              @click="pourcentageAideOuverte = !pourcentageAideOuverte"
            >
              ?
            </button>
          </div>
        </div>
        <div
          v-show="pourcentageAideOuverte"
          id="hint-mode-pourcentage"
          class="tours-player-info mode-pct-hint"
          role="region"
          aria-label="Aide sur le mode pourcentage"
        >
          <div class="mode-pct-hint-body">
            <p class="mode-pct-hint-title">Fonctionnement</p>
            <p class="mode-pct-hint-text">
              En mode <strong>pourcentage</strong>, la valeur s’applique à la
              <strong>production cumulée du tour</strong> (après les règles précédentes, par ordre des identifiants),
              pas au stock total.
            </p>
            <p class="mode-pct-hint-title">Arrondi et tirage</p>
            <p class="mode-pct-hint-text">
              Si le résultat n’est pas entier, il est <strong>tronqué vers le bas</strong> (partie entière) ; la
              <strong>partie décimale</strong> (ex. 0,3 pour 1,3) correspond à la probabilité d’ajouter
              <strong>+1</strong> lors du calcul de la production du tour.
            </p>
            <p class="mode-pct-hint-title">Exemples</p>
            <ul class="mode-pct-hint-list">
              <li>
                <strong>1,3</strong> → base <strong>1</strong> ; environ <strong>30&nbsp;%</strong> de chance que la
                ligne produise <strong>2</strong> pour ce tour.
              </li>
              <li>
                <strong>47,8</strong> → base <strong>47</strong> ; environ <strong>80&nbsp;%</strong> de chance
                d’obtenir <strong>48</strong>.
              </li>
            </ul>
            <p class="mode-pct-hint-text mode-pct-hint-foot">
              L’éventuel <strong>+1</strong> est comptabilisé avec la balise
              <strong>«&nbsp;Récolte fructueuse&nbsp;»</strong>.
            </p>
          </div>
        </div>
        <label class="form-label">
          {{
            gainForm.mode_production === "pourcentage"
              ? "Pourcentage (−100 = tout perdre, +10 = +10 %)"
              : "Quantité (unités par tour)"
          }}
          <input
            ref="gainQteInputRef"
            v-model.number="gainForm.quantite_par_tour"
            type="number"
            class="input"
            @focus="selectAllInputText"
            @click="selectAllInputText"
          />
        </label>
        <label class="form-label">
          Démarre dans
          <input
            v-model.number="gainForm.delai_tours"
            type="number"
            min="0"
            class="input"
            @focus="selectAllInputText"
            @click="selectAllInputText"
          />
          tour(s)
        </label>
        <div class="delay-quick-actions">
          <button
            type="button"
            class="button secondary small"
            @click="gainForm.delai_tours = 0"
          >
            Immédiat
          </button>
          <button
            type="button"
            class="button secondary small"
            @click="gainForm.delai_tours = 1"
          >
            1 tour
          </button>
          <button
            type="button"
            class="button secondary small"
            @click="gainForm.delai_tours = 2"
          >
            2 tours
          </button>
        </div>
        <label class="form-label">
          Nombre de tours restants
          <div class="tours-input-row">
            <input
              v-model="toursRestantsInput"
              type="text"
              inputmode="numeric"
              class="input input-tours-restants"
              autocomplete="off"
              spellcheck="false"
              :aria-describedby="toursRestantsAideOuverte ? 'hint-tours-restants' : undefined"
              title="Illimité : vide, ∞, infini, illimité… — Limité : un entier positif (ex. 6)"
              @blur="onToursRestantsBlur"
              @focus="selectAllInputText"
              @click="selectAllInputText"
            />
            <button
              type="button"
              class="tours-help-btn"
              :aria-expanded="toursRestantsAideOuverte"
              aria-controls="hint-tours-restants"
              title="Aide : durée illimitée ou limitée"
              @click="toursRestantsAideOuverte = !toursRestantsAideOuverte"
            >
              ?
            </button>
          </div>
          <div
            v-show="toursRestantsAideOuverte"
            id="hint-tours-restants"
            class="tours-player-info"
            role="region"
            aria-label="Aide sur le nombre de tours restants"
          >
            <div class="tours-player-info-title">Comment indiquer une durée ?</div>
            <ul class="tours-player-info-list">
              <li>
                <strong>Durée illimitée</strong> (défaut) : laissez le champ vide après modification, le symbole
                <strong>∞</strong> réapparaît, ou utilisez le bouton « Sans limite ». Vous pouvez aussi écrire
                <em>infini</em>, <em>illimité</em>, <em>sans limite</em>… (pas besoin du clavier ∞).
              </li>
              <li>
                <strong>Durée limitée</strong> : saisissez un <strong>nombre entier strictement positif</strong>
                (ex. <strong>6</strong> pour 6 tours). Autre texte ou valeur invalide → retour à l’illimité.
              </li>
            </ul>
          </div>
        </label>
        <div class="temp-quick-actions">
          <button type="button" class="button secondary small" @click="setToursRestantsIllimite">
            Sans limite (∞)
          </button>
          <button type="button" class="button secondary small" @click="setToursRestantsRapide(1)">
            1 tour
          </button>
          <button type="button" class="button secondary small" @click="setToursRestantsRapide(2)">
            2 tours
          </button>
        </div>
        <label class="form-label checkbox-label">
          <input v-model="gainForm.actif" type="checkbox" />
          Actif
        </label>
        <div class="modal-footer modal-footer-stack">
          <button type="button" class="button secondary" @click="gainFormModal = null">Annuler</button>
          <template v-if="gainFormModal.mode === 'create'">
            <button type="button" class="button secondary" @click="sauvegarderGainForm(true)">
              Enregistrer &amp; ajouter une autre
            </button>
          </template>
          <button type="button" class="button" @click="sauvegarderGainForm(false)">Enregistrer</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.full-width {
  width: 100%;
  margin-top: 6px;
}
.productions-empty {
  padding: 24px;
  color: #94a3b8;
  font-size: 15px;
  border: 1px dashed #334155;
  border-radius: 10px;
  margin-bottom: 16px;
}
.banner-salon {
  margin-bottom: 16px;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.5;
  color: #cbd5e1;
  background: #1e293b;
  border: 1px solid #475569;
  border-radius: 10px;
}
.inline-link {
  margin-left: 6px;
  color: #93c5fd;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.page-subtitle-filtre {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
}
.page-subtitle-filtre-text {
  flex: 1;
  min-width: 200px;
}
.page-ressource-courante {
  color: #7dd3fc;
}
.productions-back-all {
  flex-shrink: 0;
  text-decoration: none;
}
.banner-vue-ressource {
  border-color: #0ea5e9;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.12), rgba(15, 23, 42, 0.95));
  box-shadow: 0 0 0 1px rgba(14, 165, 233, 0.25);
}
.banner-vue-ressource-title {
  font-size: 1.05rem;
  font-weight: 800;
  color: #e0f2fe;
  margin: 0;
  letter-spacing: 0.02em;
}
.modal-overlay-gain {
  z-index: 4000;
}
.modal-gain-form {
  max-height: min(92vh, 880px);
  overflow-y: auto;
}
.modal-resource-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px 12px;
  margin: 0 0 12px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(56, 189, 248, 0.45);
  background: rgba(56, 189, 248, 0.1);
}
.modal-resource-banner-label {
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #7dd3fc;
}
.modal-resource-banner-nom {
  font-size: 1.1rem;
  font-weight: 800;
  color: #f0f9ff;
}
.modal-resource-missing {
  margin: 0 0 10px;
  padding: 8px 10px;
  font-size: 13px;
  color: #fcd34d;
  background: rgba(180, 83, 9, 0.15);
  border: 1px solid rgba(251, 191, 36, 0.35);
  border-radius: 8px;
}
.tours-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}
.tours-input-row .input-tours-restants {
  flex: 1;
  min-width: 0;
}
.tours-help-btn {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1px solid #475569;
  background: #1e293b;
  color: #94a3b8;
  font-weight: 700;
  font-size: 15px;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.tours-help-btn:hover,
.tours-help-btn[aria-expanded="true"] {
  border-color: #38bdf8;
  color: #e2e8f0;
  background: #0f172a;
}
.tours-player-info {
  margin: 10px 0 8px;
  padding: 10px 12px 10px 14px;
  font-size: 13px;
  line-height: 1.5;
  color: #cbd5e1;
  background: #0f172a;
  border: 1px solid #334155;
  border-left: 4px solid #38bdf8;
  border-radius: 8px;
  max-width: 100%;
}
.tours-player-info-title {
  font-weight: 700;
  font-size: 13px;
  color: #e2e8f0;
  margin-bottom: 8px;
}
.tours-player-info-list {
  margin: 0;
  padding-left: 1.15em;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.tours-player-info-list li {
  margin: 0;
}
.input-tours-restants {
  font-size: 1.15rem;
  font-variant-numeric: tabular-nums;
}
.mode-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}
.mode-pct-line {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
}
.mode-pct-label {
  flex: 1;
  min-width: 0;
}
.mode-pct-help {
  flex-shrink: 0;
  margin-top: 2px;
}
.mode-pct-hint {
  margin-top: -4px;
  margin-bottom: 12px;
}
.mode-pct-hint-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.mode-pct-hint-title {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #94a3b8;
}
.mode-pct-hint-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: #cbd5e1;
}
.mode-pct-hint-foot {
  padding-top: 4px;
  border-top: 1px solid #334155;
  color: #e2e8f0;
}
.mode-pct-hint-list {
  margin: 0;
  padding-left: 1.2em;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  line-height: 1.5;
  color: #cbd5e1;
}
.mode-pct-hint-list li {
  margin: 0;
}
.radio-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #cbd5e1;
  cursor: pointer;
}
.tag-balise {
  display: inline-block;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  font-weight: 600;
}
.tag-balise-science {
  background: #1e3a5f;
  color: #93c5fd;
}
.tag-balise-politique {
  background: #422006;
  color: #fcd34d;
}
.tag-balise-evenement {
  background: #4c1d95;
  color: #e9d5ff;
}
.tag-balise-batiment {
  background: #0f766e;
  color: #b9f6f0;
}
.tag-balise-autre {
  background: #334155;
  color: #cbd5e1;
}
.tag-balise-recolte_fructueuse {
  background: #14532d;
  color: #bbf7d0;
}
.effet-cell {
  white-space: nowrap;
}

.productions-dropdown {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prod-dropdown-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.temp-quick-actions {
  display: flex;
  gap: 8px;
  margin-top: 6px;
}

.delay-quick-actions {
  display: flex;
  gap: 8px;
  margin-top: 6px;
}

/* Rendre le <summary> de <details> visuellement "bouton" */
details.details-summary {
  margin: 0;
}

.details-summary {
  cursor: pointer;
  user-select: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #334155;
  background: #0f172a;
  color: #cbd5e1;
  font-weight: 600;
}

.details-summary::-webkit-details-marker {
  display: none;
}

.details-summary::after {
  content: "▼";
  font-size: 11px;
  color: #94a3b8;
}

details[open] .details-summary::after {
  content: "▲";
}

.productions-header {
  margin: 10px 0 14px;
  padding: 12px 14px;
  background: rgba(15, 23, 42, 0.25);
  border: 1px solid #334155;
  border-radius: 12px;
}

.productions-header-title {
  font-size: 12px;
  font-weight: 800;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 10px;
}

.productions-header-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.productions-header-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid rgba(51, 65, 85, 0.9);
  background: rgba(30, 41, 59, 0.4);
  color: #e2e8f0;
  cursor: pointer;
}

.productions-header-item:hover {
  border-color: rgba(148, 163, 184, 0.35);
  background: rgba(30, 41, 59, 0.7);
}

.productions-header-item.active {
  border-color: #38bdf8;
  background: rgba(56, 189, 248, 0.16);
  box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25);
  color: #f0f9ff;
}

.productions-header-nom {
  font-weight: 700;
}

.productions-header-count {
  min-width: 20px;
  height: 20px;
  display: inline-grid;
  place-items: center;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.16);
  color: #cbd5e1;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
</style>
