<script setup>
import { computed, nextTick, reactive, ref, watch } from "vue";
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
const mj = useMjView({
  authState: props.authState,
  utilisateursListeRef: utilisateurs,
  isMjRef: isMj,
  currentUserIdStrRef: currentUserIdStr,
  allowGlobal: false,
  storageKey: "mj_view_choice_uid",
});
const gainsPassifs = ref([]);
const ressourcesListe = ref([]);
const balisesDisponibles = ref([]);
const chronologie = ref(null);
const erreur = ref("");
const gainQteInputRef = ref(null);

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
    isMj.value && mj.mjVueChoix.value
      ? `?uid=${encodeURIComponent(String(mj.mjVueChoix.value))}`
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

async function chargerChronologie() {
  const rid = ressourceIdFiltre.value;
  if (!rid) {
    chronologie.value = null;
    return;
  }
  const uidParam =
    isMj.value && mj.mjVueChoix.value
      ? `&uid=${encodeURIComponent(String(mj.mjVueChoix.value))}`
      : "";
  try {
    chronologie.value = await get(`/api/gains-passifs/chronologie?ressource_id=${rid}${uidParam}`);
  } catch (e) {
    erreur.value = e.message;
    chronologie.value = null;
  }
}

watch(mj.mjVueChoix, charger);
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
    mj.mjVueSetChoix(fromRoute);
    return;
  }
  const cur = String(mj.mjVueChoix.value ?? "");
  if (!cur || !ids.has(cur)) {
    const me = props.authState.user?.id;
    if (me != null && ids.has(String(me))) {
      mj.mjVueSetChoix(String(me));
    } else {
      mj.mjVueSetChoix(String(list[0].id));
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
      mj.mjVueSetChoix(fromRoute);
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
  const q = { ressource: String(rid) };
  if (isMj.value && mj.mjVueChoix.value) {
    q.uid = String(mj.mjVueChoix.value);
  }
  router.push({ path: "/productions", query: q });
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
  definitif: true,
  tours_restants: 6,
  delai_tours: 0,
});

function resetGainForm() {
  gainForm.ressource_id = null;
  gainForm.quantite_par_tour = 1;
  gainForm.balise = "autre";
  gainForm.mode_production = "fixe";
  gainForm.actif = true;
  gainForm.definitif = true;
  gainForm.tours_restants = 6;
  gainForm.delai_tours = 0;
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
    await nextTick();
    gainQteInputRef.value?.select?.();
  }
});

function selectGainQuantite() {
  // Sélectionne toute la valeur quand on focus le champ.
  gainQteInputRef.value?.select?.();
}

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
  gainForm.definitif = g.definitif;
  gainForm.tours_restants = g.tours_restants ?? 6;
  gainForm.delai_tours = g.delai_tours ?? 0;
  gainFormModal.value = {
    mode: "edit",
    gain: g,
    nomHint: g.ressource?.nom ?? "",
  };
}

