<script setup>
const props = defineProps({
  categories: { type: Array, required: true },
  formatPct: { type: Function, required: true },
});
const emit = defineEmits(["create", "edit", "delete"]);
</script>

<template>
  <section class="cat-panel">
    <div class="cat-panel-head">
      <h3 class="section-title">Catégories (modificateur en %)</h3>
      <button type="button" class="button secondary small" @click="emit('create')">
        + Catégorie
      </button>
    </div>
    <p class="section-hint">
      Par défaut 100 %. Une nouvelle ressource est à 100 % et les prix intègrent automatiquement les % des catégories cochées.
      La modification d’une catégorie propage automatiquement les prix des ressources liées.
    </p>
    <div class="cat-chips">
      <div v-for="c in categories" :key="c.id" class="cat-chip cat-chip-row">
        <div class="cat-chip-text">
          <span class="cat-chip-nom">{{ c.nom }}</span>
          <span class="cat-chip-mod">{{ formatPct(c.modificateur_pct) }}</span>
        </div>
        <div class="cat-chip-actions">
          <button type="button" class="button secondary btn-cat-lg" @click="emit('edit', c)">
            Modifier
          </button>
          <button type="button" class="button btn-cat-lg btn-cat-danger" @click="emit('delete', c)">
            Supprimer
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

