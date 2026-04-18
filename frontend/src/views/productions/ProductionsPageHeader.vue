<script setup>
import MjViewSelect from "../../components/MjViewSelect.vue";

defineProps({
  isMj: { type: Boolean, default: false },
  mj: { type: Object, required: true },
  currentUserIdStr: { type: String, default: "" },
  ressourceIdFiltre: { type: [Number, null], default: null },
  nomRessourceFiltre: { type: String, default: "" },
  productionsQueryAll: { type: Object, default: () => ({}) },
});

defineEmits(["nouvelle-production"]);
</script>

<template>
  <div class="page-header">
    <div>
      <h2 class="page-title">Mes productions</h2>
      <p v-if="!ressourceIdFiltre" class="page-subtitle">
        Gains et pertes passifs par <strong>tour</strong> (mercredi & samedi 00h00). Vous pouvez définir
        <strong>plusieurs règles distinctes</strong> pour la même ressource (ex. +10 et −2 par tour).
      </p>
      <p v-else class="page-subtitle page-subtitle-filtre">
        <span class="page-subtitle-filtre-text">
          Vue actuelle : <strong class="page-ressource-courante">{{ nomRessourceFiltre }}</strong>
          — une seule ressource à la fois.
        </span>
        <router-link
          class="button secondary small productions-back-all"
          :to="{ path: '/productions', query: productionsQueryAll }"
        >
          ← Toutes les productions
        </router-link>
      </p>
    </div>
    <div class="header-actions">
      <MjViewSelect
        v-if="isMj"
        :open="mj.mjVueOpen"
        :label="mj.mjVueLabel"
        :search="mj.mjVueSearch"
        :options="mj.mjVueAutres"
        :current-choice="mj.mjVueChoix"
        :current-user-id-str="currentUserIdStr"
        :show-global="false"
        @update:open="(v) => (mj.mjVueOpen = v)"
        @update:search="(v) => (mj.mjVueSearch = v)"
        @select="mj.mjVueSetChoix"
      />
      <button type="button" class="button" @click="$emit('nouvelle-production')">+ Nouvelle production</button>
    </div>
  </div>
</template>

<style scoped>
.page-subtitle-filtre {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
}
.page-subtitle-filtre-text {
  flex: 1;
  min-width: 200px;
}
.page-ressource-courante {
  color: #7dd3fc;
}
.productions-back-all {
  flex-shrink: 0;
  text-decoration: none;
}
</style>
