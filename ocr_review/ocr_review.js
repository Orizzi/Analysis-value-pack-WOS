(() => {
  let state = {
    packs: [],
  };

  function showAlert(msg) {
    const el = document.getElementById("or-alert");
    el.textContent = msg;
    el.hidden = !msg;
  }

  function renderPacks() {
    const list = document.getElementById("or-list");
    list.innerHTML = "";
    state.packs.forEach((p, idx) => {
      const card = document.createElement("article");
      card.className = "or-card";
      const imgName = p.source_image ? p.source_image.split("/").pop() : "";
      card.innerHTML = `
        <header>
          <div>
            <div class="or-muted">${imgName || "No image"}</div>
          </div>
          <label class="or-discard">
            <input type="checkbox" data-discard="${idx}" ${p.discarded ? "checked" : ""}/> discard
          </label>
        </header>
        <div>
          <label>Name</label>
          <input class="or-input" data-field="name" data-idx="${idx}" value="${p.name || p.name_ocr || ""}" />
        </div>
        <div class="or-row">
          <div>
            <label>Price</label>
            <input class="or-input" data-field="price" data-idx="${idx}" value="${p.price ?? p.price_ocr ?? ""}" />
          </div>
          <div>
            <label>Currency</label>
            <input class="or-input" data-field="currency" data-idx="${idx}" value="${p.currency || p.currency_ocr || ""}" />
          </div>
        </div>
        <div>
          <div class="or-actions">
            <span class="or-badge">Items</span>
            <button class="or-btn" data-add-item="${idx}">Add item</button>
          </div>
          <table class="or-item-table" data-table="${idx}">
            <thead><tr><th>Name</th><th>Qty</th><th></th></tr></thead>
            <tbody>
              ${(p.items || p.items_ocr || [])
                .map(
                  (it, iidx) =>
                    `<tr>
                      <td><input class="or-input" data-item-name="${idx}-${iidx}" value="${it.name || ""}"></td>
                      <td><input class="or-input" data-item-qty="${idx}-${iidx}" value="${it.quantity || ""}"></td>
                      <td><button class="or-btn" data-del-item="${idx}-${iidx}">✕</button></td>
                    </tr>`
                )
                .join("")}
            </tbody>
          </table>
        </div>
      `;
      list.appendChild(card);
    });
    bindPackInputs();
    document.getElementById("or-download").disabled = state.packs.length === 0;
  }

  function bindPackInputs() {
    document.querySelectorAll("[data-field]").forEach((input) => {
      input.addEventListener("input", (e) => {
        const idx = Number(e.target.dataset.idx);
        const field = e.target.dataset.field;
        const value = e.target.value;
        if (field === "price") {
          const num = parseFloat(value);
          state.packs[idx][field] = Number.isFinite(num) ? num : value;
        } else {
          state.packs[idx][field] = value;
        }
      });
    });
    document.querySelectorAll("[data-add-item]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const idx = Number(e.target.dataset.addItem);
        const arr = state.packs[idx].items || state.packs[idx].items_ocr || [];
        arr.push({ name: "", quantity: 0 });
        state.packs[idx].items = arr;
        renderPacks();
      });
    });
    document.querySelectorAll("[data-del-item]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const [pidx, iidx] = e.target.dataset.delItem.split("-").map(Number);
        const arr = state.packs[pidx].items || state.packs[pidx].items_ocr || [];
        arr.splice(iidx, 1);
        state.packs[pidx].items = arr;
        renderPacks();
      });
    });
    document.querySelectorAll("[data-item-name]").forEach((input) => {
      input.addEventListener("input", (e) => {
        const [pidx, iidx] = e.target.dataset.itemName.split("-").map(Number);
        const arr = state.packs[pidx].items || state.packs[pidx].items_ocr || [];
        arr[iidx].name = e.target.value;
      });
    });
    document.querySelectorAll("[data-item-qty]").forEach((input) => {
      input.addEventListener("input", (e) => {
        const [pidx, iidx] = e.target.dataset.itemQty.split("-").map(Number);
        const arr = state.packs[pidx].items || state.packs[pidx].items_ocr || [];
        const num = parseFloat(e.target.value);
        arr[iidx].quantity = Number.isFinite(num) ? num : e.target.value;
      });
    });
    document.querySelectorAll("[data-discard]").forEach((input) => {
      input.addEventListener("change", (e) => {
        const idx = Number(e.target.dataset.discard);
        state.packs[idx].discarded = e.target.checked;
      });
    });
  }

  function loadFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        const arr = Array.isArray(data) ? data : data.packs || [];
        state.packs = arr.map((p) => ({
          ...p,
          items: p.items || p.items_ocr || [],
        }));
        renderPacks();
        showAlert("");
      } catch (err) {
        console.error(err);
        showAlert("Failed to parse JSON.");
      }
    };
    reader.readAsText(file);
  }

  function buildReviewedPayload() {
    return state.packs.map((p, idx) => {
      if (p.discarded) {
        return { id: p.id || `ocr_pack_${idx + 1:03}`, discarded: true, reason: p.reason || "discarded" };
      }
      return {
        id: p.id || `ocr_pack_${idx + 1:03}`,
        source_image: p.source_image,
        name: p.name || p.name_ocr,
        price: p.price ?? p.price_ocr ?? 0,
        currency: p.currency || p.currency_ocr || "USD",
        items: (p.items || p.items_ocr || []).map((it, iidx) => ({
          name: it.name || `Item ${iidx + 1}`,
          quantity: parseFloat(it.quantity) || 0,
        })),
        notes: p.notes || "",
      };
    });
  }

  function downloadReviewed() {
    const payload = buildReviewedPayload();
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ocr_packs_reviewed.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  function bindUI() {
    document.getElementById("or-file-input").addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (file) loadFile(file);
    });
    document.getElementById("or-download").addEventListener("click", downloadReviewed);
  }

  document.addEventListener("DOMContentLoaded", bindUI);

  // Manual sanity test:
  // 1) Open ocr_review.html in a browser.
  // 2) Load data_review/ocr_packs_raw.json.
  // 3) Edit fields, add/remove items.
  // 4) Click "Download reviewed JSON" and place the file into data_review/ocr_packs_reviewed.json.
})();
