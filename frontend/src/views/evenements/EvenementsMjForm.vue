<script setup>
import { computed, ref, toRef } from "vue";
import { usePlayerPicker } from "../resources/composables/usePlayerPicker.js";
import EvenementsMjPreviewAside from "./EvenementsMjPreviewAside.vue";

const props = defineProps({
  form: { type: Object, required: true },
  categories: { type: Array, default: () => [] },
  ressources: { type: Array, default: () => [] },
  utilisateurs: { type: Array, default: () => [] },
  currentUserIdStr: { type: String, default: "" },
  previewData: { type: Object, default: null },
  previewLoading: { type: Boolean, default: false },
  previewErreur: { type: String, default: "" },
});

defineEmits(["reset", "save", "cancel", "toggle-joueur", "add-categorie", "add-ressource", "add-production"]);

const userSearch = ref("");

const utilisateursListe = computed(() => props.utilisateurs || []);
const selectedIdsRef = toRef(props.form, "cible_utilisateur_ids");
const currentUserIdStrRef = computed(() => props.currentUserIdStr ?? "");

const { visible: joueursListeVisible } = usePlayerPicker({
  utilisateursListeRef: utilisateursListe,
  currentUserIdStrRef,
  selectedIdsRef,
  searchRef: userSearch,
});

const allUsersSelected = computed(() => {
  const u = utilisateursListe.value;
  if (!u.length) return false;
  const s = new Set(selectedIdsRef.value.map(String));
  return u.every((x) => s.has(String(x.id)));
});

function toggleToutLeMonde() {
  const all = utilisateursListe.value.map((u) => u.id);
  if (!all.length) return;
  if (allUsersSelected.value) {
    props.form.cible_utilisateur_ids = [];
  } else {
    props.form.cible_utilisateur_ids = [...all];
  }
}

function userSelected(uid) {
  return props.form.cible_utilisateur_ids.map(String).includes(String(uid));
}

/** Champ nombre nullable : vide ⇒ illimité (null), comme un gain passif. */
function setProductionToursRestants(row, event) {
  const raw = event?.target?.value;
  if (raw === "" || raw == null) {
    row.tours_restants = null;
    return;
  }
  const n = Number(raw);
  row.tours_restants = Number.isFinite(n) && n > 0 ? n : null;
}
</script>

