<script setup>
import { ref } from "vue";
import PrixSparkline from "../../components/PrixSparkline.vue";

defineProps({
  commerceModal: { type: Object, default: null },
  commerceAchatMode: { type: String, default: "local" },
  commerceErr: { type: String, default: "" },
  commerceLoading: { type: Boolean, default: false },
  historiquePrix: { type: Array, default: () => [] },
  commercePrixUnitaire: { type: Number, default: 0 },
  commerceTotal: { type: Number, default: 0 },
  isMjOtherView: { type: Boolean, default: false },
  formatFlorin: { type: Function, required: true },
  formatFlorinExact: { type: Function, required: true },
  estFlorins: { type: Function, required: true },
});

const commerceQte = defineModel("commerceQte", { type: Number, default: 1 });

defineEmits(["close", "set-achat-mode", "executer"]);

const qteInputRef = ref(null);

defineExpose({
  focusQte() {
    qteInputRef.value?.select?.();
  },
});
</script>

<template>
  <div v-if="commerceModal" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal modal-wide commerce-modal">
      <h3 class="modal-title">
        {{
          commerceModal.sens === "achat" ? "Acheter contre des florins" : "Vendre pour des florins"
        }}
        — {{ commerceModal.stock.ressource.nom }}
      </h3>
      <p class="modal-hint">
        <template v-if="commerceModal.sens === 'achat'">
          Prix unitaire :
          <strong>{{ formatFlorin(commercePrixUnitaire) }}</strong>.
          Le montant est débité de votre stock « Florins ».
        </template>
        <template v-else>
          Prix unitaire (revente) : <strong>{{ formatFlorin(commercePrixUnitaire) }}</strong>.
          Les florins sont ajoutés à votre stock « Florins ».
        </template>
      </p>
      <p v-if="isMjOtherView" class="error">
        En tant que MJ, vous ne pouvez pas acheter/vendre pour un autre joueur. Utilisez uniquement l’ajustement manuel
        des stocks.
      </p>
      <div v-if="commerceModal.sens === 'achat'" class="commerce-mode">
        <button
          type="button"
          :class="['button', 'secondary', 'small', commerceAchatMode === 'local' ? 'is-active' : '']"
          @click="$emit('set-achat-mode', 'local')"
        >
          Achat local
        </button>
        <button
          type="button"
          :class="['button', 'secondary', 'small', commerceAchatMode === 'lointain' ? 'is-active' : '']"
          @click="$emit('set-achat-mode', 'lointain')"
        >
          Achat lointain
        </button>
      </div>
      <div v-if="!estFlorins(commerceModal.stock) && historiquePrix.length < 2" class="sparkline-single">
        Historique insuffisant ({{ historiquePrix.length }} point) — achat/vente possible.
      </div>
      <PrixSparkline
        v-else-if="!estFlorins(commerceModal.stock)"
        :points="historiquePrix"
        :value-key="commerceModal.sens === 'vente' ? 'prix_modifie' : 'prix_achat'"
        :label="
          commerceModal.sens === 'vente'
            ? 'Évolution du prix de revente catalogue (ƒ)'
            : 'Évolution du prix d’achat catalogue (ƒ)'
        "
      />
      <p v-if="commerceErr" class="error">{{ commerceErr }}</p>
      <label class="form-label">
        Quantité
        <input
          ref="qteInputRef"
          v-model.number="commerceQte"
          type="number"
          min="1"
          class="input"
          @focus="(e) => e.target.select()"
          @click="(e) => e.target.select()"
        />
      </label>
      <div class="modal-total" :title="formatFlorinExact(commerceTotal)">
        <span class="modal-total-label">Total</span>
        <strong class="modal-total-value">{{ formatFlorin(commerceTotal) }}</strong>
      </div>
      <div class="modal-footer">
        <button class="button secondary" :disabled="commerceLoading" @click="$emit('close')">Annuler</button>
        <button class="button" :disabled="commerceLoading || isMjOtherView" @click="$emit('executer')">
          {{ commerceLoading ? "…" : "Confirmer" }}
        </button>
      </div>
    </div>
  </div>
</template>
