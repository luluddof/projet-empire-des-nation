<script setup>
const props = defineProps({
  recherche: { type: String, required: true },
  filtreCategorieId: { type: String, required: true },
  categories: { type: Array, required: true },
});
const emit = defineEmits(["update:recherche", "update:filtreCategorieId"]);
</script>

<template>
  <div class="filters">
    <input
      class="input-search"
      type="text"
      placeholder="Rechercher…"
      :value="recherche"
      @input="emit('update:recherche', $event.target.value)"
    />
    <select
      class="select"
      :value="filtreCategorieId"
      @change="emit('update:filtreCategorieId', $event.target.value)"
    >
      <option value="">Toutes les catégories</option>
      <option v-for="c in categories" :key="c.id" :value="String(c.id)">{{ c.nom }}</option>
    </select>
  </div>
</template>

