#!/usr/bin/env python3
"""
JSON 文件翻译脚本

功能：
- 读取 JSON 文件
- 翻译指定字段的内容
- 保存翻译后的文件

使用方法：
    python translate_json.py <输入文件> --target-language <语言代码> [--fields <字段名>] [--source-language <语言代码>] [--output <输出文件>]

示例：
    python translate_json.py data.json --target-language zh
    python translate_json.py data.json --target-language en --fields name,description
"""

import json
import requests
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional


# 语言配置
LANGUAGES = {
    'zh': 'zh-cn',
    'en': 'en',
    'ja': 'ja',
    'ko': 'ko'
}

SOURCE_LANGUAGES = {
    'auto': 'auto',
    'zh': 'zh-cn',
    'en': 'en',
    'ja': 'ja',
    'ko': 'ko'
}


def translate_text(text: str, from_lang: str = 'auto', to_lang: str = 'zh') -> str:
    """
    翻译文本
    :param text: 要翻译的文本
    :param from_lang: 源语言代码 ('auto' 或语言代码)
    :param to_lang: 目标语言代码
    :return: 翻译后的文本
    """
    if not text or not text.strip():
        return text

    try:
        # 使用 MyMemory API 进行翻译
        url = f"https://api.mymemory.translated.net/get"
        params = {
            'q': text,
            'langpair': f"{SOURCE_LANGUAGES.get(from_lang, 'auto')}|{LANGUAGES[to_lang]}"
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if 'responseData' in data and 'translatedText' in data['responseData']:
            return data['responseData']['translatedText']
        else:
            # API失败，返回带标记的原文
            return _get_error_marker(to_lang) + text

    except Exception as e:
        print(f"翻译错误: {e}")
        return _get_error_marker(to_lang) + text


def _get_error_marker(language: str) -> str:
    """获取错误标记"""
    markers = {
        'zh': '【翻译失败-保持原文】',
        'en': '【Translation Failed-Kept Original】',
        'ja': '【翻訳失敗-原文保持】',
        'ko': '【번역 실패-원문 유지】'
    }
    return markers.get(language, '【翻译失败】')


def find_all_fields(obj: Any, path: str = '', fields: set = None) -> set:
    """
    递归查找JSON中所有字段名
    :param obj: JSON对象
    :param path: 当前路径
    :param fields: 字段集合
    :return: 所有字段名集合
    """
    if fields is None:
        fields = set()

    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            fields.add(current_path)

            # 如果值是对象或数组，继续递归
            if isinstance(value, (dict, list)):
                find_all_fields(value, current_path, fields)

    return fields


def find_fields_by_name(obj: Any, target_fields: List[str], path: str = '') -> List[Dict[str, Any]]:
    """
    递归查找指定字段的位置
    :param obj: JSON对象
    :param target_fields: 目标字段名列表
    :param path: 当前路径
    :return: 字段信息列表
    """
    results: List[Dict[str, Any]] = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key

            if key in target_fields and isinstance(value, str):
                results.append({
                    'path': current_path,
                    'parent': obj,
                    'key': key,
                    'value': value
                })

            if isinstance(value, (dict, list)):
                results.extend(find_fields_by_name(value, target_fields, current_path))

    return results


def read_json_file(file_path: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    读取JSON文件
    :param file_path: 文件路径
    :return: (数据, 错误信息)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON格式错误: {e}"
    except Exception as e:
        return None, f"读取文件错误: {e}"


def save_json_file(data: Dict[str, Any], output_path: str) -> bool:
    """
    保存JSON文件
    :param data: JSON数据
    :param output_path: 输出文件路径
    :return: 是否成功
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存文件错误: {e}")
        return False


def translate_json(
    input_file: str,
    target_language: str,
    source_language: str = 'auto',
    target_fields: List[str] = None,
    output_file: str = None
) -> Tuple[bool, int, List[str], Optional[Dict[str, Any]]]:
    """
    翻译 JSON 文件中的指定字段
    :param input_file: 输入文件路径
    :param target_language: 目标语言代码
    :param source_language: 源语言代码
    :param target_fields: 目标字段名列表
    :param output_file: 输出文件路径
    :return: (成功状态, 翻译数量, 缺失字段列表, 翻译后的数据)
    """
    # 解析字段列表
    if target_fields is None or not target_fields:
        target_fields = ['description']

    # 读取文件
    data, error = read_json_file(input_file)
    if error:
        return False, 0, [], None

    # 查找所有存在的字段
    all_fields = find_all_fields(data)
    missing_fields = [f for f in target_fields if f not in all_fields]
    existing_fields = [f for f in target_fields if f in all_fields]

    if not existing_fields:
        print(f"错误: 未找到指定的字段: {target_fields}")
        return False, 0, missing_fields, data

    # 查找所有目标字段的位置
    field_locations = find_fields_by_name(data, existing_fields)

    if not field_locations:
        print(f"错误: 指定字段中没有可翻译的字符串内容")
        return False, 0, missing_fields, data

    # 执行翻译
    total_count = len(field_locations)
    translated_count = 0

    print(f"\n开始翻译，共 {total_count} 个字段...")
    print(f"目标语言: {LANGUAGES.get(target_language, target_language)}")
    print(f"源语言: {source_language if source_language != 'auto' else '自动检测'}")
    print(f"字段: {', '.join(existing_fields)}")
    print()

    for i, field_info in enumerate(field_locations, 1):
        field_name = field_info['key']
        field_path = field_info['path']

        try:
            print(f"[{i}/{total_count}] 翻译字段: {field_name} ({field_path})")
            print(f"  原文: {field_info['value'][:50]}{'...' if len(field_info['value']) > 50 else ''}")

            # 翻译文本
            translated = translate_text(field_info['value'], source_language, target_language)

            # 更新字段值
            field_info['parent'][field_info['key']] = translated
            translated_count += 1

            print(f"  译文: {translated[:50]}{'...' if len(translated) > 50 else ''}")

            # 添加延迟避免 API 限流
            if i < total_count:
                import time
                time.sleep(0.1)

        except Exception as e:
            print(f"翻译失败: {field_name} - {e}")

    print()
    print(f"翻译完成！共翻译 {translated_count}/{total_count} 个字段")

    # 生成输出文件名
    if output_file is None:
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"{input_path.stem}_translated.json")

    # 保存文件
    if save_json_file(data, output_file):
        print(f"已保存到: {output_file}")

    return True, translated_count, missing_fields, data


def main():
    """命令行入口"""
    if len(sys.argv) < 3:
        print(__doc__)
        print("\n使用示例:")
        print("  python translate_json.py data.json --target-language zh")
        print("  python translate_json.py data.json --target-language en --fields name,description")
        print("  python translate_json.py data.json --target-language ja --source-language zh --output output.json")
        sys.exit(1)

    # 解析参数
    input_file = sys.argv[1]
    target_language = None
    source_language = 'auto'
    target_fields = ['description']
    output_file = None

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '--target-language' and i + 1 < len(sys.argv):
            target_language = sys.argv[i + 1]
            i += 2
        elif arg == '--source-language' and i + 1 < len(sys.argv):
            source_language = sys.argv[i + 1]
            i += 2
        elif arg == '--fields' and i + 1 < len(sys.argv):
            target_fields = sys.argv[i + 1].split(',')
            i += 2
        elif arg == '--output' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # 验证目标语言
    if target_language not in LANGUAGES:
        print(f"错误: 不支持的目标语言。可用: {', '.join(LANGUAGES.keys())}")
        sys.exit(1)

    # 执行翻译
    success, count, missing, data = translate_json(
        input_file=input_file,
        target_language=target_language,
        source_language=source_language,
        target_fields=target_fields,
        output_file=output_file
    )

    if missing:
        print(f"\n警告: 以下字段在文件中不存在: {', '.join(missing)}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
