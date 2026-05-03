from __future__ import annotations

import httpx

from app.config import settings


class AIDescriptionError(Exception):
    pass


def generate_item_description_draft(title: str, category: str) -> str:
    if not settings.llm_api_key:
        return _fallback_description(title=title, category=category)

    prompt = (
        "你是校园二手交易平台的文案助手。"
        "请为给定商品生成简洁、真实、适合学生交易的中文描述草稿。"
        "输出 3-4 句话，包含成色、功能、交易建议。"
    )

    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"商品标题：{title}\n商品分类：{category or '未指定'}",
            },
        ],
        "temperature": 0.5,
    }

    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
            response = client.post(
                f"{settings.llm_base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            if not content:
                raise AIDescriptionError("AI 返回空结果")
            return content
    except (httpx.HTTPError, KeyError, IndexError, AIDescriptionError) as exc:
        raise AIDescriptionError(str(exc)) from exc


def _fallback_description(title: str, category: str) -> str:
    return (
        f"【{category or '二手商品'}】{title}，正常使用中，成色良好。"
        "功能完好，可现场验货后交易。"
        "价格可小刀，优先校内当面交易。"
    )
