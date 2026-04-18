import { computed, nextTick, reactive, ref, watch } from "vue";
import { useApi } from "../../composables/useApi.js";
import { textMeansInfinity } from "./toursRestantsInfinity.js";

/**
 * Modale création / édition d’un gain passif (production).
 */
export function useGainPassifModal(deps) {
  const { post, put, del } = useApi();
  const {
    erreur,
    charger,
    ressourceIdFiltre,
    ressourcesListe,
    isMj,
    mjRaw,
    buildProductionsQuery,
    router,
  } = deps;

  const gainModalRef = ref(null);
  const gainFormModal = ref(null);
  const gainForm = reactive({
    ressource_id: null,
    quantite_par_tour: 1,
    balise: "autre",
    mode_production: "fixe",
    actif: true,
    tours_restants: null,
    delai_tours: 0,
  });

  const toursRestantsInput = ref("∞");
  const toursRestantsAideOuverte = ref(false);
  const pourcentageAideOuverte = ref(false);

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

  function ouvrirCreationVide() {
    ouvrirCreation();
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

  watch(gainFormModal, async (m) => {
    if (m) {
      toursRestantsAideOuverte.value = false;
      pourcentageAideOuverte.value = false;
      await nextTick();
      gainModalRef.value?.focusQte?.();
    }
  });

  watch(
    () => gainForm.mode_production,
    (mode) => {
      if (mode !== "pourcentage") pourcentageAideOuverte.value = false;
    },
  );

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

  const nomRessourceForm = computed(() => {
    const id = gainForm.ressource_id;
    if (id == null) return "";
    const r = ressourcesListe.value.find((x) => Number(x.id) === Number(id));
    return r?.nom ?? `Ressource #${id}`;
  });

  /** Sélectionne toute la valeur ; rAF aide certains navigateurs sur `type="number"`. */
  function selectAllInputText(e) {
    const el = e.target;
    requestAnimationFrame(() => {
      if (typeof el.select === "function") el.select();
    });
  }

  function toggleToursAide() {
    toursRestantsAideOuverte.value = !toursRestantsAideOuverte.value;
  }

  function togglePctAide() {
    pourcentageAideOuverte.value = !pourcentageAideOuverte.value;
  }

  return reactive({
    gainModalRef,
    gainFormModal,
    gainForm,
    toursRestantsInput,
    toursRestantsAideOuverte,
    pourcentageAideOuverte,
    ressourceVerrouilleeEnCreation,
    onToursRestantsBlur,
    setToursRestantsRapide,
    setToursRestantsIllimite,
    ouvrirCreationSelonContexte,
    ouvrirAjoutProductionPourRessource,
    ouvrirEditionGain,
    sauvegarderGainForm,
    supprimerGain,
    nomRessourceForm,
    selectAllInputText,
    toggleToursAide,
    togglePctAide,
  });
}
