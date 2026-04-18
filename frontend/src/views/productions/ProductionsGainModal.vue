<script setup>
import { ref } from "vue";
import ProductionsGainModalPctHelp from "./ProductionsGainModalPctHelp.vue";
import ProductionsGainModalToursHelp from "./ProductionsGainModalToursHelp.vue";

defineProps({
  gainFormModal: { type: Object, default: null },
  gainForm: { type: Object, required: true },
  ressourcesListe: { type: Array, default: () => [] },
  balisesFormulaireProduction: { type: Array, default: () => [] },
  nomRessourceForm: { type: String, default: "" },
  ressourceVerrouilleeEnCreation: { type: Boolean, default: false },
  toursRestantsAideOuverte: { type: Boolean, default: false },
  pourcentageAideOuverte: { type: Boolean, default: false },
});

const toursRestantsInput = defineModel("toursRestantsInput", { type: String, required: true });

defineEmits([
  "close",
  "save",
  "save-and-add",
  "blur-tours",
  "set-tours-rapide",
  "set-tours-illimite",
  "toggle-aide-tours",
  "toggle-aide-pct",
  "select-all",
]);

const gainQteInputRef = ref(null);

defineExpose({
  focusQte() {
    gainQteInputRef.value?.select?.();
  },
});
</script>

