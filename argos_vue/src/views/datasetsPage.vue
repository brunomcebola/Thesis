<template>
  <div id="container" class="d-flex justify-content-center">
    <div id="content">
      <div id="searchbar-container" class="d-flex justify-content-center mt-3">
        <div class="input-group mb-3" id="searchbar">
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
      <div id="favourite-datasets-list" v-if="favourite_datasets.length">
        <h5 class="text-start">Favourite datasets</h5>
        <div
          v-for="dataset in favourite_datasets"
          :key="dataset.id"
          class="list-item d-flex justify-content-center mb-3"
        >
          <div class="item-content p-3 d-flex">
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
          </div>
        </div>
      </div>
      <div id="other-datasets-list" v-if="other_datasets.length">
        <h5 class="text-start">Other datasets</h5>
        <div
          v-for="dataset in other_datasets"
          :key="dataset.id"
          class="list-item d-flex justify-content-center mb-3"
        >
          <div class="item-content p-3 d-flex">
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
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
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
  },
};
</script>

<style lang="scss" scoped>
#container {
  #content {
    width: 90%;

    #searchbar-container {
      #searchbar {
        width: 50%;
      }
    }

    .list-item {
      .item-content {
        width: 100%;
        max-width: 1100px;
        background-color: #5dbfd420;
        border: none;
        cursor: pointer;

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
}
</style>
