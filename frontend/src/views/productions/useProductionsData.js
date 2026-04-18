import { computed, reactive, ref, watch, proxyRefs } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useMjView } from "../../composables/useMjView.js";
import { useApi } from "../../composables/useApi.js";

/**
 * Données, route, tri, chargements API — page Productions (sans modale gain).
 */
export function useProductionsData(props) {
  const { get } = useApi();
  const route = useRoute();
  const router = useRouter();

  const isMj = computed(() => props.authState.user?.is_mj);
  const currentUserIdStr = computed(() => String(props.authState.user?.id ?? ""));

  const utilisateurs = ref([]);
  const mjRaw = useMjView({
    authState: props.authState,
    utilisateursListeRef: utilisateurs,
    isMjRef: isMj,
    currentUserIdStrRef: currentUserIdStr,
    allowGlobal: false,
    storageKey: "mj_view_choice_uid",
  });
  const mj = proxyRefs(mjRaw);
  const gainsPassifs = ref([]);
  const ressourcesListe = ref([]);
  const balisesDisponibles = ref([]);
  const chronologie = ref(null);
  const erreur = ref("");

  const sort = reactive({ key: "nom", dir: "asc" });

  const ressourceIdFiltre = computed(() => {
    const q = route.query.ressource;
    if (q == null || q === "") return null;
    const n = Number(q);
    return Number.isNaN(n) ? null : n;
  });

  const nomRessourceFiltre = computed(() => {
    if (!ressourceIdFiltre.value) return "";
    const r = ressourcesListe.value.find((x) => x.id === ressourceIdFiltre.value);
    return r?.nom ?? chronologie.value?.ressource?.nom ?? "";
  });

  function buildProductionsQuery({ ressource } = {}) {
    const q = {};
    if (ressource != null && ressource !== "") q.ressource = String(ressource);
    if (isMj.value && mjRaw.mjVueChoix.value) {
      q.uid = String(mjRaw.mjVueChoix.value);
    }
    return q;
  }

  const productionsQueryAll = computed(() => buildProductionsQuery({}));

  async function chargerUtilisateurs() {
    if (!isMj.value) return;
    try {
      utilisateurs.value = await get("/api/utilisateurs");
    } catch (e) {
      erreur.value = e.message;
    }
  }

  async function chargerChronologie() {
    const rid = ressourceIdFiltre.value;
    if (!rid) {
      chronologie.value = null;
      return;
    }
    const uidParam =
      isMj.value && mjRaw.mjVueChoix.value
        ? `&uid=${encodeURIComponent(String(mjRaw.mjVueChoix.value))}`
        : "";
    try {
      chronologie.value = await get(`/api/gains-passifs/chronologie?ressource_id=${rid}${uidParam}`);
    } catch (e) {
      erreur.value = e.message;
      chronologie.value = null;
    }
  }

  async function charger() {
    erreur.value = "";
    const uid =
      isMj.value && mjRaw.mjVueChoix.value
        ? `?uid=${encodeURIComponent(String(mjRaw.mjVueChoix.value))}`
        : "";
    const qRes = isMj.value ? "?global=1" : "";
    try {
      const [g, r, balises] = await Promise.all([
        get(`/api/gains-passifs${uid}`),
        get(`/api/ressources${qRes}`),
        get("/api/gains-passifs/balises"),
      ]);
      gainsPassifs.value = g;
      ressourcesListe.value = r || [];
      balisesDisponibles.value = balises || [];
    } catch (e) {
      erreur.value = e.message;
    }
    await chargerChronologie();
  }

  function libelleBalise(b) {
    const map = new Map((balisesDisponibles.value || []).map((x) => [x.id, x.label]));
    return map.get(b) ?? map.get("autre") ?? b ?? "—";
  }

  const balisesFormulaireProduction = computed(() =>
    (balisesDisponibles.value || []).filter((b) => b.id !== "recolte_fructueuse"),
  );

  watch(() => mjRaw.mjVueChoix.value, charger);
  watch(
    () => route.query.ressource,
    () => charger(),
  );

  watch(utilisateurs, (list) => {
    if (!isMj.value || !list?.length) return;
    const ids = new Set(list.map((u) => String(u.id)));
    const fromRoute =
      route.query.uid != null && route.query.uid !== "" ? String(route.query.uid) : null;
    if (fromRoute && ids.has(fromRoute)) {
      mjRaw.mjVueSetChoix(fromRoute);
      return;
    }
    const cur = String(mjRaw.mjVueChoix.value ?? "");
    if (!cur || !ids.has(cur)) {
      const me = props.authState.user?.id;
      if (me != null && ids.has(String(me))) {
        mjRaw.mjVueSetChoix(String(me));
      } else {
        mjRaw.mjVueSetChoix(String(list[0].id));
      }
    }
  });

  watch(
    () => route.query.uid,
    () => {
      const list = utilisateurs.value;
      if (!isMj.value || !list?.length) return;
      const ids = new Set(list.map((u) => String(u.id)));
      const fromRoute =
        route.query.uid != null && route.query.uid !== "" ? String(route.query.uid) : null;
      if (fromRoute && ids.has(fromRoute)) {
        mjRaw.mjVueSetChoix(fromRoute);
      }
    },
  );

  chargerUtilisateurs();
  charger();

  const gainsFiltres = computed(() => {
    const id = ressourceIdFiltre.value;
    if (id == null) return gainsPassifs.value;
    return gainsPassifs.value.filter((g) => Number(g.ressource_id) === Number(id));
  });

  const gainsTries = computed(() => {
    const dir = sort.dir === "asc" ? 1 : -1;
    const list = [...gainsFiltres.value];
    return list.sort((a, b) => {
      let va;
      let vb;
      switch (sort.key) {
        case "nom":
          va = (a.ressource?.nom ?? "").toLowerCase();
          vb = (b.ressource?.nom ?? "").toLowerCase();
          break;
        case "qte":
          va = a.quantite_par_tour;
          vb = b.quantite_par_tour;
          break;
        case "balise":
          va = (a.balise || "autre").toLowerCase();
          vb = (b.balise || "autre").toLowerCase();
          break;
        case "actif":
          va = a.actif ? 1 : 0;
          vb = b.actif ? 1 : 0;
          break;
        case "duree":
          va = a.definitif ? 1e9 : a.tours_restants ?? 0;
          vb = b.definitif ? 1e9 : b.tours_restants ?? 0;
          break;
        default:
          va = (a.ressource?.nom ?? "").toLowerCase();
          vb = (b.ressource?.nom ?? "").toLowerCase();
      }
      return va === vb ? 0 : va < vb ? -dir : dir;
    });
  });

  const productionsParRessource = computed(() => {
    const m = new Map();
    for (const g of gainsPassifs.value || []) {
      const rid = Number(g.ressource_id);
      if (!m.has(rid)) {
        m.set(rid, { ressource_id: rid, ressource: g.ressource, gains: [] });
      }
      m.get(rid).gains.push(g);
    }
    const out = Array.from(m.values());
    out.sort((a, b) => (a.ressource?.nom ?? "").localeCompare(b.ressource?.nom ?? "", "fr"));
    for (const x of out) {
      x.gains.sort((a, b) => (a.id ?? 0) - (b.id ?? 0));
    }
    return out;
  });

  function ouvrirDetailRessource(rid) {
    if (!rid) return;
    router.push({ path: "/productions", query: buildProductionsQuery({ ressource: rid }) });
  }

  function toggleSort(k) {
    if (sort.key === k) sort.dir = sort.dir === "asc" ? "desc" : "asc";
    else {
      sort.key = k;
      sort.dir = "asc";
    }
  }

  function sortLabel(k) {
    if (sort.key !== k) return "";
    return sort.dir === "asc" ? " ▲" : " ▼";
  }

  /** reactive : dé-référence les refs dans le template (props enfants). */
  return reactive({
    isMj,
    currentUserIdStr,
    utilisateurs,
    mjRaw,
    mj,
    gainsPassifs,
    ressourcesListe,
    balisesDisponibles,
    chronologie,
    erreur,
    sort,
    ressourceIdFiltre,
    nomRessourceFiltre,
    productionsQueryAll,
    buildProductionsQuery,
    router,
    route,
    charger,
    libelleBalise,
    balisesFormulaireProduction,
    gainsFiltres,
    gainsTries,
    productionsParRessource,
    ouvrirDetailRessource,
    toggleSort,
    sortLabel,
  });
}
