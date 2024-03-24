<template>
  <div class="container pt-3">
    <div id="searchbar-container" class="d-flex justify-content-center">
      <div id="searchbar" class="input-group mb-3">
        <span class="input-group-text" id="basic-addon1">
          <i class="mdi mdi-magnify"></i>
        </span>
        <input
          type="text"
          class="form-control shadow-none"
          placeholder="Dataset"
          aria-label="Dataset"
          v-model="search_key"
        />
      </div>
    </div>

    <div
      id="favourite-datasets-container"
      class="d-flex justify-content-center"
    >
      <div
        id="favourite-datasets-list"
        class="datasets-list"
        v-if="favourite_datasets.length"
      >
        <h6 class="text-start">Other datasets</h6>
        <router-link
          v-for="dataset in favourite_datasets"
          :key="dataset.id"
          class="list-item d-flex justify-content-center mb-3 p-2"
          :to="'/datasets/' + dataset.id"
        >
          <div class="favourite-container p-0 ps-1 d-flex align-items-center">
            <button type="button" class="btn">
              <i class="mdi mdi-star-outline"></i>
            </button>
          </div>
          <div class="text-container p-0 ms-3 text-start">
            <p class="m-0">{{ dataset.name }}</p>
            <p class="m-0 text-secondary">{{ dataset.path }}</p>
          </div>
          <div class="actions-container p-0 pe-1 d-flex align-items-center">
            <button type="button" class="btn">
              <i class="mdi mdi-pencil"></i>
            </button>
            <button type="button" class="btn ms-3">
              <i class="mdi mdi-delete"></i>
            </button>
          </div>
        </router-link>
      </div>
    </div>

    <div
      id="favourite-datasets-container"
      class="d-flex justify-content-center"
    >
      <div
        id="other-datasets-list"
        class="datasets-list mt-3"
        v-if="other_datasets.length"
      >
        <h6 class="text-start">Other datasets</h6>
        <router-link
          v-for="dataset in other_datasets"
          :key="dataset.id"
          class="list-item d-flex justify-content-center mb-3 p-2"
          :to="'/datasets/' + dataset.id"
        >
          <div class="favourite-container p-0 ps-1 d-flex align-items-center">
            <button type="button" class="btn">
              <i class="mdi mdi-star-outline"></i>
            </button>
          </div>
          <div class="text-container p-0 ms-3 text-start">
            <p class="m-0">{{ dataset.name }}</p>
            <p class="m-0 text-secondary">{{ dataset.path }}</p>
          </div>
          <div class="actions-container p-0 pe-1 d-flex align-items-center">
            <button type="button" class="btn">
              <i class="mdi mdi-pencil"></i>
            </button>
            <button type="button" class="btn ms-3">
              <i class="mdi mdi-delete"></i>
            </button>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import api from "@/axios";

export default {
  name: "DatasetsPage",
  data() {
    return {
      datasets: [
        {
          id: 1,
          name: "Dataset 1",
          path: "/path/to/dataset1",
          favourite: true,
        },
        {
          id: 2,
          name: "Dataset 2",
          path: "/path/to/dataset2",
          favourite: false,
        },
        {
          id: 3,
          name: "Dataset 3",
          path: "/path/to/dataset3",
          favourite: false,
        },
        {
          id: 4,
          name: "Dataset 4",
          path: "/path/to/dataset4",
          favourite: false,
        },
      ],
      search_key: "",
    };
  },
  computed: {
    favourite_datasets() {
      return this.datasets.filter(
        (dataset) => dataset.favourite && dataset.name.includes(this.search_key)
      );
    },
    other_datasets() {
      return this.datasets.filter(
        (dataset) =>
          !dataset.favourite && dataset.name.includes(this.search_key)
      );
    },
  },
  methods: {
    add_to_favourite() {
      alert("Not implemented yet");
    },
    remove_from_favourite() {
      alert("Not implemented yet");
    },
    go_to_edit() {
      alert("Not implemented yet");
    },
  },
  created() {
    api.get("/datasets").then((response) => {
      this.datasets = response.data;
    });
  },
};
</script>

<style lang="scss" scoped>
.container {
  #searchbar-container {
    width: 100%;

    #searchbar {
      width: 50%;
    }
  }

  #favoutite-datasets-container {
    width: 100%;
  }

  .datasets-list {
    width: 100%;
    max-width: 1100px;

    .list-item {
      width: 100%;
      background-color: #5dbfd420;
      border: none;
      cursor: pointer;
      text-decoration: none;

      .favourite-container,
      .actions-container {
        width: fit-content;
      }

      .actions-container {
        margin-left: auto;
      }

      .favourite-container .btn,
      .actions-container .btn {
        width: 32px;
        height: 32px;
        padding: 0;
        background-color: #5dbfd440;
        border-radius: 2px;
        border: none;

        &:hover {
          background-color: #5dbfd420;
        }

        &:active {
          background-color: #5dbfd450;
        }
      }

      .text-container {
        color: #0c0d29;
        p {
          line-height: 1.2;
        }
      }
    }
  }
}
</style>
