<script setup>
import { computed, reactive, ref } from "vue";
import { formatFlorin, useApi } from "../composables/useApi.js";

const props = defineProps({
  authState: { type: Object, required: true },
});

const { get, post, put, del } = useApi();
const isMj = computed(() => props.authState.user?.is_mj);

const ressources = ref([]);
const erreur = ref("");
const recherche = ref("");
const filtreType = ref("Tous");
const filtreCategorie = ref("Toutes");

const CATEGORIES = [
  "Toutes", "Métallurgie", "Construction", "Chauffage",
  "Agro-alimentaire", "Textile", "Animal", "Réserve de valeur",
];

async function charger() {
  try {
    ressources.value = await get("/api/ressources");
  } catch (e) {
    erreur.value = e.message;
  }
}
charger();

const ressourcesFiltrees = computed(() => {
  return ressources.value.filter((r) => {
    const matchRecherche = r.nom.toLowerCase().includes(recherche.value.toLowerCase());
    const matchType = filtreType.value === "Tous" || r.type === filtreType.value;
    const matchCat =
      filtreCategorie.value === "Toutes" ||
      (r.categories ?? "").includes(filtreCategorie.value);
    return matchRecherche && matchType && matchCat;
  });
});

// --- Modal ---
const modalVisible = ref(false);
const modeEdition = ref(false);
const erreurModal = ref("");
const form = reactive({
  id: null,
  nom: "",
  type: "Première",
  prix_base: "",
  modificateur: 0,
  prix_modifie: "",
  prix_achat: "",
  prix_lointain: "",
  categories: "",
});

function ouvrirCreation() {
  Object.assign(form, {
    id: null, nom: "", type: "Première", prix_base: "",
    modificateur: 0, prix_modifie: "", prix_achat: "",
    prix_lointain: "", categories: "",
  });
  erreurModal.value = "";
  modeEdition.value = false;
  modalVisible.value = true;
}

function ouvrirEdition(r) {
  Object.assign(form, { ...r });
  erreurModal.value = "";
  modeEdition.value = true;
  modalVisible.value = true;
}

async function sauvegarder() {
  erreurModal.value = "";
  const payload = {
    nom: form.nom,
    type: form.type,
    prix_base: Number(form.prix_base),
    modificateur: Number(form.modificateur),
    prix_modifie: Number(form.prix_modifie),
    prix_achat: Number(form.prix_achat),
    prix_lointain: Number(form.prix_lointain),
    categories: form.categories,
  };
  try {
    if (modeEdition.value) {
      await put(`/api/ressources/${form.id}`, payload);
    } else {
      await post("/api/ressources", payload);
    }
    await charger();
    modalVisible.value = false;
  } catch (e) {
    erreurModal.value = e.message;
  }
}

async function supprimer(r) {
  if (!confirm(`Supprimer "${r.nom}" ?`)) return;
  try {
    await del(`/api/ressources/${r.id}`);
    await charger();
  } catch (e) {
    erreur.value = e.message;
  }
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">Catalogue des Ressources</h2>
        <p class="page-subtitle">Prix exprimés en florins (ƒ)</p>
      </div>
      <button v-if="isMj" class="button" @click="ouvrirCreation">+ Ajouter</button>
    </div>

    <p v-if="erreur" class="error">{{ erreur }}</p>

    <div class="filters">
      <input v-model="recherche" type="text" placeholder="Rechercher…" class="input-search" />
      <div class="filter-group">
        <button
          v-for="t in ['Tous', 'Première', 'Manufacturé']"
          :key="t"
          class="filter-btn"
          :class="{ active: filtreType === t }"
          @click="filtreType = t"
        >{{ t }}</button>
      </div>
      <select v-model="filtreCategorie" class="select">
        <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option>
      </select>
    </div>

    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Ressource</th>
            <th>Type</th>
            <th>Prix base</th>
            <th>Modif.</th>
            <th>Prix modifié</th>
            <th>Prix d'achat</th>
            <th>Si lointain</th>
            <th>Catégories</th>
            <th v-if="isMj"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in ressourcesFiltrees" :key="r.id">
            <td class="nom">{{ r.nom }}</td>
            <td>
              <span :class="['badge', r.type === 'Manufacturé' ? 'badge-manuf' : 'badge-prem']">
                {{ r.type }}
              </span>
            </td>
            <td class="prix">{{ formatFlorin(r.prix_base) }}</td>
            <td class="prix">{{ r.modificateur > 0 ? `×${r.modificateur}` : "—" }}</td>
            <td class="prix">{{ formatFlorin(r.prix_modifie) }}</td>
            <td class="prix accent">{{ formatFlorin(r.prix_achat) }}</td>
            <td class="prix">{{ formatFlorin(r.prix_lointain) }}</td>
            <td class="categories">
              <span
                v-for="cat in (r.categories ?? '').split(';').map(c => c.trim()).filter(Boolean)"
                :key="cat"
                class="tag"
              >{{ cat }}</span>
            </td>
            <td v-if="isMj" class="actions">
              <button class="btn-icon" title="Modifier" @click="ouvrirEdition(r)">✏</button>
              <button class="btn-icon danger" title="Supprimer" @click="supprimer(r)">🗑</button>
            </td>
          </tr>
          <tr v-if="ressourcesFiltrees.length === 0">
            <td :colspan="isMj ? 9 : 8" class="empty">Aucune ressource trouvée.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal création / édition (MJ uniquement) -->
    <div v-if="modalVisible" class="modal-overlay" @click.self="modalVisible = false">
      <div class="modal">
        <h3 class="modal-title">{{ modeEdition ? "Modifier" : "Nouvelle ressource" }}</h3>
        <p v-if="erreurModal" class="error">{{ erreurModal }}</p>
        <div class="form-grid">
          <label>Nom<input v-model="form.nom" class="input" /></label>
          <label>Type
            <select v-model="form.type" class="select">
              <option>Première</option>
              <option>Manufacturé</option>
            </select>
          </label>
          <label>Prix base (ƒ)<input v-model="form.prix_base" type="number" class="input" /></label>
          <label>Modificateur<input v-model="form.modificateur" type="number" step="0.1" class="input" /></label>
          <label>Prix modifié (ƒ)<input v-model="form.prix_modifie" type="number" class="input" /></label>
          <label>Prix d'achat (ƒ)<input v-model="form.prix_achat" type="number" class="input" /></label>
          <label>Prix lointain (ƒ)<input v-model="form.prix_lointain" type="number" class="input" /></label>
          <label class="full">Catégories<input v-model="form.categories" class="input" placeholder="ex : Métallurgie ; Construction" /></label>
        </div>
        <div class="modal-footer">
          <button class="button secondary" @click="modalVisible = false">Annuler</button>
          <button class="button" @click="sauvegarder">Sauvegarder</button>
        </div>
      </div>
    </div>
  </div>
</template>
