<script setup>
defineProps({
  evenements: { type: Array, default: () => [] },
});
defineEmits(["edit", "supprimer", "retirer-joueur"]);

function libelleCible(e) {
  const c = String(e.cible || "aucun").trim().toLowerCase();
  if (c === "tous") return "Tous les joueurs (non-MJ)";
  if (c === "joueurs") {
    const n = (e.cible_utilisateur_ids || []).length;
    return n ? `${n} joueur(s) sélectionné(s)` : "Joueurs (liste vide)";
  }
  return "Aucun";
}
</script>

<template>
  <section class="card">
    <h3 class="card-title">Liste</h3>
    <div v-if="evenements.length === 0" class="muted">Aucun évènement.</div>
    <div v-else class="events-list">
      <div v-for="e in evenements" :key="e.id" class="event-item">
        <div class="event-top">
          <div class="event-badges">
            <span class="tag" :class="e.actif ? 'tag-ok' : 'tag-off'">{{ e.actif ? "Actif" : "Inactif" }}</span>
            <span v-if="e.brouillon" class="tag tag-draft">Brouillon</span>
            <span v-else class="tag tag-cible">{{ libelleCible(e) }}</span>
          </div>
          <div class="event-actions">
            <button type="button" class="button secondary small" @click="$emit('edit', e)">Modifier</button>
            <button type="button" class="button secondary small danger" @click="$emit('supprimer', e)">Supprimer</button>
          </div>
        </div>
        <h4 class="event-title-text">{{ e.titre?.trim() ? e.titre : "(Sans titre)" }}</h4>
        <p v-if="e.description?.trim()" class="event-desc line-clamp">{{ e.description }}</p>
        <p v-else class="event-desc muted-desc">Aucune description.</p>
        <div v-if="e.joueurs?.length" class="joueurs-liste">
          <div class="impact-title">Joueurs</div>
          <ul class="joueurs-ul">
            <li v-for="j in e.joueurs" :key="j.id">
              <span>{{ j.username || j.utilisateur_id }}</span>
              <span class="muted"
                >délai {{ j.delai_tours }} · reste
                {{ j.tours_restants == null ? "∞" : j.tours_restants }} · {{ j.actif ? "inclus" : "retiré" }}</span
              >
              <button
                v-if="j.actif"
                type="button"
                class="button secondary small danger"
                @click="$emit('retirer-joueur', e.id, j.utilisateur_id)"
              >
                Retirer
              </button>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.card-title {
  margin-top: 0;
}
.muted {
  color: #94a3b8;
}
.muted-desc {
  font-size: 13px;
  font-style: italic;
}
.impact-title {
  font-weight: 800;
  color: #e2e8f0;
  margin-bottom: 10px;
}
.events-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.event-item {
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 12px;
  background: rgba(15, 23, 42, 0.2);
}
.event-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  flex-wrap: wrap;
}
.event-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  min-width: 0;
}
.event-actions {
  display: inline-flex;
  gap: 8px;
  flex-shrink: 0;
}
.event-title-text {
  margin: 0.75rem 0 0.35rem;
  font-size: 1.1rem;
  font-weight: 700;
  color: #f1f5f9;
  line-height: 1.35;
  word-break: break-word;
}
.event-desc {
  margin: 0;
  color: #cbd5e1;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.45;
}
.line-clamp {
  display: -webkit-box;
  -webkit-line-clamp: 6;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.joueurs-liste {
  margin-top: 12px;
}
.joueurs-ul {
  margin: 0;
  padding-left: 1.2em;
  color: #cbd5e1;
}
.joueurs-ul li {
  margin: 6px 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid #334155;
}
.tag-ok {
  color: #bbf7d0;
  border-color: rgba(34, 197, 94, 0.35);
  background: rgba(34, 197, 94, 0.12);
}
.tag-off {
  color: #fca5a5;
  border-color: rgba(239, 68, 68, 0.35);
  background: rgba(239, 68, 68, 0.12);
}
.tag-draft {
  color: #fde68a;
  border-color: rgba(251, 191, 36, 0.35);
  background: rgba(251, 191, 36, 0.12);
}
.tag-cible {
  color: #bae6fd;
  border-color: rgba(56, 189, 248, 0.35);
  background: rgba(56, 189, 248, 0.1);
}
</style>
