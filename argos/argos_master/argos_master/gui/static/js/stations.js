const form = document.querySelector("#station-form");
const btn = document.querySelector("#close-modal");

form.addEventListener(
  "submit",
  (event) => {
    event.preventDefault();
    event.stopPropagation();

    let valid = form.checkValidity();
    if (!valid) {
      form.classList.add("was-validated");
    } else {
      const data = Object.fromEntries(new FormData(event.target).entries());

      axios
        .post("api/stations/add", data)
        .then(function (response) {
          sessionStorage.setItem("station_creation_success", response.data);
          window.location.reload();
        })
        .catch(function (error) {
          const alert_msg = document.querySelector("#alert");
          const alert_msg_text = document.querySelector("#alert-text");
          const alert_msg_icon = document.querySelector("#alert-icon");

          alert_msg_text.innerHTML = error.response.data;
          alert_msg_icon.setAttribute("href", "#exclamation-triangle-fill");
          alert_msg.classList.add("show");
          alert_msg.classList.add("alert-danger");
        });
    }
  },
  false
);

btn.addEventListener(
  "click",
  (event) => {
    form.classList.remove("was-validated");
    form.reset();
  },
  false
);
