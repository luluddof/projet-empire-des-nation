<script setup>
import { computed, reactive, ref, watch } from "vue";
import {
  FLORINS_NOM,
  formatFlorin,
  formatFlorinExact,
  useApi,
} from "../composables/useApi.js";

const props = defineProps({
  authState: { type: Object, required: true },
});

const { get, post, put, del } = useApi();
const isMj = computed(() => props.authState.user?.is_mj);

const ressources = ref([]);
const categories = ref([]);
const erreur = ref("");
const recherche = ref("");
const filtreCategorieId = ref("");

const sort = reactive({ key: "nom", dir: "asc" });

function formatPct(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "100 %";
  if (Number.isInteger(n)) return `${n} %`;
  return `${n} %`;
}

async function chargerCategories() {
  try {
    categories.value = await get("/api/categories");
  } catch (e) {
    erreur.value = e.message;
  }
}

async function chargerRessources() {
  try {
    const q = isMj.value ? "?global=1" : "";
    ressources.value = await get(`/api/ressources${q}`);
  } catch (e) {
    erreur.value = e.message;
  }
}

const utilisateursListe = ref([]);

async function chargerUtilisateurs() {
  if (!isMj.value) return;
  try {
    utilisateursListe.value = await get("/api/utilisateurs");
  } catch (e) {
    erreur.value = e.message;
  }
}

function charger() {
  chargerCategories();
  chargerRessources();
  chargerUtilisateurs();
}
charger();

watch(isMj, () => {
  chargerRessources();
  chargerUtilisateurs();
});

function previewPrix(prixBase, facteur) {
  const m = Number(facteur) || 1;
  const pb = Number(prixBase) || 0;
  const pm = Math.round(pb * m);
  return {
    prix_modifie: pm,
    prix_achat: Math.round(pm * 1.2),
    prix_lointain: Math.round(pm * 2.5),
  };
}

const ressourcesFiltrees = computed(() => {
  return ressources.value.filter((r) => {
    const okNom = r.nom.toLowerCase().includes(recherche.value.toLowerCase());
    const okCat =
      !filtreCategorieId.value ||
      (r.categorie_ids || []).includes(Number(filtreCategorieId.value));
    return okNom && okCat;
  });
});

function categorieSortKey(r) {
  const cats = r.categories || [];
  return cats.map((c) => c.nom).sort().join(", ") || "zzz";
}

function sortedList(list) {
  const key = sort.key;
  const dir = sort.dir === "asc" ? 1 : -1;
  return [...list].sort((a, b) => {
    let va;
    let vb;
    switch (key) {
      case "nom":
        va = a.nom.toLowerCase();
        vb = b.nom.toLowerCase();
        break;
      case "type":
        va = a.type;
        vb = b.type;
        break;
      case "prix_base":
        va = a.prix_base;
        vb = b.prix_base;
        break;
      case "modificateur_pct":
        va = a.modificateur_pct;
        vb = b.modificateur_pct;
        break;
      case "facteur_prix":
        va = a.facteur_prix;
        vb = b.facteur_prix;
        break;
      case "prix_modifie":
        va = a.prix_modifie;
        vb = b.prix_modifie;
        break;
      case "prix_achat":
        va = a.prix_achat;
        vb = b.prix_achat;
        break;
      case "prix_lointain":
        va = a.prix_lointain;
        vb = b.prix_lointain;
        break;
      case "categories":
        va = categorieSortKey(a);
        vb = categorieSortKey(b);
        break;
      default:
        va = a.nom;
        vb = b.nom;
    }
    if (typeof va === "string") {
      return va < vb ? -dir : va > vb ? dir : 0;
    }
    return va === vb ? 0 : va < vb ? -dir : dir;
  });
}

const listePremiere = computed(() =>
  sortedList(ressourcesFiltrees.value.filter((r) => r.type === "Première"))
);
const listeManufacture = computed(() =>
  sortedList(ressourcesFiltrees.value.filter((r) => r.type === "Manufacturé"))
);

/** Sélection MJ pour ajustement groupé du % marché (hors monnaie Florins). */
const selectedIds = ref([]);
const bulkModal = ref(false);
const bulkPct = ref(100);
const bulkCible = ref("tous");
const bulkUserIds = ref([]);
const bulkErr = ref("");
const bulkLoading = ref(false);

function idSelectionne(id) {
  return selectedIds.value.includes(id);
}

function toggleSelection(id) {
  if (idSelectionne(id)) {
    selectedIds.value = selectedIds.value.filter((x) => x !== id);
  } else {
    selectedIds.value = [...selectedIds.value, id];
  }
}

function selectionnerToutListe(liste) {
  const ids = liste.filter((r) => r.nom !== FLORINS_NOM).map((r) => r.id);
  const set = new Set([...selectedIds.value, ...ids]);
  selectedIds.value = [...set];
}

function selectionnerVueFiltree() {
  const ids = ressourcesFiltrees.value.filter((r) => r.nom !== FLORINS_NOM).map((r) => r.id);
  selectedIds.value = [...new Set(ids)];
}

function viderSelection() {
  selectedIds.value = [];
}

