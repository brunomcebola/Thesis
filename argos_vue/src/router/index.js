import Vue from "vue";
import VueRouter from "vue-router";

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
    },
    {
      path: "*",
      redirect: "/",
    },
  ],
});

export default router;
