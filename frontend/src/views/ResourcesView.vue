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
  let f = (Number(form.modificateur_pct) || 100) / 100;
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
const catForm = reactive({ id: null, nom: "", modificateur_pct: 100, propager: false });
const erreurCat = ref("");

// Modificateur de catégorie par joueur (surcharge)
const catPlayerModal = ref(false);
const catPlayerErreur = ref("");
const catPlayerForm = reactive({
  categorie_id: null,
  utilisateur_id: null,
  modificateur_pct: 100,
});
const catPlayerCategorieNom = computed(() => {
  const id = catPlayerForm.categorie_id;
  if (id == null) return "";
  return categories.value.find((x) => x.id === id)?.nom ?? "";
});

function ouvrirNouvelleCategorie() {
  Object.assign(catForm, { id: null, nom: "", modificateur_pct: 100, propager: false });
  erreurCat.value = "";
  catModal.value = true;
}

function ouvrirEditCategorie(c) {
  Object.assign(catForm, {
    id: c.id,
    nom: c.nom,
    modificateur_pct: c.modificateur_pct,
    propager: false,
  });
  erreurCat.value = "";
  catModal.value = true;
}

function ouvrirModifCategorieParJoueur(c) {
  catPlayerErreur.value = "";
  catPlayerForm.categorie_id = c.id;
  catPlayerForm.modificateur_pct = Number(c.modificateur_pct) || 100;
  catPlayerForm.utilisateur_id = utilisateursListe.value?.[0]?.id ?? null;
  catPlayerModal.value = true;
}

async function appliquerModifCategorieParJoueur(supprimer) {
  catPlayerErreur.value = "";
  if (catPlayerForm.categorie_id == null) {
    catPlayerErreur.value = "Catégorie requise.";
    return;
  }
  if (!catPlayerForm.utilisateur_id) {
    catPlayerErreur.value = "Sélectionnez un joueur.";
    return;
  }

  const payload = {
    utilisateur_id: String(catPlayerForm.utilisateur_id),
    supprimer: !!supprimer,
  };
  if (!supprimer) payload.modificateur_pct = Number(catPlayerForm.modificateur_pct);

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
      await put(`/api/categories/${catForm.id}`, {
        nom: catForm.nom,
        modificateur_pct: Number(catForm.modificateur_pct),
        propager: catForm.propager,
      });
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
            Modificateurs en % (100 % = neutre). Facteur total = ( % ressource / 100 ) × ∏( % catégorie / 100 ).
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
        « Propager » sur une catégorie recalcule les prix de toutes les ressources qui l’utilisent.
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
            <button type="button" class="button secondary btn-cat-lg" @click="ouvrirModifCategorieParJoueur(c)">
              Par joueur
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
        <label class="form-label">Modificateur (%)
          <input v-model.number="catForm.modificateur_pct" type="number" step="0.1" min="0.1" class="input" />
        </label>
        <p class="form-hint">100 % = aucun effet sur le facteur ; 120 % = ×1,2 pour cette catégorie.</p>
        <label v-if="catForm.id != null" class="form-label checkbox-label">
          <input v-model="catForm.propager" type="checkbox" />
          Propager : recalculer les prix de toutes les ressources liées à cette catégorie
        </label>
        <div class="modal-footer">
          <button class="button secondary" @click="catModal = false">Annuler</button>
          <button class="button" @click="sauvegarderCategorie">Enregistrer</button>
        </div>
      </div>
    </div>

    <div v-if="catPlayerModal" class="modal-overlay" @click.self="catPlayerModal = false">
      <div class="modal modal-sm">
        <h3 class="modal-title">
          Modificateur de catégorie — {{ catPlayerCategorieNom || "…" }}
        </h3>
        <p v-if="catPlayerErreur" class="error">{{ catPlayerErreur }}</p>
        <label class="form-label">
          Joueur
          <select v-model="catPlayerForm.utilisateur_id" class="select full-width">
            <option v-for="u in utilisateursListe" :key="u.id" :value="u.id">
              {{ u.username }}{{ u.is_mj ? " (MJ)" : "" }}
            </option>
          </select>
        </label>
        <label class="form-label">
          Modificateur (%)
          <input
            v-model.number="catPlayerForm.modificateur_pct"
            type="number"
            step="0.1"
            min="0.1"
            class="input"
          />
        </label>
        <p class="form-hint">100 % = neutre ; 80 % = ×0,8 pour ce joueur.</p>
        <div class="modal-footer">
          <button class="button secondary" @click="appliquerModifCategorieParJoueur(true)">
            Réinitialiser
          </button>
          <button class="button" @click="appliquerModifCategorieParJoueur(false)">
            Appliquer
          </button>
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
          <label>% modificateur ressource
            <input v-model.number="form.modificateur_pct" type="number" step="0.1" min="0.1" class="input" />
          </label>
        </div>
        <div v-if="modeEdition" class="cible-mod-block">
          <div class="cible-mod-title">À l’enregistrement, appliquer ce % ressource à :</div>
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
            <label v-for="u in utilisateursListe" :key="u.id" class="checkbox-label user-pick-item">
              <input
                type="checkbox"
                :checked="formUserSelected(u.id)"
                @change="toggleFormUser(u.id)"
              />
              {{ u.username }}
            </label>
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
