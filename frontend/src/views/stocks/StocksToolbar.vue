<script setup>
const voirToutes = defineModel("voirToutes", { type: Boolean, required: true });
const recherche = defineModel("recherche", { type: String, required: true });

defineProps({
  nbStocksRecherche: { type: Number, default: 0 },
  nbStocksFiltres: { type: Number, default: 0 },
  nbStocksTotal: { type: Number, default: 0 },
  aUneRechercheStock: { type: Boolean, default: false },
  stocksFiltresLength: { type: Number, default: 0 },
});
</script>

<template>
  <div class="stocks-toolbar">
    <div class="stocks-toolbar-row stocks-mode-row" role="group" aria-label="Mode d'affichage des stocks">
      <span class="stocks-mode-label" :class="{ 'is-active': !voirToutes }">Mes stocks</span>
      <button
        type="button"
        class="stocks-switch"
        role="switch"
        :aria-checked="voirToutes"
        :aria-label="
          voirToutes ? 'Afficher tout le catalogue : activé' : 'Afficher uniquement les ressources possédées'
        "
        @click="voirToutes = !voirToutes"
      >
        <span class="stocks-switch-track" :class="{ 'is-on': voirToutes }">
          <span class="stocks-switch-thumb" />
        </span>
      </button>
      <span class="stocks-mode-label" :class="{ 'is-active': voirToutes }">Tout le catalogue</span>
    </div>
    <div class="stocks-toolbar-row">
      <label class="stocks-search-label">
        <span class="stocks-search-title">Rechercher une ressource</span>
        <input
          v-model.trim="recherche"
          type="search"
          class="input stocks-search-input"
          placeholder="Nom ou type…"
          autocomplete="off"
          spellcheck="false"
        />
      </label>
    </div>
    <p class="stocks-filter-meta">
      <template v-if="aUneRechercheStock">
        {{ nbStocksRecherche }} résultat{{ nbStocksRecherche !== 1 ? "s" : "" }} sur {{ nbStocksFiltres }}
        ressource{{ nbStocksFiltres !== 1 ? "s" : "" }} affichée{{ nbStocksFiltres !== 1 ? "s" : "" }}.
      </template>
      <template v-else-if="voirToutes"> Catalogue complet : {{ nbStocksFiltres }} ressources. </template>
      <template v-else>
        {{ nbStocksFiltres }} ressource{{ nbStocksFiltres !== 1 ? "s" : "" }} en possession sur
        {{ nbStocksTotal }} au catalogue (activez « Tout le catalogue » pour tout voir).
      </template>
    </p>
  </div>

  <p v-if="aUneRechercheStock && nbStocksRecherche === 0 && stocksFiltresLength > 0" class="stocks-empty-search">
    Aucune ressource ne correspond à « {{ recherche }} ».
  </p>
</template>

<style scoped>
.stocks-toolbar {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 14px;
  padding: 14px 16px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 10px;
  max-width: 100%;
}

.stocks-toolbar-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.stocks-mode-row {
  gap: 14px;
  padding: 4px 0;
}

.stocks-mode-label {
  font-size: 15px;
  font-weight: 600;
  color: #64748b;
  transition: color 0.15s ease;
  user-select: none;
}

.stocks-mode-label.is-active {
  color: #e2e8f0;
}

.stocks-switch {
  border: none;
  background: transparent;
  padding: 6px 10px;
  cursor: pointer;
  flex-shrink: 0;
  border-radius: 8px;
}

.stocks-switch:focus-visible {
  outline: 2px solid #38bdf8;
  outline-offset: 3px;
}

.stocks-switch-track {
  display: block;
  width: 56px;
  height: 30px;
  border-radius: 999px;
  background: #334155;
  position: relative;
  transition: background 0.2s ease;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.35);
}

.stocks-switch-track.is-on {
  background: #0284c7;
}

.stocks-switch-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #f8fafc;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
  transition: transform 0.2s ease;
}

.stocks-switch-track.is-on .stocks-switch-thumb {
  transform: translateX(26px);
}

.stocks-search-label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  max-width: 420px;
  margin: 0;
}

.stocks-search-title {
  font-size: 13px;
  font-weight: 600;
  color: #cbd5e1;
}

.stocks-search-input {
  width: 100%;
  min-height: 42px;
  font-size: 15px;
}

.stocks-filter-meta {
  margin: 0;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.5;
}

.stocks-empty-search {
  margin: 0 0 12px;
  padding: 12px 14px;
  border-radius: 8px;
  background: rgba(251, 191, 36, 0.08);
  border: 1px solid rgba(251, 191, 36, 0.35);
  color: #fcd34d;
  font-size: 14px;
}
</style>
