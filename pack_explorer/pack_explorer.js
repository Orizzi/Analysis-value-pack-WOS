(() => {
  const basePath = window.PACK_EXPLORER_BASE || "./site_data/";
  const state = {
    packs: [],
    rankings: { overall: {}, byCategory: {} },
    filtered: [],
  };

  async function fetchJson(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
    return res.json();
  }

  function mergePacksWithRankings(packs, overallData, byCategoryData) {
    const overallMap = {};
    (overallData.packs || []).forEach((p) => {
      overallMap[p.id] = p;
    });
    const categoryRanks = byCategoryData.by_category || byCategoryData.byCategory || {};

    return packs.map((p) => {
      const merged = { ...p };
      const o = overallMap[p.id] || {};
      merged.rank_overall = o.rank_overall ?? null;
      merged.value_per_dollar = o.value_per_dollar ?? p.value_per_dollar ?? p.value || 0;
      merged.category_scores = {};
      Object.entries(categoryRanks).forEach(([cat, list]) => {
        const found = (list || []).find((entry) => entry.id === p.id);
        if (found) {
          merged.category_scores[cat] = { score: found.score, rank: found.rank };
        }
      });
      return merged;
    });
  }

  function applyFiltersAndSort(packs, filters) {
    let result = [...packs];
    if (filters.search) {
      const term = filters.search.toLowerCase();
      result = result.filter((p) => p.name.toLowerCase().includes(term));
    }
    if (filters.excludeReference) {
      result = result.filter((p) => !p.is_reference);
    }
    if (filters.focusCategory) {
      result = result.filter((p) => p.category_scores && p.category_scores[filters.focusCategory]);
    }
    const sortField = filters.sortField || "rank_overall";
    const dir = filters.sortDir === "asc" ? 1 : -1;
    result.sort((a, b) => {
      const av =
        sortField === "rank_overall"
          ? a.rank_overall ?? Number.POSITIVE_INFINITY
          : sortField === "value_per_dollar"
            ? a.value_per_dollar ?? 0
            : a.price?.amount ?? a.price ?? 0;
      const bv =
        sortField === "rank_overall"
          ? b.rank_overall ?? Number.POSITIVE_INFINITY
          : sortField === "value_per_dollar"
            ? b.value_per_dollar ?? 0
            : b.price?.amount ?? b.price ?? 0;
      return av > bv ? dir : av < bv ? -dir : 0;
    });
    if (filters.topN && filters.topToggle) {
      result = result.slice(0, filters.topN);
    }
    return result;
  }

  function renderList() {
    const listEl = document.getElementById("pe-list");
    listEl.innerHTML = "";
    state.filtered.forEach((p) => {
      const card = document.createElement("article");
      card.className = "pe-card";
      const refBadge = p.is_reference ? '<span class="pe-chip">Reference</span>' : "";
      const categoryRank = document.getElementById("pe-category").value;
      const focusInfo =
        categoryRank && p.category_scores && p.category_scores[categoryRank]
          ? `<span class="pe-chip">${categoryRank} rank #${p.category_scores[categoryRank].rank}</span>`
          : "";
      card.innerHTML = `
        <header>
          <div>
            <div>${p.name}</div>
            <div class="pe-muted">${p.price?.amount ?? p.price ?? 0} ${p.price?.currency ?? ""}</div>
          </div>
          <div>${refBadge}${focusInfo}</div>
        </header>
        <div>VPD: <strong>${(p.value_per_dollar ?? 0).toFixed(2)}</strong> | Rank: ${p.rank_overall ?? "?"}</div>
        <div class="pe-muted">Source: ${p.source?.sheet || ""}</div>
        <button class="pe-btn" data-pack="${p.id}">Details</button>
      `;
      card.querySelector("button").addEventListener("click", () => showModal(p));
      listEl.appendChild(card);
    });
  }

  function showModal(pack) {
    const modal = document.getElementById("pe-modal");
    const body = document.getElementById("pe-modal-body");
    const itemsHtml = (pack.items || [])
      .map(
        (it) =>
          `<tr><td>${it.name}</td><td>${it.quantity}</td><td>${it.category || ""}</td><td>${(it.value || 0).toFixed(2)}</td></tr>`
      )
      .join("");
    const categoriesHtml = Object.entries(pack.category_scores || {})
      .map(([cat, val]) => `<li>${cat}: score ${val.score?.toFixed?.(2) ?? val.score}, rank #${val.rank ?? "?"}</li>`)
      .join("");
    body.innerHTML = `
      <h2>${pack.name}</h2>
      <p class="pe-muted">Price: ${pack.price?.amount ?? pack.price ?? 0} ${pack.price?.currency ?? ""}</p>
      <p>Value per dollar: ${(pack.value_per_dollar ?? 0).toFixed(2)} | Rank overall: ${pack.rank_overall ?? "?"}</p>
      <p>Reference: ${pack.is_reference ? "Yes" : "No"}</p>
      <h3>Items</h3>
      <table class="pe-table">
        <thead><tr><th>Name</th><th>Qty</th><th>Category</th><th>Value</th></tr></thead>
        <tbody>${itemsHtml}</tbody>
      </table>
      <h3>Category scores</h3>
      <ul>${categoriesHtml || "<li>None</li>"}</ul>
    `;
    modal.hidden = false;
  }

  function bindControls() {
    document.getElementById("pe-modal-close").onclick = () => (document.getElementById("pe-modal").hidden = true);
    const inputs = [
      "pe-search",
      "pe-exclude-ref",
      "pe-top-toggle",
      "pe-top-n",
      "pe-sort",
      "pe-sort-dir",
      "pe-category",
    ];
    inputs.forEach((id) => {
      document.getElementById(id).addEventListener("input", updateFiltered);
      document.getElementById(id).addEventListener("change", updateFiltered);
    });
  }

  function updateFiltered() {
    const filters = {
      search: document.getElementById("pe-search").value.trim(),
      excludeReference: document.getElementById("pe-exclude-ref").checked,
      topToggle: document.getElementById("pe-top-toggle").checked,
      topN: parseInt(document.getElementById("pe-top-n").value, 10) || 0,
      sortField: document.getElementById("pe-sort").value,
      sortDir: document.getElementById("pe-sort-dir").value,
      focusCategory: document.getElementById("pe-category").value || null,
    };
    state.filtered = applyFiltersAndSort(state.packs, filters);
    renderList();
  }

  async function init() {
    try {
      const [packsData, overallData, catData] = await Promise.all([
        fetchJson(basePath + "packs.json"),
        fetchJson(basePath + "pack_ranking_overall.json"),
        fetchJson(basePath + "pack_ranking_by_category.json"),
      ]);
      const packs = packsData.packs || [];
      state.packs = mergePacksWithRankings(packs, overallData, catData);
      const catSelect = document.getElementById("pe-category");
      const categories = Object.keys(catData.by_category || {});
      categories.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = c;
        catSelect.appendChild(opt);
      });
      bindControls();
      updateFiltered();
    } catch (err) {
      const alert = document.getElementById("pe-alert");
      alert.textContent = err.message;
      alert.hidden = false;
      console.error(err);
    }
  }

  document.addEventListener("DOMContentLoaded", init);

  // Export pure functions for testing
  window.PackExplorer = { mergePacksWithRankings, applyFiltersAndSort };
})();