async function sauvegarderGainForm(etAjouterAutre = false) {
  const uidParam =
    isMj.value && mj.mjVueChoix.value ? `?uid=${encodeURIComponent(String(mj.mjVueChoix.value))}` : "";
  const m = gainFormModal.value;
  if (!m) return;
  if (m.mode === "create" && !gainForm.ressource_id) {
    erreur.value = "Choisissez une ressource.";
    return;
  }
  try {
    if (m.mode === "create") {
      await post(`/api/gains-passifs${uidParam}`, {
        ressource_id: Number(gainForm.ressource_id),
        quantite_par_tour: Number(gainForm.quantite_par_tour),
        balise: gainForm.balise,
        mode_production: gainForm.mode_production,
        actif: gainForm.actif,
        definitif: gainForm.definitif,
        tours_restants: gainForm.definitif ? undefined : Number(gainForm.tours_restants),
        delai_tours: Number(gainForm.delai_tours),
      });
    } else {
      await put(`/api/gains-passifs/${m.gain.id}${uidParam}`, {
        quantite_par_tour: Number(gainForm.quantite_par_tour),
        balise: gainForm.balise,
        mode_production: gainForm.mode_production,
        actif: gainForm.actif,
        definitif: gainForm.definitif,
        tours_restants: gainForm.definitif ? null : Number(gainForm.tours_restants),
        delai_tours: Number(gainForm.delai_tours),
      });
    }
    await charger();
    if (m.mode === "create") {
      const rid = Number(gainForm.ressource_id);
      if (!Number.isNaN(rid)) {
        const filtre = ressourceIdFiltre.value;
        if (filtre == null || Number(filtre) !== rid) {
          await router.replace({
            path: "/productions",
            query: { ressource: String(rid) },
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
    isMj.value && mj.mjVueChoix.value ? `?uid=${encodeURIComponent(String(mj.mjVueChoix.value))}` : "";
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
        <p v-else class="page-subtitle">
          Vue filtrée sur une seule ressource : les règles ci‑dessous concernent uniquement
          <strong>{{ nomRessourceFiltre }}</strong>.
          <router-link class="inline-link" :to="{ path: '/productions', query: {} }">
            Afficher toutes les productions
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

    <div v-if="ressourceIdFiltre" class="banner-salon">
      <strong>Une ressource à la fois.</strong>
      Sur Discord, un salon correspond à une ressource : ne mélangez pas les bilans de production sur le même fil.
      Ici vous ne voyez que <strong>{{ nomRessourceFiltre }}</strong>.
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
                      <span v-if="g.definitif" class="tag tag-durable">Définitif</span>
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
        <router-link class="inline-link" :to="{ path: '/productions', query: {} }">toutes les productions</router-link>.
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
                <span v-if="g.definitif" class="tag tag-durable">Définitif</span>
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
    <div v-if="gainFormModal" class="modal-overlay" @click.self="gainFormModal = null">
      <div class="modal modal-sm">
        <h3 class="modal-title">
          {{
            gainFormModal.mode === "create" ? "Nouvelle production" : "Modifier la production"
          }}
          <span v-if="gainFormModal.nomHint"> — {{ gainFormModal.nomHint }}</span>
        </h3>
        <p class="modal-hint">
          Une ligne = une règle indépendante. En mode <strong>pourcentage</strong>, la valeur s’applique au stock
          <strong>avant cette ligne</strong> (plusieurs règles : ordre des identifiants).
        </p>
        <label
          v-if="gainFormModal.mode === 'create' && !gainForm.ressource_id"
          class="form-label"
        >
          Ressource
          <select v-model.number="gainForm.ressource_id" class="select full-width">
            <option :value="null" disabled>Choisir…</option>
            <option v-for="r in ressourcesListe" :key="r.id" :value="r.id">
              {{ r.nom }} ({{ r.type }})
            </option>
          </select>
        </label>
        <label class="form-label">
          Justification (balise)
          <select v-model="gainForm.balise" class="select full-width">
            <option v-if="balisesDisponibles.length === 0" value="autre">Chargement…</option>
            <option v-for="b in balisesDisponibles" :key="b.id" :value="b.id">
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
          <label class="radio-label">
            <input v-model="gainForm.mode_production" type="radio" value="pourcentage" />
            % du stock actuel
          </label>
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
            @focus="selectGainQuantite"
          />
        </label>
        <label class="form-label checkbox-label">
          <input v-model="gainForm.definitif" type="checkbox" />
          Définitif (sans limite de tours)
        </label>
        <label class="form-label">
          Démarre dans
          <input
            v-model.number="gainForm.delai_tours"
            type="number"
            min="0"
            class="input"
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
        <label v-if="!gainForm.definitif" class="form-label">
          Nombre de tours restants
          <input v-model.number="gainForm.tours_restants" type="number" min="1" class="input" />
        </label>
        <div v-if="!gainForm.definitif" class="temp-quick-actions">
          <button type="button" class="button secondary small" @click="gainForm.tours_restants = 1">
            1 tour
          </button>
          <button type="button" class="button secondary small" @click="gainForm.tours_restants = 2">
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
.mode-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
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
  border-color: rgba(147, 197, 253, 0.35);
  background: rgba(147, 197, 253, 0.08);
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
