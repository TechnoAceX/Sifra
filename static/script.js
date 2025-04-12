const sign_in_btn = document.querySelector("#sign-in-btn");
const sign_up_btn = document.querySelector("#sign-up-btn");
const container = document.querySelector(".container");

sign_up_btn.addEventListener("click", () => {
  container.classList.add("sign-up-mode");
});

sign_in_btn.addEventListener("click", () => {
  container.classList.remove("sign-up-mode");
});

document.querySelector('form').addEventListener('submit', function (e) {
    e.preventDefault(); // Prevent default form submission

    let formData = new FormData(this);

    fetch('/login', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            window.location.href = '/index';  // Redirect on success
        } else {
            alert('Invalid Credentials');
        }
    });
});
