"""gitingest 库的封装。"""

import os
import asyncio
from gitingest import ingest_async
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
    default_branch: Optional[str] = None,
    timeout: int = 120
) -> Dict[str, Any]:
    """
    分析 GitHub 仓库。

    Args:
        url: GitHub 仓库 URL
        subdirectory: 可选的子目录路径
        github_token: 可选的 GitHub token（用于私有仓库）
        default_branch: 可选的默认分支名（默认为 'main'，也可指定为 'master' 等）
        timeout: 超时时间（秒），默认为 120

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

        # 使用 ingest_async 并处理事件循环
        try:
            loop = asyncio.get_event_loop()
            # 如果已经有运行中的事件循环，使用 run_until_complete
            if loop.is_running():
                # 在新线程中运行以避免事件循环冲突
                import threading
                import traceback
                result = {}
                exception = None

                def run_ingest():
                    nonlocal exception
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        coro = ingest_async(full_url)
                        try:
                            r = new_loop.run_until_complete(coro)
                            result['data'] = r
                        except Exception as e:
                            traceback.print_exc()
                            exception = e
                    except Exception as e:
                        traceback.print_exc()
                        exception = e
                    finally:
                        new_loop.close()

                thread = threading.Thread(target=run_ingest)
                thread.start()
                thread.join(timeout=timeout)

                if thread.is_alive():
                    raise RuntimeError(f"Ingest timed out after {timeout} seconds")
                if exception:
                    raise exception
                if 'data' not in result:
                    raise RuntimeError("Ingest failed")

                summary, tree, content = result['data']
            else:
                summary, tree, content = loop.run_until_complete(ingest_async(full_url))
        except RuntimeError:
            # 没有事件循环，创建新的
            summary, tree, content = asyncio.run(ingest_async(full_url))

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
