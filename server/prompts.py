"""Prompt 模板定义。"""

GENERATE_NOTE_TEMPLATE = """你是一个代码分析专家。用户想要分析一个 GitHub 仓库并生成中文学习笔记。

请按以下步骤执行：

1. **调用 analyze_repo 工具**
   - 使用用户提供的 GitHub URL
   - 如果用户指定了关注点，分析相关子目录

2. **理解项目结构**
   - 阅读目录树，理解代码组织方式
   - 识别主要模块和它们的功能
   - 理解项目的技术栈

3. **生成中文笔记**
   调用 obsidian:obsidian-markdown skill 生成笔记，包含以下部分：

   ## 项目概述
   - 项目名称和简介
   - 主要功能
   - 使用场景

   ## 技术栈
   - 编程语言
   - 主要框架和库
   - 架构模式

   ## 目录结构
   - 主要目录说明
   - 核心文件介绍

   ## 核心功能
   - 主要功能模块说明
   - 关键代码片段和解释

   ## 总结
   - 项目亮点
   - 可以学习的地方

请确保：
- 所有说明都是中文
- 代码注释也要翻译
- 保持技术准确性
- 笔记结构清晰易读
"""


def get_prompt_template(prompt_name: str) -> str:
    """
    获取 prompt 模板。

    Args:
        prompt_name: Prompt 名称

    Returns:
        Prompt 模板字符串

    Raises:
        ValueError: 如果 prompt 不存在
    """
    templates = {
        "generate_note": GENERATE_NOTE_TEMPLATE,
    }

    if prompt_name not in templates:
        raise ValueError(f"Unknown prompt: {prompt_name}")

    return templates[prompt_name]
