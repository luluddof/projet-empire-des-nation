<script setup>
import { computed } from "vue";

const props = defineProps({
  passe: { type: Array, default: () => [] },
  futur: { type: Array, default: () => [] },
  futurBreakdown: { type: Array, default: () => [] },
  ressourceNom: { type: String, default: "" },
});

const W = 440;
const H = 148;
const PAD_L = 32;
const PAD_R = 12;
const PAD_T = 14;
const PAD_B = 30;

const COLOR_UP = "#22c55e";
const COLOR_DOWN = "#ef4444";
const COLOR_FLAT = "#64748b";

const points = computed(() => {
  const p = props.passe || [];
  const f = props.futur || [];
  const n = p.length;
  const pastPts = p.map((row, i) => ({
    kind: "passe",
    label: n ? `T-${n - i}` : "",
    value: Number(row.quantite) || 0,
    at: row.at,
  }));
  const futPts = f.map((row) => ({
    kind: "futur",
    label: `T+${row.tour}`,
    value: Number(row.quantite) || 0,
  }));
  return [...pastPts, ...futPts];
});

const innerW = computed(() => W - PAD_L - PAD_R);

const yScale = computed(() => {
  const vals = points.value.map((x) => x.value);
  if (!vals.length) return { min: 0, max: 1 };
  let min = Math.min(...vals);
  let max = Math.max(...vals);
  if (min === max) {
    min -= 1;
    max += 1;
  }
  const pad = (max - min) * 0.1 || 1;
  return { min: min - pad, max: max + pad };
});

const plotH = H - PAD_T - PAD_B;

const zeroY = computed(() => {
  const { min, max } = yScale.value;
  const span = max - min || 1;
  return PAD_T + plotH * (1 - (0 - min) / span);
});

/** Coordonnées des points + séparateur passé / futur */
const chartGeometry = computed(() => {
  const pts = points.value;
  const n = pts.length;
  if (!n) return { nodes: [], segments: [], sepX: null };

  const { min, max } = yScale.value;
  const span = max - min || 1;
  const yAt = (v) => PAD_T + plotH * (1 - (v - min) / span);
  const iw = innerW.value;

  const xAt = (i) => {
    if (n === 1) return PAD_L + iw / 2;
    return PAD_L + (i / (n - 1)) * iw;
  };

  const nodes = pts.map((p, i) => ({
    ...p,
    cx: xAt(i),
    cy: yAt(p.value),
  }));

  const segments = [];
  for (let i = 0; i < n - 1; i++) {
    const a = nodes[i];
    const b = nodes[i + 1];
    const dv = b.value - a.value;
    let stroke = COLOR_FLAT;
    if (dv > 0) stroke = COLOR_UP;
    else if (dv < 0) stroke = COLOR_DOWN;
    segments.push({
      x1: a.cx,
      y1: a.cy,
      x2: b.cx,
      y2: b.cy,
      stroke,
    });
  }

  let sepX = null;
  const fi = pts.findIndex((p) => p.kind === "futur");
  if (fi > 0) {
    sepX = (nodes[fi - 1].cx + nodes[fi].cx) / 2;
  }

  return { nodes, segments, sepX };
});

const futurBreakdownRows = computed(() => {
  const rows = props.futurBreakdown || [];
  return rows.map((r) => ({
    tour: Number(r.tour) || 0,
    actif: Number(r.actif) || 0,
    pending: Number(r.pending) || 0,
    total: Number(r.actif || 0) + Number(r.pending || 0),
  }));
});
</script>