function toggleBulkUser(uid) {
  const i = bulkUserIds.value.indexOf(uid);
  if (i >= 0) bulkUserIds.value.splice(i, 1);
  else bulkUserIds.value.push(uid);
}

function bulkUserSelected(uid) {
  return bulkUserIds.value.includes(uid);
}

async function appliquerBulkPrix() {
  bulkErr.value = "";
  if (selectedIds.value.length === 0) {
    bulkErr.value = "Sélectionnez au moins une ressource.";
    return;
  }
  if (bulkCible.value === "joueurs" && bulkUserIds.value.length === 0) {
    bulkErr.value = "Sélectionnez au moins un joueur.";
    return;
  }
  bulkLoading.value = true;
  try {
    await post("/api/ressources/bulk-prix-marche", {
      ids: selectedIds.value,
      modificateur_pct: Number(bulkPct.value),
      cible_modificateur: bulkCible.value,
      utilisateur_ids:
        bulkCible.value === "joueurs" ? [...bulkUserIds.value] : [],
    });
    bulkModal.value = false;
    await chargerRessources();
  } catch (e) {
    bulkErr.value = e.message;
  } finally {
    bulkLoading.value = false;
  }
}

function toggleSort(key) {
  if (sort.key === key) {
    sort.dir = sort.dir === "asc" ? "desc" : "asc";
  } else {
    sort.key = key;
    sort.dir = "asc";
  }
}

function sortLabel(key) {
  if (sort.key !== key) return "";
  return sort.dir === "asc" ? " ▲" : " ▼";
}

// --- Modal ressource ---
const modalVisible = ref(false);
const modeEdition = ref(false);
const erreurModal = ref("");
const resModMode = ref("set"); // 'set' | 'add' | 'remove' pour le % ressource
const resBaseModificateurPct = ref(100); // base courante (global) pour aperçu add/remove
const form = reactive({
  id: null,
  nom: "",
  type: "Première",
  prix_base: "",
  modificateur_pct: 100,
  categorie_ids: [],
  cible_modificateur: "tous",
  utilisateur_ids: [],
});

const previewFacteur = computed(() => {
  let pctRessource;
  if (!modeEdition.value || resModMode.value === "set") {
    pctRessource = Number(form.modificateur_pct) || 100;
  } else {
    const base = Number(resBaseModificateurPct.value) || 100;
    const delta = Number(form.modificateur_pct) || 0;
    pctRessource = resModMode.value === "add" ? base + delta : base - delta;
  }

  let f = pctRessource / 100;
  for (const id of form.categorie_ids) {
    const c = categories.value.find((x) => x.id === id);
    if (c) {
      f *= (Number(c.modificateur_pct) || 100) / 100;
    }
  }
  return f;
});

const preview = computed(() => previewPrix(form.prix_base, previewFacteur.value));

function ouvrirCreation() {
  Object.assign(form, {
    id: null,
    nom: "",
    type: "Première",
    prix_base: "",
    modificateur_pct: 100,
    categorie_ids: [],
    cible_modificateur: "tous",
    utilisateur_ids: [],
  });
  resModMode.value = "set";
  resBaseModificateurPct.value = 100;
  resPlayerSearch.value = "";
  erreurModal.value = "";
  modeEdition.value = false;
  modalVisible.value = true;
}

function ouvrirEdition(r) {
  Object.assign(form, {
    id: r.id,
    nom: r.nom,
    type: r.type,
    prix_base: r.prix_base,
    modificateur_pct: r.modificateur_pct,
    categorie_ids: [...(r.categorie_ids || [])],
    cible_modificateur: "tous",
    utilisateur_ids: [],
  });
  resModMode.value = "set";
  resBaseModificateurPct.value = Number(r.modificateur_pct) || 100;
  resPlayerSearch.value = "";
  erreurModal.value = "";
  modeEdition.value = true;
  modalVisible.value = true;
}

function toggleFormUser(uid) {
  const i = form.utilisateur_ids.indexOf(uid);
  if (i >= 0) form.utilisateur_ids.splice(i, 1);
  else form.utilisateur_ids.push(uid);
}

function formUserSelected(uid) {
  return form.utilisateur_ids.includes(uid);
}

function setCategorieChecked(catId, checked) {
  const i = form.categorie_ids.indexOf(catId);
  if (checked && i < 0) {
    form.categorie_ids.push(catId);
  }
  if (!checked && i >= 0) {
    form.categorie_ids.splice(i, 1);
  }
}

async function appliquerProduitCategories() {
  if (!form.id) return;
  erreurModal.value = "";
  try {
    const r = await post(`/api/ressources/${form.id}/appliquer-modificateurs-categories`, {});
    form.modificateur_pct = r.modificateur_pct;
    resModMode.value = "set";
    resBaseModificateurPct.value = 100;
  } catch (e) {
    erreurModal.value = e.message;
  }
}

