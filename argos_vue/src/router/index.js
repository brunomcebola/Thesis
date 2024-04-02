import Vue from "vue";
import VueRouter from "vue-router";

import DatasetsPage from "@/views/DatasetsPage.vue";
import DatasetPage from "@/views/DatasetPage.vue";

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
      component: DatasetsPage,
    },
    {
      path: "/datasets/:name",
      name: "dataset",
      component: DatasetPage,
    },
    {
      path: "*",
      redirect: "/",
    },
  ],
});

export default router;
