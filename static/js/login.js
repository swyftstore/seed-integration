import { GoogleAuthProvider, signInWithPopup, onAuthStateChanged }
  from "https://www.gstatic.com/firebasejs/10.7.2/firebase-auth.js";

import { auth } from "./firebase-init.js";

const provider = new GoogleAuthProvider();

document.getElementById("loginBtn").onclick = () => {
  signInWithPopup(auth, provider);
};

onAuthStateChanged(auth, (user) => {
  if (user) {
    window.location.href = "/ui/store-market-map";
  }
});