async function sauvegarderRessource() {
  erreurModal.value = "";
  if (
    modeEdition.value &&
    form.cible_modificateur === "joueurs" &&
    form.utilisateur_ids.length === 0
  ) {
    erreurModal.value = "Sélectionnez au moins un joueur pour cette cible.";
    return;
  }
  const payload = {
    nom: form.nom,
    type: form.type,
    prix_base: Number(form.prix_base),
    modificateur_pct: Number(form.modificateur_pct),
    categorie_ids: [...form.categorie_ids],
  };
  if (modeEdition.value) {
    payload.cible_modificateur = form.cible_modificateur;
    payload.utilisateur_ids =
      form.cible_modificateur === "joueurs" ? [...form.utilisateur_ids] : [];
    payload.operation = resModMode.value;
  }
  try {
    if (modeEdition.value) {
      await put(`/api/ressources/${form.id}`, payload);
    } else {
      await post("/api/ressources", payload);
    }
    await chargerRessources();
    modalVisible.value = false;
  } catch (e) {
    erreurModal.value = e.message;
  }
}

async function supprimerRessource(r) {
  if (!confirm(`Supprimer "${r.nom}" ?`)) return;
  try {
    await del(`/api/ressources/${r.id}`);
    await chargerRessources();
  } catch (e) {
    erreur.value = e.message;
  }
}

// --- Panneau catégories (MJ) ---
const catModal = ref(false);
const catForm = reactive({ id: null, nom: "", modificateur_pct: 100 });
const catModMode = ref("set"); // 'set' | 'add' | 'remove'
const catBaseModificateurPct = ref(100); // valeur avant add/remove
const erreurCat = ref("");

// Modificateur de catégorie par joueur (surcharge)
const catPlayerModal = ref(false);
const catPlayerErreur = ref("");
const catPlayerModMode = ref("set"); // 'set' | 'add' | 'remove'
const catPlayerForm = reactive({
  categorie_id: null,
  utilisateur_ids: [],
  modificateur_pct: 100,
});
const catPlayerCategorieNom = computed(() => {
  const id = catPlayerForm.categorie_id;
  if (id == null) return "";
  return categories.value.find((x) => x.id === id)?.nom ?? "";
});

// Multi-sélection de joueurs (avec recherche).
// Règle UX demandée : en cas de recherche, les joueurs sélectionnés restent visibles et
// sont affichés à la fin de la liste filtrée.
const catPlayerSearch = ref("");
const catPlayerSearchNorm = computed(() => catPlayerSearch.value.trim().toLowerCase());
const catPlayerSelectedSet = computed(() =>
  new Set((catPlayerForm.utilisateur_ids || []).map(String)),
);
const currentUserIdStr = computed(() => String(props.authState.user?.id ?? ""));
const catPlayerSearchResults = computed(() => {
  const q = catPlayerSearchNorm.value;
  const all = utilisateursListe.value || [];
  if (!q) return all;
  return all.filter(
    (u) =>
      String(u.username || "").toLowerCase().includes(q) || String(u.id).includes(q),
  );
});
const catPlayerVisibleJoueurs = computed(() => {
  if (catForm.id == null) return [];
  const q = catPlayerSearchNorm.value;

  const selected = catPlayerSelectedSet.value;
  // On retire d'abord les sélectionnés des résultats pour les ré-afficher systématiquement à la fin.
  const listPourRecherche = q ? catPlayerSearchResults.value : utilisateursListe.value || [];
  const resultsSansSelection = listPourRecherche.filter((u) => !selected.has(String(u.id)));
  // Les sélectionnés doivent toujours être visibles, même s'ils ne matchent pas la recherche.
  const selectedExtras = (utilisateursListe.value || []).filter((u) => selected.has(String(u.id)));

  // Afficher le joueur courant en 1er (tout en gardant les sélectionnés en fin de bloc).
  const uid = currentUserIdStr.value;
  const currentFirst = (list) => {
    if (!uid) return list;
    const cur = list.find((u) => String(u.id) === uid);
    if (!cur) return list;
    return [cur, ...list.filter((u) => String(u.id) !== uid)];
  };

  return [...currentFirst(resultsSansSelection), ...currentFirst(selectedExtras)];
});

const catPlayerEtat = ref({}); // uid -> pct actuel
const catPlayerEtatLoading = ref(false);
const catPlayerEtatErreur = ref("");

async function chargerCatPlayerEtat() {
  catPlayerEtatErreur.value = "";
  catPlayerEtatLoading.value = false;

  if (!catForm.id) {
    catPlayerEtat.value = {};
    return;
  }
  const ids = catPlayerForm.utilisateur_ids || [];
  if (ids.length === 0) {
    catPlayerEtat.value = {};
    return;
  }

  try {
    catPlayerEtatLoading.value = true;
    const params = new URLSearchParams();
    for (const uid of ids) params.append("utilisateur_ids", String(uid));
    const data = await get(
      `/api/categories/${catForm.id}/modificateur-joueur?${params.toString()}`
    );
    catPlayerEtat.value = data.valeurs || {};
  } catch (e) {
    catPlayerEtatErreur.value = e?.message || String(e);
  } finally {
    catPlayerEtatLoading.value = false;
  }
}

watch(
  () => catModal.value,
  (open) => {
    if (!open) catPlayerEtat.value = {};
    else void chargerCatPlayerEtat();
  }
);

