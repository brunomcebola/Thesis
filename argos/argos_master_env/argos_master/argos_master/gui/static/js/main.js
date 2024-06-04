let close_alert_msg_btn = document.querySelector("#close-alert");

function reset_alert() {
  let alert_msg = document.querySelector("#alert");
  let alert_msg_text = document.querySelector("#alert-text");
  let alert_msg_icon = document.querySelector("#alert-icon");

  alert_msg.addEventListener("animationend", () => {
    alert_msg_text.innerHTML = "";
    alert_msg_icon.setAttribute("href", "");
    alert_msg.classList.remove("hide");
    alert_msg.classList.remove("alert-success");
    alert_msg.classList.remove("alert-danger");
    alert_msg.classList.remove("alert-warning");

    var new_alert_msg = alert_msg.cloneNode(true);
    alert_msg.parentNode.replaceChild(new_alert_msg, alert_msg);

    let close_alert_msg_btn = document.querySelector("#close-alert");
    close_alert_msg_btn.addEventListener("click", reset_alert);
  });

  alert_msg.classList.add("hide");
  alert_msg.classList.remove("show");
}

close_alert_msg_btn.addEventListener("click", reset_alert);

if(sessionStorage.getItem("station_creation_success")) {
  let alert_msg = document.querySelector("#alert");
  let alert_msg_text = document.querySelector("#alert-text");
  let alert_msg_icon = document.querySelector("#alert-icon");

  alert_msg_text.innerHTML = sessionStorage.getItem("station_creation_success");
  alert_msg_icon.setAttribute("href", "#check-circle-fill");
  alert_msg.classList.add("show");
  alert_msg.classList.add("alert-success");

  sessionStorage.removeItem("station_creation_success");
}