<template>
  <section class="card evenements-form-card">
    <div class="evenements-split">
      <div class="evenements-main">
    <h3 class="card-title">{{ form.id ? "Modifier un évènement" : "Créer un évènement" }}</h3>

    <label class="form-label">
      Titre
      <input v-model="form.titre" class="input" />
    </label>

    <label class="form-label">
      Description (texte libre)
      <textarea v-model="form.description" class="input" rows="4"></textarea>
    </label>

    <div class="switch-rows">
      <div v-if="!form.deja_publie" class="switch-row">
        <div class="switch-text">
          <div class="switch-title">Brouillon</div>
          <div class="switch-desc">
            Tant qu’il est activé, aucun joueur n’est affecté — vous préparez l’évènement pour plus tard. Après la
            première publication, ce réglage disparaît : seul <strong>Actif</strong> compte.
          </div>
        </div>
        <label class="switch switch-brouillon">
          <input v-model="form.brouillon" type="checkbox" />
          <span class="switch-slider" aria-hidden="true" />
        </label>
      </div>
      <p v-else class="brouillon-locked">
        Cet évènement a déjà été publié : le mode brouillon n’est plus proposé. Utilisez uniquement l’interrupteur
        <strong>Actif</strong> ci‑dessous (ou retirez tous les joueurs ciblés si l’évènement ne doit toucher personne).
      </p>

      <div class="switch-row">
        <div class="switch-text">
          <div class="switch-title">Actif</div>
          <div class="switch-desc">
            Interrupteur global : désactivé, aucun effet ne s’applique pour personne, même si des joueurs sont listés.
          </div>
        </div>
        <label class="switch switch-actif">
          <input v-model="form.actif" type="checkbox" />
          <span class="switch-slider" aria-hidden="true" />
        </label>
      </div>
    </div>

    <div class="joueurs-pick">
      <div class="impact-title">Joueurs concernés</div>
      <p class="hint">
        <strong>C’est cette liste qui définit qui est impacté par l’évènement</strong> une fois publié (hors brouillon) :
        les mêmes comptes reçoivent <strong>tous</strong> les effets ci‑dessous — modificateurs de prix (% catégorie, %
        ressource) <strong>et</strong> productions (gains passifs). « Tout le monde » coche ou décoche toute la liste ;
        aucune case cochée = personne ciblé. En brouillon, vous préparez la liste pour plus tard.
      </p>
      <label class="form-label">
        Rechercher par nom
        <input
          v-model.trim="userSearch"
          class="input player-search"
          type="search"
          placeholder="Rechercher un joueur…"
          autocomplete="off"
        />
      </label>

      <label class="checkbox-label row-tout-le-monde">
        <input type="checkbox" :checked="allUsersSelected" @change="toggleToutLeMonde" />
        <span>
          <strong>Tout le monde</strong>
          — sélectionne ou désélectionne tous les comptes de la liste
        </span>
      </label>

      <div class="player-picker-list">
        <label v-for="u in joueursListeVisible" :key="u.id" class="checkbox-label user-pick-item">
          <input type="checkbox" :checked="userSelected(u.id)" @change="$emit('toggle-joueur', u.id)" />
          <span class="user-pick-name" v-if="String(u.id) === currentUserIdStr">Vous — {{ u.username }}</span>
          <span class="user-pick-name" v-else>{{ u.username }}</span>
          <span v-if="u.is_mj" class="mj-badge">MJ</span>
        </label>
      </div>
    </div>

    <div class="timing-row">
      <label class="form-label">
        Délai avant effets (tours)
        <input v-model.number="form.delai_tours" type="number" min="0" class="input" />
      </label>
      <label class="form-label checkbox-label timing-illim">
        <input v-model="form.tours_restants_illimite" type="checkbox" />
        Durée illimitée (jusqu'à MJ / joueur retiré)
      </label>
      <label v-if="!form.tours_restants_illimite" class="form-label">
        Durée des effets (tours après le délai)
        <input v-model.number="form.tours_restants" type="number" min="1" class="input" />
      </label>
    </div>

    <div class="impacts-grid">
      <div class="impact-block">
        <div class="impact-title">Prix pour les joueurs — modificateur des catégories (%)</div>
        <p class="hint">
          Pour les comptes de <strong>Joueurs concernés</strong> uniquement : delta sur la part <strong>catégorie</strong>
          du prix affiché (pas des unités produites). Même idée que le bulk prix par catégorie.
        </p>
        <button type="button" class="button secondary small" @click="$emit('add-categorie')">+ Ajouter</button>
        <div v-for="(x, i) in form.impacts.categories" :key="i" class="impact-row">
          <select v-model.number="x.categorie_id" class="select">
            <option :value="null" disabled>Catégorie…</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.nom }}</option>
          </select>
          <select v-model="x.operation" class="select">
            <option value="add">Ajouter (%)</option>
            <option value="remove">Retirer (%)</option>
          </select>
          <input v-model.number="x.valeur_pct" type="number" class="input small" />
          <button type="button" class="button secondary small danger" @click="form.impacts.categories.splice(i, 1)">
            Retirer
          </button>
        </div>
      </div>

      <div class="impact-block">
        <div class="impact-title">Prix pour les joueurs — % propre à une ressource</div>
        <p class="hint">
          Pour les comptes de <strong>Joueurs concernés</strong> uniquement : delta sur le <strong>% ressource</strong>
          du prix (hors catégories). Ce n’est pas une production : pas de quantité / tour ici.
        </p>
        <button type="button" class="button secondary small" @click="$emit('add-ressource')">+ Ajouter</button>
        <div v-for="(x, i) in form.impacts.ressources" :key="i" class="impact-row">
          <select v-model.number="x.ressource_id" class="select">
            <option :value="null" disabled>Ressource…</option>
            <option v-for="r in ressources" :key="r.id" :value="r.id">{{ r.nom }}</option>
          </select>
          <select v-model="x.operation" class="select">
            <option value="add">Ajouter (%)</option>
            <option value="remove">Retirer (%)</option>
          </select>
          <input v-model.number="x.valeur_pct" type="number" class="input small" />
          <button type="button" class="button secondary small danger" @click="form.impacts.ressources.splice(i, 1)">
            Retirer
          </button>
        </div>
      </div>

      <div class="impact-block">
        <div class="impact-title">Gains passifs — nouvelles productions (quantités / tour)</div>
        <p class="hint">
          Pour les comptes de <strong>Joueurs concernés</strong> uniquement : une <strong>ligne de production</strong>
          (gain passif) est créée <strong>par joueur coché</strong> — mêmes paramètres (ressource, mode, quantités,
          délais). Comme à l’écran Productions, mais la cible est toujours la liste ci‑dessus.
        </p>
        <button type="button" class="button secondary small" @click="$emit('add-production')">+ Ajouter</button>
        <div
          v-for="(x, i) in form.impacts.productions"
          :key="i"
          class="impact-row impact-row-prod"
          :class="{ 'prod-row-divider': i > 0 }"
        >
          <div class="prod-field prod-field-wide">
            <span class="prod-label">Ressource produite</span>
            <select v-model.number="x.ressource_id" class="select prod-select">
              <option :value="null" disabled>Choisir une ressource…</option>
              <option v-for="r in ressources" :key="r.id" :value="r.id">{{ r.nom }}</option>
            </select>
          </div>
          <div class="prod-field">
            <span class="prod-label">Mode</span>
            <select v-model="x.mode_production" class="select prod-select">
              <option value="fixe">Quantité fixe / tour</option>
              <option value="pourcentage">Pourcentage / tour</option>
            </select>
          </div>
          <div class="prod-field">
            <span class="prod-label">Quantité / tour</span>
            <input v-model.number="x.quantite_par_tour" type="number" class="input small prod-num" min="0" step="1" />
          </div>
          <div class="prod-field">
            <span class="prod-label">Délai (tours)</span>
            <input
              v-model.number="x.delai_tours"
              type="number"
              class="input small prod-num"
              min="0"
              step="1"
              title="Nombre de tours avant que cette production ne commence à s’appliquer"
            />
          </div>
          <div class="prod-field">
            <span class="prod-label">Durée (tours)</span>
            <input
              class="input small prod-num"
              type="number"
              min="1"
              step="1"
              placeholder="vide = illimité"
              :value="x.tours_restants == null ? '' : x.tours_restants"
              title="Nombre de tours pendant lesquels la ligne est active après le délai ; laisser vide = illimité"
              @input="setProductionToursRestants(x, $event)"
            />
          </div>
          <label class="checkbox-label compact prod-actif">
            <input v-model="x.actif" type="checkbox" />
            Actif
          </label>
          <button type="button" class="button secondary small danger" @click="form.impacts.productions.splice(i, 1)">
            Retirer
          </button>
        </div>
      </div>
    </div>

    <div class="row-actions">
      <button type="button" class="button secondary" @click="$emit('cancel')">Annuler</button>
      <button type="button" class="button secondary" @click="$emit('reset')">Réinitialiser</button>
      <button type="button" class="button" @click="$emit('save')">Enregistrer</button>
    </div>
      </div>

      <EvenementsMjPreviewAside
        class="evenements-preview-slot"
        :loading="previewLoading"
        :erreur="previewErreur"
        :data="previewData"
      />
    </div>
  </section>
