import { createRouter, createWebHistory } from "vue-router";
import HomePage from "./pages/HomePage.vue";
import DashboardPage from "./pages/DashboardPage.vue";

const routes = [
  { path: "/", component: HomePage },
  { path: "/dashboard", component: DashboardPage },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