watch(
  () => (catPlayerForm.utilisateur_ids || []).slice().sort().join("|"),
  () => {
    if (catModal.value) void chargerCatPlayerEtat();
  }
);

// Multi-sélection de joueurs pour la modale "Ressource" (avec recherche).
const resPlayerSearch = ref("");
const resPlayerSearchNorm = computed(() => resPlayerSearch.value.trim().toLowerCase());
const resPlayerSelectedSet = computed(() => new Set((form.utilisateur_ids || []).map(String)));
const resPlayerSearchResults = computed(() => {
  const q = resPlayerSearchNorm.value;
  const all = utilisateursListe.value || [];
  if (!q) return all;
  return all.filter(
    (u) =>
      String(u.username || "").toLowerCase().includes(q) || String(u.id).includes(q),
  );
});
const resPlayerVisibleJoueurs = computed(() => {
  if (form.cible_modificateur !== "joueurs") return [];

  const q = resPlayerSearchNorm.value;
  const selected = resPlayerSelectedSet.value;

  const listPourRecherche = q ? resPlayerSearchResults.value : utilisateursListe.value || [];
  const resultsSansSelection = listPourRecherche.filter((u) => !selected.has(String(u.id)));
  const selectedExtras = (utilisateursListe.value || []).filter((u) => selected.has(String(u.id)));

  const uid = currentUserIdStr.value;
  const currentFirst = (list) => {
    if (!uid) return list;
    const cur = list.find((u) => String(u.id) === uid);
    if (!cur) return list;
    return [cur, ...list.filter((u) => String(u.id) !== uid)];
  };

  return [...currentFirst(resultsSansSelection), ...currentFirst(selectedExtras)];
});

const resPlayerEtat = ref({}); // uid -> {modificateur_pct, facteur_prix, ...}
const resPlayerEtatLoading = ref(false);
const resPlayerEtatErreur = ref("");

async function chargerResPlayerEtat() {
  resPlayerEtatErreur.value = "";
  resPlayerEtatLoading.value = false;

  if (!modeEdition.value || !form.id || form.cible_modificateur !== "joueurs") {
    resPlayerEtat.value = {};
    return;
  }
  const ids = form.utilisateur_ids || [];
  if (ids.length === 0) {
    resPlayerEtat.value = {};
    return;
  }

  try {
    resPlayerEtatLoading.value = true;
    const params = new URLSearchParams();
    for (const uid of ids) params.append("utilisateur_ids", String(uid));
    const data = await get(
      `/api/ressources/${form.id}/modificateur-joueur?${params.toString()}`
    );
    resPlayerEtat.value = data.valeurs || {};
  } catch (e) {
    resPlayerEtatErreur.value = e?.message || String(e);
  } finally {
    resPlayerEtatLoading.value = false;
  }
}

watch(
  () => [modalVisible.value, modeEdition.value, form.cible_modificateur],
  () => {
    if (!modalVisible.value) resPlayerEtat.value = {};
    else void chargerResPlayerEtat();
  }
);

watch(
  () => (form.utilisateur_ids || []).slice().sort().join("|"),
  () => {
    if (modalVisible.value) void chargerResPlayerEtat();
  }
);

function ouvrirNouvelleCategorie() {
  Object.assign(catForm, { id: null, nom: "", modificateur_pct: 100 });
  catModMode.value = "set";
  catBaseModificateurPct.value = 100;
  erreurCat.value = "";
  catPlayerForm.categorie_id = null;
  catPlayerForm.utilisateur_ids = [];
  catPlayerSearch.value = "";
  catModal.value = true;
}

function ouvrirEditCategorie(c) {
  Object.assign(catForm, {
    id: c.id,
    nom: c.nom,
    modificateur_pct: c.modificateur_pct,
  });
  catModMode.value = "set";
  catBaseModificateurPct.value = Number(c.modificateur_pct) || 100;
  erreurCat.value = "";
  catPlayerForm.categorie_id = c.id;
  catPlayerForm.utilisateur_ids = [];
  catPlayerSearch.value = "";
  catModal.value = true;
}

function ouvrirModifCategorieParJoueur(c) {
  catPlayerErreur.value = "";
  catPlayerForm.categorie_id = c.id;
  catPlayerForm.modificateur_pct = Number(c.modificateur_pct) || 100;
  catPlayerModMode.value = "set";
  catPlayerForm.utilisateur_ids = utilisateursListe.value?.[0]?.id
    ? [String(utilisateursListe.value[0].id)]
    : [];
  catPlayerModal.value = true;
}

function fixerCategorieModificateurA100() {
  // En pratique, on force le mode "Définir" pour obtenir exactement 100 %.
  catModMode.value = "set";
  catBaseModificateurPct.value = 100;
  catForm.modificateur_pct = 100;
  erreurCat.value = "";
}

function fixerCategorieModificateurJoueurA100() {
  // Même principe : on force le mode "Définir" pour obtenir exactement 100 %.
  catPlayerModMode.value = "set";
  catPlayerForm.modificateur_pct = 100;
  catPlayerErreur.value = "";
}

