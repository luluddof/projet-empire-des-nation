<script setup>
defineProps({
  nbStocksRecherche: { type: Number, default: 0 },
  colonnesTri: { type: Array, required: true },
  stocksTries: { type: Array, default: () => [] },
  sortLabel: { type: Function, required: true },
  toggleSort: { type: Function, required: true },
  isMj: { type: Boolean, default: false },
  isMjOtherView: { type: Boolean, default: false },
  mj: { type: Object, required: true },
  getModif: { type: Function, required: true },
  setModif: { type: Function, required: true },
  hasModif: { type: Function, required: true },
  affichageStockQuantite: { type: Function, required: true },
  titleStockQuantite: { type: Function, required: true },
  titleValeurStock: { type: Function, required: true },
  texteProchainTour: { type: Function, required: true },
  estFlorins: { type: Function, required: true },
  formatFlorin: { type: Function, required: true },
  qteAffichee: { type: Function, required: true },
  ouvrirCommerce: { type: Function, required: true },
  ajusterQuantiteMj: { type: Function, required: true },
});
</script>

<template>
  <div class="table-wrap">
    <table v-show="nbStocksRecherche > 0" class="data-table">
      <thead>
        <tr>
          <th v-for="[k, lab] in colonnesTri" :key="k" class="th-sort" @click="toggleSort(k)">
            {{ lab }}{{ sortLabel(k) }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in stocksTries" :key="s.ressource_id" :class="{ modified: hasModif(s) }">
          <td class="nom">{{ s.ressource.nom }}</td>
          <td>
            <span :class="['badge', s.ressource.type === 'Manufacturé' ? 'badge-manuf' : 'badge-prem']">
              {{ s.ressource.type }}
            </span>
          </td>
          <td class="prix" :title="titleStockQuantite(s)">
            {{ affichageStockQuantite(s) }}
          </td>
          <td v-if="isMj">
            <div class="mj-qty-cell">
              <input
                type="number"
                class="input-qty"
                :value="getModif(s.ressource_id)"
                :placeholder="s.quantite"
                min="0"
                step="any"
                @input="setModif(s.ressource_id, $event.target.value)"
              />
              <div v-if="isMjOtherView" class="mj-qty-delta" :title="'Ajouter ou retirer une unité (puis Sauvegarder)'">
                <button type="button" class="button secondary tiny" @click="ajusterQuantiteMj(s, -1)">−</button>
                <button type="button" class="button secondary tiny" @click="ajusterQuantiteMj(s, 1)">+</button>
              </div>
            </div>
          </td>
          <td class="gain-cell">
            <span
              v-if="!estFlorins(s)"
              class="prod-next-tour"
              :title="'Somme des règles actives pour le prochain tour (mercredi ou samedi 00h00)'"
            >
              {{ texteProchainTour(s) }}
            </span>
            <router-link
              class="button secondary small link-as-button"
              :to="{
                path: '/productions',
                query: {
                  ressource: String(s.ressource_id),
                  ...(isMj && mj.mjVueChoix ? { uid: String(mj.mjVueChoix) } : {}),
                },
              }"
            >
              Voir la production
            </router-link>
          </td>
          <td class="commerce-actions">
            <template v-if="!estFlorins(s)">
              <button
                type="button"
                class="button small secondary"
                :disabled="isMjOtherView"
                @click="ouvrirCommerce(s, 'achat')"
              >
                Acheter
              </button>
              <button
                type="button"
                class="button small secondary"
                :disabled="isMjOtherView"
                @click="ouvrirCommerce(s, 'vente')"
              >
                Vendre
              </button>
            </template>
            <span v-else class="commerce-na">—</span>
          </td>
          <td class="prix accent" :title="titleValeurStock(s)">
            {{ formatFlorin(qteAffichee(s) * s.ressource.prix_achat) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.mj-qty-cell {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.mj-qty-delta {
  display: inline-flex;
  gap: 4px;
}

.button.tiny {
  min-width: 2rem;
  padding: 2px 8px;
  font-size: 14px;
  line-height: 1.2;
}
</style>
