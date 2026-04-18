<script setup>
defineProps({
  productionsParRessource: { type: Array, default: () => [] },
  ressourceIdFiltre: { type: [Number, null], default: null },
});

defineEmits(["select"]);
</script>

<template>
  <div v-if="productionsParRessource.length > 0" class="productions-header">
    <div class="productions-header-title">Aperçu</div>
    <div class="productions-header-list">
      <button
        v-for="p in productionsParRessource"
        :key="p.ressource_id"
        type="button"
        class="productions-header-item"
        :class="{ active: Number(ressourceIdFiltre) === Number(p.ressource_id) }"
        @click="$emit('select', p.ressource_id)"
      >
        <span class="productions-header-nom">{{ p.ressource?.nom ?? "—" }}</span>
        <span class="productions-header-count">{{ p.gains.length }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.productions-header {
  margin: 10px 0 14px;
  padding: 12px 14px;
  background: rgba(15, 23, 42, 0.25);
  border: 1px solid #334155;
  border-radius: 12px;
}

.productions-header-title {
  font-size: 12px;
  font-weight: 800;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 10px;
}

.productions-header-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.productions-header-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid rgba(51, 65, 85, 0.9);
  background: rgba(30, 41, 59, 0.4);
  color: #e2e8f0;
  cursor: pointer;
}

.productions-header-item:hover {
  border-color: rgba(148, 163, 184, 0.35);
  background: rgba(30, 41, 59, 0.7);
}

.productions-header-item.active {
  border-color: #38bdf8;
  background: rgba(56, 189, 248, 0.16);
  box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25);
  color: #f0f9ff;
}

.productions-header-nom {
  font-weight: 700;
}

.productions-header-count {
  min-width: 20px;
  height: 20px;
  display: inline-grid;
  place-items: center;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.16);
  color: #cbd5e1;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
</style>
