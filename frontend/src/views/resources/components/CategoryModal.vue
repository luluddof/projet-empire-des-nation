<script setup>
const props = defineProps({
  open: { type: Boolean, required: true },
  catForm: { type: Object, required: true },
  catModMode: { type: String, required: true },
  erreurCat: { type: String, required: true },
  playerSearch: { type: String, required: true },
  playersVisible: { type: Array, required: true }, // [{id, username, is_mj}]
  currentUserIdStr: { type: String, required: true },
  playerUserSelected: { type: Function, required: true },
  canBulkSelectUsers: { type: Boolean, required: true },
  allUsersSelected: { type: Boolean, required: true },
  playerEtat: { type: Object, required: true }, // uid -> pct
  playerEtatLoading: { type: Boolean, required: true },
  playerEtatErreur: { type: String, required: true },
  selectedUserIds: { type: Array, required: true }, // string[]
  formatPct: { type: Function, required: true },
  utilisateursListe: { type: Array, required: true },
});

const emit = defineEmits([
  "close",
  "save",
  "reset-100",
  "update:nom",
  "update:modificateur_pct",
  "update:catModMode",
  "update:playerSearch",
  "toggle-player",
  "select-all-users",
  "clear-all-users",
]);

function getUsername(uid) {
  return props.utilisateursListe.find((u) => String(u.id) === String(uid))?.username || String(uid);
}
function currentPct(uid) {
  const v = props.playerEtat?.[uid];
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? n : 100;
}
function nextPctFromCurrent(cur) {
  const input = Number(props.catForm?.modificateur_pct);
  const delta = Number.isFinite(input) ? input : 0;
  let next;
  if (props.catModMode === "set") next = delta;
  else if (props.catModMode === "add") next = cur + delta;
  else next = cur - delta;
  return Math.max(10, next);
}
function barMaxPct(uid) {
  const cur = currentPct(uid);
  const next = nextPctFromCurrent(cur);
  return Math.max(200, cur, next);
}
function pctToBar(uid, pct) {
  const n = Number(pct);
  if (!Number.isFinite(n)) return 0;
  const max = barMaxPct(uid);
  return (Math.max(0, n) / max) * 100;
}
</script>

