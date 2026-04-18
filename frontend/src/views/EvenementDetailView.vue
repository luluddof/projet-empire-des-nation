<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useApi } from "../composables/useApi.js";

const props = defineProps({
  authState: { type: Object, required: true },
});

const route = useRoute();
const router = useRouter();

const maLigneJoueur = computed(() => {
  const uid = String(props.authState?.user?.id ?? "");
  return (evenement.value?.joueurs || []).filter((j) => String(j.utilisateur_id) === uid);
});

const { get } = useApi();

const chargement = ref(true);
const erreur = ref("");
const evenement = ref(null);
const apercu = ref(null);
const apercuErreur = ref("");

const blocsMarche = computed(() =>
  (apercu.value?.blocs || []).filter((b) => b.kind === "categorie" || b.kind === "ressource"),
);
const blocsProduction = computed(() => (apercu.value?.blocs || []).filter((b) => b.kind === "production"));

const resumeCategories = computed(() =>
  (apercu.value?.resume || []).filter((r) => r.kind === "categorie"),
);
const resumeRessources = computed(() =>
  (apercu.value?.resume || []).filter((r) => r.kind === "ressource"),
);
const resumeProductions = computed(() =>
  (apercu.value?.resume || []).filter((r) => r.kind === "production"),
);
const compteRenduVisible = computed(() => {
  const n =
    resumeCategories.value.length + resumeRessources.value.length + resumeProductions.value.length;
  return n > 0;
});
const resumeNotesProduction = computed(() =>
  (apercu.value?.resume || []).filter((r) => r.kind === "production" && r.note),
);

function ligneJoueur(bloc) {
  const j = (bloc?.joueurs || [])[0];
  return j || null;
}

function couleurBloc(b) {
  if (b.kind === "categorie") return "marche-cat";
  if (b.kind === "ressource") return "marche-res";
  return "prod";
}

async function charger() {
  const id = route.params.id;
  if (!id) return;
  if (!props.authState?.user) return;
  if (props.authState.user.is_mj) {
    router.replace({ path: "/mj/evenements", query: { edit: String(id) } });
    return;
  }
  chargement.value = true;
  erreur.value = "";
  apercuErreur.value = "";
  evenement.value = null;
  apercu.value = null;
  try {
    evenement.value = await get(`/api/evenements/${id}`);
    try {
      apercu.value = await get(`/api/evenements/${id}/apercu-joueur`);
    } catch (e) {
      apercuErreur.value = e.message || "Aperçu indisponible";
      apercu.value = null;
    }
  } catch (e) {
    erreur.value = e.message;
  } finally {
    chargement.value = false;
  }
}

onMounted(charger);
watch(() => route.params.id, charger);
watch(
  () => [props.authState?.user?.id, props.authState?.user?.is_mj],
  () => charger(),
);
</script>

