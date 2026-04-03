<script setup>
defineProps({
  open: { type: Boolean, required: true },
  selectedCount: { type: Number, required: true },
  err: { type: String, required: true },
  loading: { type: Boolean, required: true },
  modMode: { type: String, required: true },
  pct: { type: Number, required: true },
  userSearch: { type: String, required: true },
  usersVisible: { type: Array, required: true },
  currentUserIdStr: { type: String, required: true },
  userSelected: { type: Function, required: true },
  canBulkSelectUsers: { type: Boolean, required: true },
  allUsersSelected: { type: Boolean, required: true },
  previewLoading: { type: Boolean, required: true },
  previewErr: { type: String, required: true },
  /** { key, title, players: [{ key, nom, color, currentPct, newPct, isDefault, invalid }] }[] */
  previewPanels: { type: Array, required: true },
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

function fmtPct(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "?";
  return Number.isInteger(n) ? String(n) : n.toFixed(1);
}
</script>

<template>
  <div v-if="open" class="modal-overlay" @click.self="emit('close')">
    <div class="modal modal-bulk-split">

      <!-- ── Colonne gauche : formulaire ── -->
      <div class="bulk-modal-left">
        <h3 class="modal-title">Prix marché — modificateur % (ressource)</h3>
        <p class="modal-hint">
          S'applique aux <strong>{{ selectedCount }}</strong> ressource(s) sélectionnée(s).
        </p>
        <p v-if="err" class="error">{{ err }}</p>

        <div class="cible-mod-block">
          <div class="cible-mod-title">Mise à jour</div>
          <label class="radio-line">
            <input :checked="modMode === 'set'" type="radio" value="set" @change="emit('update:modMode', 'set')" />Définir
          </label>
          <label class="radio-line">
            <input :checked="modMode === 'add'" type="radio" value="add" @change="emit('update:modMode', 'add')" />Ajouter
          </label>
          <label class="radio-line">
            <input :checked="modMode === 'remove'" type="radio" value="remove" @change="emit('update:modMode', 'remove')" />Retirer
          </label>
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
            @focus="(e) => e.target.select()"
            @click="(e) => e.target.select()"
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
              <span class="user-pick-name" v-else>{{ u.username }}</span>
              {{ u.is_mj ? " (MJ)" : "" }}
            </label>
          </div>
        </label>

        <p class="form-hint">Si aucun joueur n'est sélectionné : modification du catalogue global (tous).</p>

        <div class="modal-footer">
          <button class="button secondary" :disabled="loading" @click="emit('close')">Annuler</button>
          <button class="button" :disabled="loading" @click="emit('apply')">
            {{ loading ? "…" : "Appliquer" }}
          </button>
        </div>
      </div>

      <!-- ── Colonne droite : aperçu des modifications ── -->
      <aside class="bulk-modal-right">
        <div class="bulk-preview-head">
          <span class="bulk-preview-title">Aperçu de la modification</span>
          <span v-if="previewLoading" class="bulk-preview-muted">Chargement…</span>
        </div>

        <p v-if="previewErr" class="error bulk-preview-err">{{ previewErr }}</p>

        <p v-if="!previewLoading && selectedCount === 0" class="bulk-preview-empty">
          Sélectionnez des ressources pour voir l'aperçu.
        </p>

        <div v-else class="bulk-preview-scroll">
          <div
            v-for="panel in previewPanels"
            :key="panel.key"
            class="bulk-preview-panel"
          >
            <div class="bulk-preview-resource-title">{{ panel.title }}</div>

            <div
              v-for="p in panel.players"
              :key="p.key"
              class="bulk-preview-player-row"
            >
              <span class="bulk-preview-dot" :style="{ background: p.color }" />

              <span class="bulk-preview-player-name">{{ p.nom }}</span>
              <span v-if="p.isDefault" class="bulk-preview-default">(100 % — défaut)</span>

              <span class="bulk-preview-pcts">
                <span class="bulk-pct-before">{{ fmtPct(p.currentPct) }} %</span>
                <span class="bulk-pct-arrow">──→</span>
                <span
                  class="bulk-pct-after"
                  :class="{
                    'pct-up': p.newPct > p.currentPct,
                    'pct-down': p.newPct < p.currentPct,
                    'pct-same': Math.abs(p.newPct - p.currentPct) < 0.05,
                    'pct-invalid': p.invalid,
                  }"
                >
                  <template v-if="p.invalid">⚠ {{ fmtPct(p.newPct) }} %</template>
                  <template v-else>{{ fmtPct(p.newPct) }} %</template>
                </span>
              </span>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
/* ── Layout global ─────────────────────────────────────────── */
.modal-bulk-split {
  display: grid;
  grid-template-columns: minmax(380px, 1fr) minmax(340px, 1.1fr);
  gap: 20px;
  align-items: start;
  width: min(1060px, 100%);
  max-height: 92vh;
  overflow: hidden;
}

.bulk-modal-left {
  min-width: 0;
  max-height: 92vh;
  overflow-y: auto;
  padding-right: 4px;
}

.bulk-modal-right {
  min-width: 0;
  border-left: 1px solid rgba(148, 163, 184, 0.2);
  padding-left: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 92vh;
  overflow: hidden;
}

/* ── En-tête aperçu ───────────────────────────────────────── */
.bulk-preview-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.bulk-preview-title {
  font-size: 13px;
  font-weight: 700;
  color: #e2e8f0;
}

.bulk-preview-muted {
  font-size: 12px;
  color: #64748b;
}

.bulk-preview-err {
  margin: 0;
  font-size: 13px;
  flex-shrink: 0;
}

.bulk-preview-empty {
  font-size: 12px;
  color: #64748b;
  margin: 0;
  font-style: italic;
}

/* ── Scroll zone ─────────────────────────────────────────── */
.bulk-preview-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 12px;
  padding-right: 2px;
  scrollbar-width: thin;
  scrollbar-color: #334155 transparent;
}

