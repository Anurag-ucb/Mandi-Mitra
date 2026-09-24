function showAuth(type) {

    const loginForm =
        document.getElementById("loginForm");

    const signupForm =
        document.getElementById("signupForm");

    const loginTab =
        document.getElementById("loginTab");

    const signupTab =
        document.getElementById("signupTab");


    if (type === "login") {

        loginForm.style.display = "block";
        signupForm.style.display = "none";

        loginTab.classList.add("active");
        signupTab.classList.remove("active");

    }


    if (type === "signup") {

        loginForm.style.display = "none";
        signupForm.style.display = "block";

        loginTab.classList.remove("active");
        signupTab.classList.add("active");

    }

}