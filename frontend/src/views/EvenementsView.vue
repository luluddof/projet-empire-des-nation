<script setup>
import { onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useEvenementsMj } from "./evenements/useEvenementsMj.js";
import EvenementsMjForm from "./evenements/EvenementsMjForm.vue";
import EvenementsMjList from "./evenements/EvenementsMjList.vue";

const props = defineProps({
  authState: { type: Object, required: true },
});

const route = useRoute();
const router = useRouter();
const page = useEvenementsMj(() => props.authState);

function tryOpenEditFromQuery() {
  if (!page.isMj) return;
  const raw = route.query.edit;
  if (raw == null || raw === "") return;
  const id = Number(raw);
  if (!Number.isFinite(id)) return;
  const ev = page.evenements.find((x) => x.id === id);
  if (ev) {
    page.startEdit(ev);
    router.replace({ path: "/mj/evenements", query: {} });
  }
}

onMounted(async () => {
  await page.init();
  tryOpenEditFromQuery();
});

watch(() => route.query.edit, tryOpenEditFromQuery);
watch(() => page.evenements, tryOpenEditFromQuery);
</script>

<template>
  <main class="container">
    <h2>Évènements (MJ)</h2>

    <p v-if="!page.isMj" class="error">Accès refusé.</p>
    <p v-else-if="page.erreur" class="error">{{ page.erreur }}</p>

    <div v-if="page.isMj" class="evenements-mj-actions">
      <button v-if="!page.showForm" type="button" class="button" @click="page.openCreate">Créer un évènement</button>
    </div>

    <EvenementsMjForm
      v-if="page.isMj && page.showForm"
      :form="page.form"
      :categories="page.categories"
      :ressources="page.ressources"
      :utilisateurs="page.utilisateurs"
      :current-user-id-str="page.currentUserIdStr"
      :preview-data="page.previewData"
      :preview-loading="page.previewLoading"
      :preview-erreur="page.previewErreur"
      @reset="page.resetForm"
      @cancel="page.cancelForm"
      @save="page.save"
      @toggle-joueur="page.toggleJoueur"
      @add-categorie="page.addImpactCategorie"
      @add-ressource="page.addImpactRessource"
      @add-production="page.addImpactProduction"
    />

    <EvenementsMjList
      v-if="page.isMj"
      :evenements="page.evenements"
      @edit="page.startEdit"
      @supprimer="page.supprimer"
      @retirer-joueur="page.retirerJoueur"
    />
  </main>
</template>

<style scoped>
.evenements-mj-actions {
  margin-bottom: 16px;
}
</style>
