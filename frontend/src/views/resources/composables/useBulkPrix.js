import { computed, ref, watch } from "vue";
import { useApi, FLORINS_NOM } from "../../../composables/useApi.js";
import { usePlayerPicker } from "./usePlayerPicker.js";

export function useBulkPrix({
  isMjRef,
  mjVueChoixRef,
  currentUserIdStrRef,
  utilisateursListeRef,
  ressourcesFiltreesRef,
  chargerRessources,
}) {
  const { post } = useApi();

  const selectedIds = ref([]);
  const bulkModal = ref(false);
  const bulkPct = ref(100);
  const bulkModMode = ref("set");
  const bulkUserIds = ref([]);
  const bulkUserSearch = ref("");
  const bulkErr = ref("");
  const bulkLoading = ref(false);

  function idSelectionne(id) {
    return selectedIds.value.includes(id);
  }
  function toggleSelection(id) {
    if (idSelectionne(id)) selectedIds.value = selectedIds.value.filter((x) => x !== id);
    else selectedIds.value = [...selectedIds.value, id];
  }
  function selectionnerToutListe(liste) {
    const ids = (liste || []).filter((r) => r.nom !== FLORINS_NOM).map((r) => r.id);
    const set = new Set([...selectedIds.value, ...ids]);
    selectedIds.value = [...set];
  }
  function selectionnerVueFiltre() {
    const ids = (ressourcesFiltreesRef.value || [])
      .filter((r) => r.nom !== FLORINS_NOM)
      .map((r) => r.id);
    selectedIds.value = [...new Set(ids)];
  }
  function viderSelection() {
    selectedIds.value = [];
  }

  function toggleBulkUser(uid) {
    const s = String(uid);
    const i = bulkUserIds.value.indexOf(s);
    if (i >= 0) bulkUserIds.value.splice(i, 1);
    else bulkUserIds.value.push(s);
  }
  function bulkUserSelected(uid) {
    return bulkUserIds.value.includes(String(uid));
  }

  function bulkSelectAllUsers() {
    bulkUserIds.value = (utilisateursListeRef.value || []).map((u) => String(u.id));
  }
  function bulkClearAllUsers() {
    bulkUserIds.value = [];
  }

  const bulkAllUsersSelected = computed(() => {
    const all = (utilisateursListeRef.value || []).map((u) => String(u.id));
    if (all.length === 0) return false;
    const selected = new Set((bulkUserIds.value || []).map((x) => String(x)));
    if (selected.size !== all.length) return false;
    for (const id of all) if (!selected.has(id)) return false;
    return true;
  });

  const picker = usePlayerPicker({
    utilisateursListeRef,
    currentUserIdStrRef,
    selectedIdsRef: bulkUserIds,
    searchRef: bulkUserSearch,
  });

  watch(
    () => bulkModal.value,
    (open) => {
      if (!open) return;
      if (isMjRef.value && mjVueChoixRef.value !== "global" && String(mjVueChoixRef.value).trim() !== "") {
        bulkUserIds.value = [String(mjVueChoixRef.value)];
      } else if (isMjRef.value && mjVueChoixRef.value === "global") {
        bulkUserIds.value = (utilisateursListeRef.value || []).map((u) => String(u.id));
      } else {
        bulkUserIds.value = [];
      }
      bulkUserSearch.value = "";
      bulkErr.value = "";
      bulkLoading.value = false;
      bulkModMode.value = "set";
    },
  );

  async function appliquerBulkPrix() {
    bulkErr.value = "";
    if (selectedIds.value.length === 0) {
      bulkErr.value = "Sélectionnez au moins une ressource.";
      return;
    }
    bulkLoading.value = true;
    try {
      const cible = bulkUserIds.value.length > 0 ? "joueurs" : "tous";
      await post("/api/ressources/bulk-prix-marche", {
        ids: selectedIds.value,
        modificateur_pct: Number(bulkPct.value),
        operation: bulkModMode.value,
        cible_modificateur: cible,
        utilisateur_ids: cible === "joueurs" ? [...bulkUserIds.value] : [],
      });
      bulkModal.value = false;
      await chargerRessources();
    } catch (e) {
      bulkErr.value = e.message;
    } finally {
      bulkLoading.value = false;
    }
  }

  const bulkUserVisibleJoueurs = computed(() => picker.visible.value);

  return {
    selectedIds,
    bulkModal,
    bulkPct,
    bulkModMode,
    bulkUserIds,
    bulkUserSearch,
    bulkErr,
    bulkLoading,
    idSelectionne,
    toggleSelection,
    selectionnerToutListe,
    selectionnerVueFiltre,
    viderSelection,
    toggleBulkUser,
    bulkUserSelected,
    bulkUserVisibleJoueurs,
    bulkSelectAllUsers,
    bulkClearAllUsers,
    bulkAllUsersSelected,
    appliquerBulkPrix,
  };
}

