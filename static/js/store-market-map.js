import { signOut } from "https://www.gstatic.com/firebasejs/10.7.2/firebase-auth.js";
import { auth } from "./firebase-init.js";
import { requireAuth } from "./auth-guard.js";

requireAuth(initPage);

async function authFetch(url, options = {}) {
  options.headers = options.headers || {};
  options.headers["Authorization"] = "Bearer " + window.idToken;
  return fetch(url, options);
}

function initPage() {
  document.getElementById("userEmail").innerText = window.userEmail;
  loadData();
  loadCurrentMappings();
}

window.logout = () => signOut(auth).then(() => location.href = "/login");

async function loadData() {
    const stores = await fetch("/stores").then(r => r.json());
    const markets = await fetch("/markets").then(r => r.json());

    const marketOptions = markets
        .map(m => `<option value="${m.market_id}">${m.market_name} (ID: ${m.market_id})</option>`)
        .join("");

    const storeOptions = stores
        .map(s => `<option value="${s.estation_name}">${s.estation_name}</option>`)
        .join("");

    const table = document.getElementById("storeTable");

    const tr = document.createElement("tr");

    tr.innerHTML = `
    <td class="p-3 border">
        <select id="market" class="p-2 border rounded w-full">
        <option value="">Select Market</option>
        ${marketOptions}
        </select>
    </td>
    <td class="p-3 border">
        <select id="store" class="p-2 border rounded w-full">
        <option value="">Select Store</option>
        ${storeOptions}
        </select>
    </td>
    <td class="p-3 border">
        <button onclick="saveMapping()"
        class="px-4 py-2 bg-blue-600 text-white rounded">
        Save
        </button>
    </td>
    `;

    table.appendChild(tr);
}

// ---------- CURRENT MAPPINGS ----------
async function loadCurrentMappings() {
    const data = await fetch("/store-market-map/current").then(r => r.json());

    const tbody = document.getElementById("mappingTableBody");
    tbody.innerHTML = "";

    if (data.length === 0) {
        tbody.innerHTML = `
        <tr>
            <td colspan="5" class="p-4 text-center text-gray-500">
            No active mappings found
            </td>
        </tr>`;
        return;
    }

    data.forEach(row => {
        const tr = document.createElement("tr");

        tr.innerHTML = `
        <td class="p-3 border">${row.estation_name}</td>
        <td class="p-3 border">${row.market_id}</td>
        <td class="p-3 border">${row.updated_by}</td>
        <td class="p-3 border">${new Date(row.updated_at).toLocaleString()}</td>
        <td class="p-3 border">
            ${
            window.userRole === "admin"
            ? `
                <button
                onclick="deleteMapping('${row.estation_name}')"
                class="px-3 py-1 bg-red-600 text-white rounded text-xs">
                Delete
                </button>
            `
            : `<span class="text-gray-500 italic">View only</span>`
            }
        </td>
        `;

        tbody.appendChild(tr);
    });
}

window.saveMapping = async() => {
    alert("hello");
    const storeId = document.getElementById("store").value;
    const marketId = document.getElementById("market").value;

    if (!storeId || !marketId) {
      alert("Select a market first");
      return;
    }

    const body = { estation_name: storeId, market_id: marketId };

    const resp = await fetch("/store-market-map", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });

    if (resp.ok) {
      console.log(resp.body);
      alert(`Saved mapping: ${storeId} → ${marketId}`);
    } else {
      alert("Error saving mapping");
    }
    
    setTimeout(loadCurrentMappings, 3000);
}

async function deleteMapping(storeName) {
    if (!confirm(`Delete mapping for ${storeName}?`)) return;

    const resp = await fetch("/store-market-map/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ store_name: storeName })
    });

    if (resp.ok) {
      alert("Mapping deleted");
      loadCurrentMappings();
    } else {
      alert("Delete failed");
    }
}
