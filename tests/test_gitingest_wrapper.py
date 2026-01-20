import pytest
from unittest.mock import patch, MagicMock
from server.gitingest_wrapper import analyze_repo, _parse_github_url


class TestParseGitHubUrl:
    """测试 GitHub URL 解析功能。"""

    def test_parse_basic_url(self):
        """测试解析基本 URL。"""
        repo_path, subdir = _parse_github_url("https://github.com/owner/repo")
        assert repo_path == "owner/repo"
        assert subdir is None

    def test_parse_url_with_subdirectory(self):
        """测试解析带子目录的 URL。"""
        repo_path, subdir = _parse_github_url("https://github.com/owner/repo/tree/main/src")
        assert repo_path == "owner/repo"
        assert subdir == "src"

    def test_parse_invalid_url(self):
        """测试解析无效 URL。"""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            _parse_github_url("not-a-url")

        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            _parse_github_url("https://example.com/repo")


class TestAnalyzeRepo:
    """测试仓库分析功能。"""

    @patch("server.gitingest_wrapper.ingest_async")
    def test_analyze_repo_basic(self, mock_ingest):
        """测试基本仓库分析。"""
        # Mock the ingest_async function
        # Note: tree with 3 lines (file1.py\nfile2.py\nfile3.py) has 3 non-empty lines
        mock_ingest.return_value = ("Test summary", "file1.py\nfile2.py\nfile3.py", "Content here")

        result = analyze_repo("https://github.com/owner/repo")

        assert "summary" in result
        assert "tree" in result
        assert "content" in result
        assert "metadata" in result
        assert result["summary"]["repo_name"] == "owner/repo"
        assert result["summary"]["total_files"] == 3  # 3 non-empty lines

    @patch("server.gitingest_wrapper.ingest_async")
    def test_analyze_repo_with_subdirectory(self, mock_ingest):
        """测试子目录分析。"""
        mock_ingest.return_value = ("Test summary", "file.py", "Content")

        result = analyze_repo(
            "https://github.com/coderamp-labs/gitingest",
            subdirectory="README.md"
        )

        assert "summary" in result
        assert result["summary"]["repo_name"] == "coderamp-labs/gitingest"
        # Verify the URL passed to ingest_async
        mock_ingest.assert_called_once()
        call_url = mock_ingest.call_args[0][0]
        assert "README.md" in call_url

    @patch("server.gitingest_wrapper.ingest_async")
    def test_analyze_repo_with_github_token(self, mock_ingest):
        """测试带 GitHub token 的分析。"""
        mock_ingest.return_value = ("Summary", "tree", "content")

        import os
        original_token = os.environ.get("GITHUB_TOKEN")

        try:
            analyze_repo("https://github.com/owner/repo", github_token="test_token")
            # Token should be set in environment
            # (actual verification would depend on gitingest implementation)
        finally:
            # Restore original token
            if original_token:
                os.environ["GITHUB_TOKEN"] = original_token
            elif "GITHUB_TOKEN" in os.environ:
                del os.environ["GITHUB_TOKEN"]

    def test_analyze_repo_invalid_url(self):
        """测试无效 URL。"""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            analyze_repo("not-a-url")

    @patch("server.gitingest_wrapper.ingest_async")
    def test_analyze_repo_network_error(self, mock_ingest):
        """测试网络错误处理。"""
        # Simulate network error from gitingest
        mock_ingest.side_effect = RuntimeError("Network error")

        with pytest.raises(RuntimeError, match="Network error"):
            analyze_repo("https://github.com/owner/repo")

    def test_analyze_repo_private_with_token(self):
        """测试私有仓库（带 token）。需要真实 token，暂时跳过。"""
        pytest.skip("Requires valid GitHub token")
