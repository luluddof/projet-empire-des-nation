import { computed, reactive, ref, watch } from "vue";
import { useApi } from "../../composables/useApi.js";

/**
 * État et actions page MJ « Évènements » — séparé de la présentation (SRP).
 */
export function useEvenementsMj(getAuthState) {
  const { get, post, put, del } = useApi();

  const erreur = ref("");
  const evenements = ref([]);
  const ressources = ref([]);
  const categories = ref([]);
  const utilisateurs = ref([]);
  /** Formulaire visible (création / édition) — sinon liste + bouton « Créer ». */
  const showForm = ref(false);

  const previewData = ref(null);
  const previewLoading = ref(false);
  const previewErreur = ref("");
  let previewTimer = null;

  const isMj = computed(() => !!getAuthState()?.user?.is_mj);
  const currentUserIdStr = computed(() => String(getAuthState()?.user?.id ?? ""));

  const form = reactive({
    id: null,
    titre: "",
    description: "",
    actif: true,
    brouillon: true,
    /** Synchronisé depuis l’API : après première publication, plus de switch brouillon. */
    deja_publie: false,
    cible_utilisateur_ids: [],
    delai_tours: 0,
    tours_restants: null,
    tours_restants_illimite: true,
    impacts: {
      categories: [],
      ressources: [],
      productions: [],
    },
  });

  function resetForm() {
    form.id = null;
    form.titre = "";
    form.description = "";
    form.actif = true;
    form.brouillon = true;
    form.deja_publie = false;
    form.cible_utilisateur_ids = [];
    form.delai_tours = 0;
    form.tours_restants = null;
    form.tours_restants_illimite = true;
    form.impacts = { categories: [], ressources: [], productions: [] };
  }

  async function chargerRef() {
    const [r, c, u] = await Promise.all([
      get("/api/ressources?global=1"),
      get("/api/categories"),
      get("/api/utilisateurs"),
    ]);
    ressources.value = r || [];
    categories.value = c || [];
    utilisateurs.value = u || [];
  }

  function openCreate() {
    resetForm();
    showForm.value = true;
  }

  function cancelForm() {
    resetForm();
    showForm.value = false;
  }

  async function chargerEvenements() {
    erreur.value = "";
    try {
      const res = await get("/api/evenements");
      evenements.value = res?.evenements || [];
    } catch (e) {
      erreur.value = e.message;
    }
  }

  function startEdit(e) {
    form.id = e.id;
    form.titre = e.titre || "";
    form.description = e.description || "";
    form.actif = !!e.actif;
    form.brouillon = !!e.brouillon;
    form.deja_publie = !!e.deja_publie;
    const c = String(e.cible || "aucun").trim().toLowerCase();
    if (c === "tous") {
      form.cible_utilisateur_ids = utilisateurs.value.filter((x) => !x.is_mj).map((x) => x.id);
    } else if (c === "joueurs") {
      form.cible_utilisateur_ids = [...(e.cible_utilisateur_ids || [])];
    } else {
      form.cible_utilisateur_ids = [];
    }
    form.delai_tours = e.delai_tours ?? 0;
    const tr = e.tours_restants;
    form.tours_restants_illimite = tr == null;
    form.tours_restants = tr == null ? null : tr;
    form.impacts = {
      categories: (e.impacts?.categories || []).map((x) => ({
        categorie_id: x.categorie_id,
        operation: x.operation === "set" ? "add" : x.operation || "add",
        valeur_pct: x.valeur_pct ?? 0,
      })),
      ressources: (e.impacts?.ressources || []).map((x) => ({
        ressource_id: x.ressource_id,
        operation: x.operation === "set" ? "add" : x.operation || "add",
        valeur_pct: x.valeur_pct ?? 0,
      })),
      productions: (e.impacts?.productions || []).map((x) => ({
        utilisateur_id: "",
        ressource_id: x.ressource_id,
        quantite_par_tour: x.quantite_par_tour ?? 0,
        mode_production: x.mode_production || "fixe",
        delai_tours: x.delai_tours ?? 0,
        tours_restants: x.tours_restants ?? null,
        actif: x.actif ?? true,
      })),
    };
    showForm.value = true;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function toggleJoueur(uid) {
    const s = new Set(form.cible_utilisateur_ids.map(String));
    const k = String(uid);
    if (s.has(k)) s.delete(k);
    else s.add(k);
    form.cible_utilisateur_ids = Array.from(s);
  }

  function addImpactCategorie() {
    form.impacts.categories.push({ categorie_id: null, operation: "add", valeur_pct: 0 });
  }
  function addImpactRessource() {
    form.impacts.ressources.push({ ressource_id: null, operation: "add", valeur_pct: 0 });
  }
  function addImpactProduction() {
    form.impacts.productions.push({
      utilisateur_id: "",
      ressource_id: null,
      quantite_par_tour: 0,
      mode_production: "fixe",
      delai_tours: 0,
      tours_restants: null,
      actif: true,
    });
  }

  function cleanPayload() {
    const tr = form.tours_restants_illimite ? null : form.tours_restants;
    const ids = (form.cible_utilisateur_ids || []).map((x) => String(x));
    const cible = ids.length === 0 ? "aucun" : "joueurs";
    const out = {
      titre: form.titre,
      description: form.description,
      actif: form.actif,
      brouillon: form.brouillon,
      cible,
      cible_utilisateur_ids: cible === "joueurs" ? ids : [],
      delai_tours: Number(form.delai_tours) || 0,
      tours_restants: tr,
      impacts: JSON.parse(JSON.stringify(form.impacts)),
    };
    out.impacts.categories = (out.impacts.categories || [])
      .filter((x) => x.categorie_id != null)
      .map((x) => ({ ...x, operation: x.operation === "set" ? "add" : x.operation }));
    out.impacts.ressources = (out.impacts.ressources || [])
      .filter((x) => x.ressource_id != null)
      .map((x) => ({ ...x, operation: x.operation === "set" ? "add" : x.operation }));
    out.impacts.productions = (out.impacts.productions || []).filter((x) => x.ressource_id != null);
    for (const p of out.impacts.productions) {
      const u = String(p.utilisateur_id || "").trim();
      p.utilisateur_id = u === "" ? null : u;
    }
    return out;
  }

  async function runPreview() {
    if (!isMj.value || !showForm.value) return;
    previewLoading.value = true;
    previewErreur.value = "";
    try {
      const body = { ...cleanPayload(), evenement_id: form.id || null };
      previewData.value = await post("/api/evenements/preview-impacts", body);
    } catch (e) {
      previewErreur.value = e.message;
      previewData.value = null;
    } finally {
      previewLoading.value = false;
    }
  }

  function schedulePreview() {
    if (!showForm.value) {
      previewData.value = null;
      previewErreur.value = "";
      return;
    }
    clearTimeout(previewTimer);
    previewTimer = setTimeout(() => {
      runPreview();
    }, 450);
  }

  watch(showForm, (v) => {
    if (!v) {
      previewData.value = null;
      previewErreur.value = "";
      clearTimeout(previewTimer);
    } else {
      schedulePreview();
    }
  });

  watch(
    () => ({
      ids: form.cible_utilisateur_ids.slice(),
      brouillon: form.brouillon,
      actif: form.actif,
      delai: form.delai_tours,
      trIllim: form.tours_restants_illimite,
      tr: form.tours_restants,
      impactsJson: JSON.stringify({
        c: form.impacts.categories,
        r: form.impacts.ressources,
        p: form.impacts.productions,
      }),
    }),
    () => {
      if (showForm.value) schedulePreview();
    },
    { deep: true },
  );

  async function save() {
    erreur.value = "";
    if (!isMj.value) return;
    const payload = cleanPayload();
    try {
      if (form.id) await put(`/api/evenements/${form.id}`, payload);
      else await post("/api/evenements", payload);
      resetForm();
      showForm.value = false;
      await chargerEvenements();
    } catch (e) {
      erreur.value = e.message;
    }
  }

  async function supprimer(e) {
    if (!confirm(`Supprimer l'évènement « ${e.titre} » ?`)) return;
    erreur.value = "";
    try {
      await del(`/api/evenements/${e.id}`);
      await chargerEvenements();
    } catch (er) {
      erreur.value = er.message;
    }
  }

  async function retirerJoueur(evenementId, uid) {
    if (!confirm("Retirer ce joueur de l'évènement (supprime ses productions liées) ?")) return;
    erreur.value = "";
    try {
      await put(`/api/evenements/${evenementId}/joueurs/${uid}`, { actif: false });
      await chargerEvenements();
    } catch (er) {
      erreur.value = er.message;
    }
  }

  async function init() {
    await Promise.all([chargerRef(), chargerEvenements()]);
  }

  return reactive({
    erreur,
    evenements,
    ressources,
    categories,
    utilisateurs,
    form,
    showForm,
    previewData,
    previewLoading,
    previewErreur,
    currentUserIdStr,
    isMj,
    openCreate,
    cancelForm,
    resetForm,
    startEdit,
    toggleJoueur,
    addImpactCategorie,
    addImpactRessource,
    addImpactProduction,
    save,
    supprimer,
    retirerJoueur,
    init,
  });
}
