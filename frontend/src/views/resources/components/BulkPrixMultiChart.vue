<script setup>
import { computed } from "vue";

const props = defineProps({
  title: { type: String, required: true },
  /** { key?, nom, color, points: [{ created_at, prix_achat }] }[] — une série = un joueur. */
  series: { type: Array, required: true },
  valueKey: { type: String, default: "prix_achat" },
});

const W = 300;
const H = 110;
const PAD = 12;

// ── Échelle Y partagée (toutes séries, pour comparaison) ────────────────────
const yExtent = computed(() => {
  const key = props.valueKey;
  const vals = [];
  for (const s of props.series || []) {
    for (const p of s.points || []) vals.push(Number(p[key]) || 0);
  }
  if (vals.length === 0) return { min: 0, max: 1, span: 1 };
  let min = Math.min(...vals);
  let max = Math.max(...vals);
  if (!Number.isFinite(min) || !Number.isFinite(max)) return { min: 0, max: 1, span: 1 };
  if (max - min < 1e-9) {
    const c = min;
    const pad = Math.abs(c) < 1e-9 ? 1 : Math.max(1, Math.abs(c) * 0.14);
    min = c - pad;
    max = c + pad;
  } else {
    const pad = (max - min) * 0.1;
    min -= pad;
    max += pad;
  }
  return { min, max, span: Math.max(1e-9, max - min) };
});

// ── Métadonnées temporelles (axe X partagé) ─────────────────────────────────
const timeMeta = computed(() => {
  const times = [];
  for (const s of props.series || []) {
    for (const p of s.points || []) {
      const t = new Date(p.created_at).getTime();
      if (!Number.isNaN(t)) times.push(t);
    }
  }
  if (times.length === 0) return { spreadTime: false, tMin: 0, tMax: 1, span: 1 };
  const tMin = Math.min(...times);
  const tMax = Math.max(...times);
  const span = tMax - tMin;
  return { spreadTime: span >= 2, tMin, tMax, span: Math.max(1, span) };
});

function yFor(v) {
  const { min, span } = yExtent.value;
  return PAD + (1 - (Number(v) - min) / span) * (H - 2 * PAD);
}

function xAtIndex(i, n) {
  if (n <= 1) return PAD + (W - 2 * PAD) / 2;
  return PAD + (i / (n - 1)) * (W - 2 * PAD);
}

function xAtTime(createdAt) {
  const { tMin, span } = timeMeta.value;
  const tm = new Date(createdAt).getTime();
  return PAD + ((tm - tMin) / span) * (W - 2 * PAD);
}

function pathForSeries(s) {
  const key = props.valueKey;
  const { spreadTime } = timeMeta.value;
  const pts = [...(s.points || [])].sort((a, b) => {
    const ta = new Date(a.created_at).getTime();
    const tb = new Date(b.created_at).getTime();
    return ta !== tb ? ta - tb : (Number(a.id) || 0) - (Number(b.id) || 0);
  });
  const n = pts.length;
  if (n === 0) return "";
  const xOf = (i) => (!spreadTime ? xAtIndex(i, n) : xAtTime(pts[i].created_at));
  if (n === 1) {
    const x = xOf(0);
    const y = yFor(Number(pts[0][key]) || 0);
    return `M${(x - 24).toFixed(1)},${y.toFixed(1)} L${(x + 24).toFixed(1)},${y.toFixed(1)}`;
  }
  return pts.map((p, i) => `${i === 0 ? "M" : "L"}${xOf(i).toFixed(1)},${yFor(Number(p[key]) || 0).toFixed(1)}`).join(" ");
}

