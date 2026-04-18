<script setup>
import { formatEffetProduction } from "../../utils/gainPassif.js";

defineProps({
  productionsParRessource: { type: Array, default: () => [] },
  libelleBalise: { type: Function, required: true },
});

defineEmits(["open-detail", "add-for-resource"]);
</script>

<template>
  <div>
    <div v-if="productionsParRessource.length === 0" class="productions-empty">
      Aucune production passive pour l’instant. Cliquez sur « Nouvelle production » pour choisir une ressource et
      ajouter une ou plusieurs règles.
    </div>

    <div v-else class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Ressource</th>
            <th>Règles</th>
            <th>Détail (menu)</th>
            <th class="actions"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in productionsParRessource" :key="p.ressource_id">
            <td class="nom">{{ p.ressource?.nom ?? "—" }}</td>
            <td>{{ p.gains.length }}</td>
            <td>
              <details>
                <summary class="details-summary">Détails</summary>
                <div class="productions-dropdown">
                  <div v-for="g in p.gains" :key="g.id" class="prod-dropdown-row">
                    <span :class="['tag-balise', 'tag-balise-' + (g.balise || 'autre')]">
                      {{ libelleBalise(g.balise || "autre") }}
                    </span>
                    <span class="prix effet-cell">{{ formatEffetProduction(g) }}</span>
                    <span v-if="g.definitif" class="tag tag-durable">Sans limite</span>
                    <span v-else class="tag tag-temp">{{ g.tours_restants }} tour(s) restant(s)</span>
                    <span v-if="(g.delai_tours ?? 0) > 0" class="muted"> Démarre dans {{ g.delai_tours }} tour(s) </span>
                    <span class="muted">{{ g.actif ? "Actif" : "Inactif" }}</span>
                  </div>
                </div>
              </details>
            </td>
            <td class="actions">
              <button type="button" class="button secondary table-row-action" @click="$emit('open-detail', p.ressource_id)">
                Ouvrir le graphe
              </button>
              <button
                type="button"
                class="button secondary table-row-action"
                @click="$emit('add-for-resource', p.ressource_id, p.ressource?.nom ?? '')"
              >
                Ajouter
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
.productions-dropdown {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.prod-dropdown-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}
details.details-summary {
  margin: 0;
}
.details-summary {
  cursor: pointer;
  user-select: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #334155;
  background: #0f172a;
  color: #cbd5e1;
  font-weight: 600;
}
.details-summary::-webkit-details-marker {
  display: none;
}
.details-summary::after {
  content: "▼";
  font-size: 11px;
  color: #94a3b8;
}
details[open] .details-summary::after {
  content: "▲";
}
</style>
