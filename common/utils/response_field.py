"""API 响应字段取值工具"""
from __future__ import annotations

import json
import re
from typing import Any


RESPONSE_FIELD_EMPTY_MESSAGE = "响应字段取值失败为空"
_MISSING = object()

# 内容模板中代表"API提取后内容"的变量名
API_CONTENT_VARIABLE = "api_content"
# 内容模板中"原始JSON字段"变量的前缀，用法 {api_json.data.code}
API_JSON_VARIABLE_PREFIX = "api_json."
# 占位符匹配：花括号内不含花括号和换行
_TEMPLATE_PLACEHOLDER = re.compile(r"\{([^{}\n]+)\}")


def extract_card_api_response_content(response_text: str, response_field: str | None = None) -> str:
    """从卡券 API 响应里提取发货内容，集中处理旧逻辑和新响应字段路径。"""
    normalized_field = (response_field or "").strip()
    if normalized_field:
        try:
            response_data = json.loads(response_text)
        except Exception:
            return RESPONSE_FIELD_EMPTY_MESSAGE

        value = get_response_field_value(response_data, normalized_field)
        return stringify_response_value(value)

    try:
        response_data = json.loads(response_text)
        if isinstance(response_data, dict):
            value = response_data.get("data") or response_data.get("content") or response_data.get("card") or response_data
            return stringify_response_value(value)
        return stringify_response_value(response_data)
    except Exception:
        return response_text


def get_response_field_value(data: Any, field_path: str) -> Any:
    """按类 lodash get 的路径读取响应值，支持 data.cards[0].key 这类常见写法。"""
    current = data
    tokens = parse_response_field_path(field_path)
    if not tokens:
        return _MISSING

    for token in tokens:
        if isinstance(token, int):
            if not isinstance(current, list) or token < 0 or token >= len(current):
                return _MISSING
            current = current[token]
            continue

        if not isinstance(current, dict) or token not in current:
            return _MISSING
        current = current[token]

    return current


def parse_response_field_path(field_path: str) -> list[str | int]:
    """把点号和数组下标路径拆成令牌，避免在业务代码里重复解析字符串。"""
    tokens: list[str | int] = []
    buffer = ""
    index = 0

    while index < len(field_path):
        char = field_path[index]
        if char == ".":
            if buffer:
                tokens.append(buffer)
                buffer = ""
            index += 1
            continue

        if char == "[":
            if buffer:
                tokens.append(buffer)
                buffer = ""

            end_index = field_path.find("]", index)
            if end_index == -1:
                return []

            raw_index = field_path[index + 1:end_index].strip()
            if raw_index.isdigit():
                tokens.append(int(raw_index))
            else:
                tokens.append(raw_index.strip("\"'"))
            index = end_index + 1
            continue

        buffer += char
        index += 1

    if buffer:
        tokens.append(buffer)

    return tokens


def stringify_response_value(value: Any) -> str:
    """把取到的响应值转成最终发货文本，缺失或空字符串按约定返回提示。"""
    if value is _MISSING or value is None:
        return RESPONSE_FIELD_EMPTY_MESSAGE

    if isinstance(value, str):
        if not value.strip():
            return RESPONSE_FIELD_EMPTY_MESSAGE
        return value

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)

    if isinstance(value, bool):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


def render_api_content_template(template: str | None, content: str, response_text: str) -> str:
    """渲染 API 卡券内容模板（api_config.content_template，选填）。

    支持把 API 返回内容当作变量与固定文字拼接：
    - {api_content}: 按响应字段/默认规则提取后的内容
    - {api_json.路径}: 原始响应 JSON 中的任意字段值（如 {api_json.data.code}、{api_json.list[0].name}）

    规则：
    - 模板为空 → 原样返回提取内容（保持旧行为）
    - 未知占位符原样保留，便于和固定文字混排
    - api_json 取值失败（响应非 JSON / 路径缺失）替换为空字符串，不中断发货
    """
    normalized = (template or "").strip()
    if not normalized:
        return content

    def _replace(match: re.Match[str]) -> str:
        expr = match.group(1).strip()
        if expr == API_CONTENT_VARIABLE:
            return content
        if expr.startswith(API_JSON_VARIABLE_PREFIX):
            path = expr[len(API_JSON_VARIABLE_PREFIX):].strip()
            if not path:
                return ""
            try:
                data = json.loads(response_text)
            except Exception:
                return ""
            value = get_response_field_value(data, path)
            if value is _MISSING or value is None:
                return ""
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False)
            return "" if isinstance(value, str) and not value.strip() else str(value)
        # 未知占位符原样保留
        return match.group(0)

    return _TEMPLATE_PLACEHOLDER.sub(_replace, normalized)
