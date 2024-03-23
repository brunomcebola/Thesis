import Vue from "vue";
import VueRouter from "vue-router";

import datasetsPage from "@/views/datasetsPage.vue";

Vue.use(VueRouter);

const router = new VueRouter({
  mode: "history",
  routes: [
    {
      path: "/",
    },
    {
      path: "/sections",
      name: "sections",
    },
    {
      path: "/datasets",
      name: "datasets",
      component: datasetsPage,
    },
    {
      path: "*",
      redirect: "/",
    },
  ],
});

export default router;
