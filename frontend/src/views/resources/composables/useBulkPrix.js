import { computed, ref, watch } from "vue";
import { useApi, FLORINS_NOM } from "../../../composables/useApi.js";
import { usePlayerPicker } from "./usePlayerPicker.js";

const BULK_CHART_COLORS = [
  "#a5b4fc",
  "#f472b6",
  "#34d399",
  "#fbbf24",
  "#f87171",
  "#38bdf8",
  "#c084fc",
  "#fb923c",
  "#4ade80",
  "#facc15",
  "#2dd4bf",
  "#e879f9",
];

function pctModCatalogue(r) {
  if (!r) return 100;
  const p = Number(r.modificateur_pct);
  return Number.isFinite(p) && p > 0 ? Math.round(p * 10) / 10 : 100;
}

function calcNewPct(current, delta, mode) {
  let val;
  if (mode === "set") val = delta;
  else if (mode === "add") val = current + delta;
  else val = current - delta;
  return Math.round(val * 10) / 10;
}

export function useBulkPrix({
  isMjRef,
  mjVueChoixRef,
  currentUserIdStrRef,
  utilisateursListeRef,
  ressourcesFiltreesRef,
  ressourcesRef,
  chargerRessources,
}) {
  const { post, get } = useApi();

  const selectedIds = ref([]);
  const bulkModal = ref(false);
  const bulkPct = ref(100);
  const bulkModMode = ref("set");
  const bulkUserIds = ref([]);
  const bulkUserSearch = ref("");
  const bulkErr = ref("");
  const bulkLoading = ref(false);
  const bulkHistoriqueLoading = ref(false);
  const bulkHistoriqueErr = ref("");

  /**
   * Modificateurs effectifs par ressource et par joueur.
   * { resourceId: { uid: { modificateur_pct, prix_achat, ... } } }
   */
  const bulkPlayerMods = ref({});

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

  function libelleJoueur(uid) {
    const u = (utilisateursListeRef.value || []).find((x) => String(x.id) === String(uid));
    if (u && String(u.id) === String(currentUserIdStrRef.value)) return `Vous — ${u.username}`;
    if (u) return u.username;
    return `Joueur ${uid}`;
  }

  // ── Chargement des modificateurs joueurs ─────────────────────────────────
  async function chargerPlayerMods(ids, uids) {
    if (ids.length === 0) { bulkPlayerMods.value = {}; return; }
    if (uids.length === 0) { bulkPlayerMods.value = {}; return; }
    const uidQs = uids.map((u) => `utilisateur_ids=${encodeURIComponent(String(u))}`).join("&");
    const results = await Promise.allSettled(
      ids.map((id) => get(`/api/ressources/${id}/modificateur-joueur?${uidQs}`)),
    );
    const mods = {};
    ids.forEach((id, i) => {
      const res = results[i];
      mods[Number(id)] =
        res.status === "fulfilled" && res.value?.valeurs ? res.value.valeurs : {};
    });
    bulkPlayerMods.value = mods;
  }

  async function chargerBulkData() {
    bulkHistoriqueErr.value = "";
    const ids = [...selectedIds.value];
    const uids = bulkUserIds.value || [];
    if (ids.length === 0) { bulkPlayerMods.value = {}; return; }
    bulkHistoriqueLoading.value = true;
    try {
      await chargerPlayerMods(ids, uids);
    } catch (e) {
      bulkHistoriqueErr.value = e.message;
    } finally {
      bulkHistoriqueLoading.value = false;
    }
  }

  // Re-charger quand la modale s'ouvre ou que les ressources sélectionnées changent.
  watch(
    () => ({ open: bulkModal.value, ids: [...selectedIds.value].sort((a, b) => a - b).join(",") }),
    ({ open }) => { if (!open) return; void chargerBulkData(); },
  );

  // Re-charger quand la sélection de joueurs change (modale ouverte).
  watch(
    () => (bulkUserIds.value || []).slice().sort().join(","),
    async (cur, prev) => {
      if (cur === prev || !bulkModal.value) return;
      const ids = [...selectedIds.value];
      const uids = bulkUserIds.value || [];
      bulkHistoriqueLoading.value = true;
      try {
        await chargerPlayerMods(ids, uids);
      } finally {
        bulkHistoriqueLoading.value = false;
      }
    },
  );

  // ── Panneaux d'aperçu ─────────────────────────────────────────────────────
  /**
   * Un panneau par ressource sélectionnée.
   * Chaque panneau : { key, title, players: [{ key, nom, color, currentPct, newPct, isDefault, invalid }] }
   */
  const bulkPreviewPanels = computed(() => {
    const ids = selectedIds.value;
    const uids = bulkUserIds.value || [];
    const liste = ressourcesRef?.value || [];
    const delta = Number(bulkPct.value) || 0;
    const mode = bulkModMode.value;

    return ids.map((id) => {
      const r = liste.find((x) => Number(x.id) === Number(id));
      const catalogueMod = pctModCatalogue(r);
      const nom = r?.nom ?? `Ressource #${id}`;

      if (uids.length === 0) {
        const newPct = calcNewPct(catalogueMod, delta, mode);
        return {
          key: `r-${id}`,
          title: nom,
          players: [{
            key: `r-${id}-catalog`,
            nom: "Catalogue global",
            color: BULK_CHART_COLORS[0],
            currentPct: catalogueMod,
            newPct,
            isDefault: false,
            invalid: newPct <= 0,
          }],
        };
      }

      const ressourceMods = bulkPlayerMods.value[Number(id)] || {};
      return {
        key: `r-${id}`,
        title: nom,
        players: uids.map((uid, i) => {
          const playerData = ressourceMods[String(uid)] ?? null;
          const currentPct =
            playerData?.modificateur_pct != null
              ? Math.round(Number(playerData.modificateur_pct) * 10) / 10
              : 100;
          const newPct = calcNewPct(currentPct, delta, mode);
          return {
            key: `r-${id}-u-${uid}`,
            nom: libelleJoueur(uid),
            color: BULK_CHART_COLORS[i % BULK_CHART_COLORS.length],
            currentPct,
            newPct,
            isDefault: playerData == null,
            invalid: newPct <= 0,
          };
        }),
      };
    });
  });

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
    bulkHistoriqueLoading,
    bulkHistoriqueErr,
    bulkPreviewPanels,
  };
}
