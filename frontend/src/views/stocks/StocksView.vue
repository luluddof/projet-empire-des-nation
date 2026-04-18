<script setup>
import { ref, toRef } from "vue";
import StocksPageHeader from "./StocksPageHeader.vue";
import StocksToolbar from "./StocksToolbar.vue";
import StocksTable from "./StocksTable.vue";
import StocksCommerceModal from "./StocksCommerceModal.vue";
import { useStocksData } from "./useStocksData.js";
import { useStocksCommerce } from "./useStocksCommerce.js";

const props = defineProps({
  authState: { type: Object, required: true },
});

const page = useStocksData(props);
const commerceModalRef = ref(null);
const commerce = useStocksCommerce({
  get: page.get,
  post: page.post,
  isMj: toRef(page, "isMj"),
  mjRaw: page.mjRaw,
  chargerStocks: page.chargerStocks,
  isMjOtherView: toRef(page, "isMjOtherView"),
  estFlorins: page.estFlorins,
  commerceModalRef,
});
</script>

<template>
  <div class="page">
    <StocksPageHeader
      :is-mj="page.isMj"
      :is-mj-other-view="page.isMjOtherView"
      :mj="page.mj"
      :current-user-id-str="page.currentUserIdStr"
      :stock-florins="page.stockFlorins"
      :qte-affichee="page.qteAffichee"
      :format-florin="page.formatFlorin"
      :format-florin-exact="page.formatFlorinExact"
      :sauvegarde="page.sauvegarde"
      :nb-modifications="page.nbModifications"
      @sauvegarder="page.sauvegarderTout"
    />

    <p v-if="page.erreur" class="error">{{ page.erreur }}</p>

    <StocksToolbar
      v-model:voir-toutes="page.voirToutesLesRessources"
      v-model:recherche="page.rechercheStocks"
      :nb-stocks-recherche="page.nbStocksRecherche"
      :nb-stocks-filtres="page.nbStocksFiltres"
      :nb-stocks-total="page.nbStocksTotal"
      :a-une-recherche-stock="page.aUneRechercheStock"
      :stocks-filtres-length="page.stocksFiltres.length"
    />

    <StocksTable
      :nb-stocks-recherche="page.nbStocksRecherche"
      :colonnes-tri="page.colonnesTri"
      :stocks-tries="page.stocksTries"
      :sort-label="page.sortLabel"
      :toggle-sort="page.toggleSort"
      :is-mj="page.isMj"
      :is-mj-other-view="page.isMjOtherView"
      :mj="page.mj"
      :get-modif="page.getModif"
      :set-modif="page.setModif"
      :has-modif="page.hasModif"
      :affichage-stock-quantite="page.affichageStockQuantite"
      :title-stock-quantite="page.titleStockQuantite"
      :title-valeur-stock="page.titleValeurStock"
      :texte-prochain-tour="page.texteProchainTour"
      :est-florins="page.estFlorins"
      :format-florin="page.formatFlorin"
      :qte-affichee="page.qteAffichee"
      :ouvrir-commerce="commerce.ouvrirCommerce"
      :ajuster-quantite-mj="page.ajusterQuantiteMj"
    />

    <StocksCommerceModal
      ref="commerceModalRef"
      v-model:commerce-qte="commerce.commerceQte"
      :commerce-modal="commerce.commerceModal"
      :commerce-achat-mode="commerce.commerceAchatMode"
      :commerce-err="commerce.commerceErr"
      :commerce-loading="commerce.commerceLoading"
      :historique-prix="commerce.historiquePrix"
      :commerce-prix-unitaire="commerce.commercePrixUnitaire"
      :commerce-total="commerce.commerceTotal"
      :is-mj-other-view="page.isMjOtherView"
      :format-florin="page.formatFlorin"
      :format-florin-exact="page.formatFlorinExact"
      :est-florins="page.estFlorins"
      @close="commerce.commerceModal = null"
      @set-achat-mode="(m) => (commerce.commerceAchatMode = m)"
      @executer="commerce.executerCommerce"
    />
  </div>
</template>
