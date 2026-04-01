import { computed, ref, watch } from "vue";

export function useMjView({ authState, utilisateursListeRef, isMjRef, currentUserIdStrRef }) {
  const STORAGE_KEY = "mj_view_choice";
  function readStoredChoice() {
    try {
      const v = window?.localStorage?.getItem(STORAGE_KEY);
      return v == null || String(v).trim() === "" ? null : String(v);
    } catch {
      return null;
    }
  }
  function writeStoredChoice(v) {
    try {
      window?.localStorage?.setItem(STORAGE_KEY, String(v));
    } catch {
      // ignore (privacy mode, disabled storage, etc.)
    }
  }

  const mjVueChoix = ref(readStoredChoice() ?? "global"); // 'global' ou utilisateur_id
  const mjVueOpen = ref(false);
  const mjVueSearch = ref("");

  const mjVueLabel = computed(() => {
    if (!isMjRef.value) return `Vous — ${authState.user?.username ?? ""}`;
    if (mjVueChoix.value === "global") return "Global (catalogue)";
    const u = (utilisateursListeRef.value || []).find(
      (x) => String(x.id) === String(mjVueChoix.value),
    );
    if (!u) return `Vous voyez : ${mjVueChoix.value}`;
    const isMe = String(u.id) === currentUserIdStrRef.value;
    return isMe
      ? `Vous — ${u.username}${u.is_mj ? " (MJ)" : ""}`
      : `Vous voyez : ${u.username}${u.is_mj ? " (MJ)" : ""}`;
  });

  const mjVueQueryNorm = computed(() => mjVueSearch.value.trim().toLowerCase());
  const mjVueAutres = computed(() => {
    const q = mjVueQueryNorm.value;
    const all = utilisateursListeRef.value || [];
    if (!q) return all;
    return all.filter(
      (u) =>
        String(u.username || "").toLowerCase().includes(q) ||
        String(u.id).includes(q),
    );
  });

  function mjVueSetChoix(val) {
    mjVueChoix.value = val;
    if (isMjRef.value) writeStoredChoice(val);
    mjVueOpen.value = false;
    mjVueSearch.value = "";
  }

  // MJ : restaurer le choix si possible, sinon voir "soi" plutôt que global
  watch(
    () => [isMjRef.value, currentUserIdStrRef.value, (utilisateursListeRef.value || []).length],
    () => {
      if (!isMjRef.value) return;
      const all = utilisateursListeRef.value || [];
      const stored = readStoredChoice();
      if (stored && (stored === "global" || all.some((u) => String(u.id) === String(stored)))) {
        if (mjVueChoix.value !== stored) mjVueChoix.value = stored;
        return;
      }
      if (mjVueChoix.value === "global") {
        const me = all.find((u) => String(u.id) === currentUserIdStrRef.value);
        if (me) {
          mjVueChoix.value = String(me.id);
          writeStoredChoice(String(me.id));
        }
      } else {
        writeStoredChoice(mjVueChoix.value);
      }
    },
  );

  return {
    mjVueChoix,
    mjVueOpen,
    mjVueSearch,
    mjVueLabel,
    mjVueAutres,
    mjVueSetChoix,
  };
}

