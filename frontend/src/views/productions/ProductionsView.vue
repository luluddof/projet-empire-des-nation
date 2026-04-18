<script setup>
import { toRef } from "vue";
import ProductionChronologieChart from "../../components/ProductionChronologieChart.vue";
import ProductionsPageHeader from "./ProductionsPageHeader.vue";
import ProductionsResourcePills from "./ProductionsResourcePills.vue";
import ProductionsOverviewTable from "./ProductionsOverviewTable.vue";
import ProductionsDetailTable from "./ProductionsDetailTable.vue";
import ProductionsGainModal from "./ProductionsGainModal.vue";
import { useProductionsData } from "./useProductionsData.js";
import { useGainPassifModal } from "./useGainPassifModal.js";

const props = defineProps({
  authState: { type: Object, required: true },
});

const data = useProductionsData(props);
const modal = useGainPassifModal({
  erreur: toRef(data, "erreur"),
  charger: data.charger,
  ressourceIdFiltre: toRef(data, "ressourceIdFiltre"),
  ressourcesListe: toRef(data, "ressourcesListe"),
  isMj: toRef(data, "isMj"),
  mjRaw: data.mjRaw,
  buildProductionsQuery: data.buildProductionsQuery,
  router: data.router,
});

const {
  gainModalRef,
  toursRestantsInput,
  toursRestantsAideOuverte,
  pourcentageAideOuverte,
  ouvrirCreationSelonContexte,
  ouvrirAjoutProductionPourRessource,
  ouvrirEditionGain,
  sauvegarderGainForm,
  supprimerGain,
  gainFormModal,
  gainForm,
  nomRessourceForm,
  ressourceVerrouilleeEnCreation,
  onToursRestantsBlur,
  setToursRestantsRapide,
  setToursRestantsIllimite,
  selectAllInputText,
  toggleToursAide,
  togglePctAide,
} = modal;
</script>

<template>
  <div class="page">
    <ProductionsPageHeader
      :is-mj="data.isMj"
      :mj="data.mj"
      :current-user-id-str="data.currentUserIdStr"
      :ressource-id-filtre="data.ressourceIdFiltre"
      :nom-ressource-filtre="data.nomRessourceFiltre"
      :productions-query-all="data.productionsQueryAll"
      @nouvelle-production="ouvrirCreationSelonContexte"
    />

    <p v-if="data.erreur" class="error">{{ data.erreur }}</p>

    <ProductionsResourcePills
      :productions-par-ressource="data.productionsParRessource"
      :ressource-id-filtre="data.ressourceIdFiltre"
      @select="data.ouvrirDetailRessource"
    />

    <div v-if="data.ressourceIdFiltre" class="banner-salon banner-vue-ressource">
      <div class="banner-vue-ressource-title">Production — {{ data.nomRessourceFiltre }}</div>
    </div>

    <ProductionChronologieChart
      v-if="data.ressourceIdFiltre && data.chronologie"
      :passe="data.chronologie.passe"
      :futur="data.chronologie.futur"
      :futur-breakdown="data.chronologie.futur_breakdown || []"
      :ressource-nom="data.nomRessourceFiltre"
    />

    <div v-if="!data.ressourceIdFiltre">
      <ProductionsOverviewTable
        :productions-par-ressource="data.productionsParRessource"
        :libelle-balise="data.libelleBalise"
        @open-detail="data.ouvrirDetailRessource"
        @add-for-resource="(rid, nom) => ouvrirAjoutProductionPourRessource(rid, nom)"
      />
    </div>

    <div v-else>
      <ProductionsDetailTable
        :gains-tries="data.gainsTries"
        :gains-filtres="data.gainsFiltres"
        :nom-ressource-filtre="data.nomRessourceFiltre"
        :productions-query-all="data.productionsQueryAll"
        :sort="data.sort"
        :libelle-balise="data.libelleBalise"
        @toggle-sort="data.toggleSort"
        @edit="ouvrirEditionGain"
        @delete="supprimerGain"
      />
    </div>

    <ProductionsGainModal
      ref="gainModalRef"
      v-model:tours-restants-input="toursRestantsInput"
      :gain-form-modal="gainFormModal"
      :gain-form="gainForm"
      :ressources-liste="data.ressourcesListe"
      :balises-formulaire-production="data.balisesFormulaireProduction"
      :nom-ressource-form="nomRessourceForm"
      :ressource-verrouillee-en-creation="ressourceVerrouilleeEnCreation"
      :tours-restants-aide-ouverte="toursRestantsAideOuverte"
      :pourcentage-aide-ouverte="pourcentageAideOuverte"
      @close="gainFormModal = null"
      @save="sauvegarderGainForm(false)"
      @save-and-add="sauvegarderGainForm(true)"
      @blur-tours="onToursRestantsBlur"
      @set-tours-rapide="setToursRestantsRapide"
      @set-tours-illimite="setToursRestantsIllimite"
      @toggle-aide-tours="toggleToursAide"
      @toggle-aide-pct="togglePctAide"
      @select-all="selectAllInputText"
    />
  </div>
</template>

<style scoped>
.banner-salon {
  margin-bottom: 16px;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.5;
  color: #cbd5e1;
  background: #1e293b;
  border: 1px solid #475569;
  border-radius: 10px;
}
.banner-vue-ressource {
  border-color: #0ea5e9;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.12), rgba(15, 23, 42, 0.95));
  box-shadow: 0 0 0 1px rgba(14, 165, 233, 0.25);
}
.banner-vue-ressource-title {
  font-size: 1.05rem;
  font-weight: 800;
  color: #e0f2fe;
  margin: 0;
  letter-spacing: 0.02em;
}
</style>
