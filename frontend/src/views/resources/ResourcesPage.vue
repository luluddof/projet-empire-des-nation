<script setup>
import { proxyRefs } from "vue";
import { useResourcesPage } from "./useResourcesPage.js";
import MjViewSelect from "../../components/MjViewSelect.vue";
import CategoryPanel from "./components/CategoryPanel.vue";
import FiltersBar from "./components/FiltersBar.vue";
import ResourcesTableBlock from "./components/ResourcesTableBlock.vue";
import BulkPrixModal from "./components/BulkPrixModal.vue";
import CategoryModal from "./components/CategoryModal.vue";
import ResourceModal from "./components/ResourceModal.vue";

const props = defineProps({
  authState: { type: Object, required: true },
});

const vm = proxyRefs(useResourcesPage(props.authState));
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">Catalogue des ressources</h2>
        <p class="page-subtitle">
          <template v-if="vm.isMj">
            Modificateurs en % (100 % = neutre). Facteur total = ( % ressource / 100 ) × moyenne( % catégorie / 100 ).
            Tableau : <strong>prix catalogue</strong> (global). Vous pouvez appliquer un % à tout le monde, à vous seul ou à des joueurs choisis.
          </template>
          <template v-else>
            <strong>Consultation</strong> : les montants affichés utilisent <strong>votre</strong> modificateur (catalogue et éventuelle surcharge MJ).
          </template>
        </p>
      </div>
      <div v-if="vm.isMj" class="header-actions">
        <MjViewSelect
          :open="vm.mjVueOpen"
          :label="vm.mjVueLabel"
          :search="vm.mjVueSearch"
          :options="vm.mjVueAutres"
          :current-choice="vm.mjVueChoix"
          :current-user-id-str="vm.currentUserIdStr"
          :show-global="true"
          @update:open="(v) => (vm.mjVueOpen = v)"
          @update:search="(v) => (vm.mjVueSearch = v)"
          @select="vm.mjVueSetChoix"
        />
        <button class="button" @click="vm.ouvrirCreation">+ Ressource</button>
      </div>
    </div>

    <p v-if="vm.erreur" class="error">{{ vm.erreur }}</p>

    <CategoryPanel
      v-if="vm.isMj"
      :categories="vm.categories"
      :format-pct="vm.formatPct"
      @create="vm.ouvrirNouvelleCategorie"
      @edit="vm.ouvrirEditCategorie"
      @delete="vm.supprimerCategorie"
    />

    <FiltersBar
      :recherche="vm.recherche"
      :filtre-categorie-id="vm.filtreCategorieId"
      :categories="vm.categories"
      @update:recherche="(v) => (vm.recherche = v)"
      @update:filtreCategorieId="(v) => (vm.filtreCategorieId = v)"
    />

    <div v-if="vm.isMj" class="bulk-toolbar">
      <span class="bulk-count">{{ vm.selectedIds.length }} sélectionnée(s)</span>
      <button type="button" class="button secondary small" @click="vm.selectionnerVueFiltre">
        Tout sélectionner (vue filtrée)
      </button>
      <button type="button" class="button secondary small" @click="vm.viderSelection">
        Vider la sélection
      </button>
      <button
        type="button"
        class="button"
        :disabled="vm.selectedIds.length === 0"
        @click="vm.bulkModal = true"
      >
        Prix marché groupé (% ressource)…
      </button>
    </div>

    <ResourcesTableBlock
      v-for="(bloc, idx) in [
        { titre: 'Matières premières', liste: vm.listePremiere },
        { titre: 'Matières manufacturées', liste: vm.listeManufacture },
      ]"
      :key="idx"
      :is-mj="vm.isMj"
      :titre="bloc.titre"
      :liste="bloc.liste"
      :colonnes="vm.colonnes"
      :sort-label="vm.sortLabel"
      :format-pct="vm.formatPct"
      :format-florin="vm.formatFlorin"
      :format-florin-exact="vm.formatFlorinExact"
      :florins-nom="vm.FLORINS_NOM"
      :id-selectionne="vm.idSelectionne"
      @select-all="() => vm.selectionnerToutListe(bloc.liste)"
      @toggle-sort="vm.toggleSort"
      @toggle-selection="vm.toggleSelection"
      @edit="vm.ouvrirEdition"
      @delete="vm.supprimerRessource"
    />

    <BulkPrixModal
      :open="vm.bulkModal"
      :selected-count="vm.selectedIds.length"
      :err="vm.bulkErr"
      :loading="vm.bulkLoading"
      :mod-mode="vm.bulkModMode"
      :pct="vm.bulkPct"
      :user-search="vm.bulkUserSearch"
      :users-visible="vm.bulkUserVisibleJoueurs"
      :current-user-id-str="vm.currentUserIdStr"
      :user-selected="vm.bulkUserSelected"
      :can-bulk-select-users="vm.isMj && vm.mjVueChoix === 'global'"
      :all-users-selected="vm.bulkAllUsersSelected"
      @close="vm.bulkModal = false"
      @apply="vm.appliquerBulkPrix"
      @update:modMode="(v) => (vm.bulkModMode = v)"
      @update:pct="(v) => (vm.bulkPct = v)"
      @update:userSearch="(v) => (vm.bulkUserSearch = v)"
      @toggle-user="vm.toggleBulkUser"
      @select-all-users="vm.bulkSelectAllUsers"
      @clear-all-users="vm.bulkClearAllUsers"
    />

    <CategoryModal
      :open="vm.catModal"
      :cat-form="vm.catForm"
      :cat-mod-mode="vm.catModMode"
      :erreur-cat="vm.erreurCat"
      :player-search="vm.catPlayerSearch"
      :players-visible="vm.catPlayerVisibleJoueurs"
      :current-user-id-str="vm.currentUserIdStr"
      :player-user-selected="vm.catPlayerUserSelected"
      :can-bulk-select-users="vm.isMj && vm.mjVueChoix === 'global'"
      :all-users-selected="vm.catAllUsersSelected"
      :player-etat="vm.catPlayerEtat"
      :player-etat-loading="vm.catPlayerEtatLoading"
      :player-etat-erreur="vm.catPlayerEtatErreur"
      :selected-user-ids="vm.catPlayerForm.utilisateur_ids"
      :format-pct="vm.formatPct"
      :utilisateurs-liste="vm.utilisateursListe"
      @close="vm.catModal = false"
      @save="vm.sauvegarderCategorie"
      @reset-100="vm.fixerCategorieModificateurA100"
      @update:nom="(v) => (vm.catForm.nom = v)"
      @update:modificateur_pct="(v) => (vm.catForm.modificateur_pct = v)"
      @update:catModMode="(v) => (vm.catModMode = v)"
      @update:playerSearch="(v) => (vm.catPlayerSearch = v)"
      @toggle-player="vm.toggleCatPlayerUser"
      @select-all-users="vm.catSelectAllUsers"
      @clear-all-users="vm.catClearAllUsers"
    />

    <ResourceModal
      :open="vm.modalVisible"
      :mode-edition="vm.modeEdition"
      :erreur="vm.erreurModal"
      :form="vm.form"
      :res-mod-mode="vm.resModMode"
      :categories="vm.categories"
      :format-pct="vm.formatPct"
      :player-search="vm.resPlayerSearch"
      :players-visible="vm.resPlayerVisibleJoueurs"
      :current-user-id-str="vm.currentUserIdStr"
      :user-selected="vm.formUserSelected"
      :can-bulk-select-users="vm.isMj && vm.mjVueChoix === 'global'"
      :all-users-selected="vm.resAllUsersSelected"
      :player-etat="vm.resPlayerEtat"
      :player-etat-loading="vm.resPlayerEtatLoading"
      :player-etat-erreur="vm.resPlayerEtatErreur"
      :preview-facteur="vm.previewFacteur"
      :preview="vm.preview"
      :format-florin="vm.formatFlorin"
      :format-florin-exact="vm.formatFlorinExact"
      :utilisateurs-liste="vm.utilisateursListe"
      @close="vm.modalVisible = false"
      @save="vm.sauvegarderRessource"
      @apply-categories-neutral="vm.appliquerProduitCategories"
      @update:nom="(v) => (vm.form.nom = v)"
      @update:type="(v) => (vm.form.type = v)"
      @update:prix_base="(v) => (vm.form.prix_base = v)"
      @update:modificateur_pct="(v) => (vm.form.modificateur_pct = v)"
      @update:resModMode="(v) => (vm.resModMode = v)"
      @update:playerSearch="(v) => (vm.resPlayerSearch = v)"
      @toggle-user="vm.toggleFormUser"
      @select-all-users="vm.resSelectAllUsers"
      @clear-all-users="vm.resClearAllUsers"
      @set-categorie-checked="vm.setCategorieChecked"
    />
  </div>
</template>

<style scoped src="./ResourcesPage.css"></style>

