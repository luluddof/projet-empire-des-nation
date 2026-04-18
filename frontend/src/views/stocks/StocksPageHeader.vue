<script setup>
import MjViewSelect from "../../components/MjViewSelect.vue";

defineProps({
  isMj: { type: Boolean, default: false },
  isMjOtherView: { type: Boolean, default: false },
  mj: { type: Object, required: true },
  currentUserIdStr: { type: String, default: "" },
  stockFlorins: { type: Object, default: null },
  qteAffichee: { type: Function, required: true },
  formatFlorin: { type: Function, required: true },
  formatFlorinExact: { type: Function, required: true },
  sauvegarde: { type: Boolean, default: false },
  nbModifications: { type: Number, default: 0 },
});

defineEmits(["sauvegarder"]);
</script>

<template>
  <div class="page-header">
    <div>
      <h2 class="page-title">Gestion des Stocks</h2>
      <p class="page-subtitle">
        <template v-if="isMj && isMjOtherView">
          Vue stocks de <strong>{{ mj.mjVueLabel }}</strong> : l’achat et la vente automatiques sont désactivés.
          Utilisez la colonne « Nouvelle quantité » (saisie ou boutons +/−) puis
          <strong>Sauvegarder</strong> pour ajouter ou retirer des unités (y compris les florins).
        </template>
        <template v-else-if="isMj">Modifiez les quantités puis sauvegardez, ou utilisez Acheter / Vendre.</template>
        <template v-else>Consultez vos stocks et effectuez des achats/ventes.</template>
        <span
          v-if="stockFlorins"
          class="solde-florins"
          :title="formatFlorinExact(qteAffichee(stockFlorins))"
        >
          Solde monnaie : {{ formatFlorin(qteAffichee(stockFlorins)) }}
        </span>
        <span class="stocks-sub-hint">
          Détail et historique des productions :
          <router-link to="/productions">Mes productions</router-link>.
        </span>
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
      <button
        v-if="isMj"
        class="button"
        :disabled="nbModifications === 0 || sauvegarde"
        @click="$emit('sauvegarder')"
      >
        {{ sauvegarde ? "Sauvegarde…" : `Sauvegarder (${nbModifications})` }}
      </button>
    </div>
  </div>
</template>
