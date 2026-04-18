<script setup>
import { formatEffetProduction } from "../../utils/gainPassif.js";

const COLONNES = [
  ["nom", "Ressource"],
  ["balise", "Justification"],
  ["qte", "Effet"],
  ["duree", "Durée"],
  ["actif", "Actif"],
];

defineProps({
  gainsTries: { type: Array, default: () => [] },
  gainsFiltres: { type: Array, default: () => [] },
  nomRessourceFiltre: { type: String, default: "" },
  productionsQueryAll: { type: Object, default: () => ({}) },
  sort: { type: Object, required: true },
  libelleBalise: { type: Function, required: true },
});

defineEmits(["toggle-sort", "edit", "delete"]);

function sortLabel(sort, k) {
  if (sort.key !== k) return "";
  return sort.dir === "asc" ? " ▲" : " ▼";
}
</script>

<template>
  <div>
    <div v-if="gainsFiltres.length === 0" class="productions-empty">
      Aucune règle de production pour « {{ nomRessourceFiltre }} ». Utilisez « Nouvelle production » en choisissant
      cette ressource, ou revenez à
      <router-link class="inline-link" :to="{ path: '/productions', query: productionsQueryAll }"
        >toutes les productions</router-link
      >.
    </div>

    <div v-else class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th v-for="[k, lab] in COLONNES" :key="k" class="th-sort" @click="$emit('toggle-sort', k)">
              {{ lab }}{{ sortLabel(sort, k) }}
            </th>
            <th class="actions"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="g in gainsTries" :key="g.id">
            <td class="nom">{{ g.ressource?.nom ?? "—" }}</td>
            <td>
              <span :class="['tag-balise', 'tag-balise-' + (g.balise || 'autre')]">
                {{ libelleBalise(g.balise || "autre") }}
              </span>
            </td>
            <td class="prix effet-cell">{{ formatEffetProduction(g) }}</td>
            <td>
              <span v-if="g.definitif" class="tag tag-durable">Sans limite</span>
              <span v-else class="tag tag-temp">{{ g.tours_restants }} tour(s) restant(s)</span>
              <span v-if="(g.delai_tours ?? 0) > 0" class="muted"> Démarre dans {{ g.delai_tours }} tour(s) </span>
            </td>
            <td>{{ g.actif ? "Oui" : "Non" }}</td>
            <td class="actions">
              <button type="button" class="button secondary table-row-action" @click="$emit('edit', g)">Modifier</button>
              <button type="button" class="button secondary table-row-action danger" @click="$emit('delete', g)">
                Supprimer
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.productions-empty {
  padding: 24px;
  color: #94a3b8;
  font-size: 15px;
  border: 1px dashed #334155;
  border-radius: 10px;
  margin-bottom: 16px;
}
.inline-link {
  margin-left: 6px;
  color: #93c5fd;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.muted {
  color: #94a3b8;
}
.tag-balise {
  display: inline-block;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  font-weight: 600;
}
.tag-balise-science {
  background: #1e3a5f;
  color: #93c5fd;
}
.tag-balise-politique {
  background: #422006;
  color: #fcd34d;
}
.tag-balise-evenement {
  background: #4c1d95;
  color: #e9d5ff;
}
.tag-balise-batiment {
  background: #0f766e;
  color: #b9f6f0;
}
.tag-balise-autre {
  background: #334155;
  color: #cbd5e1;
}
.tag-balise-recolte_fructueuse {
  background: #14532d;
  color: #bbf7d0;
}
.effet-cell {
  white-space: nowrap;
}
</style>
