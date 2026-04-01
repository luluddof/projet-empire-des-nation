import { computed } from "vue";

export function usePlayerPicker({
  utilisateursListeRef,
  currentUserIdStrRef,
  selectedIdsRef, // array-like ref (strings or ids)
  searchRef,
}) {
  const searchNorm = computed(() => String(searchRef.value || "").trim().toLowerCase());
  const selectedSet = computed(() => new Set((selectedIdsRef.value || []).map(String)));

  const searchResults = computed(() => {
    const q = searchNorm.value;
    const all = utilisateursListeRef.value || [];
    if (!q) return all;
    return all.filter(
      (u) =>
        String(u.username || "").toLowerCase().includes(q) ||
        String(u.id).includes(q),
    );
  });

  // Règles UX :
  // - si recherche : les sélectionnés restent visibles (en fin de liste)
  // - utilisateur courant en premier
  const visible = computed(() => {
    const q = searchNorm.value;
    const selected = selectedSet.value;
    const listPourRecherche = q ? searchResults.value : utilisateursListeRef.value || [];

    let resultsSansSelection = listPourRecherche.filter((u) => !selected.has(String(u.id)));
    const selectedExtras = (utilisateursListeRef.value || []).filter((u) =>
      selected.has(String(u.id)),
    );

    const uid = currentUserIdStrRef.value;
    if (uid) {
      const cur = (utilisateursListeRef.value || []).find((u) => String(u.id) === uid);
      if (cur && !selected.has(String(cur.id))) {
        const alreadyPresent = resultsSansSelection.some((u) => String(u.id) === uid);
        if (!alreadyPresent) resultsSansSelection = [cur, ...resultsSansSelection];
      }
    }

    const combined = [...resultsSansSelection, ...selectedExtras];
    if (uid) {
      const cur = combined.find((u) => String(u.id) === uid);
      if (cur) return [cur, ...combined.filter((u) => String(u.id) !== uid)];
    }
    return combined;
  });

  return { visible, searchNorm, selectedSet, searchResults };
}

