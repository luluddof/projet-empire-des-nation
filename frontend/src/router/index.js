import { createRouter, createWebHistory } from "vue-router";

import DashboardPage from "../pages/DashboardPage.vue";
import EarningsView from "../views/EarningsView.vue";
import EvenementDetailView from "../views/EvenementDetailView.vue";
import EvenementsView from "../views/EvenementsView.vue";
import HomeView from "../views/HomeView.vue";
import MjJoueursView from "../views/MjJoueursView.vue";
import ProductionsView from "../views/productions/ProductionsView.vue";
import ResourcesView from "../views/ResourcesView.vue";
import StocksView from "../views/stocks/StocksView.vue";

const routes = [
  { path: "/", name: "home", component: HomeView },
  {
    path: "/dashboard",
    name: "dashboard",
    component: DashboardPage,
    meta: { requiresAuth: true },
  },
  {
    path: "/ressources",
    name: "ressources",
    component: ResourcesView,
    meta: { requiresAuth: true },
  },
  {
    path: "/stocks",
    name: "stocks",
    component: StocksView,
    meta: { requiresAuth: true },
  },
  {
    path: "/productions",
    name: "productions",
    component: ProductionsView,
    meta: { requiresAuth: true },
  },
  {
    path: "/gains",
    name: "gains",
    component: EarningsView,
    meta: { requiresAuth: true },
  },
  {
    path: "/mj/joueurs",
    name: "mj-joueurs",
    component: MjJoueursView,
    meta: { requiresAuth: true },
  },
  {
    path: "/mj/evenements",
    name: "mj-evenements",
    component: EvenementsView,
    meta: { requiresAuth: true },
  },
  {
    path: "/evenements/:id",
    name: "evenement-detail",
    component: EvenementDetailView,
    meta: { requiresAuth: true },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
