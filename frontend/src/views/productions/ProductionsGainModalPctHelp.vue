<script setup>
defineProps({
  ouverte: { type: Boolean, default: false },
});
</script>

<template>
  <div
    v-show="ouverte"
    id="hint-mode-pourcentage"
    class="tours-player-info mode-pct-hint"
    role="region"
    aria-label="Aide sur le mode pourcentage"
  >
    <div class="mode-pct-hint-body">
      <p class="mode-pct-hint-title">Fonctionnement</p>
      <p class="mode-pct-hint-text">
        En mode <strong>pourcentage</strong>, la valeur s’applique à la
        <strong>production cumulée du tour</strong> (après les règles précédentes, par ordre des identifiants), pas au
        stock total.
      </p>
      <p class="mode-pct-hint-title">Arrondi et tirage</p>
      <p class="mode-pct-hint-text">
        Si le résultat n’est pas entier, il est <strong>tronqué vers le bas</strong> (partie entière) ; la
        <strong>partie décimale</strong> (ex. 0,3 pour 1,3) correspond à la probabilité d’ajouter
        <strong>+1</strong> lors du calcul de la production du tour.
      </p>
      <p class="mode-pct-hint-title">Exemples</p>
      <ul class="mode-pct-hint-list">
        <li>
          <strong>1,3</strong> → base <strong>1</strong> ; environ <strong>30&nbsp;%</strong> de chance que la ligne
          produise <strong>2</strong> pour ce tour.
        </li>
        <li>
          <strong>47,8</strong> → base <strong>47</strong> ; environ <strong>80&nbsp;%</strong> de chance d’obtenir
          <strong>48</strong>.
        </li>
      </ul>
      <p class="mode-pct-hint-text mode-pct-hint-foot">
        L’éventuel <strong>+1</strong> est comptabilisé avec la balise
        <strong>«&nbsp;Récolte fructueuse&nbsp;»</strong>.
      </p>
    </div>
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
.mode-pct-hint {
  margin-top: -4px;
  margin-bottom: 12px;
}
.mode-pct-hint-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.mode-pct-hint-title {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #94a3b8;
}
.mode-pct-hint-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: #cbd5e1;
}
.mode-pct-hint-foot {
  padding-top: 4px;
  border-top: 1px solid #334155;
  color: #e2e8f0;
}
.mode-pct-hint-list {
  margin: 0;
  padding-left: 1.2em;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  line-height: 1.5;
  color: #cbd5e1;
}
.mode-pct-hint-list li {
  margin: 0;
}
</style>
