<script setup>
const props = defineProps({
  open: { type: Boolean, required: true },
  modeEdition: { type: Boolean, required: true },
  erreur: { type: String, required: true },
  form: { type: Object, required: true },
  resModMode: { type: String, required: true },
  categories: { type: Array, required: true },
  formatPct: { type: Function, required: true },
  // joueurs
  playerSearch: { type: String, required: true },
  playersVisible: { type: Array, required: true }, // [{id, username}]
  currentUserIdStr: { type: String, required: true },
  userSelected: { type: Function, required: true },
  canBulkSelectUsers: { type: Boolean, required: true },
  allUsersSelected: { type: Boolean, required: true },
  // état joueurs
  playerEtat: { type: Object, required: true }, // uid -> {modificateur_pct,facteur_prix}
  playerEtatLoading: { type: Boolean, required: true },
  playerEtatErreur: { type: String, required: true },
  // aperçu
  previewFacteur: { type: Number, required: true },
  preview: { type: Object, required: true },
  formatFlorin: { type: Function, required: true },
  formatFlorinExact: { type: Function, required: true },
  utilisateursListe: { type: Array, required: true },
});

const emit = defineEmits([
  "close",
  "save",
  "apply-categories-neutral",
  "update:nom",
  "update:type",
  "update:prix_base",
  "update:modificateur_pct",
  "update:resModMode",
  "update:playerSearch",
  "toggle-user",
  "select-all-users",
  "clear-all-users",
  "set-categorie-checked",
]);

function getUsername(uid) {
  return props.utilisateursListe.find((u) => String(u.id) === String(uid))?.username || String(uid);
}
function currentPct(uid) {
  const v = props.playerEtat?.[uid]?.modificateur_pct;
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? n : 100;
}
function nextPctFromCurrent(cur) {
  const input = Number(props.form?.modificateur_pct);
  const delta = Number.isFinite(input) ? input : 0;
  let next;
  if (props.resModMode === "set") next = delta;
  else if (props.resModMode === "add") next = cur + delta;
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
        <h3 class="modal-title">{{ modeEdition ? "Modifier la ressource" : "Nouvelle ressource" }}</h3>
        <p v-if="erreur" class="error">{{ erreur }}</p>

        <div class="form-grid">
          <label>Nom<input class="input" :value="form.nom" @input="emit('update:nom', $event.target.value)" /></label>
          <label>Type
            <select class="select" :value="form.type" @change="emit('update:type', $event.target.value)">
              <option>Première</option>
              <option>Manufacturé</option>
            </select>
          </label>
          <label>Prix de base (ƒ, entier)
            <input
              class="input"
              type="number"
              min="0"
              :value="form.prix_base"
              @focus="(e) => e.target.select()"
              @click="(e) => e.target.select()"
              @input="emit('update:prix_base', Number($event.target.value))"
            />
          </label>
          <label>
            <span v-if="!modeEdition || resModMode === 'set'">% modificateur ressource</span>
            <span v-else>Delta (%) sur % ressource</span>
            <input
              class="input"
              type="number"
              step="0.1"
              :min="(!modeEdition || resModMode === 'set') ? 10 : 0.1"
              :value="form.modificateur_pct"
              @focus="(e) => e.target.select()"
              @click="(e) => e.target.select()"
              @input="emit('update:modificateur_pct', Number($event.target.value))"
            />
          </label>
        </div>

        <div v-if="modeEdition" class="cible-mod-block">
          <div class="cible-mod-title">Mise à jour</div>
          <label class="radio-line"><input :checked="resModMode === 'set'" type="radio" value="set" @change="emit('update:resModMode','set')" />Définir</label>
          <label class="radio-line"><input :checked="resModMode === 'add'" type="radio" value="add" @change="emit('update:resModMode','add')" />Ajouter</label>
          <label class="radio-line"><input :checked="resModMode === 'remove'" type="radio" value="remove" @change="emit('update:resModMode','remove')" />Retirer</label>

        <div class="cible-mod-title">
          À l’enregistrement,
          {{ resModMode === "set" ? "appliquer ce % ressource à :" : "ajouter/retirer ce delta sur le % ressource à :" }}
        </div>

        <label class="form-label">
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
          <div class="player-picker-list is-vertical">
            <label v-for="u in playersVisible" :key="u.id" class="checkbox-label user-pick-item">
              <input type="checkbox" :checked="userSelected(u.id)" @change="emit('toggle-user', u.id)" />
              <span class="user-pick-name" v-if="String(u.id) === currentUserIdStr">Vous — {{ u.username }}</span>
              <span class="user-pick-name" v-else>{{ u.username }}</span>
            </label>
          </div>
        </label>

        <p class="form-hint">
          Si aucun joueur n’est sélectionné : modification du catalogue global (tous). Si tu sélectionnes des joueurs,
          tu modifies une surcharge par joueur : le tableau MJ (catalogue) reste global, et l’état est visible ci‑dessous.
        </p>

        </div>

        <p class="form-hint">Nouvelle ressource : 100 % par défaut ; les catégories cochées appliquent leur % dans le facteur total.</p>

        <div class="cat-pick">
          <div class="cat-pick-title">Catégories</div>
          <div class="cat-pick-grid">
            <label v-for="c in categories" :key="c.id" class="checkbox-label cat-pick-item">
              <input
                type="checkbox"
                :checked="form.categorie_ids.includes(c.id)"
                @change="emit('set-categorie-checked', c.id, $event.target.checked)"
              />
              {{ c.nom }} ({{ formatPct(c.modificateur_pct) }})
            </label>
          </div>
        </div>

        <div v-if="modeEdition" class="modal-actions-row">
          <button type="button" class="button secondary" @click="emit('apply-categories-neutral')">
            Remettre % ressource à 100 % (neutre)
          </button>
        </div>

        <div class="preview-box">
          <strong>Aperçu</strong>
          <span>Facteur ×{{ previewFacteur.toFixed(4) }}</span>
          <span :title="formatFlorinExact(preview.prix_modifie)">Prix modifié : {{ formatFlorin(preview.prix_modifie) }}</span>
          <span :title="formatFlorinExact(preview.prix_achat)">Prix d’achat : {{ formatFlorin(preview.prix_achat) }}</span>
          <span :title="formatFlorinExact(preview.prix_lointain)">Si lointain : {{ formatFlorin(preview.prix_lointain) }}</span>
        </div>

        <div class="modal-footer">
          <button class="button secondary" @click="emit('close')">Annuler</button>
          <button class="button" @click="emit('save')">Enregistrer</button>
        </div>
      </div>

      <aside v-if="modeEdition" class="modal-right">
        <div class="evo-title">Évolution (joueurs concernés)</div>
        <div v-if="(form.utilisateur_ids || []).length === 0" class="muted evo-empty">
          Sélectionne un ou plusieurs joueurs pour voir l’évolution (avant → après).
        </div>
        <div v-else class="evo-list">
          <div v-for="uid in form.utilisateur_ids" :key="uid" class="evo-row">
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
  grid-template-columns: minmax(520px, 1fr) 380px;
  gap: 16px;
  align-items: start;
  width: min(1040px, 100%);
}

@media (max-width: 1100px) {
  .modal-split {
    grid-template-columns: 1fr;
  }
  .modal-right {
    border-top: 1px solid rgba(148, 163, 184, 0.18);
    padding-top: 12px;
  }
}

.modal-right {
  max-height: 720px;
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
  max-height: 380px; /* ~20 joueurs visibles avant scroll */
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