<template>
  <div v-if="open" class="modal-overlay" @click.self="emit('close')">
    <div class="modal modal-wide modal-split">
      <div class="modal-left">
        <h3 class="modal-title">{{ catForm.id == null ? "Nouvelle catégorie" : "Modifier la catégorie" }}</h3>
        <p v-if="erreurCat" class="error">{{ erreurCat }}</p>

        <label class="form-label">
          Nom
          <input class="input" :value="catForm.nom" @input="emit('update:nom', $event.target.value)" />
        </label>

        <div v-if="catForm.id != null" class="cible-mod-block">
          <div class="cible-mod-title">Mise à jour</div>
          <label class="radio-line"><input :checked="catModMode === 'set'" type="radio" value="set" @change="emit('update:catModMode','set')" />Définir</label>
          <label class="radio-line"><input :checked="catModMode === 'add'" type="radio" value="add" @change="emit('update:catModMode','add')" />Ajouter</label>
          <label class="radio-line"><input :checked="catModMode === 'remove'" type="radio" value="remove" @change="emit('update:catModMode','remove')" />Retirer</label>
        </div>

        <label class="form-label">
          <span v-if="catForm.id == null || catModMode === 'set'">Modificateur (%)</span>
          <span v-else>Delta (%)</span>
          <input
            class="input"
            type="number"
            step="0.1"
          :min="(catForm.id == null || catModMode === 'set') ? 10 : 0.1"
            :value="catForm.modificateur_pct"
            @focus="(e) => e.target.select()"
            @click="(e) => e.target.select()"
            @input="emit('update:modificateur_pct', Number($event.target.value))"
          />
        </label>

        <label v-if="catForm.id != null" class="form-label">
          Joueurs
          <input
            class="input player-search"
            type="text"
            placeholder="Rechercher un joueur…"
            :value="playerSearch"
            @input="emit('update:playerSearch', $event.target.value)"
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
            <label v-for="u in playersVisible" :key="u.id" class="checkbox-label user-pick-item">
              <input type="checkbox" :checked="playerUserSelected(u.id)" @change="emit('toggle-player', u.id)" />
              <span class="user-pick-name" v-if="String(u.id) === currentUserIdStr">Vous — {{ u.username }}</span>
              <span class="user-pick-name" v-else>{{ u.username }}</span>{{ u.is_mj ? " (MJ)" : "" }}
            </label>
          </div>
        </label>

        <p v-if="catForm.id == null || selectedUserIds.length === 0" class="form-hint">
          Propagation automatique sur toutes les ressources liées.
        </p>
        <p v-else class="form-hint">
          Applique uniquement la surcharge de catégorie aux joueurs sélectionnés (le catalogue global reste inchangé).
        </p>

        <div class="modal-footer">
          <button class="button secondary" @click="emit('close')">Annuler</button>
          <button class="button secondary" type="button" @click="emit('reset-100')">À 100 %</button>
          <button class="button" @click="emit('save')">Enregistrer</button>
        </div>
      </div>

      <aside v-if="catForm.id != null" class="modal-right">
        <div class="evo-title">Évolution (joueurs concernés)</div>
        <div v-if="selectedUserIds.length === 0" class="muted evo-empty">
          Sélectionne un ou plusieurs joueurs pour voir l’évolution (avant → après).
        </div>
        <div v-else class="evo-list">
          <div v-for="uid in selectedUserIds" :key="uid" class="evo-row">
            <div class="evo-row-top">
              <div class="evo-name">
                <span v-if="String(uid) === currentUserIdStr">Vous — {{ getUsername(uid) }}</span>
                <span v-else>{{ getUsername(uid) }}</span>
              </div>
              <div class="evo-values">
                <span class="evo-old">{{ formatPct(currentPct(uid)) }}</span>
                <span class="evo-arrow">→</span>
                <span class="evo-new">{{ formatPct(nextPctFromCurrent(currentPct(uid))) }}</span>
              </div>
            </div>

            <div class="evo-bar" aria-hidden="true">
              <div class="evo-bar-track"></div>
              <div class="evo-dot old" :style="{ left: pctToBar(uid, currentPct(uid)) + '%' }"></div>
              <div
                class="evo-dot new"
                :style="{ left: pctToBar(uid, nextPctFromCurrent(currentPct(uid))) + '%' }"
              ></div>
            </div>
          </div>
        </div>
        <div v-if="playerEtatLoading" class="muted">Chargement…</div>
        <div v-if="playerEtatErreur" class="error">{{ playerEtatErreur }}</div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.modal-split {
  display: grid;
  grid-template-columns: minmax(420px, 1fr) 360px;
  gap: 16px;
  align-items: start;
  width: min(960px, 100%);
}

@media (max-width: 980px) {
  .modal-split {
    grid-template-columns: 1fr;
  }
  .modal-right {
    border-top: 1px solid rgba(148, 163, 184, 0.18);
    padding-top: 12px;
  }
}

.modal-right {
  max-height: 560px;
  overflow: auto;
  padding-left: 10px;
}

.evo-title {
  font-weight: 800;
  font-size: 13px;
  color: #cbd5e1;
  margin-bottom: 10px;
}

.evo-empty {
  padding: 10px 0;
}

.evo-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.evo-row {
  border: 1px solid rgba(51, 65, 85, 0.8);
  background: rgba(15, 23, 42, 0.25);
  border-radius: 12px;
  padding: 10px 10px;
}

.evo-row-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.evo-name {
  color: #e2e8f0;
  font-weight: 700;
  font-size: 13px;
}

.evo-values {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-variant-numeric: tabular-nums;
}

.evo-old {
  color: #cbd5e1;
}

.evo-arrow {
  color: #94a3b8;
}

.evo-new {
  color: #93c5fd;
  font-weight: 800;
}

.evo-bar {
  position: relative;
  height: 18px;
  margin-top: 8px;
}

.evo-bar-track {
  position: absolute;
  left: 0;
  right: 0;
  top: 8px;
  height: 2px;
  background: rgba(148, 163, 184, 0.25);
  border-radius: 999px;
}

.evo-dot {
  position: absolute;
  top: 4px;
  width: 10px;
  height: 10px;
  border-radius: 999px;
  transform: translateX(-50%);
  border: 2px solid rgba(2, 6, 23, 0.8);
}

.evo-dot.old {
  background: #e2e8f0;
}

.evo-dot.new {
  background: #60a5fa;
}

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

