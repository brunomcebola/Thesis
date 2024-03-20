<template>
  <nav class="navbar sticky-top navbar-expand-sm p-0">
    <div class="container-fluid">
      <a
        class="navbar-brand pe-2"
        href="https://www.thalesgroup.com/en"
        target="_blank"
      >
        <img
          src="../../public/logo.png"
          alt="Thales"
          height="14"
          width="auto"
        />
      </a>
      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarNav"
        aria-controls="navbarNav"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <img
          src="@/assets/images/menu.svg"
          alt="Menu"
          height="auto"
          width="25px"
        />
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav">
          <li
            v-for="m in menu"
            :key="m.title"
            :class="'nav-item ' + ($route.name == m.url ? 'active' : '')"
          >
            <router-link class="nav-link" aria-current="page" :to="m.url">
              {{ m.title }}
            </router-link>
          </li>
          <li class="nav-item logout">
            <a class="nav-link" href="#">
              Logout
              <img
                src="@/assets/images/logout.svg"
                class="ms-1"
                alt="Menu"
                height="auto"
                width="14px"
              />
            </a>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: "NavBar",
  data() {
    return {
      menu: [
        { url: "stations", title: "Stations" },
        { url: "areas", title: "Areas" },
        { url: "analytics", title: "Analytics" },
        { url: "admin", title: "Admin" },
      ],
    };
  },
  created() {
    alert(this.$route.name);
  },
};
</script>

<style lang="scss" scoped>
@import "@/assets/scss/_mixins.scss";

.navbar {
  background-color: #0c0d29;

  .navbar-toggler {
    margin: 6px 0px;
    transition: transform 25ms ease-in-out;

    &:hover {
      transform: scale(1.05);
    }

    &:active {
      transform: scale(0.95);
    }

    &:focus {
      box-shadow: none;
    }
  }

  .navbar-brand {
    border-top: 6px solid transparent;
    border-bottom: 6px solid transparent;
  }

  .navbar-nav {
    width: 100%;

    .nav-item {
      position: relative;
      margin-top: 6px;
      margin-bottom: 6px;

      &:last-of-type {
        margin-bottom: 16px;
      }

      &::after {
        display: block;
        content: "";
        position: absolute;
        top: 0;
        left: 0px;
        height: 100%;
        width: 0px;
        transform-origin: center;
        border-left: 6px solid #5dbfd4;
        transform: scaleY(0);
        transition: transform 250ms ease-in-out;
      }

      &:hover::after {
        transform: scaleY(1);
      }

      &.active {
        border-left: 6px solid #5dbfd4;

        &::after {
          display: none;
        }

        .nav-link {
          padding-left: 4px;
        }
      }

      .nav-link {
        padding-left: 10px;
      }

      &.logout {
        a {
          display: flex;
        }
      }

      .nav-link,
      .nav-link:hover {
        color: #fff;
      }

      @include sm {
        border-right: 1px solid #1e2039;

        &:first-of-type {
          border-left: 1px solid #1e2039;
        }

        &:last-of-type {
          margin-bottom: auto;
        }

        &::after {
          display: block;
          content: "";
          position: absolute;
          top: unset;
          left: unset;
          height: 0px;
          width: 100%;
          transform-origin: center;
          transform: scaleX(0);
          border-bottom: solid 6px #5dbfd4;
          transition: transform 250ms ease-in-out;
        }

        &:hover::after {
          transform: scaleX(1);
        }

        &.active {
          transform: scaleX(1);
        }

        &.logout {
          margin-left: auto !important;
          border-right: none;
        }

        &.active {
          border-bottom: 6px solid #5dbfd4;
          margin-bottom: 0px;

          &:not(:first-of-type) {
            border-left: none;
          }

          &::after {
            display: none;
          }

          .nav-link {
            padding-left: 8px;
          }
        }

        .nav-link {
          padding-left: 8px;
        }
      }
    }
  }
}
</style>