<template>
  <div v-if="gainFormModal" class="modal-overlay modal-overlay-gain" @click.self="$emit('close')">
    <div class="modal modal-sm modal-gain-form">
      <h3 class="modal-title">
        {{ gainFormModal.mode === "create" ? "Nouvelle production" : "Modifier la production" }}
      </h3>
      <div v-if="gainForm.ressource_id" class="modal-resource-banner">
        <span class="modal-resource-banner-label">Ressource</span>
        <span class="modal-resource-banner-nom">{{ nomRessourceForm }}</span>
      </div>
      <p v-else-if="gainFormModal.mode === 'create' && !ressourceVerrouilleeEnCreation" class="modal-resource-missing">
        Choisissez une ressource ci-dessous pour cette règle.
      </p>
      <label v-if="gainFormModal.mode === 'create' && !ressourceVerrouilleeEnCreation" class="form-label">
        Ressource
        <select v-model.number="gainForm.ressource_id" class="select full-width">
          <option :value="null" disabled>Choisir une ressource…</option>
          <option v-for="r in ressourcesListe" :key="r.id" :value="r.id">
            {{ r.nom }} ({{ r.type }})
          </option>
        </select>
      </label>
      <label class="form-label">
        Justification (balise)
        <select v-model="gainForm.balise" class="select full-width">
          <option v-if="balisesFormulaireProduction.length === 0" value="autre">Chargement…</option>
          <option v-for="b in balisesFormulaireProduction" :key="b.id" :value="b.id">
            {{ b.label }}
          </option>
        </select>
      </label>
      <div class="form-label">Mode</div>
      <div class="mode-row">
        <label class="radio-label">
          <input v-model="gainForm.mode_production" type="radio" value="fixe" />
          unités fixes (par tour)
        </label>
        <div class="mode-pct-line">
          <label class="radio-label mode-pct-label">
            <input v-model="gainForm.mode_production" type="radio" value="pourcentage" />
            <span>% de la production du tour (après les règles précédentes)</span>
          </label>
          <button
            type="button"
            class="tours-help-btn mode-pct-help"
            :aria-expanded="pourcentageAideOuverte"
            aria-controls="hint-mode-pourcentage"
            title="Aide : mode pourcentage"
            @click="$emit('toggle-aide-pct')"
          >
            ?
          </button>
        </div>
      </div>
      <ProductionsGainModalPctHelp :ouverte="pourcentageAideOuverte" />
      <label class="form-label">
        {{
          gainForm.mode_production === "pourcentage"
            ? "Pourcentage (−100 = tout perdre, +10 = +10 %)"
            : "Quantité (unités par tour)"
        }}
        <input
          ref="gainQteInputRef"
          v-model.number="gainForm.quantite_par_tour"
          type="number"
          class="input"
          @focus="$emit('select-all', $event)"
          @click="$emit('select-all', $event)"
        />
      </label>
      <label class="form-label">
        Démarre dans
        <input
          v-model.number="gainForm.delai_tours"
          type="number"
          min="0"
          class="input"
          @focus="$emit('select-all', $event)"
          @click="$emit('select-all', $event)"
        />
        tour(s)
      </label>
      <div class="delay-quick-actions">
        <button type="button" class="button secondary small" @click="gainForm.delai_tours = 0">Immédiat</button>
        <button type="button" class="button secondary small" @click="gainForm.delai_tours = 1">1 tour</button>
        <button type="button" class="button secondary small" @click="gainForm.delai_tours = 2">2 tours</button>
      </div>
      <label class="form-label">
        Nombre de tours restants
        <div class="tours-input-row">
          <input
            v-model="toursRestantsInput"
            type="text"
            inputmode="numeric"
            class="input input-tours-restants"
            autocomplete="off"
            spellcheck="false"
            :aria-describedby="toursRestantsAideOuverte ? 'hint-tours-restants' : undefined"
            title="Illimité : vide, ∞, infini, illimité… — Limité : un entier positif (ex. 6)"
            @blur="$emit('blur-tours')"
            @focus="$emit('select-all', $event)"
            @click="$emit('select-all', $event)"
          />
          <button
            type="button"
            class="tours-help-btn"
            :aria-expanded="toursRestantsAideOuverte"
            aria-controls="hint-tours-restants"
            title="Aide : durée illimitée ou limitée"
            @click="$emit('toggle-aide-tours')"
          >
            ?
          </button>
        </div>
        <ProductionsGainModalToursHelp :ouverte="toursRestantsAideOuverte" />
      </label>
      <div class="temp-quick-actions">
        <button type="button" class="button secondary small" @click="$emit('set-tours-illimite')">
          Sans limite (∞)
        </button>
        <button type="button" class="button secondary small" @click="$emit('set-tours-rapide', 1)">1 tour</button>
        <button type="button" class="button secondary small" @click="$emit('set-tours-rapide', 2)">2 tours</button>
      </div>
      <label class="form-label checkbox-label">
        <input v-model="gainForm.actif" type="checkbox" />
        Actif
      </label>
      <div class="modal-footer modal-footer-stack">
        <button type="button" class="button secondary" @click="$emit('close')">Annuler</button>
        <template v-if="gainFormModal.mode === 'create'">
          <button type="button" class="button secondary" @click="$emit('save-and-add')">Enregistrer &amp; ajouter une autre</button>
        </template>
        <button type="button" class="button" @click="$emit('save')">Enregistrer</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.full-width {
  width: 100%;
  margin-top: 6px;
}
.modal-overlay-gain {
  z-index: 4000;
}
.modal-gain-form {
  max-height: min(92vh, 880px);
  overflow-y: auto;
}
.modal-resource-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px 12px;
  margin: 0 0 12px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(56, 189, 248, 0.45);
  background: rgba(56, 189, 248, 0.1);
}
.modal-resource-banner-label {
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #7dd3fc;
}
.modal-resource-banner-nom {
  font-size: 1.1rem;
  font-weight: 800;
  color: #f0f9ff;
}
.modal-resource-missing {
  margin: 0 0 10px;
  padding: 8px 10px;
  font-size: 13px;
  color: #fcd34d;
  background: rgba(180, 83, 9, 0.15);
  border: 1px solid rgba(251, 191, 36, 0.35);
  border-radius: 8px;
}
.tours-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}
.tours-input-row .input-tours-restants {
  flex: 1;
  min-width: 0;
}
.tours-help-btn {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1px solid #475569;
  background: #1e293b;
  color: #94a3b8;
  font-weight: 700;
  font-size: 15px;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.tours-help-btn:hover,
.tours-help-btn[aria-expanded="true"] {
  border-color: #38bdf8;
  color: #e2e8f0;
  background: #0f172a;
}
.input-tours-restants {
  font-size: 1.15rem;
  font-variant-numeric: tabular-nums;
}
.mode-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}
.mode-pct-line {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
}
.mode-pct-label {
  flex: 1;
  min-width: 0;
}
.mode-pct-help {
  flex-shrink: 0;
  margin-top: 2px;
}
.radio-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #cbd5e1;
  cursor: pointer;
}
.temp-quick-actions {
  display: flex;
  gap: 8px;
  margin-top: 6px;
}
.delay-quick-actions {
  display: flex;
  gap: 8px;
  margin-top: 6px;
}
</style>
