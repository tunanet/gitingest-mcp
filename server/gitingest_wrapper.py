"""gitingest 库的封装。"""

import os
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
    github_token: Optional[str] = None,
    default_branch: Optional[str] = None
) -> Dict[str, Any]:
    """
    分析 GitHub 仓库。

    Args:
        url: GitHub 仓库 URL
        subdirectory: 可选的子目录路径
        github_token: 可选的 GitHub token（用于私有仓库）
        default_branch: 可选的默认分支名（默认为 'main'，也可指定为 'master' 等）

    Returns:
        包含 summary, tree, content, metadata 的字典

    Raises:
        ValueError: 如果 URL 格式无效
        OSError: 如果无法访问仓库
        RuntimeError: 如果 gitingest 调用失败
    """
    # 验证 URL
    repo_path, url_subdir = _parse_github_url(url)
    final_subdir = subdirectory or url_subdir
    branch = default_branch or "main"

    # 安全地设置 token
    original_token = os.environ.get("GITHUB_TOKEN")
    try:
        if github_token:
            os.environ["GITHUB_TOKEN"] = github_token

        # 调用 gitingest
        if final_subdir:
            full_url = f"https://github.com/{repo_path}/tree/{branch}/{final_subdir}"
        else:
            full_url = url

        summary, tree, content = ingest(full_url)
    finally:
        # 恢复原始状态
        if original_token is None:
            os.environ.pop("GITHUB_TOKEN", None)
        else:
            os.environ["GITHUB_TOKEN"] = original_token

    # 构建返回结果
    # 正确计算文件数：tree 中每行代表一个文件或目录
    file_count = len([line for line in tree.split('\n') if line.strip()])

    return {
        "summary": {
            "repo_name": repo_path,
            "description": summary,
            "total_files": file_count,
        },
        "tree": tree,
        "content": content,
        "metadata": {
            "source_url": full_url,
        }
    }
