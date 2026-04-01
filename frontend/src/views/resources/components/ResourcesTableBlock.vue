<script setup>
const props = defineProps({
  isMj: { type: Boolean, required: true },
  titre: { type: String, required: true },
  liste: { type: Array, required: true },
  colonnes: { type: Array, required: true },
  sortLabel: { type: Function, required: true },
  formatPct: { type: Function, required: true },
  formatFlorin: { type: Function, required: true },
  formatFlorinExact: { type: Function, required: true },
  florinsNom: { type: String, required: true },
  idSelectionne: { type: Function, required: true },
});

const emit = defineEmits([
  "select-all",
  "toggle-sort",
  "toggle-selection",
  "edit",
  "delete",
]);
</script>

<template>
  <h3 class="table-block-title">
    {{ titre }}
    <button
      v-if="isMj"
      type="button"
      class="button secondary small bloc-select-all"
      @click="emit('select-all')"
    >
      Sélectionner tout ({{ titre }})
    </button>
  </h3>

  <div class="table-wrap">
    <table class="data-table">
      <thead>
        <tr>
          <th v-if="isMj" class="th-check"></th>
          <th
            v-for="[k, lab] in colonnes"
            :key="k"
            class="th-sort"
            @click="emit('toggle-sort', k)"
          >
            {{ lab }}{{ sortLabel(k) }}
          </th>
          <th v-if="isMj"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in liste" :key="r.id">
          <td v-if="isMj" class="td-check">
            <input
              v-if="r.nom !== florinsNom"
              type="checkbox"
              :checked="idSelectionne(r.id)"
              @change="emit('toggle-selection', r.id)"
            />
            <span v-else class="muted" title="Monnaie — pas d’ajustement groupé">—</span>
          </td>
          <td class="nom">{{ r.nom }}</td>
          <td class="categories">
            <span v-for="c in r.categories || []" :key="c.id" class="tag">
              {{ c.nom }} ({{ formatPct(c.modificateur_pct) }})
            </span>
            <span v-if="!(r.categories || []).length" class="muted">—</span>
          </td>
          <td class="prix">{{ formatPct(r.modificateur_pct) }}</td>
          <td class="prix">×{{ r.facteur_prix }}</td>
          <td class="prix" :title="formatFlorinExact(r.prix_base)">{{ formatFlorin(r.prix_base) }}</td>
          <td class="prix" :title="formatFlorinExact(r.prix_modifie)">{{ formatFlorin(r.prix_modifie) }}</td>
          <td class="prix accent" :title="formatFlorinExact(r.prix_achat)">{{ formatFlorin(r.prix_achat) }}</td>
          <td class="prix" :title="formatFlorinExact(r.prix_lointain)">{{ formatFlorin(r.prix_lointain) }}</td>
          <td v-if="isMj" class="actions">
            <button type="button" class="button secondary table-row-action" @click="emit('edit', r)">
              Modifier
            </button>
            <button type="button" class="button secondary table-row-action danger" @click="emit('delete', r)">
              Supprimer
            </button>
          </td>
        </tr>
        <tr v-if="liste.length === 0">
          <td :colspan="isMj ? 10 : 8" class="empty">Aucune ressource.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

