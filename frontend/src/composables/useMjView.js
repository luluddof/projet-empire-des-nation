import { computed, ref, watch } from "vue";

export function useMjView({
  authState,
  utilisateursListeRef,
  isMjRef,
  currentUserIdStrRef,
  allowGlobal = true,
  storageKey = "mj_view_choice",
}) {
  const STORAGE_KEY = storageKey;
  function readStoredChoice() {
    try {
      const v = window?.localStorage?.getItem(STORAGE_KEY);
      const s = v == null || String(v).trim() === "" ? null : String(v);
      if (!allowGlobal && s === "global") return null;
      return s;
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

  // Par défaut : toujours "vous". Global est un choix explicite.
  const mjVueChoix = ref(readStoredChoice() ?? String(authState.user?.id ?? ""));
  const mjVueOpen = ref(false);
  const mjVueSearch = ref("");

  const mjVueLabel = computed(() => {
    if (!isMjRef.value) return `Vous — ${authState.user?.username ?? ""}`;
    if (allowGlobal && mjVueChoix.value === "global") return "Global (catalogue)";
    const u = (utilisateursListeRef.value || []).find((x) => String(x.id) === String(mjVueChoix.value));
    if (!u) return `Vous voyez : ${mjVueChoix.value}`;
    const isMe = String(u.id) === currentUserIdStrRef.value;
    return isMe ? `Vous — ${u.username}${u.is_mj ? " (MJ)" : ""}` : `Vous voyez : ${u.username}${u.is_mj ? " (MJ)" : ""}`;
  });

  const mjVueQueryNorm = computed(() => mjVueSearch.value.trim().toLowerCase());
  const mjVueAutres = computed(() => {
    const q = mjVueQueryNorm.value;
    const all = utilisateursListeRef.value || [];
    if (!q) return all;
    return all.filter(
      (u) => String(u.username || "").toLowerCase().includes(q) || String(u.id).includes(q),
    );
  });

  function mjVueSetChoix(val) {
    const next = String(val);
    if (!allowGlobal && next === "global") return;
    mjVueChoix.value = allowGlobal ? val : next;
    if (isMjRef.value) writeStoredChoice(mjVueChoix.value);
    mjVueOpen.value = false;
    mjVueSearch.value = "";
  }

  watch(
    () => [isMjRef.value, currentUserIdStrRef.value, (utilisateursListeRef.value || []).length, allowGlobal],
    () => {
      if (!isMjRef.value) return;
      const all = utilisateursListeRef.value || [];

      // Si "global" est stocké/présent mais que cette page ne le propose pas,
      // on doit retomber sur "vous" (sans attendre la liste utilisateurs).
      const meId = currentUserIdStrRef.value || String(authState.user?.id ?? "");
      const cur = String(mjVueChoix.value ?? "");
      if (!allowGlobal && cur === "global" && meId) {
        mjVueChoix.value = String(meId);
      }

      const stored = readStoredChoice();
      if (!allowGlobal && stored === "global" && meId) {
        mjVueChoix.value = String(meId);
        return;
      }
      if (stored && (stored === "global" ? allowGlobal : all.some((u) => String(u.id) === String(stored)))) {
        if (mjVueChoix.value !== stored) mjVueChoix.value = stored;
        return;
      }

      const curIsValid =
        (allowGlobal && cur === "global") || all.some((u) => String(u.id) === String(cur));
      if (curIsValid) {
        writeStoredChoice(cur);
        return;
      }

      if (meId) {
        // On privilégie toujours le compte connecté, même si la liste n'est pas encore chargée.
        mjVueChoix.value = String(meId);
        writeStoredChoice(String(meId));
      } else if (all.length > 0) {
        mjVueChoix.value = String(all[0].id);
        writeStoredChoice(String(all[0].id));
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

