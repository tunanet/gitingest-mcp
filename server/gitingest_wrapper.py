"""gitingest 库的封装。"""

from gitingest import ingest
from typing import Optional, Dict, Any
import re


def _parse_github_url(url: str) -> tuple[str, Optional[str]]:
    """
    解析 GitHub URL，返回 (owner/repo, subdirectory)。

    Args:
        url: GitHub 仓库 URL

    Returns:
        (owner/repo, subdirectory) 元组

    Raises:
        ValueError: 如果 URL 格式无效
    """
    # 支持 https://github.com/owner/repo 格式
    pattern = r"github\.com/([^/]+)/([^/?]+)(?:/tree/[^/]+/([^?]+))?"
    match = re.search(pattern, url)

    if not match:
        raise ValueError(f"Invalid GitHub URL: {url}")

    owner, repo, subdirectory = match.groups()
    repo_path = f"{owner}/{repo}"
    return repo_path, subdirectory


def analyze_repo(
    url: str,
    subdirectory: Optional[str] = None,
    github_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    分析 GitHub 仓库。

    Args:
        url: GitHub 仓库 URL
        subdirectory: 可选的子目录路径
        github_token: 可选的 GitHub token（用于私有仓库）

    Returns:
        包含 summary, tree, content, metadata 的字典
    """
    # 验证 URL
    repo_path, url_subdir = _parse_github_url(url)
    final_subdir = subdirectory or url_subdir

    # 设置 token
    import os
    if github_token:
        os.environ["GITHUB_TOKEN"] = github_token

    # 调用 gitingest
    if final_subdir:
        full_url = f"https://github.com/{repo_path}/tree/main/{final_subdir}"
    else:
        full_url = url

    summary, tree, content = ingest(full_url)

    # 构建返回结果
    return {
        "summary": {
            "repo_name": repo_path,
            "description": summary,
            "total_files": tree.count("\n"),
        },
        "tree": tree,
        "content": content,
        "metadata": {
            "source_url": full_url,
        }
    }
