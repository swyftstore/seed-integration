import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.2/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.7.2/firebase-auth.js";

const firebaseConfig = {
    apiKey: "AIzaSyDiBf4C4K5uoK_PS_kpMtaHLUvxnKLytF0",
    authDomain: "zoom-shops-dev.firebaseapp.com",
    databaseURL: "https://zoom-shops-dev.firebaseio.com",
    projectId: "zoom-shops-dev",
    storageBucket: "zoom-shops-dev.appspot.com",
    messagingSenderId: "664912892527",
    appId: "1:664912892527:web:d38c1d6f14f311ab",
    measurementId: "G-TDJME6Q1L1"
};

export const firebaseApp = initializeApp(firebaseConfig);
export const auth = getAuth(firebaseApp);
