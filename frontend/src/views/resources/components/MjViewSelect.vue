<script setup>
const props = defineProps({
  open: { type: Boolean, required: true },
  label: { type: String, required: true },
  search: { type: String, required: true },
  options: { type: Array, required: true }, // [{ id, username, is_mj }]
  currentChoice: { type: [String, Number], required: true },
  currentUserIdStr: { type: String, required: true },
});

const emit = defineEmits(["update:open", "update:search", "select"]);
</script>

<template>
  <div class="mj-view-select">
    <div class="mj-view-label">Voir comme</div>
    <div class="mj-view-autocomplete" @keydown.esc="emit('update:open', false)">
      <input
        class="input mj-view-input"
        :value="label"
        readonly
        @focus="emit('update:open', true)"
        @click="emit('update:open', !open)"
      />

      <div v-if="open" class="mj-view-menu">
        <div class="mj-view-section">
          <div class="mj-view-section-title">Choix actuel</div>
          <button
            type="button"
            class="mj-view-option is-active"
            @click="emit('select', currentChoice)"
          >
            {{ label }}
          </button>
        </div>

        <div class="mj-view-sep"></div>

        <div class="mj-view-section">
          <div class="mj-view-section-title">Global</div>
          <button type="button" class="mj-view-option" @click="emit('select', 'global')">
            Global (catalogue)
          </button>
        </div>

        <div class="mj-view-sep"></div>

        <div class="mj-view-section">
          <div class="mj-view-section-title">Joueurs</div>
          <input
            class="input mj-view-search"
            :value="search"
            placeholder="Rechercher un joueur…"
            @input="emit('update:search', $event.target.value)"
          />
          <div class="mj-view-list">
            <button
              v-for="u in options"
              :key="u.id"
              type="button"
              class="mj-view-option"
              @click="emit('select', String(u.id))"
            >
              <template v-if="String(u.id) === currentUserIdStr">Vous — {{ u.username }}</template>
              <template v-else>{{ u.username }}</template>{{ u.is_mj ? " (MJ)" : "" }}
            </button>
            <div v-if="options.length === 0" class="muted mj-view-empty">Aucun résultat.</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mj-view-select {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-right: 12px;
}

.mj-view-label {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 600;
}

.mj-view-autocomplete {
  position: relative;
}

.mj-view-input {
  min-width: 340px;
  cursor: pointer;
}

.mj-view-menu {
  position: absolute;
  z-index: 50;
  top: calc(100% + 6px);
  left: 0;
  width: 420px;
  max-width: 80vw;
  background: #0b1220;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 10px;
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.45);
}

.mj-view-section-title {
  font-size: 12px;
  font-weight: 700;
  color: #94a3b8;
  margin: 2px 0 8px;
}

.mj-view-option {
  width: 100%;
  text-align: left;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  color: #e2e8f0;
  cursor: pointer;
}

.mj-view-option:hover {
  background: rgba(148, 163, 184, 0.12);
  border-color: rgba(148, 163, 184, 0.2);
}

.mj-view-option.is-active {
  background: rgba(147, 197, 253, 0.12);
  border-color: rgba(147, 197, 253, 0.25);
}

.mj-view-sep {
  height: 1px;
  background: rgba(148, 163, 184, 0.2);
  margin: 10px 0;
}

.mj-view-search {
  width: 100%;
}

.mj-view-list {
  margin-top: 10px;
  max-height: 260px;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mj-view-empty {
  padding: 8px 10px;
}
</style>

