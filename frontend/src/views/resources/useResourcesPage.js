import { computed, reactive, ref, watch } from "vue";
import { FLORINS_NOM, formatFlorin, formatFlorinExact, useApi } from "../../composables/useApi.js";
import { useResourcesApiData } from "./composables/useResourcesApiData.js";
import { useMjView } from "../../composables/useMjView.js";
import { useResourcesList } from "./composables/useResourcesList.js";
import { useBulkPrix } from "./composables/useBulkPrix.js";
import { usePlayerPicker } from "./composables/usePlayerPicker.js";

export function useResourcesPage(authState) {
  const { post, put, del, get } = useApi();
  const isMj = computed(() => authState.user?.is_mj);
  const currentUserIdStr = computed(() => String(authState.user?.id ?? ""));

  const recherche = ref("");
  const filtreCategorieId = ref("");

  function formatPct(v) {
    const n = Number(v);
    if (!Number.isFinite(n)) return "100 %";
    if (Number.isInteger(n)) return `${n} %`;
    return `${n} %`;
  }

  const data = useResourcesApiData();

  const mj = useMjView({
    authState,
    utilisateursListeRef: data.utilisateursListe,
    isMjRef: isMj,
    currentUserIdStrRef: currentUserIdStr,
    allowGlobal: true,
    // Même clé que les autres pages pour conserver le joueur observé en naviguant.
    storageKey: "mj_view_choice_uid",
  });

  async function chargerRessources() {
    return data.chargerRessources({ isMj: isMj.value, mjVueChoix: mj.mjVueChoix.value });
  }

  watch(isMj, async () => {
    await data.chargerUtilisateurs({ enabled: isMj.value });
    await chargerRessources();
  });
  watch(
    () => [isMj.value, mj.mjVueChoix.value],
    () => {
      if (isMj.value) void chargerRessources();
    },
  );

  void data.chargerTout({ isMj: isMj.value, mjVueChoix: mj.mjVueChoix.value });

  const list = useResourcesList({
    ressourcesRef: data.ressources,
    categoriesRef: data.categories,
    rechercheRef: recherche,
    filtreCategorieIdRef: filtreCategorieId,
  });

  const bulk = useBulkPrix({
    isMjRef: isMj,
    mjVueChoixRef: mj.mjVueChoix,
    currentUserIdStrRef: currentUserIdStr,
    utilisateursListeRef: data.utilisateursListe,
    ressourcesFiltreesRef: list.ressourcesFiltrees,
    ressourcesRef: data.ressources,
    chargerRessources,
  });

  // --- Modale ressource ---
  const modalVisible = ref(false);
  const modeEdition = ref(false);
  const erreurModal = ref("");
  const resModMode = ref("set");
  const resBaseModificateurPct = ref(100);
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
    if (!modeEdition.value || resModMode.value === "set") pctRessource = Number(form.modificateur_pct) || 100;
    else {
      const base = Number(resBaseModificateurPct.value) || 100;
      const delta = Number(form.modificateur_pct) || 0;
      pctRessource = resModMode.value === "add" ? base + delta : base - delta;
    }
    let f = pctRessource / 100;
    for (const id of form.categorie_ids) {
      const c = list.getCategorieById(id);
      if (c) f *= (Number(c.modificateur_pct) || 100) / 100;
    }
    return f;
  });
  const preview = computed(() => list.previewPrix(form.prix_base, previewFacteur.value));

  const resPlayerSearch = ref("");
  const resPicker = usePlayerPicker({
    utilisateursListeRef: data.utilisateursListe,
    currentUserIdStrRef: currentUserIdStr,
    selectedIdsRef: computed({
      get: () => form.utilisateur_ids,
      set: (v) => (form.utilisateur_ids = v),
    }),
    searchRef: resPlayerSearch,
  });
  const resPlayerVisibleJoueurs = computed(() => resPicker.visible.value);

  function formUserSelected(uid) {
    return (form.utilisateur_ids || []).includes(String(uid)) || (form.utilisateur_ids || []).includes(uid);
  }
  function toggleFormUser(uid) {
    const s = String(uid);
    const idx = form.utilisateur_ids.findIndex((x) => String(x) === s);
    if (idx >= 0) form.utilisateur_ids.splice(idx, 1);
    else form.utilisateur_ids.push(s);
  }

  watch(
    () => (form.utilisateur_ids || []).slice().sort().join("|"),
    () => {
      if (!modeEdition.value) return;
      form.cible_modificateur = (form.utilisateur_ids || []).length > 0 ? "joueurs" : "tous";
    },
  );

  function setCategorieChecked(catId, checked) {
    const i = form.categorie_ids.indexOf(catId);
    if (checked && i < 0) form.categorie_ids.push(catId);
    if (!checked && i >= 0) form.categorie_ids.splice(i, 1);
  }

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
    if (isMj.value && mj.mjVueChoix.value && mj.mjVueChoix.value !== "global") {
      form.utilisateur_ids = [String(mj.mjVueChoix.value)];
      form.cible_modificateur = "joueurs";
    } else if (isMj.value && mj.mjVueChoix.value === "global") {
      form.utilisateur_ids = (data.utilisateursListe.value || []).map((u) => String(u.id));
      form.cible_modificateur = form.utilisateur_ids.length > 0 ? "joueurs" : "tous";
    }
    resModMode.value = "set";
    resBaseModificateurPct.value = Number(r.modificateur_pct) || 100;
    resPlayerSearch.value = "";
    erreurModal.value = "";
    modeEdition.value = true;
    modalVisible.value = true;
  }

  function resSelectAllUsers() {
    form.utilisateur_ids = (data.utilisateursListe.value || []).map((u) => String(u.id));
    form.cible_modificateur = form.utilisateur_ids.length > 0 ? "joueurs" : "tous";
  }
  function resClearAllUsers() {
    form.utilisateur_ids = [];
    form.cible_modificateur = "tous";
  }

  const resAllUsersSelected = computed(() => {
    const all = (data.utilisateursListe.value || []).map((u) => String(u.id));
    if (all.length === 0) return false;
    const selected = new Set((form.utilisateur_ids || []).map((x) => String(x)));
    if (selected.size !== all.length) return false;
    for (const id of all) if (!selected.has(id)) return false;
    return true;
  });

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

  const resPlayerEtat = ref({});
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
      const dataEtat = await get(`/api/ressources/${form.id}/modificateur-joueur?${params.toString()}`);
      resPlayerEtat.value = dataEtat.valeurs || {};
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
    },
  );
  watch(
    () => (form.utilisateur_ids || []).slice().sort().join("|"),
    () => {
      if (modalVisible.value) void chargerResPlayerEtat();
    },
  );

  async function sauvegarderRessource() {
    erreurModal.value = "";
    const payload = {
      nom: form.nom,
      type: form.type,
      prix_base: Number(form.prix_base),
      modificateur_pct: Number(form.modificateur_pct),
      categorie_ids: [...form.categorie_ids],
    };
    if (modeEdition.value) {
      payload.cible_modificateur = form.cible_modificateur;
      payload.utilisateur_ids = form.cible_modificateur === "joueurs" ? [...form.utilisateur_ids] : [];
      payload.operation = resModMode.value;
    }
    try {
      let saved;
      if (modeEdition.value) saved = await put(`/api/ressources/${form.id}`, payload);
      else saved = await post("/api/ressources", payload);
      modalVisible.value = false;

      const isOverrideJoueurs =
        modeEdition.value && form.cible_modificateur === "joueurs" && (form.utilisateur_ids || []).length > 0;
      if (!isOverrideJoueurs && saved && saved.id != null) {
        const idx = data.ressources.value.findIndex((r) => r.id === saved.id);
        if (idx >= 0) data.ressources.value.splice(idx, 1, saved);
        else data.ressources.value.unshift(saved);
      }

      void chargerRessources();
      void chargerResPlayerEtat();
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
      data.erreur.value = e.message;
    }
  }

  // --- Modale catégorie ---
  const catModal = ref(false);
  const catForm = reactive({ id: null, nom: "", modificateur_pct: 100 });
  const catModMode = ref("set");
  const catBaseModificateurPct = ref(100);
  const erreurCat = ref("");
  const catPlayerForm = reactive({ categorie_id: null, utilisateur_ids: [], modificateur_pct: 100 });
  const catPlayerSearch = ref("");
  const catPicker = usePlayerPicker({
    utilisateursListeRef: data.utilisateursListe,
    currentUserIdStrRef: currentUserIdStr,
    selectedIdsRef: computed({
      get: () => catPlayerForm.utilisateur_ids,
      set: (v) => (catPlayerForm.utilisateur_ids = v),
    }),
    searchRef: catPlayerSearch,
  });
  const catPlayerVisibleJoueurs = computed(() => {
    if (catForm.id == null) return [];
    return catPicker.visible.value;
  });

  function catPlayerUserSelected(uid) {
    return (catPlayerForm.utilisateur_ids || []).includes(String(uid));
  }
  function toggleCatPlayerUser(uid) {
    const s = String(uid);
    const idx = catPlayerForm.utilisateur_ids.findIndex((x) => String(x) === s);
    if (idx >= 0) catPlayerForm.utilisateur_ids.splice(idx, 1);
    else catPlayerForm.utilisateur_ids.push(s);
  }
  function fixerCategorieModificateurA100() {
    catModMode.value = "set";
    catBaseModificateurPct.value = 100;
    catForm.modificateur_pct = 100;
    erreurCat.value = "";
  }

  const catPlayerEtat = ref({});
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
      const dataEtat = await get(`/api/categories/${catForm.id}/modificateur-joueur?${params.toString()}`);
      catPlayerEtat.value = dataEtat.valeurs || {};
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
    },
  );
  watch(
    () => (catPlayerForm.utilisateur_ids || []).slice().sort().join("|"),
    () => {
      if (catModal.value) void chargerCatPlayerEtat();
    },
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
    Object.assign(catForm, { id: c.id, nom: c.nom, modificateur_pct: c.modificateur_pct });
    catModMode.value = "set";
    catBaseModificateurPct.value = Number(c.modificateur_pct) || 100;
    erreurCat.value = "";
    catPlayerForm.categorie_id = c.id;
    catPlayerForm.utilisateur_ids = [];
    if (isMj.value && mj.mjVueChoix.value && mj.mjVueChoix.value !== "global") {
      catPlayerForm.utilisateur_ids = [String(mj.mjVueChoix.value)];
    } else if (isMj.value && mj.mjVueChoix.value === "global") {
      catPlayerForm.utilisateur_ids = (data.utilisateursListe.value || []).map((u) => String(u.id));
    }
    catPlayerSearch.value = "";
    catModal.value = true;
  }

  function catSelectAllUsers() {
    catPlayerForm.utilisateur_ids = (data.utilisateursListe.value || []).map((u) => String(u.id));
  }
  function catClearAllUsers() {
    catPlayerForm.utilisateur_ids = [];
  }

  const catAllUsersSelected = computed(() => {
    const all = (data.utilisateursListe.value || []).map((u) => String(u.id));
    if (all.length === 0) return false;
    const selected = new Set((catPlayerForm.utilisateur_ids || []).map((x) => String(x)));
    if (selected.size !== all.length) return false;
    for (const id of all) if (!selected.has(id)) return false;
    return true;
  });

  async function sauvegarderCategorie() {
    erreurCat.value = "";
    try {
      if (catForm.id == null) {
        await post("/api/categories", { nom: catForm.nom, modificateur_pct: Number(catForm.modificateur_pct) });
      } else {
        const selected = catPlayerForm.utilisateur_ids || [];
        const input = Number(catForm.modificateur_pct);
        if (selected.length > 0) {
          await put(`/api/categories/${catForm.id}/modificateur-joueur`, {
            utilisateur_ids: selected,
            modificateur_pct: input,
            operation: catModMode.value,
          });
        } else {
          const base = Number(catBaseModificateurPct.value);
          let newPct;
          if (catModMode.value === "set") newPct = input;
          else if (catModMode.value === "add") newPct = base + input;
          else newPct = base - input;
          if (!Number.isFinite(newPct) || newPct <= 0) {
            erreurCat.value = "modificateur_pct doit rester > 0.";
            return;
          }
          await put(`/api/categories/${catForm.id}`, { nom: catForm.nom, modificateur_pct: newPct });
        }
      }
      catModal.value = false;
      await data.chargerCategories();
      await chargerRessources();
    } catch (e) {
      erreurCat.value = e.message;
    }
  }
  async function supprimerCategorie(c) {
    if (!confirm(`Supprimer la catégorie « ${c.nom} » ? (elle sera retirée des ressources)`)) return;
    try {
      await del(`/api/categories/${c.id}`);
      await data.chargerCategories();
      await chargerRessources();
    } catch (e) {
      data.erreur.value = e.message;
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

  return {
    FLORINS_NOM,
    formatFlorin,
    formatFlorinExact,
    formatPct,
    isMj,
    currentUserIdStr,
    ressources: data.ressources,
    categories: data.categories,
    utilisateursListe: data.utilisateursListe,
    erreur: data.erreur,
    recherche,
    filtreCategorieId,
    colonnes,
    ...mj,
    ...list,
    ...bulk,
    // resource modal
    modalVisible,
    modeEdition,
    erreurModal,
    form,
    resModMode,
    previewFacteur,
    preview,
    ouvrirCreation,
    ouvrirEdition,
    sauvegarderRessource,
    supprimerRessource,
    appliquerProduitCategories,
    setCategorieChecked,
    resPlayerSearch,
    resPlayerVisibleJoueurs,
    formUserSelected,
    toggleFormUser,
    resPlayerEtat,
    resPlayerEtatLoading,
    resPlayerEtatErreur,
    resSelectAllUsers,
    resClearAllUsers,
    resAllUsersSelected,
    // category modal
    catModal,
    catForm,
    catModMode,
    erreurCat,
    ouvrirNouvelleCategorie,
    ouvrirEditCategorie,
    supprimerCategorie,
    sauvegarderCategorie,
    fixerCategorieModificateurA100,
    catPlayerSearch,
    catPlayerVisibleJoueurs,
    catPlayerForm,
    catPlayerUserSelected,
    toggleCatPlayerUser,
    catPlayerEtat,
    catPlayerEtatLoading,
    catPlayerEtatErreur,
    catSelectAllUsers,
    catClearAllUsers,
    catAllUsersSelected,
  };
}

