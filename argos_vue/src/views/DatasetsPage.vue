<template>
  <div class="container pt-3">
    <div id="filter-container" class="d-flex justify-content-between">
      <ul class="nav nav-tabs">
        <li class="nav-item">
          <a
            :class="'nav-link ' + (tab == 'datasets' ? 'active' : '')"
            @click="() => changeTab('datasets')"
          >
            Datasets
          </a>
        </li>
        <li class="nav-item">
          <a
            :class="'nav-link ' + (tab == 'raw' ? 'active' : '')"
            @click="() => changeTab('raw')"
            >Raw Data</a
          >
        </li>
      </ul>
      <div id="searchbar" class="input-group mb-3">
        <span class="input-group-text" id="basic-addon1">
          <i class="mdi mdi-magnify"></i>
        </span>
        <input
          type="text"
          class="form-control shadow-none"
          placeholder="Search by name..."
          aria-label="Search by name..."
          v-model="search_key"
        />
      </div>
    </div>

    <div id="data-list-container" class="d-flex justify-content-center mt-2">
      <div class="data-list">
        <router-link
          v-for="item in list"
          :key="item.id"
          class="list-item d-flex justify-content-center mb-3 p-2"
          :to="'/datasets/' + item.id"
        >
          <div class="type-icon p-0 ps-1 d-flex align-items-center">
            <i :class="'mdi mdi-' + (tab == 'datasets' ? 'database' : 'raw')">
            </i>
          </div>
          <div class="text-container p-0 ms-3 text-start">
            <p class="m-0">{{ item.name }}</p>
            <p class="m-0 text-secondary">{{ item.path }}</p>
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
        },
        {
          id: 2,
          name: "Dataset 2",
          path: "/path/to/dataset2",
        },
        {
          id: 3,
          name: "Dataset 3",
          path: "/path/to/dataset3",
        },
      ],
      raw_data: [
        {
          id: 1,
          name: "Raw 1",
          path: "/path/to/raw1",
        },
        {
          id: 2,
          name: "Raw 2",
          path: "/path/to/raw2",
        },
        {
          id: 3,
          name: "Raw 3",
          path: "/path/to/raw3",
        },
      ],
      search_key: "",
    };
  },
  computed: {
    tab() {
      return this.$route.query.tab;
    },
    list() {
      return (this.tab == "datasets" ? this.datasets : this.raw_data).filter(
        (item) => item.name.includes(this.search_key)
      );
    },
  },
  methods: {
    goToEdit() {
      alert("Not implemented yet");
    },
    changeTab(tab) {
      this.$router.push({
        query: { ...this.$route.query, ...{ tab: tab } },
      });
    },
  },
  created() {
    if (!this.$route.query.tab) {
      this.$router.push({
        query: { ...this.$route.query, ...{ tab: "datasets" } },
      });
    }

    api.get("/datasets").then((response) => {
      // this.datasets = response.data;
      console.log(response.data);
    });
  },
};
</script>

<style lang="scss" scoped>
.container {
  #filter-container {
    .nav {
      border: none;

      a {
        border-bottom: 1px solid #dee2e6;

        &:not(.active) {
          cursor: pointer;
        }
      }
    }

    #searchbar {
      width: 50%;
      max-width: 500px;
    }
  }

  #data-list-container {
    .data-list {
      width: 100%;

      .list-item {
        background-color: #5dbfd420;
        border: none;
        cursor: pointer;
        text-decoration: none;

        .type-icon {
          i {
            font-size: 24px;
            color: #0c0d29;
          }
        }

        .actions-container {
          width: fit-content;
          margin-left: auto;

          .btn {
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