<template>
  <main class="container detail-root">
    <h2 class="page-title">Évènement</h2>

    <p v-if="chargement" class="muted">Chargement…</p>
    <p v-else-if="erreur" class="error">{{ erreur }}</p>

    <template v-else-if="evenement">
      <section class="card hero">
        <div class="head">
          <h3 class="title">{{ evenement.titre || "(Sans titre)" }}</h3>
          <div class="badges">
            <span class="tag" :class="evenement.actif ? 'tag-ok' : 'tag-off'">{{
              evenement.actif ? "Actif" : "Inactif"
            }}</span>
            <span v-if="evenement.brouillon" class="tag tag-draft">Brouillon</span>
          </div>
        </div>
        <p v-if="evenement.description" class="desc">{{ evenement.description }}</p>
        <p v-else class="muted">Aucune description.</p>
      </section>

      <section v-if="maLigneJoueur.length" class="card block-participation">
        <h4 class="sub">Votre participation</h4>
        <ul class="liste">
          <li v-for="j in maLigneJoueur" :key="j.id">
            Délai {{ j.delai_tours }} tour(s) · effets
            {{ j.tours_restants == null ? "sans limite de durée" : `${j.tours_restants} tour(s) restants` }} ·
            {{ j.actif ? "actif" : "retiré" }}
          </li>
        </ul>
      </section>

      <p v-if="apercu?.message" class="card muted-banner">{{ apercu.message }}</p>
      <p v-else-if="apercuErreur" class="card muted-banner warn">{{ apercuErreur }}</p>

      <section v-if="compteRenduVisible" class="card resume-card">
        <h4 class="sub resume-title">Compte rendu</h4>

        <div
          v-if="resumeCategories.length || resumeRessources.length"
          class="resume-tier resume-tier-marche"
        >
          <h5 class="resume-tier-title">Marché (prix)</h5>
          <p class="resume-tier-desc">Modificateurs qui influencent vos prix d’achat.</p>

          <template v-if="resumeCategories.length">
            <h6 class="resume-subtitle">Par catégorie</h6>
            <div class="table-wrap">
              <table class="resume-table">
                <thead>
                  <tr>
                    <th scope="col">Catégorie</th>
                    <th scope="col">Avant</th>
                    <th scope="col">Après</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in resumeCategories" :key="'c' + i" class="kind-categorie">
                    <td>{{ row.titre }}</td>
                    <td class="cell-avant">{{ row.avant }}</td>
                    <td class="cell-apres">{{ row.apres }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>

          <template v-if="resumeRessources.length">
            <h6 class="resume-subtitle">Par ressource</h6>
            <div class="table-wrap">
              <table class="resume-table">
                <thead>
                  <tr>
                    <th scope="col">Ressource</th>
                    <th scope="col">Avant</th>
                    <th scope="col">Après</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in resumeRessources" :key="'r' + i" class="kind-ressource">
                    <td>{{ row.titre }}</td>
                    <td class="cell-avant">{{ row.avant }}</td>
                    <td class="cell-apres">{{ row.apres }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </div>

        <div v-if="resumeProductions.length" class="resume-tier resume-tier-prod">
          <h5 class="resume-tier-title">Production</h5>
          <p class="resume-tier-desc">Quantités produites par tour (hors prix du marché).</p>
          <div class="table-wrap">
            <table class="resume-table">
              <thead>
                <tr>
                  <th scope="col">Ligne</th>
                  <th scope="col">Avant</th>
                  <th scope="col">Après</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in resumeProductions" :key="'p' + i" class="kind-production">
                  <td>{{ row.titre }}</td>
                  <td class="cell-avant">{{ row.avant }}</td>
                  <td class="cell-apres">{{ row.apres }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-for="(row, i) in resumeNotesProduction" :key="'n' + i" class="note-pct">{{ row.note }}</p>
        </div>
      </section>

      <div v-if="blocsMarche.length || blocsProduction.length" class="impact-columns">
        <section v-if="blocsMarche.length" class="card col-marche">
          <h4 class="col-title marche">Marché (prix)</h4>
          <p class="col-intro">Modificateurs en % qui influencent le prix des ressources pour vous.</p>
          <div
            v-for="(b, i) in blocsMarche"
            :key="'m' + i"
            class="impact-card"
            :class="couleurBloc(b)"
          >
            <div class="impact-card-head">{{ b.titre || b.nom }}</div>
            <template v-if="ligneJoueur(b)">
              <div class="compare">
                <div class="compare-box avant">
                  <span class="compare-label">Avant</span>
                  <span class="compare-val">{{ ligneJoueur(b).avant_pct }} %</span>
                </div>
                <span class="compare-arrow" aria-hidden="true">→</span>
                <div class="compare-box apres">
                  <span class="compare-label">Après</span>
                  <span class="compare-val">{{ ligneJoueur(b).apres_pct }} %</span>
                </div>
              </div>
            </template>
          </div>
        </section>

        <section v-if="blocsProduction.length" class="card col-prod">
          <h4 class="col-title prod">Production (par tour)</h4>
          <div v-for="(b, i) in blocsProduction" :key="'p' + i" class="impact-card prod">
            <div class="impact-card-head">{{ b.titre || b.nom }}</div>
            <template v-if="ligneJoueur(b)">
              <div v-if="ligneJoueur(b).note" class="prod-note">{{ ligneJoueur(b).note }}</div>
              <div v-else class="compare">
                <div class="compare-box avant">
                  <span class="compare-label">Avant</span>
                  <span class="compare-val">{{ ligneJoueur(b).avant_qpt }} / tour</span>
                </div>
                <span class="compare-arrow" aria-hidden="true">→</span>
                <div class="compare-box apres">
                  <span class="compare-label">Après</span>
                  <span class="compare-val">{{ ligneJoueur(b).apres_qpt }} / tour</span>
                </div>
              </div>
            </template>
          </div>
        </section>
      </div>

      <p class="muted foot">Lecture seule. Seul un MJ peut modifier un évènement.</p>
    </template>
  </main>
</template>

<style scoped>
.detail-root {
  padding-bottom: 32px;
}
.page-title {
  margin-bottom: 16px;
}
.muted {
  color: #94a3b8;
}
.head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
}
.title {
  margin: 0;
  flex: 1;
  min-width: 0;
  font-size: 1.35rem;
}
.badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
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
.hero {
  margin-bottom: 14px;
}
.desc {
  margin-top: 12px;
  color: #cbd5e1;
  white-space: pre-wrap;
  line-height: 1.5;
}
.block-participation {
  margin-bottom: 14px;
  border-color: rgba(56, 189, 248, 0.35);
  background: rgba(56, 189, 248, 0.06);
}
.sub {
  margin: 0 0 10px;
  font-size: 15px;
  color: #e2e8f0;
}
.liste {
  margin: 0;
  padding-left: 1.2em;
  color: #cbd5e1;
}
.muted-banner {
  margin-bottom: 14px;
  color: #94a3b8;
  font-size: 14px;
}
.muted-banner.warn {
  color: #fca5a5;
  border-color: rgba(239, 68, 68, 0.35);
}
.resume-card {
  margin-bottom: 16px;
  border-color: rgba(51, 65, 85, 0.9);
  background: rgba(15, 23, 42, 0.35);
}
.resume-title {
  margin-bottom: 18px;
}
.resume-tier {
  margin-bottom: 22px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid #334155;
}
.resume-tier:last-child {
  margin-bottom: 0;
}
.resume-tier-marche {
  border-color: rgba(34, 211, 238, 0.35);
  background: rgba(34, 211, 238, 0.06);
}
.resume-tier-prod {
  border-color: rgba(74, 222, 128, 0.4);
  background: rgba(74, 222, 128, 0.07);
}
.resume-tier-title {
  margin: 0 0 6px;
  font-size: 1.05rem;
  font-weight: 800;
  color: #f1f5f9;
}
.resume-tier-marche .resume-tier-title {
  color: #67e8f9;
}
.resume-tier-prod .resume-tier-title {
  color: #86efac;
}
.resume-tier-desc {
  margin: 0 0 14px;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.45;
}
.resume-subtitle {
  margin: 16px 0 8px;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #cbd5e1;
}
.resume-tier .resume-subtitle:first-of-type {
  margin-top: 0;
}
.table-wrap {
  overflow-x: auto;
}
.resume-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.resume-table th,
.resume-table td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(51, 65, 85, 0.9);
}
.resume-table th {
  color: #e2e8f0;
  font-weight: 700;
  background: rgba(15, 23, 42, 0.5);
}
.resume-table tr.kind-categorie td:first-child {
  border-left: 3px solid #22d3ee;
}
.resume-table tr.kind-ressource td:first-child {
  border-left: 3px solid #38bdf8;
}
.resume-table tr.kind-production td:first-child {
  border-left: 3px solid #4ade80;
}
.cell-avant {
  color: #fca5a5;
  font-variant-numeric: tabular-nums;
}
.cell-apres {
  color: #86efac;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.note-pct {
  margin: 10px 0 0;
  font-size: 13px;
  color: #fde68a;
}
.impact-columns {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  margin-bottom: 16px;
}
@media (min-width: 960px) {
  .impact-columns {
    grid-template-columns: 1fr 1fr;
    align-items: start;
  }
}
.col-marche {
  border-color: rgba(34, 211, 238, 0.35);
  background: rgba(34, 211, 238, 0.06);
}
.col-prod {
  border-color: rgba(74, 222, 128, 0.35);
  background: rgba(74, 222, 128, 0.06);
}
.col-title {
  margin: 0 0 8px;
  font-size: 16px;
  letter-spacing: 0.02em;
}
.col-title.marche {
  color: #67e8f9;
}
.col-title.prod {
  color: #86efac;
}
.col-intro {
  margin: 0 0 14px;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.45;
}
.impact-card {
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 10px;
  border: 1px solid #334155;
  background: rgba(15, 23, 42, 0.45);
}
.impact-card:last-child {
  margin-bottom: 0;
}
.impact-card.marche-cat {
  border-color: rgba(34, 211, 238, 0.45);
}
.impact-card.marche-res {
  border-color: rgba(56, 189, 248, 0.45);
}
.impact-card.prod {
  border-color: rgba(74, 222, 128, 0.45);
}
.impact-card-head {
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 4px;
}
.compare {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
.compare-box {
  flex: 1 1 140px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #334155;
}
.compare-box.avant {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(248, 113, 113, 0.35);
}
.compare-box.apres {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(74, 222, 128, 0.4);
}
.compare-label {
  display: block;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #94a3b8;
  margin-bottom: 4px;
}
.compare-val {
  font-size: 1.1rem;
  font-weight: 700;
  color: #f8fafc;
  font-variant-numeric: tabular-nums;
}
.compare-arrow {
  color: #64748b;
  font-size: 1.2rem;
}
.prod-note {
  font-size: 13px;
  color: #fde68a;
  line-height: 1.45;
}
.resume-tier-prod .note-pct {
  margin-top: 12px;
}
.foot {
  margin-top: 20px;
  font-size: 13px;
}
</style>
