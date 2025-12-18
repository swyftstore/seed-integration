import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.7.2/firebase-auth.js";
import { auth } from "./firebase-init.js";

export async function requireAuth(onSuccess) {
  onAuthStateChanged(auth, async (user) => {
    if (!user) {
      window.location.href = "/login";
      return;
    }

    window.idToken = await user.getIdToken();
    window.userEmail = user.email;

    const decoded = JSON.parse(atob(window.idToken.split(".")[1]));
    window.userRole = decoded.role || "viewer";

    onSuccess();
  });
}
