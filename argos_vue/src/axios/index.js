import axios from "axios";

//Connection with server
var api;

axios.defaults.withCredentials = true;

if (process.env.NODE_ENV === "development") {
  api = axios.create({
    baseURL: "http://localhost:8080/api/",
  });
} else {
  api = axios.create({
    baseURL: window.location.origin + "/api/",
  });
}

export default api;