.bulk-preview-scroll::-webkit-scrollbar { width: 5px; }
.bulk-preview-scroll::-webkit-scrollbar-track { background: transparent; }
.bulk-preview-scroll::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }

/* ── Panel ressource ─────────────────────────────────────── */
.bulk-preview-panel {
  background: #0f172a;
  border: 1px solid #1e2d42;
  border-radius: 10px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bulk-preview-resource-title {
  font-size: 13px;
  font-weight: 700;
  color: #e2e8f0;
  margin-bottom: 4px;
  padding-bottom: 8px;
  border-bottom: 1px solid #1e2d42;
}

/* ── Ligne joueur ────────────────────────────────────────── */
.bulk-preview-player-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 13px;
}

.bulk-preview-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
}

.bulk-preview-player-name {
  color: #cbd5e1;
  font-weight: 500;
  flex-shrink: 0;
}

.bulk-preview-default {
  color: #475569;
  font-size: 11px;
  font-style: italic;
  flex-shrink: 0;
}

/* Pousse les pourcentages à droite */
.bulk-preview-pcts {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.bulk-pct-before {
  color: #94a3b8;
  font-size: 13px;
}

.bulk-pct-arrow {
  color: #475569;
  font-size: 12px;
  letter-spacing: -1px;
}

.bulk-pct-after {
  font-weight: 700;
  font-size: 13px;
  min-width: 52px;
  text-align: right;
}

.pct-up { color: #34d399; }
.pct-down { color: #f87171; }
.pct-same { color: #94a3b8; }
.pct-invalid { color: #ef4444; }

/* ── Formulaire gauche ───────────────────────────────────── */
.player-search { margin-top: 6px; }

.player-picker-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.player-picker-list {
  margin-top: 10px;
  max-height: 220px;
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

@media (max-width: 980px) {
  .modal-bulk-split {
    grid-template-columns: 1fr;
    max-height: none;
    overflow-y: auto;
  }
  .bulk-modal-right {
    border-left: none;
    padding-left: 0;
    border-top: 1px solid rgba(148, 163, 184, 0.2);
    padding-top: 16px;
    max-height: none;
    overflow: visible;
  }
  .bulk-preview-scroll {
    max-height: 50vh;
  }
}
</style>
