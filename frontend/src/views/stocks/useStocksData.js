import { computed, reactive, ref, watch, proxyRefs } from "vue";
import { useRoute } from "vue-router";
import { useMjView } from "../../composables/useMjView.js";
import {
  FLORINS_NOM,
  formatFlorin,
  formatFlorinExact,
  formatQuantiteRessource,
  useApi,
} from "../../composables/useApi.js";
import { deltaNetProchainTour } from "../../utils/gainPassif.js";
import { persistVoirToutes, readVoirToutesPref } from "./stocksPrefs.js";

/**
 * Chargements, filtres, tri, édition MJ — page Stocks (sans modale commerce).
 */
export function useStocksData(props) {
  const { get, put, post } = useApi();
  const route = useRoute();

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

  const stocks = ref([]);
  const gainsPassifs = ref([]);
  const erreur = ref("");
  const voirToutesLesRessources = ref(readVoirToutesPref());
  const modifEnCours = ref({});
  const sauvegarde = ref(false);

  const isMjOtherView = computed(
    () => isMj.value && mjRaw.mjVueChoix.value && String(mjRaw.mjVueChoix.value) !== currentUserIdStr.value,
  );

  async function chargerUtilisateurs() {
    if (!isMj.value) return;
    try {
      utilisateurs.value = await get("/api/utilisateurs");
    } catch (e) {
      erreur.value = e.message;
    }
  }

  async function chargerStocks() {
    erreur.value = "";
    const uid =
      isMj.value && mjRaw.mjVueChoix.value
        ? `?uid=${encodeURIComponent(String(mjRaw.mjVueChoix.value))}`
        : "";
    try {
      const [s, g] = await Promise.all([get(`/api/stocks${uid}`), get(`/api/gains-passifs${uid}`)]);
      stocks.value = s;
      gainsPassifs.value = g;
      modifEnCours.value = {};
    } catch (e) {
      erreur.value = e.message;
    }
  }

  function syncMjUidFromRoute() {
    if (!isMj.value) return;
    const list = utilisateurs.value;
    if (!list?.length) return;
    const ids = new Set(list.map((u) => String(u.id)));
    const raw = route.query.uid;
    if (raw != null && raw !== "" && ids.has(String(raw))) {
      mjRaw.mjVueSetChoix(String(raw));
    }
  }

  watch(() => mjRaw.mjVueChoix.value, chargerStocks);
  watch([() => utilisateurs.value, () => route.query.uid], syncMjUidFromRoute, { immediate: true });
  watch(voirToutesLesRessources, persistVoirToutes);
  chargerUtilisateurs();
  chargerStocks();

  const gainsParRid = computed(() => {
    const m = {};
    gainsPassifs.value.forEach((g) => {
      if (!m[g.ressource_id]) m[g.ressource_id] = [];
      m[g.ressource_id].push(g);
    });
    return m;
  });

  function getModif(rid) {
    return modifEnCours.value[rid] ?? "";
  }

  function setModif(rid, val) {
    modifEnCours.value[rid] = val;
  }

  function qteAffichee(stock) {
    const m = modifEnCours.value[stock.ressource_id];
    return m !== undefined && m !== "" ? Number(m) : stock.quantite;
  }

  function hasModif(stock) {
    const m = modifEnCours.value[stock.ressource_id];
    return m !== undefined && m !== "" && Number(m) !== stock.quantite;
  }

  async function sauvegarderTout() {
    erreur.value = "";
    sauvegarde.value = true;
    const uidParam =
      isMj.value && mjRaw.mjVueChoix.value
        ? `?uid=${encodeURIComponent(String(mjRaw.mjVueChoix.value))}`
        : "";
    const promesses = stocks.value
      .filter((s) => hasModif(s))
      .map((s) =>
        put(`/api/stocks/${s.ressource_id}${uidParam}`, {
          quantite: Number(modifEnCours.value[s.ressource_id]),
          motif: "ajustement_manuel",
        }),
      );
    try {
      await Promise.all(promesses);
      await chargerStocks();
    } catch (e) {
      erreur.value = e.message;
    } finally {
      sauvegarde.value = false;
    }
  }

  function texteProchainTour(stock) {
    const n = gainTourPourTri(stock);
    if (n === 0) return "0";
    return (n > 0 ? "+" : "") + String(n);
  }

  const nbModifications = computed(() => stocks.value.filter((s) => hasModif(s)).length);

  const sort = reactive({ key: "nom", dir: "asc" });

  const colonnesTri = computed(() => [
    ["nom", "Ressource"],
    ["type", "Type"],
    ["quantite", "Stock actuel"],
    ...(isMj.value ? [["nouvelle_qte", "Nouvelle quantité"]] : []),
    ["gain_tour", "Prod. prochain tour"],
    ["commerce", "Achat / vente"],
    ["valeur", "Valeur stock (ƒ)"],
  ]);

  function gainTourPourTri(stock) {
    const list = gainsParRid.value[stock.ressource_id] || [];
    return deltaNetProchainTour(qteAffichee(stock), list);
  }

  const stockFlorins = computed(() => stocks.value.find((s) => s.ressource.nom === FLORINS_NOM));

  function ressourceVisibleDansVueStocks(stock) {
    if (stock.ressource.nom === FLORINS_NOM) return true;
    return qteAffichee(stock) > 0;
  }

  const stocksFiltres = computed(() => {
    if (voirToutesLesRessources.value) return stocks.value;
    return stocks.value.filter(ressourceVisibleDansVueStocks);
  });

  const nbStocksTotal = computed(() => stocks.value.length);
  const nbStocksFiltres = computed(() => stocksFiltres.value.length);

  const rechercheStocks = ref("");

  function texteRechercheNormalise() {
    return String(rechercheStocks.value ?? "").trim().toLowerCase();
  }

  const stocksFiltresRecherche = computed(() => {
    const q = texteRechercheNormalise();
    if (!q) return stocksFiltres.value;
    return stocksFiltres.value.filter((s) => {
      const nom = (s.ressource.nom || "").toLowerCase();
      const type = (s.ressource.type || "").toLowerCase();
      return nom.includes(q) || type.includes(q);
    });
  });

  const stocksTries = computed(() => {
    const key = sort.key;
    const dir = sort.dir === "asc" ? 1 : -1;
    const sorted = [...stocksFiltresRecherche.value].sort((a, b) => {
      let va;
      let vb;
      switch (key) {
        case "nom":
          va = a.ressource.nom.toLowerCase();
          vb = b.ressource.nom.toLowerCase();
          break;
        case "type":
          va = a.ressource.type;
          vb = b.ressource.type;
          break;
        case "quantite":
          va = a.quantite;
          vb = b.quantite;
          break;
        case "nouvelle_qte":
          va = qteAffichee(a);
          vb = qteAffichee(b);
          break;
        case "gain_tour":
          va = gainTourPourTri(a);
          vb = gainTourPourTri(b);
          break;
        case "commerce":
          va = a.ressource.nom.toLowerCase();
          vb = b.ressource.nom.toLowerCase();
          break;
        case "valeur":
          va = qteAffichee(a) * a.ressource.prix_achat;
          vb = qteAffichee(b) * b.ressource.prix_achat;
          break;
        default:
          va = a.ressource.nom.toLowerCase();
          vb = b.ressource.nom.toLowerCase();
      }
      return va === vb ? 0 : va < vb ? -dir : dir;
    });
    const fi = sorted.findIndex((s) => s.ressource.nom === FLORINS_NOM);
    if (fi > 0) {
      const [row] = sorted.splice(fi, 1);
      sorted.unshift(row);
    }
    return sorted;
  });

  const nbStocksRecherche = computed(() => stocksFiltresRecherche.value.length);

  const aUneRechercheStock = computed(() => texteRechercheNormalise().length > 0);

  function estFlorins(stock) {
    return stock.ressource.nom === FLORINS_NOM;
  }

  function ajusterQuantiteMj(stock, delta) {
    const cur = Number(qteAffichee(stock)) || 0;
    const next = Math.max(0, cur + delta);
    setModif(stock.ressource_id, String(next));
  }

  function affichageStockQuantite(stock) {
    const q = qteAffichee(stock);
    if (estFlorins(stock)) return formatFlorin(q);
    return formatQuantiteRessource(q);
  }

  function titleStockQuantite(stock) {
    if (!estFlorins(stock)) return undefined;
    return formatFlorinExact(qteAffichee(stock)) || undefined;
  }

  function titleValeurStock(stock) {
    const v = qteAffichee(stock) * stock.ressource.prix_achat;
    return formatFlorinExact(v) || undefined;
  }

  function toggleSort(k) {
    if (sort.key === k) {
      sort.dir = sort.dir === "asc" ? "desc" : "asc";
    } else {
      sort.key = k;
      sort.dir = "asc";
    }
  }

  function sortLabel(k) {
    if (sort.key !== k) return "";
    return sort.dir === "asc" ? " ▲" : " ▼";
  }

  /** Objet réactif : dé-référence les refs dans le template (props enfants). */
  return reactive({
    get,
    post,
    put,
    FLORINS_NOM,
    formatFlorin,
    formatFlorinExact,
    isMj,
    currentUserIdStr,
    mjRaw,
    mj,
    stocks,
    erreur,
    voirToutesLesRessources,
    sauvegarde,
    isMjOtherView,
    chargerStocks,
    colonnesTri,
    stocksTries,
    stocksFiltres,
    stockFlorins,
    nbStocksTotal,
    nbStocksFiltres,
    nbStocksRecherche,
    aUneRechercheStock,
    rechercheStocks,
    nbModifications,
    sort,
    getModif,
    setModif,
    hasModif,
    qteAffichee,
    sauvegarderTout,
    texteProchainTour,
    estFlorins,
    ajusterQuantiteMj,
    affichageStockQuantite,
    titleStockQuantite,
    titleValeurStock,
    toggleSort,
    sortLabel,
  });
}