<template>
  <div class="prod-chart-wrap">
    <div class="prod-chart-label">
      Production par tour ({{ props.ressourceNom || "—" }}) : segment
      <span class="leg leg-up">vert</span>
      si la valeur augmente par rapport au point précédent,
      <span class="leg leg-down">rouge</span>
      si elle baisse. Les étiquettes T−… sont le passé réel, T+… la prévision.
    </div>
    <svg
      v-if="points.length"
      class="prod-chart-svg"
      :viewBox="`0 0 ${W} ${H}`"
      xmlns="http://www.w3.org/2000/svg"
    >
      <line
        :x1="PAD_L"
        :y1="zeroY"
        :x2="W - PAD_R"
        :y2="zeroY"
        class="zero-line"
      />

      <line
        v-if="chartGeometry.sepX != null"
        :x1="chartGeometry.sepX"
        :y1="PAD_T"
        :x2="chartGeometry.sepX"
        :y2="H - PAD_B + 4"
        class="sep-futur"
      />

      <line
        v-for="(s, i) in chartGeometry.segments"
        :key="'seg' + i"
        :x1="s.x1"
        :y1="s.y1"
        :x2="s.x2"
        :y2="s.y2"
        :stroke="s.stroke"
        stroke-width="2.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        fill="none"
      />

      <circle
        v-for="(n, i) in chartGeometry.nodes"
        :key="'pt' + i"
        :cx="n.cx"
        :cy="n.cy"
        r="4"
        class="node-dot"
        :stroke="n.kind === 'futur' ? '#a5b4fc' : '#e2e8f0'"
        stroke-width="1.5"
        fill="#0f172a"
      />

      <text
        v-for="(n, i) in chartGeometry.nodes"
        :key="'lab' + i"
        :x="n.cx"
        :y="H - 8"
        text-anchor="middle"
        class="axis-label"
      >
        {{ n.label }}
      </text>
      <text
        v-for="(n, i) in chartGeometry.nodes"
        :key="'val' + i"
        :x="n.cx"
        :y="n.cy - 10"
        text-anchor="middle"
        class="value-label"
      >
        {{ n.value > 0 ? "+" : "" }}{{ n.value }}
      </text>
    </svg>

    <!-- Tableau de séparation : actif vs en attente (futur) -->
    <div v-if="futurBreakdownRows.length" class="prod-breakdown-table">
      <div class="breakdown-head">
        <div>Tour</div>
        <div class="breakdown-actif">Actif</div>
        <div class="breakdown-pending">En attente</div>
        <div class="breakdown-total">Total</div>
      </div>
      <div
        v-for="row in futurBreakdownRows"
        :key="'break-' + row.tour"
        class="breakdown-row"
      >
        <div class="breakdown-tour">T+{{ row.tour }}</div>
        <div class="breakdown-actif">
          {{ row.actif > 0 ? "+" : "" }}{{ row.actif }}
        </div>
        <div class="breakdown-pending">
          {{ row.pending > 0 ? "+" : "" }}{{ row.pending }}
        </div>
        <div class="breakdown-total">
          {{ row.total > 0 ? "+" : "" }}{{ row.total }}
        </div>
      </div>
    </div>
    <p v-else class="prod-chart-empty">Pas encore de données pour ce graphique.</p>
  </div>
</template>

<style scoped>
.prod-chart-wrap {
  margin: 16px 0;
}
.prod-chart-label {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 8px;
  line-height: 1.45;
}
.leg {
  font-weight: 600;
}
.leg-up {
  color: #4ade80;
}
.leg-down {
  color: #f87171;
}
.prod-chart-svg {
  width: 100%;
  max-width: 100%;
  height: auto;
  display: block;
  border-radius: 8px;
  background: linear-gradient(180deg, #0c1222 0%, #0f172a 100%);
  border: 1px solid #334155;
}
.zero-line {
  stroke: #475569;
  stroke-width: 1;
  stroke-dasharray: 4 3;
}
.sep-futur {
  stroke: #6366f155;
  stroke-width: 1;
  stroke-dasharray: 3 4;
}
.value-label {
  fill: #e2e8f0;
  font-size: 10px;
  font-weight: 600;
}
.axis-label {
  fill: #94a3b8;
  font-size: 9px;
}
.node-dot {
  pointer-events: none;
}
.prod-chart-empty {
  font-size: 13px;
  color: #64748b;
  margin: 0;
  padding: 12px;
  background: #0f172a;
  border-radius: 8px;
  border: 1px dashed #334155;
}

.prod-breakdown-table {
  margin-top: 10px;
  border: 1px solid #334155;
  border-radius: 10px;
  overflow: hidden;
}

.breakdown-head,
.breakdown-row {
  display: grid;
  grid-template-columns: 1.1fr 1fr 1fr 1fr;
  gap: 8px;
  padding: 10px 12px;
}

.breakdown-head {
  background: #0b1224;
  color: #94a3b8;
  font-weight: 700;
  font-size: 12px;
}

.breakdown-row {
  background: #0f172a;
  color: #e2e8f0;
  font-size: 13px;
  border-top: 1px solid #1f2937;
}

.breakdown-actif {
  color: #4ade80;
  font-weight: 700;
}

.breakdown-pending {
  color: #a78bfa;
  font-weight: 700;
}

.breakdown-total {
  color: #e2e8f0;
  font-weight: 800;
}

.breakdown-tour {
  color: #94a3b8;
  font-weight: 700;
}
</style>
