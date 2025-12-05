from pathlib import Path

import pandas as pd

from wos_pack_value.knowledge.github_ingestion import extract_knowledge_from_github_root


def test_extract_knowledge_from_local_tables(tmp_path: Path):
    # Create fake repo structure with CSV and XLSX
    repo = tmp_path / "repo1"
    repo.mkdir()
    csv_path = repo / "heroes.csv"
    pd.DataFrame([{"Name": "Hero A", "Rarity": "Epic"}, {"Name": "Hero B", "Rarity": "Legendary"}]).to_csv(csv_path, index=False)
    xlsx_path = repo / "buildings.xlsx"
    pd.DataFrame([{"Building": "Hall", "Level": 1, "Cost": 1000}]).to_excel(xlsx_path, index=False)

    entities = extract_knowledge_from_github_root(
        game="whiteout_survival",
        root=tmp_path,
        table_patterns=["**/*.csv", "**/*.xlsx"],
    )
    names = [e.name for e in entities]
    assert "Hero A" in names
    assert "Hero B" in names
    assert any("Hall" in n for n in names)
