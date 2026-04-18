<script setup>
defineProps({
  ouverte: { type: Boolean, default: false },
});
</script>

<template>
  <div
    v-show="ouverte"
    id="hint-tours-restants"
    class="tours-player-info"
    role="region"
    aria-label="Aide sur le nombre de tours restants"
  >
    <div class="tours-player-info-title">Comment indiquer une durée ?</div>
    <ul class="tours-player-info-list">
      <li>
        <strong>Durée illimitée</strong> (défaut) : laissez le champ vide après modification, le symbole
        <strong>∞</strong> réapparaît, ou utilisez le bouton « Sans limite ». Vous pouvez aussi écrire
        <em>infini</em>, <em>illimité</em>, <em>sans limite</em>… (pas besoin du clavier ∞).
      </li>
      <li>
        <strong>Durée limitée</strong> : saisissez un <strong>nombre entier strictement positif</strong> (ex.
        <strong>6</strong> pour 6 tours). Autre texte ou valeur invalide → retour à l’illimité.
      </li>
    </ul>
  </div>
</template>

<style scoped>
.tours-player-info {
  margin: 10px 0 8px;
  padding: 10px 12px 10px 14px;
  font-size: 13px;
  line-height: 1.5;
  color: #cbd5e1;
  background: #0f172a;
  border: 1px solid #334155;
  border-left: 4px solid #38bdf8;
  border-radius: 8px;
  max-width: 100%;
}
.tours-player-info-title {
  font-weight: 700;
  font-size: 13px;
  color: #e2e8f0;
  margin-bottom: 8px;
}
.tours-player-info-list {
  margin: 0;
  padding-left: 1.15em;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.tours-player-info-list li {
  margin: 0;
}
</style>
