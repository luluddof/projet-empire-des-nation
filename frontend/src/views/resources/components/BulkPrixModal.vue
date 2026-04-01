<script setup>
const props = defineProps({
  open: { type: Boolean, required: true },
  selectedCount: { type: Number, required: true },
  err: { type: String, required: true },
  loading: { type: Boolean, required: true },
  modMode: { type: String, required: true },
  pct: { type: Number, required: true },
  userSearch: { type: String, required: true },
  usersVisible: { type: Array, required: true }, // [{id, username, is_mj}]
  currentUserIdStr: { type: String, required: true },
  userSelected: { type: Function, required: true },
  canBulkSelectUsers: { type: Boolean, required: true },
  allUsersSelected: { type: Boolean, required: true },
});

const emit = defineEmits([
  "close",
  "apply",
  "update:modMode",
  "update:pct",
  "update:userSearch",
  "toggle-user",
  "select-all-users",
  "clear-all-users",
]);
</script>

<template>
  <div v-if="open" class="modal-overlay" @click.self="emit('close')">
    <div class="modal modal-md">
      <h3 class="modal-title">Prix marché — modificateur % (ressource)</h3>
      <p class="modal-hint">
        S’applique aux <strong>{{ selectedCount }}</strong> ressource(s) sélectionnée(s).
      </p>
      <p v-if="err" class="error">{{ err }}</p>

      <div class="cible-mod-block">
        <div class="cible-mod-title">Mise à jour</div>
        <label class="radio-line"><input :checked="modMode === 'set'" type="radio" value="set" @change="emit('update:modMode', 'set')" />Définir</label>
        <label class="radio-line"><input :checked="modMode === 'add'" type="radio" value="add" @change="emit('update:modMode', 'add')" />Ajouter</label>
        <label class="radio-line"><input :checked="modMode === 'remove'" type="radio" value="remove" @change="emit('update:modMode', 'remove')" />Retirer</label>
      </div>

      <label class="form-label">
        <span v-if="modMode === 'set'">Nouveau % modificateur ressource</span>
        <span v-else>Delta (%) sur % ressource</span>
        <input
          class="input"
          type="number"
          step="0.1"
          min="0.1"
          :value="pct"
          @input="emit('update:pct', Number($event.target.value))"
        />
      </label>

      <label class="form-label">
        Joueurs
        <input
          class="input player-search"
          type="text"
          placeholder="Rechercher un joueur…"
          :value="userSearch"
          @input="emit('update:userSearch', $event.target.value)"
        />
        <div v-if="canBulkSelectUsers" class="player-picker-actions">
          <button
            type="button"
            class="button secondary small"
            @click="emit(allUsersSelected ? 'clear-all-users' : 'select-all-users')"
          >
            {{ allUsersSelected ? "Tout désélectionner" : "Tout sélectionner" }}
          </button>
        </div>
        <div class="player-picker-list">
          <label v-for="u in usersVisible" :key="u.id" class="checkbox-label user-pick-item">
            <input type="checkbox" :checked="userSelected(u.id)" @change="emit('toggle-user', u.id)" />
            <span class="user-pick-name" v-if="String(u.id) === currentUserIdStr">Vous — {{ u.username }}</span>
            <span class="user-pick-name" v-else>{{ u.username }}</span>{{ u.is_mj ? " (MJ)" : "" }}
          </label>
        </div>
      </label>

      <p class="form-hint">Si aucun joueur n’est sélectionné : modification du catalogue global (tous).</p>

      <div class="modal-footer">
        <button class="button secondary" :disabled="loading" @click="emit('close')">Annuler</button>
        <button class="button" :disabled="loading" @click="emit('apply')">{{ loading ? "…" : "Appliquer" }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.player-search {
  margin-top: 6px;
}

.player-picker-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.player-picker-list {
  margin-top: 10px;
  max-height: 320px;
  overflow-y: auto;
  padding-right: 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.player-picker-list label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.user-pick-name {
  display: block;
  line-height: 1.2;
}
</style>