</template>

<style scoped>
.evenements-form-card {
  overflow: visible;
}
.evenements-split {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 360px);
  gap: 20px;
  align-items: start;
}
.evenements-main {
  min-width: 0;
}
.evenements-preview-slot {
  width: 100%;
}
@media (max-width: 1080px) {
  .evenements-split {
    grid-template-columns: 1fr;
  }
}
.full-width {
  width: 100%;
  margin-top: 6px;
}
.card-title {
  margin-top: 0;
}
.hint {
  font-size: 13px;
  color: #94a3b8;
  margin: 0 0 12px;
}
.row-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  flex-wrap: wrap;
  margin-top: 14px;
}
.timing-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  align-items: flex-end;
  margin-bottom: 12px;
}
.timing-illim {
  align-self: center;
}
.joueurs-pick {
  margin-bottom: 1rem;
}
.row-tout-le-monde {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: 10px;
  background: rgba(56, 189, 248, 0.08);
  margin-bottom: 10px;
  color: #e2e8f0;
  font-size: 14px;
}
.player-search {
  margin-top: 6px;
}
.player-picker-list {
  margin-top: 10px;
  max-height: 380px;
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
.mj-badge {
  font-size: 11px;
  color: #93c5fd;
  border: 1px solid rgba(147, 197, 253, 0.4);
  border-radius: 6px;
  padding: 0 6px;
  margin-left: 4px;
}
.impacts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  margin-top: 12px;
}
.impact-block {
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 12px;
  background: rgba(15, 23, 42, 0.25);
}
.impact-title {
  font-weight: 800;
  color: #e2e8f0;
  margin-bottom: 10px;
}
.impact-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 10px;
}
.impact-row-prod {
  align-items: flex-end;
  flex-wrap: wrap;
  padding-bottom: 4px;
}
.prod-row-divider {
  border-top: 1px solid rgba(51, 65, 85, 0.6);
  padding-top: 12px;
  margin-top: 4px;
}
.prod-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 118px;
}
.prod-field-wide {
  flex: 1 1 200px;
  min-width: 200px;
}
.prod-label {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.prod-select {
  width: 100%;
  min-width: 0;
}
.prod-num {
  width: 100%;
  min-width: 0;
}
.prod-actif {
  align-self: center;
  margin-bottom: 2px;
}
.input.small {
  width: 110px;
}
.checkbox-label.compact {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  color: #cbd5e1;
  font-size: 13px;
}
.switch-rows {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin: 14px 0 18px;
}
.switch-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid #334155;
  background: rgba(15, 23, 42, 0.35);
}
.switch-text {
  flex: 1 1 220px;
  min-width: 0;
}
.switch-title {
  font-weight: 800;
  color: #e2e8f0;
  margin-bottom: 4px;
}
.switch-desc {
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.45;
}
.brouillon-locked {
  margin: 0;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(251, 191, 36, 0.35);
  background: rgba(251, 191, 36, 0.08);
  color: #fde68a;
  font-size: 13px;
  line-height: 1.45;
}
.switch {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  flex-shrink: 0;
}
.switch input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}
.switch-slider {
  width: 48px;
  height: 26px;
  border-radius: 999px;
  background: #334155;
  border: 1px solid #475569;
  transition: background 0.15s ease;
  position: relative;
}
.switch-slider::after {
  content: "";
  position: absolute;
  width: 20px;
  height: 20px;
  left: 3px;
  top: 2px;
  border-radius: 50%;
  background: #e2e8f0;
  transition: transform 0.15s ease;
}
.switch-brouillon input:checked + .switch-slider {
  background: rgba(251, 191, 36, 0.35);
  border-color: rgba(251, 191, 36, 0.55);
}
.switch-actif input:checked + .switch-slider {
  background: rgba(34, 197, 94, 0.35);
  border-color: rgba(34, 197, 94, 0.55);
}
.switch input:checked + .switch-slider::after {
  transform: translateX(21px);
}
.switch input:focus-visible + .switch-slider {
  outline: 2px solid #38bdf8;
  outline-offset: 2px;
}
</style>
