import pytest
from unittest.mock import MagicMock, patch
from scripts.discover_sources import (
    extract_domain,
    is_allowed_domain,
    discover_official_domain,
    run_discovery
)

class TestDiscoverSources:
    def test_extract_domain(self):
        assert extract_domain("https://www.vgi.ac.in/page") == "vgi.ac.in"
        assert extract_domain("http://vgi.ac.in/rules") == "vgi.ac.in"
        assert extract_domain("https://sub.ugc.gov.in/pdf") == "sub.ugc.gov.in"

    def test_is_allowed_domain(self):
        official = "vgi.ac.in"
        assert is_allowed_domain("vgi.ac.in", official) is True
        assert is_allowed_domain("portal.vgi.ac.in", official) is True
        assert is_allowed_domain("ugc.gov.in", official) is True
        assert is_allowed_domain("aicte-india.org", official) is True
        assert is_allowed_domain("antiragging.in", official) is True
        assert is_allowed_domain("randomblog.com", official) is False
        assert is_allowed_domain("shiksha.com", official) is False

    def test_ambiguous_official_domain_stops_script(self):
        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [
                {"url": "https://vgi.ac.in"},
                {"url": "https://vishveshwarya.org"}  # Two completely different root domains
            ]
        }
        with pytest.raises(ValueError, match="Ambiguous official domain"):
            discover_official_domain(mock_client, "Vishveshwarya Group of Institutions")

    def test_off_domain_and_short_text_dropped_and_20_cap(self, tmp_path):
        mock_client = MagicMock()
        # Official domain search returns clear single domain
        mock_client.search.side_effect = [
            {"results": [{"url": "https://vgi.ac.in"}]},
            # 8 subsequent searches return 30 candidates (some off-domain, some valid)
            {"results": [{"url": f"https://vgi.ac.in/page{i}"} for i in range(15)] + [{"url": "https://random-spam.com/1"}]},
            {"results": [{"url": f"https://vgi.ac.in/page{i}"} for i in range(15, 30)]},
            {"results": []},
            {"results": []},
            {"results": []},
            {"results": []},
            {"results": []},
            {"results": []}
        ]

        # Fetch returns text for each: page0 has tiny text (< 100 chars), others have long text
        def mock_fetch(urls, **kwargs):
            results = []
            for u in urls:
                if "page0" in u:
                    results.append({"url": u, "text": "Short"})  # < 100 chars, must be dropped
                else:
                    results.append({"url": u, "text": "Long valid official text " * 20})
            return {"results": results}

        mock_client.fetch.side_effect = mock_fetch

        test_sources_file = tmp_path / "sources.json"
        with patch("scripts.discover_sources.SOURCES_FILE", test_sources_file):
            sources = run_discovery(client=mock_client)
            # Must not contain off-domain
            for s in sources:
                assert "random-spam.com" not in s["url"]
            # Must not contain page0 (too short)
            assert not any("page0" in s["url"] for s in sources)
            # Must not exceed 20 pages cap
            assert len(sources) <= 20