function passerEnModifCategorieParJoueur() {
  // Accès à la surcharge "par joueur" depuis le modal global.
  if (catForm.id == null) return;
  catModal.value = false;
  ouvrirModifCategorieParJoueur(catForm);
}

function catPlayerUserSelected(uid) {
  return catPlayerForm.utilisateur_ids.includes(String(uid));
}

function toggleCatPlayerUser(uid) {
  const sid = String(uid);
  const i = catPlayerForm.utilisateur_ids.indexOf(sid);
  if (i >= 0) catPlayerForm.utilisateur_ids.splice(i, 1);
  else catPlayerForm.utilisateur_ids.push(sid);
}

async function appliquerModifCategorieParJoueur(supprimer) {
  catPlayerErreur.value = "";
  if (catPlayerForm.categorie_id == null) {
    catPlayerErreur.value = "Catégorie requise.";
    return;
  }
  if (!catPlayerForm.utilisateur_ids || catPlayerForm.utilisateur_ids.length === 0) {
    catPlayerErreur.value = "Sélectionnez au moins un joueur.";
    return;
  }

  const payload = {
    utilisateur_ids: catPlayerForm.utilisateur_ids,
    supprimer: !!supprimer,
  };
  if (!supprimer) {
    payload.modificateur_pct = Number(catPlayerForm.modificateur_pct);
    payload.operation = catPlayerModMode.value;
  }

  try {
    await put(`/api/categories/${catPlayerForm.categorie_id}/modificateur-joueur`, payload);
    catPlayerModal.value = false;
    await chargerCategories();
  } catch (e) {
    catPlayerErreur.value = e.message;
  }
}

async function sauvegarderCategorie() {
  erreurCat.value = "";
  try {
    if (catForm.id == null) {
      await post("/api/categories", {
        nom: catForm.nom,
        modificateur_pct: Number(catForm.modificateur_pct),
      });
    } else {
      const selectedIds = catPlayerForm.utilisateur_ids || [];
      const input = Number(catForm.modificateur_pct);

      // Si des joueurs sont sélectionnés, on applique la modification uniquement en surcharge joueur.
      if (selectedIds.length > 0) {
        await put(`/api/categories/${catForm.id}/modificateur-joueur`, {
          utilisateur_ids: selectedIds,
          modificateur_pct: input,
          operation: catModMode.value,
        });
      } else {
        // Sinon, on met à jour le % catalogue global (propagation sur les ressources liées).
        const base = Number(catBaseModificateurPct.value);
        let newPct;
        if (catModMode.value === "set") newPct = input;
        else if (catModMode.value === "add") newPct = base + input;
        else newPct = base - input;

        if (!Number.isFinite(newPct) || newPct <= 0) {
          erreurCat.value = "modificateur_pct doit rester > 0.";
          return;
        }

        await put(`/api/categories/${catForm.id}`, {
          nom: catForm.nom,
          modificateur_pct: newPct,
        });
      }
    }
    catModal.value = false;
    await chargerCategories();
    await chargerRessources();
  } catch (e) {
    erreurCat.value = e.message;
  }
}

async function supprimerCategorie(c) {
  if (!confirm(`Supprimer la catégorie « ${c.nom} » ? (elle sera retirée des ressources)`))
    return;
  try {
    await del(`/api/categories/${c.id}`);
    await chargerCategories();
    await chargerRessources();
  } catch (e) {
    erreur.value = e.message;
  }
}

