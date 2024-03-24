<template>
  <div class="container pt-3">
    <div class="row">
      <div
        class="col-12 col-md-6 col-xl-3 p-3"
        v-for="image in images"
        :key="image.name"
      >
        <div class="image-card">
          <img src="@/assets/images/no_media.png" class="card-img-top" />
          <input
            class="form-check-input m-0"
            type="checkbox"
            value=""
            id="flexCheckDefault"
            v-model="image.selected"
          />
          <i class="mdi mdi-arrow-expand text-secondary"></i>
        </div>
        <p class="text-start text-secondary">jdjdj</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "DatasetPage",
  data() {
    return {
      images: [
        { name: "image1", selected: true },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image1", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image1", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image1", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
        { name: "image2", selected: false },
      ],
    };
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