// ── Données par série ────────────────────────────────────────────────────────
const seriesDraw = computed(() => {
  const key = props.valueKey;
  const { spreadTime } = timeMeta.value;
  return (props.series || []).map((s, i) => {
    const pts = [...(s.points || [])].sort((a, b) => {
      const ta = new Date(a.created_at).getTime();
      const tb = new Date(b.created_at).getTime();
      return ta !== tb ? ta - tb : (Number(a.id) || 0) - (Number(b.id) || 0);
    });
    const n = pts.length;
    const xOf = (idx) => (!spreadTime ? xAtIndex(idx, n) : xAtTime(pts[idx].created_at));
    const isSinglePoint = n === 0 || !spreadTime;
    const firstPt = pts[0] ?? null;
    const lastPt = pts[n - 1] ?? null;
    const centerX = n > 0 ? xOf(Math.floor((n - 1) / 2)) : W / 2;
    const centerY = lastPt ? yFor(Number(lastPt[key]) || 0) : H / 2;
    const xFirst = n > 0 ? xOf(0) : W / 2;
    const xLast = n > 0 ? xOf(n - 1) : W / 2;
    const yFirst = firstPt ? yFor(Number(firstPt[key]) || 0) : H / 2;
    const yLast = lastPt ? yFor(Number(lastPt[key]) || 0) : H / 2;
    const lastValue = lastPt != null ? Math.round(Number(lastPt[key]) || 0) : null;
    const lastTimestamp = lastPt?.created_at ?? null;
    return {
      key: s.key ?? `k-${i}-${s.nom}`,
      color: s.color,
      nom: s.nom,
      path: pathForSeries(s),
      isSinglePoint,
      centerX,
      centerY,
      xFirst,
      xLast,
      yFirst,
      yLast,
      lastValue,
      lastTimestamp,
    };
  });
});

const hasAnyPoint = computed(() => props.series?.some((s) => (s.points || []).length > 0));

// ── Référence temporelle (pour la légende borne) ─────────────────────────────
const bornesRef = computed(() => {
  const s0 = props.series?.[0];
  if (!s0?.points?.length) return null;
  const key = props.valueKey;
  const pts = [...s0.points].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  const debut = pts[0];
  const fin = pts[pts.length - 1];
  const t0 = new Date(debut.created_at).getTime();
  const t1 = new Date(fin.created_at).getTime();
  const finDistincte = pts.length > 1 && (t1 > t0 + 1 || Math.abs(Number(fin[key]) - Number(debut[key])) > 0.5);
  return { debut, fin, finDistincte };
});

const bandeBornes = computed(() => {
  const b = bornesRef.value;
  if (!b || !b.finDistincte) return null;
  const sd = seriesDraw.value[0];
  if (!sd) return null;
  const x1 = Math.min(sd.xFirst, sd.xLast);
  const x2 = Math.max(sd.xFirst, sd.xLast);
  return Math.abs(x2 - x1) < 0.5 ? null : { x: x1, width: x2 - x1 };
});

