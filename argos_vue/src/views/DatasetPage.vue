<template>
  <div class="container pt-3">
    <div class="row">
      <div
        class="col-12 col-md-6 col-xl-3 p-3"
        v-for="image in images"
        :key="image.name"
      >
        <div class="image-card">
          <img :src="image.src" class="card-img-top" />
          <input
            class="form-check-input m-0"
            type="checkbox"
            value=""
            id="flexCheckDefault"
            v-model="image.selected"
          />
          <i class="mdi mdi-arrow-expand text-secondary"></i>
        </div>
        <p class="text-start text-secondary">{{ image.name }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import api from "@/axios";

export default {
  name: "DatasetPage",
  data() {
    return {
      images: [],
    };
  },
  created() {
    // TODO: missing val and test listing images
    // TODO: missing headers in page and way to show dataset info
    // TODO: perhaps have multiple tabs for dataset info, images, and annotations
    api
      .get("/datasets/" + this.$route.params.name + "/images")
      .then((response) => {
        response.data.forEach((image) => {
          this.images.push({
            name: image,
            selected: false,
            src:
              "http://localhost:5000/api/datasets/" +
              this.$route.params.name +
              "/images/" +
              image,
          });
        });
      });
  },
};
</script>

<style lang="scss" scoped>
.container {
  .image-card {
    position: relative;

    input {
      position: absolute;
      top: 10px;
      left: 10px;
      cursor: pointer;
    }

    i {
      position: absolute;
      bottom: 6px;
      right: 10px;
      cursor: pointer;
    }
  }
}
</style>
