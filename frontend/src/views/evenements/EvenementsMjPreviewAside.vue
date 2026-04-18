<script setup>
defineProps({
  loading: { type: Boolean, default: false },
  erreur: { type: String, default: "" },
  /** Réponse API { blocs, message, ... } */
  data: { type: Object, default: null },
});
</script>

<template>
  <aside class="preview-aside" aria-label="Aperçu des effets sur les joueurs ciblés">
    <h3 class="preview-title">Aperçu</h3>
    <p class="preview-lead">
      Les colonnes correspondent aux comptes cochés dans <strong>Joueurs concernés</strong> — la même cible que pour
      l’évènement entier. Chaque bloc : effet sur le <strong>prix</strong> (% catégorie ou % ressource) ou sur la
      <strong>somme des productions « fixe »</strong> (unités / tour).
    </p>

    <p v-if="erreur" class="error preview-err">{{ erreur }}</p>
    <p v-else-if="loading" class="preview-muted">Calcul de l’aperçu…</p>
    <template v-else-if="data">
      <p v-if="data.message && !(data.blocs || []).length" class="preview-muted">{{ data.message }}</p>
      <p v-else-if="!(data.blocs || []).length" class="preview-muted">
        Ajoutez au moins une ligne d’impact (catégorie, ressource ou production) avec des champs valides pour voir
        l’aperçu.
      </p>
      <div v-else class="preview-blocs">
        <section v-for="(b, idx) in data.blocs" :key="`${b.kind}-${b.index}-${idx}`" class="preview-bloc">
          <header class="preview-bloc-head">
            <span class="preview-bloc-kind">{{ b.kind === "categorie" ? "Catégorie" : b.kind === "ressource" ? "Ressource (prix)" : "Production" }}</span>
            <h4 class="preview-bloc-title">{{ b.titre }}</h4>
            <p v-if="b.sous_titre" class="preview-bloc-sub">{{ b.sous_titre }}</p>
          </header>
          <ul class="preview-rows">
            <li v-for="j in b.joueurs" :key="j.utilisateur_id" class="preview-row">
              <span class="preview-name">{{ j.username }}</span>
              <template v-if="b.kind === 'production'">
                <template v-if="j.avant_qpt != null">
                  <span class="preview-num">{{ j.avant_qpt }}</span>
                  <span class="preview-arrow">──→</span>
                  <span class="preview-num preview-num-after">{{ j.apres_qpt }}</span>
                </template>
                <span v-else class="preview-note">{{ j.note || "—" }}</span>
              </template>
              <template v-else>
                <span class="preview-pct">{{ j.avant_pct }} %</span>
                <span class="preview-arrow">──→</span>
                <span class="preview-pct preview-pct-after">{{ j.apres_pct }} %</span>
              </template>
            </li>
          </ul>
        </section>
      </div>
    </template>
  </aside>
</template>

<style scoped>
.preview-aside {
  position: sticky;
  top: 12px;
  align-self: start;
  min-height: 280px;
  max-height: min(88vh, 920px);
  overflow: auto;
  padding: 14px 14px 18px;
  border: 1px solid #334155;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.55);
  box-sizing: border-box;
}
.preview-title {
  margin: 0 0 8px;
  font-size: 1rem;
  font-weight: 800;
  color: #e2e8f0;
}
.preview-lead {
  margin: 0 0 14px;
  font-size: 12px;
  line-height: 1.45;
  color: #94a3b8;
}
.preview-lead strong {
  color: #cbd5e1;
}
.preview-muted {
  margin: 0;
  font-size: 13px;
  color: #64748b;
  font-style: italic;
}
.preview-err {
  margin: 0 0 8px;
  font-size: 13px;
}
.preview-blocs {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.preview-bloc {
  border: 1px solid rgba(51, 65, 85, 0.9);
  border-radius: 12px;
  padding: 10px 12px;
  background: rgba(2, 6, 23, 0.35);
}
.preview-bloc-head {
  margin-bottom: 10px;
}
.preview-bloc-kind {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #7dd3fc;
  margin-bottom: 4px;
}
.preview-bloc-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #f1f5f9;
  line-height: 1.35;
}
.preview-bloc-sub {
  margin: 6px 0 0;
  font-size: 11px;
  color: #94a3b8;
  line-height: 1.4;
}
.preview-rows {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.preview-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto auto;
  gap: 6px 8px;
  align-items: baseline;
  font-size: 13px;
  color: #cbd5e1;
}
.preview-name {
  font-weight: 600;
  color: #e2e8f0;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.preview-pct,
.preview-num {
  font-variant-numeric: tabular-nums;
  text-align: right;
}
.preview-pct-after,
.preview-num-after {
  color: #93c5fd;
  font-weight: 700;
}
.preview-arrow {
  color: #64748b;
  font-size: 12px;
  text-align: center;
}
.preview-note {
  grid-column: 2 / -1;
  font-size: 12px;
  color: #94a3b8;
}
</style>