function formatDateCourte(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return String(iso);
  return d.toLocaleString("fr-FR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
</script>

<template>
  <div class="bulk-chart-wrap">
    <div class="bulk-chart-title">{{ title }}</div>

    <p v-if="!hasAnyPoint" class="bulk-chart-empty">
      Pas encore d'historique : les points s'ajoutent lorsque le MJ modifie les prix du marché.
    </p>

    <template v-else>
      <!-- Légende borne temporelle (partagée) -->
      <div v-if="bornesRef" class="borne-legende">
        <template v-if="bornesRef.finDistincte">
          <span class="borne-pill"><span class="borne-dot" />Début — {{ formatDateCourte(bornesRef.debut.created_at) }}</span>
          <span class="borne-pill"><span class="borne-dot fin" />Fin — {{ formatDateCourte(bornesRef.fin.created_at) }}</span>
        </template>
        <span v-else class="borne-pill">
          <span class="borne-dot" />Point unique — {{ formatDateCourte(bornesRef.debut.created_at) }}
        </span>
      </div>

      <!-- Mini-graphiques côte à côte (un par joueur), avec scroll horizontal -->
      <div class="player-mini-row">
        <div v-for="row in seriesDraw" :key="row.key" class="player-mini-col">
          <!-- Label joueur -->
          <div class="player-mini-label">
            <span class="player-mini-dot" :style="{ background: row.color }" />
            <span class="player-mini-name">{{ row.nom }}</span>
          </div>

          <!-- SVG -->
          <div class="player-mini-svg-wrap">
            <svg class="player-mini-svg" :viewBox="`0 0 ${W} ${H}`" xmlns="http://www.w3.org/2000/svg">
              <!-- Zone borne (multi-point) -->
              <rect v-if="!row.isSinglePoint && bandeBornes"
                :x="bandeBornes.x" y="0" :width="bandeBornes.width" :height="H"
                fill="#5865f2" fill-opacity="0.07" />

              <!-- Guides verticaux borne début/fin -->
              <line v-if="!row.isSinglePoint"
                :x1="row.xFirst" :y1="PAD" :x2="row.xFirst" :y2="H - PAD"
                stroke="#94a3b8" stroke-width="1" stroke-dasharray="4 3" stroke-opacity="0.7" />
              <line v-if="!row.isSinglePoint && bornesRef?.finDistincte"
                :x1="row.xLast" :y1="PAD" :x2="row.xLast" :y2="H - PAD"
                stroke="#cbd5e1" stroke-width="1" stroke-dasharray="4 3" stroke-opacity="0.8" />

              <!-- Guide vertical centre (point unique) -->
              <line v-if="row.isSinglePoint"
                :x1="row.centerX" :y1="PAD" :x2="row.centerX" :y2="H - PAD"
                :stroke="row.color" stroke-width="1" stroke-dasharray="4 3" stroke-opacity="0.35" />

              <!-- Courbe (multi-point) -->
              <path v-if="row.path && !row.isSinglePoint"
                :d="row.path" fill="none" :stroke="row.color" stroke-width="2.5"
                stroke-linecap="round" stroke-linejoin="round" />

              <!-- Point unique : tick + gros cercle -->
              <line v-if="row.isSinglePoint"
                :x1="row.centerX - 26" :y1="row.centerY"
                :x2="row.centerX + 26" :y2="row.centerY"
                :stroke="row.color" stroke-width="2" stroke-linecap="round" />
              <circle v-if="row.isSinglePoint"
                :cx="row.centerX" :cy="row.centerY" r="6"
                :fill="row.color" stroke="#0f172a" stroke-width="1.5" />

              <!-- Multi-point : marqueurs début/fin -->
              <circle v-if="!row.isSinglePoint && row.path"
                :cx="row.xFirst" :cy="row.yFirst" r="4"
                fill="#94a3b8" stroke="#0f172a" stroke-width="1" />
              <circle v-if="!row.isSinglePoint && row.path && bornesRef?.finDistincte"
                :cx="row.xLast" :cy="row.yLast" r="4"
                fill="#e2e8f0" stroke="#0f172a" stroke-width="1" />
            </svg>
          </div>

          <!-- Prix actuel -->
          <div v-if="row.lastValue !== null" class="player-mini-price" :style="{ color: row.color }">
            {{ row.lastValue.toLocaleString("fr-FR") }} ƒ
          </div>
          <div v-else class="player-mini-price player-mini-price-na">—</div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.bulk-chart-wrap {
  padding: 12px 12px 10px;
  background: #0f172a;
  border-radius: 10px;
  border: 1px solid #334155;
}

.bulk-chart-title {
  font-size: 12px;
  font-weight: 700;
  color: #cbd5e1;
  margin-bottom: 8px;
}

.bulk-chart-empty {
  font-size: 12px;
  color: #64748b;
  margin: 0;
  padding: 12px;
  border-radius: 8px;
  border: 1px dashed #334155;
}

/* ── Légende borne ─────────────────────────────────────────── */
.borne-legende {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  align-items: center;
  margin-bottom: 10px;
  font-size: 11px;
  color: #94a3b8;
}

.borne-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.borne-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #94a3b8;
  flex-shrink: 0;
}

.borne-dot.fin {
  background: #e2e8f0;
}

/* ── Mini-charts côte à côte ───────────────────────────────── */
.player-mini-row {
  display: flex;
  flex-wrap: nowrap;
  overflow-x: auto;
  gap: 10px;
  padding-bottom: 6px;
  scrollbar-width: thin;
  scrollbar-color: #334155 transparent;
}

.player-mini-row::-webkit-scrollbar {
  height: 5px;
}
.player-mini-row::-webkit-scrollbar-track {
  background: transparent;
}
.player-mini-row::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 3px;
}

.player-mini-col {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  width: 130px;
}

.player-mini-label {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 5px;
  font-size: 10px;
  color: #94a3b8;
  min-height: 16px;
}

.player-mini-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.player-mini-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.2;
}

.player-mini-svg-wrap {
  background: #060d1a;
  border-radius: 7px;
  border: 1px solid #1e2d42;
  overflow: hidden;
}

.player-mini-svg {
  width: 100%;
  height: auto;
  display: block;
}

.player-mini-price {
  font-size: 11px;
  font-weight: 700;
  text-align: center;
  margin-top: 5px;
  font-variant-numeric: tabular-nums;
}

.player-mini-price-na {
  color: #64748b;
}
</style>
