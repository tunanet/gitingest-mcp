"""gitingest 库的封装。"""

import os
import asyncio
from gitingest import ingest_async
from typing import Optional, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)

# 默认文档文件模式
DEFAULT_DOC_PATTERNS = "*.md,*.json,*.toml,*.yaml,*.yml,*.txt,*.cfg,*.ini,*.conf"

# README 优先模式（用于大仓库降级）
README_ONLY_PATTERN = "README*,readme*"

# 256k token 限制 - 粗略估计（约4字符/token）
MAX_TOKEN_LIMIT = 256 * 1024
# 转换为字符数估计（留一些余量）
ESTIMATED_CHAR_LIMIT = MAX_TOKEN_LIMIT * 3


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


def _estimate_tokens(text: str) -> int:
    """
    估算文本的 token 数量。

    粗略估计：英文约 4 字符/token，中文约 2 字符/token。
    这里使用保守估计 3 字符/token。
    """
    return len(text) // 3


def _ingest_with_retry(
    full_url: str,
    include_patterns: Optional[str],
    timeout: int,
    force_readme_mode: bool
) -> tuple[str, str, str, bool]:
    """
    执行 ingest，如果结果超过限制且未强制 README 模式，则自动降级。

    Returns:
        (summary, tree, content, was_fallback)
    """
    summary, tree, content = _run_ingest(full_url, include_patterns, timeout)

    # 检查内容大小
    estimated_tokens = _estimate_tokens(tree + content)
    logger.info(f"估算 token 数: {estimated_tokens}, 限制: {MAX_TOKEN_LIMIT}")

    # 如果超过限制且未强制 README 模式，自动降级
    if estimated_tokens > MAX_TOKEN_LIMIT and not force_readme_mode:
        logger.warning(f"内容超过 {MAX_TOKEN_LIMIT} token，自动降级到 README 模式")
        summary, tree, content = _run_ingest(full_url, README_ONLY_PATTERN, timeout)
        return summary, tree, content, True

    return summary, tree, content, False


def _run_ingest(
    full_url: str,
    include_patterns: Optional[str],
    timeout: int
) -> tuple[str, str, str]:
    """
    执行 gitingest 获取内容。
    """
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
                    coro = ingest_async(full_url, include_patterns=include_patterns)
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

            return result['data']
        else:
            return loop.run_until_complete(ingest_async(full_url, include_patterns=include_patterns))
    except RuntimeError:
        # 没有事件循环，创建新的
        return asyncio.run(ingest_async(full_url, include_patterns=include_patterns))


def analyze_repo(
    url: str,
    subdirectory: Optional[str] = None,
    github_token: Optional[str] = None,
    default_branch: Optional[str] = None,
    timeout: int = 120,
    include_patterns: Optional[str] = None,
    fallback_to_readme: Optional[bool] = None
) -> Dict[str, Any]:
    """
    分析 GitHub 仓库。

    Args:
        url: GitHub 仓库 URL
        subdirectory: 可选的子目录路径
        github_token: 可选的 GitHub token（用于私有仓库）
        default_branch: 可选的默认分支名（默认为 'main'，也可指定为 'master' 等）
        timeout: 超时时间（秒），默认为 120
        include_patterns: 可选的文件包含模式（逗号分隔）。如未指定，默认使用文档文件模式。
                         设置为 "all" 可分析所有文件。
        fallback_to_readme: 可选，强制只分析 README。如未指定，当内容超过 256k token 时自动降级。

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

    # 处理 include_patterns：默认使用文档模式，"all" 表示全部文件
    if include_patterns is None or include_patterns == "":
        include_patterns = DEFAULT_DOC_PATTERNS
        logger.info(f"使用默认文档模式: {DEFAULT_DOC_PATTERNS}")
    elif include_patterns == "all":
        include_patterns = None  # gitingest 的 None 表示包含所有文件
        logger.info("使用全文件模式")
    else:
        logger.info(f"使用自定义模式: {include_patterns}")

    # 强制降级到 README 模式
    force_readme_mode = fallback_to_readme is True
    if force_readme_mode:
        include_patterns = README_ONLY_PATTERN
        logger.info("强制使用 README 模式")

    # 安全地设置 token
    original_token = os.environ.get("GITHUB_TOKEN")
    try:
        if github_token:
            os.environ["GITHUB_TOKEN"] = github_token

        # 调用 gitingest（带自动降级）
        if final_subdir:
            full_url = f"https://github.com/{repo_path}/tree/{branch}/{final_subdir}"
        else:
            full_url = url

        summary, tree, content, was_fallback = _ingest_with_retry(
            full_url=full_url,
            include_patterns=include_patterns,
            timeout=timeout,
            force_readme_mode=force_readme_mode
        )

    finally:
        # 恢复原始状态
        if original_token is None:
            os.environ.pop("GITHUB_TOKEN", None)
        else:
            os.environ["GITHUB_TOKEN"] = original_token

    # 构建返回结果
    # 正确计算文件数：tree 中每行代表一个文件或目录
    file_count = len([line for line in tree.split('\n') if line.strip()])
    estimated_tokens = _estimate_tokens(tree + content)

    return {
        "summary": {
            "repo_name": repo_path,
            "description": summary,
            "total_files": file_count,
            "estimated_tokens": estimated_tokens,
        },
        "tree": tree,
        "content": content,
        "metadata": {
            "source_url": full_url,
            "include_patterns": include_patterns,
            "was_fallback": was_fallback,
            "fallback_reason": "Content exceeded 256k token limit" if was_fallback else None,
        }
    }
