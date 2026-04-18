import { computed, nextTick, reactive, ref, watch } from "vue";
import { playCashSound } from "../../utils/playCashSound.js";

/**
 * Modale achat / vente (commerce) — isolée du reste de la page Stocks.
 */
export function useStocksCommerce(deps) {
  const { get, post, isMj, mjRaw, chargerStocks, isMjOtherView, estFlorins, commerceModalRef } = deps;

  const commerceModal = ref(null);
  const commerceQte = ref(1);
  const commerceAchatMode = ref("local");
  const commerceErr = ref("");
  const commerceLoading = ref(false);
  const historiquePrix = ref([]);

  function ouvrirCommerce(stock, sens) {
    commerceModal.value = { stock, sens };
    commerceQte.value = 1;
    commerceAchatMode.value = "local";
    commerceErr.value = "";
  }

  const commercePrixUnitaire = computed(() => {
    if (!commerceModal.value) return 0;
    const r = commerceModal.value.stock.ressource;
    if (commerceModal.value.sens === "vente") return r.prix_modifie;
    return commerceAchatMode.value === "lointain" ? r.prix_lointain : r.prix_achat;
  });

  const commerceTotal = computed(() => {
    if (!commerceModal.value) return 0;
    const q = Math.max(0, Math.floor(Number(commerceQte.value) || 0));
    return q * (Number(commercePrixUnitaire.value) || 0);
  });

  async function executerCommerce() {
    if (!commerceModal.value) return;
    if (isMjOtherView.value) {
      commerceErr.value =
        "Achat / vente indisponible pour un autre joueur : utilisez la colonne des quantités et Sauvegarder.";
      return;
    }
    commerceErr.value = "";
    const q = Math.floor(Number(commerceQte.value) || 0);
    if (q <= 0) {
      commerceErr.value = "Indiquez une quantité entière positive.";
      return;
    }
    const uidParam =
      isMj.value && mjRaw.mjVueChoix.value
        ? `?uid=${encodeURIComponent(String(mjRaw.mjVueChoix.value))}`
        : "";
    commerceLoading.value = true;
    try {
      const payload = {
        ressource_id: commerceModal.value.stock.ressource_id,
        quantite: q,
        sens: commerceModal.value.sens,
      };
      if (commerceModal.value.sens === "achat") {
        payload.achat_mode = commerceAchatMode.value;
      }
      await post(`/api/stocks/commerce${uidParam}`, payload);
      playCashSound();
      commerceModal.value = null;
      await chargerStocks();
    } catch (e) {
      commerceErr.value = e.message;
    } finally {
      commerceLoading.value = false;
    }
  }

  watch(commerceModal, async (m) => {
    if (!m || estFlorins(m.stock)) {
      historiquePrix.value = [];
    } else {
      try {
        historiquePrix.value = await get(`/api/ressources/${m.stock.ressource_id}/historique-prix?limit=80`);
      } catch {
        historiquePrix.value = [];
      }
    }
    if (m) {
      await nextTick();
      commerceModalRef?.value?.focusQte?.();
    }
  });

  return reactive({
    commerceModal,
    commerceQte,
    commerceAchatMode,
    commerceErr,
    commerceLoading,
    historiquePrix,
    ouvrirCommerce,
    commercePrixUnitaire,
    commerceTotal,
    executerCommerce,
  });
}