const colonnes = [
  ["nom", "Ressource"],
  ["categories", "Catégories"],
  ["modificateur_pct", "% ressource"],
  ["facteur_prix", "Facteur total"],
  ["prix_base", "Prix base"],
  ["prix_modifie", "Prix modifié"],
  ["prix_achat", "Prix d'achat"],
  ["prix_lointain", "Si lointain"],
];
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">Catalogue des ressources</h2>
        <p class="page-subtitle">
          <template v-if="isMj">
            Modificateurs en % (100 % = neutre). Facteur total = ( % ressource / 100 ) × moyenne( % catégorie / 100 ).
            Tableau : <strong>prix catalogue</strong> (global). Vous pouvez appliquer un % à tout le monde, à vous seul ou à des joueurs choisis.
          </template>
          <template v-else>
            <strong>Consultation</strong> : les montants affichés utilisent <strong>votre</strong> modificateur (catalogue et éventuelle surcharge MJ).
          </template>
        </p>
      </div>
      <div v-if="isMj" class="header-actions">
        <button class="button" @click="ouvrirCreation">+ Ressource</button>
      </div>
    </div>

    <p v-if="erreur" class="error">{{ erreur }}</p>

    <section v-if="isMj" class="cat-panel">
      <div class="cat-panel-head">
        <h3 class="section-title">Catégories (modificateur en %)</h3>
        <button type="button" class="button secondary small" @click="ouvrirNouvelleCategorie">+ Catégorie</button>
      </div>
      <p class="section-hint">
        Par défaut 100 %. Une nouvelle ressource est à 100 % et les prix intègrent automatiquement les % des catégories cochées.
        La modification d’une catégorie propage automatiquement les prix des ressources liées.
      </p>
      <div class="cat-chips">
        <div v-for="c in categories" :key="c.id" class="cat-chip cat-chip-row">
          <div class="cat-chip-text">
            <span class="cat-chip-nom">{{ c.nom }}</span>
            <span class="cat-chip-mod">{{ formatPct(c.modificateur_pct) }}</span>
          </div>
          <div class="cat-chip-actions">
            <button type="button" class="button secondary btn-cat-lg" @click="ouvrirEditCategorie(c)">
              Modifier
            </button>
            <button type="button" class="button btn-cat-lg btn-cat-danger" @click="supprimerCategorie(c)">
              Supprimer
            </button>
          </div>
        </div>
      </div>
    </section>

    <div class="filters">
      <input v-model="recherche" type="text" placeholder="Rechercher…" class="input-search" />
      <select v-model="filtreCategorieId" class="select">
        <option value="">Toutes les catégories</option>
        <option v-for="c in categories" :key="c.id" :value="String(c.id)">{{ c.nom }}</option>
      </select>
    </div>

    <div v-if="isMj" class="bulk-toolbar">
      <span class="bulk-count">{{ selectedIds.length }} sélectionnée(s)</span>
      <button type="button" class="button secondary small" @click="selectionnerVueFiltre">
        Tout sélectionner (vue filtrée)
      </button>
      <button type="button" class="button secondary small" @click="viderSelection">
        Vider la sélection
      </button>
      <button
        type="button"
        class="button"
        :disabled="selectedIds.length === 0"
        @click="bulkModal = true"
      >
        Prix marché groupé (% ressource)…
      </button>
    </div>

    <template v-for="(bloc, idx) in [
      { titre: 'Matières premières', liste: listePremiere },
      { titre: 'Matières manufacturées', liste: listeManufacture },
    ]" :key="idx">
      <h3 class="table-block-title">
        {{ bloc.titre }}
        <button
          v-if="isMj"
          type="button"
          class="button secondary small bloc-select-all"
          @click="selectionnerToutListe(bloc.liste)"
        >
          Sélectionner tout ({{ bloc.titre }})
        </button>
      </h3>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th v-if="isMj" class="th-check"></th>
              <th
                v-for="[k, lab] in colonnes"
                :key="k"
                class="th-sort"
                @click="toggleSort(k)"
              >
                {{ lab }}{{ sortLabel(k) }}
              </th>
              <th v-if="isMj"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in bloc.liste" :key="r.id">
              <td v-if="isMj" class="td-check">
                <input
                  v-if="r.nom !== FLORINS_NOM"
                  type="checkbox"
                  :checked="idSelectionne(r.id)"
                  @change="toggleSelection(r.id)"
                />
                <span v-else class="muted" title="Monnaie — pas d’ajustement groupé">—</span>
              </td>
              <td class="nom">{{ r.nom }}</td>
              <td class="categories">
                <span v-for="c in r.categories || []" :key="c.id" class="tag">
                  {{ c.nom }} ({{ formatPct(c.modificateur_pct) }})
                </span>
                <span v-if="!(r.categories || []).length" class="muted">—</span>
              </td>
              <td class="prix">{{ formatPct(r.modificateur_pct) }}</td>
              <td class="prix">×{{ r.facteur_prix }}</td>
              <td class="prix" :title="formatFlorinExact(r.prix_base)">
                {{ formatFlorin(r.prix_base) }}
              </td>
              <td class="prix" :title="formatFlorinExact(r.prix_modifie)">
                {{ formatFlorin(r.prix_modifie) }}
              </td>
              <td class="prix accent" :title="formatFlorinExact(r.prix_achat)">
                {{ formatFlorin(r.prix_achat) }}
              </td>
              <td class="prix" :title="formatFlorinExact(r.prix_lointain)">
                {{ formatFlorin(r.prix_lointain) }}
              </td>
              <td v-if="isMj" class="actions">
                <button type="button" class="button secondary table-row-action" @click="ouvrirEdition(r)">
                  Modifier
                </button>
                <button type="button" class="button secondary table-row-action danger" @click="supprimerRessource(r)">
                  Supprimer
                </button>
              </td>
            </tr>
            <tr v-if="bloc.liste.length === 0">
              <td :colspan="isMj ? 10 : 8" class="empty">Aucune ressource.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div v-if="bulkModal" class="modal-overlay" @click.self="bulkModal = false">
      <div class="modal modal-md">
        <h3 class="modal-title">Prix marché — modificateur % (ressource)</h3>
        <p class="modal-hint">
          S’applique aux <strong>{{ selectedIds.length }}</strong> ressource(s) sélectionnée(s).
        </p>
        <p v-if="bulkErr" class="error">{{ bulkErr }}</p>
        <label class="form-label">
          Nouveau % modificateur ressource
          <input v-model.number="bulkPct" type="number" step="0.1" min="0.1" class="input" />
        </label>
        <div class="cible-mod-block">
          <div class="cible-mod-title">Cible</div>
          <label class="radio-line">
            <input v-model="bulkCible" type="radio" value="tous" />
            Tous les joueurs (met à jour le catalogue et retire les surcharges sur ces ressources)
          </label>
          <label class="radio-line">
            <input v-model="bulkCible" type="radio" value="moi" />
            Moi uniquement (surcharge sur mon compte)
          </label>
          <label class="radio-line">
            <input v-model="bulkCible" type="radio" value="joueurs" />
            Joueurs sélectionnés (comptes Discord liés)
          </label>
          <div v-if="bulkCible === 'joueurs'" class="user-pick-grid">
            <label v-for="u in utilisateursListe" :key="u.id" class="checkbox-label user-pick-item">
              <input
                type="checkbox"
                :checked="bulkUserSelected(u.id)"
                @change="toggleBulkUser(u.id)"
              />
              {{ u.username }}
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="button secondary" :disabled="bulkLoading" @click="bulkModal = false">Annuler</button>
          <button class="button" :disabled="bulkLoading" @click="appliquerBulkPrix">
            {{ bulkLoading ? "…" : "Appliquer" }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="catModal" class="modal-overlay" @click.self="catModal = false">
      <div class="modal modal-sm">
        <h3 class="modal-title">{{ catForm.id == null ? "Nouvelle catégorie" : "Modifier la catégorie" }}</h3>
        <p v-if="erreurCat" class="error">{{ erreurCat }}</p>
        <label class="form-label">Nom<input v-model="catForm.nom" class="input" /></label>
        <div v-if="catForm.id != null" class="cible-mod-block">
          <div class="cible-mod-title">Mise à jour</div>
          <label class="radio-line">
            <input v-model="catModMode" type="radio" value="set" />
            Définir
          </label>
          <label class="radio-line">
            <input v-model="catModMode" type="radio" value="add" />
            Ajouter
          </label>
          <label class="radio-line">
            <input v-model="catModMode" type="radio" value="remove" />
            Retirer
          </label>
        </div>
        <label class="form-label">
          <span v-if="catForm.id == null || catModMode === 'set'">Modificateur (%)</span>
          <span v-else>Delta (%)</span>
          <input
            v-model.number="catForm.modificateur_pct"
            type="number"
            step="0.1"
            min="0.1"
            class="input"
            @focus="(e) => e.target.select()"
          />
        </label>
        <label v-if="catForm.id != null" class="form-label">
          Joueurs
          <input
            v-model="catPlayerSearch"
            type="text"
            placeholder="Rechercher un joueur…"
            class="input player-search"
          />
          <div class="player-picker-list">
            <label
              v-for="u in catPlayerVisibleJoueurs"
              :key="u.id"
              class="checkbox-label user-pick-item"
            >
              <input
                type="checkbox"
                :checked="catPlayerUserSelected(u.id)"
                @change="toggleCatPlayerUser(u.id)"
              />
              {{ u.username }}{{ u.is_mj ? " (MJ)" : "" }}
            </label>
          </div>
        </label>

        <div v-if="(catPlayerForm.utilisateur_ids || []).length > 0" class="state-block">
          <div class="state-title">
            État actuel (catégorie) chez les joueurs sélectionnés
          </div>
          <div class="state-rows">
            <div
              v-for="uid in catPlayerForm.utilisateur_ids"
              :key="uid"
              class="state-row"
            >
              <span class="state-player">
                {{ utilisateursListe.find((u) => String(u.id) === String(uid))?.username || uid }}
              </span>
              <span class="state-val">{{ formatPct(catPlayerEtat[uid] ?? catForm.modificateur_pct) }}</span>
            </div>
          </div>
          <div v-if="catPlayerEtatLoading" class="muted">Chargement…</div>
          <div v-if="catPlayerEtatErreur" class="error">{{ catPlayerEtatErreur }}</div>
        </div>

        <p
          v-if="catForm.id == null || (catPlayerForm.utilisateur_ids || []).length === 0"
          class="form-hint"
        >
          Propagation automatique sur toutes les ressources liées.
        </p>
        <p v-else class="form-hint">
          Applique uniquement la surcharge de catégorie aux joueurs sélectionnés (le catalogue global reste inchangé).
        </p>
        <div class="modal-footer">
          <button class="button secondary" @click="catModal = false">Annuler</button>
          <button class="button secondary" type="button" @click="fixerCategorieModificateurA100">
            À 100 %
          </button>
          <button class="button" @click="sauvegarderCategorie">Enregistrer</button>
        </div>
      </div>
    </div>

    <div v-if="modalVisible" class="modal-overlay" @click.self="modalVisible = false">
      <div class="modal modal-wide">
        <h3 class="modal-title">{{ modeEdition ? "Modifier la ressource" : "Nouvelle ressource" }}</h3>
        <p v-if="erreurModal" class="error">{{ erreurModal }}</p>
        <div class="form-grid">
          <label>Nom<input v-model="form.nom" class="input" /></label>
          <label>Type
            <select v-model="form.type" class="select">
              <option>Première</option>
              <option>Manufacturé</option>
            </select>
          </label>
          <label>Prix de base (ƒ, entier)<input v-model.number="form.prix_base" type="number" class="input" min="0" /></label>
          <label>
            <span v-if="!modeEdition || resModMode === 'set'">% modificateur ressource</span>
            <span v-else>Delta (%) sur % ressource</span>
            <input v-model.number="form.modificateur_pct" type="number" step="0.1" min="0.1" class="input" />
          </label>
        </div>
        <div v-if="modeEdition" class="cible-mod-block">
          <div class="cible-mod-title">Mise à jour</div>
          <label class="radio-line">
            <input v-model="resModMode" type="radio" value="set" />
            Définir
          </label>
          <label class="radio-line">
            <input v-model="resModMode" type="radio" value="add" />
            Ajouter
          </label>
          <label class="radio-line">
            <input v-model="resModMode" type="radio" value="remove" />
            Retirer
          </label>
          <div class="cible-mod-title">
            À l’enregistrement,
            {{
              resModMode === "set"
                ? "appliquer ce % ressource à :"
                : "ajouter/retirer ce delta sur le % ressource à :"
            }}
          </div>
          <label class="radio-line">
            <input v-model="form.cible_modificateur" type="radio" value="tous" />
            Tous les joueurs (catalogue ; supprime les surcharges sur cette ressource)
          </label>
          <label class="radio-line">
            <input v-model="form.cible_modificateur" type="radio" value="moi" />
            Moi uniquement (surcharge)
          </label>
          <label class="radio-line">
            <input v-model="form.cible_modificateur" type="radio" value="joueurs" />
            Joueurs sélectionnés
          </label>
          <div v-if="form.cible_modificateur === 'joueurs'" class="user-pick-grid">
            <input
              v-model="resPlayerSearch"
              type="text"
              placeholder="Rechercher un joueur…"
              class="input player-search"
            />
            <div class="player-picker-list">
              <label
                v-for="u in resPlayerVisibleJoueurs"
                :key="u.id"
                class="checkbox-label user-pick-item"
              >
                <input
                  type="checkbox"
                  :checked="formUserSelected(u.id)"
                  @change="toggleFormUser(u.id)"
                />
                {{ u.username }}
              </label>
            </div>

            <div v-if="(form.utilisateur_ids || []).length > 0" class="state-block">
              <div class="state-title">
                État actuel (ressource) chez les joueurs sélectionnés
              </div>
              <div class="state-rows">
                <div
                  v-for="uid in form.utilisateur_ids"
                  :key="uid"
                  class="state-row"
                >
                  <span class="state-player">
                    {{ utilisateursListe.find((u) => String(u.id) === String(uid))?.username || uid }}
                  </span>
                  <span class="state-val">
                    {{ formatPct(resPlayerEtat[uid]?.modificateur_pct ?? 100) }}
                  </span>
                </div>
              </div>
              <div v-if="resPlayerEtatLoading" class="muted">Chargement…</div>
              <div v-if="resPlayerEtatErreur" class="error">{{ resPlayerEtatErreur }}</div>
            </div>
          </div>
        </div>
        <p class="form-hint">Nouvelle ressource : 100 % par défaut ; les catégories cochées appliquent leur % dans le facteur total.</p>

        <div class="cat-pick">
          <div class="cat-pick-title">Catégories</div>
          <div class="cat-pick-grid">
            <label v-for="c in categories" :key="c.id" class="checkbox-label cat-pick-item">
              <input
                type="checkbox"
                :checked="form.categorie_ids.includes(c.id)"
                @change="(e) => setCategorieChecked(c.id, e.target.checked)"
              />
              {{ c.nom }} ({{ formatPct(c.modificateur_pct) }})
            </label>
          </div>
        </div>

        <div v-if="modeEdition" class="modal-actions-row">
          <button type="button" class="button secondary" @click="appliquerProduitCategories">
            Remettre % ressource à 100 % (neutre)
          </button>
        </div>

        <div class="preview-box">
          <strong>Aperçu</strong>
          <span>Facteur ×{{ previewFacteur.toFixed(4) }}</span>
          <span :title="formatFlorinExact(preview.prix_modifie)">
            Prix modifié : {{ formatFlorin(preview.prix_modifie) }}
          </span>
          <span :title="formatFlorinExact(preview.prix_achat)">
            Prix d’achat : {{ formatFlorin(preview.prix_achat) }}
          </span>
          <span :title="formatFlorinExact(preview.prix_lointain)">
            Si lointain : {{ formatFlorin(preview.prix_lointain) }}
          </span>
        </div>

        <div class="modal-footer">
          <button class="button secondary" @click="modalVisible = false">Annuler</button>
          <button class="button" @click="sauvegarderRessource">Enregistrer</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.player-search {
  margin-top: 6px;
}

.player-picker-list {
  margin-top: 10px;
  max-height: 380px; /* ~20 joueurs visibles avant scroll */
  overflow-y: auto;
  padding-right: 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.player-picker-list label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.state-block {
  margin-top: 10px;
  padding: 10px 12px;
  border: 1px solid #334155;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.25);
}

.state-title {
  font-weight: 700;
  font-size: 13px;
  color: #cbd5e1;
  margin-bottom: 8px;
}

.state-rows {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.state-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  font-size: 13px;
}

.state-player {
  color: #e2e8f0;
}

.state-val {
  color: #93c5fd;
  white-space: nowrap;
}
</style>
