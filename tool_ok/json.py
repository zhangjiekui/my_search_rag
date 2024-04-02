from __future__ import annotations

import json
import re
from json import JSONDecodeError
from typing import Any, Callable, List, Optional, Type

import jsonpatch  # type: ignore[import]

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers.format_instructions import JSON_FORMAT_INSTRUCTIONS
from langchain_core.output_parsers.transform import BaseCumulativeTransformOutputParser
from langchain_core.outputs import Generation
from langchain_core.pydantic_v1 import BaseModel


def _replace_new_line(match: re.Match[str]) -> str:
    value = match.group(2)
    value = re.sub(r"\n", r"\\n", value)
    value = re.sub(r"\r", r"\\r", value)
    value = re.sub(r"\t", r"\\t", value)
    value = re.sub(r'(?<!\\)"', r"\"", value)

    return match.group(1) + value + match.group(3)


def _custom_parser(multiline_string: str) -> str:
    """
    The LLM response for `action_input` may be a multiline
    string containing unescaped newlines, tabs or quotes. This function
    replaces those characters with their escaped counterparts.
    (newlines in JSON must be double-escaped: `\\n`)
    """
    if isinstance(multiline_string, (bytes, bytearray)):
        multiline_string = multiline_string.decode()

    multiline_string = re.sub(
        r'("action_input"\:\s*")(.*?)(")',
        _replace_new_line,
        multiline_string,
        flags=re.DOTALL,
    )

    return multiline_string


# Adapted from https://github.com/KillianLucas/open-interpreter/blob/5b6080fae1f8c68938a1e4fa8667e3744084ee21/interpreter/utils/parse_partial_json.py
# MIT License
def parse_partial_json(s: str, *, strict: bool = False) -> Any:
    """Parse a JSON string that may be missing closing braces.

    Args:
        s: The JSON string to parse.
        strict: Whether to use strict parsing. Defaults to False.

    Returns:
        The parsed JSON object as a Python dictionary.
    """
    # Attempt to parse the string as-is.
    try:
        print(json.loads(s, strict=strict))
        print(s)
        pass
        return json.loads(s, strict=strict)

    except json.JSONDecodeError:
        pass

    # Initialize variables.
    new_s = ""
    stack = []
    is_inside_string = False
    escaped = False

    # Process each character in the string one at a time.
    for char in s:
        if is_inside_string:
            if char == '"' and not escaped:
                is_inside_string = False
            elif char == "\n" and not escaped:
                char = "\\n"  # Replace the newline character with the escape sequence.
            elif char == "\\":
                escaped = not escaped
            else:
                escaped = False
        else:
            if char == '"':
                is_inside_string = True
                escaped = False
            elif char == "{":
                stack.append("}")
            elif char == "[":
                stack.append("]")
            elif char == "}" or char == "]":
                if stack and stack[-1] == char:
                    stack.pop()
                else:
                    # Mismatched closing character; the input is malformed.
                    return None

        # Append the processed character to the new string.
        new_s += char

    # If we're still inside a string at the end of processing,
    # we need to close the string.
    if is_inside_string:
        new_s += '"'

    # Try to parse mods of string until we succeed or run out of characters.
    while new_s:
        final_s = new_s

        # Close any remaining open structures in the reverse
        # order that they were opened.
        for closing_char in reversed(stack):
            final_s += closing_char

        # Attempt to parse the modified string as JSON.
        try:
            print(json.loads(s, strict=strict))
            print(s)
            pass
            return json.loads(final_s, strict=strict)
        except json.JSONDecodeError:
            # If we still can't parse the string as JSON,
            # try removing the last character
            new_s = new_s[:-1]

    # If we got here, we ran out of characters to remove
    # and still couldn't parse the string as JSON, so return the parse error
    # for the original string.
    return json.loads(s, strict=strict)


def parse_json_markdown(
    json_string: str, *, parser: Callable[[str], Any] = parse_partial_json
) -> dict:
    """
    Parse a JSON string from a Markdown string.

    Args:
        json_string: The Markdown string.

    Returns:
        The parsed JSON object as a Python dictionary.
    """
    # Try to find JSON string within triple backticks
    match = re.search(r"```(json)?(.*)", json_string, re.DOTALL)

    # If no match found, assume the entire string is a JSON string
    if match is None:
        json_str = json_string
    else:
        # If match found, use the content within the backticks
        # 之前的问题出在这里
        json_str = match.group(2)
        if not ('action' in json_str and 'action_input' in json_str):
            if json_string.endswith(json_str):
                to_be_removed = match.group(0)
                json_str = json_string.replace(to_be_removed, "")

    # Strip whitespace and newlines from the start and end
    json_str = json_str.strip().strip("`")

    # handle newlines and other special characters inside the returned value
    json_str = _custom_parser(json_str)

    # Parse the JSON string into a Python dictionary
    
    parsed = None
    try:
        parsed = parser(json_str)
    except Exception as e:
        if 'python_repl' in json_str:
            print('原Langchain解码器，无法正确解析LLM输出的工具调用Json，原始错误信息为：')
            print(e)
            print('尝试自己的自定义解析方法正确解析python_repl工具所需的参数......')
            print(r'C:\Users\zjk\.conda\envs\test\Lib\site-packages\langchain_core\output_parsers\json.py#L172')
            ######
            action_input_parts = []
            action_part = ''
            action_part_dict={}
            action_input_part = ''
            action_input_part_dict={}

            for line in json_str.splitlines():
                line = line.rstrip() #不能删除了左边的空格
                if line.endswith(','): #删除末尾的,
                    line = line[:-1]
                # line = line.replace('\\n', '\n') 
                # line = line.replace('\n', '\\n') # \n 会导致代码无法正确执行，全部替换为 \\n
                if len(line.strip()) > 0:
                    if line in ['{', '}']:
                        if line == '}':
                            action_input_parts.append('"')
                            break
                    else:
                        try:
                            line_dict_str = '{' + line + '}'
                            json_parsed = json.loads(line_dict_str)
                            if 'action' in json_parsed.keys():
                                action_part_dict = json_parsed

                            # 有可能所有的action_input代码行就是放到了一个字符串里
                            if 'action_input' in json_parsed.keys():
                                action_input_part_dict = json_parsed
                                if action_part_dict:
                                    parsed =action_part_dict | action_input_part_dict
                                    return parsed



                        except json.JSONDecodeError:
                            if line.strip().startswith('"action_input":'):
                                action_input_parts.append('"action_input":')
                                action_input_parts.append('"')
                                other = line.replace('"action_input":', '').replace('"""',"").replace("'''","").rstrip()
                                if other.strip():
                                        action_input_parts.append(other)
                            else:
                                line = line.replace('"""',"")
                                line = line.replace("'''","")                                
                                line = line.replace('"',"'")
                                if line.strip():
                                    action_input_parts.append(line)
            for _line in action_input_parts:
                if _line in ['"action_input":','"',',']:
                    action_input_part+=_line
                else:
                    action_input_part+=_line + '\\n' # 必须是'\\n'

            print(action_input_part)
            action_input_part_dict_str = '{' + action_input_part + '}'
            action_input_part_dict = json.loads(action_input_part_dict_str)
            parsed =action_part_dict | action_input_part_dict
            return parsed

        else:
            print("待解析的LLM输出",json_str)

    
    return parsed


def parse_and_check_json_markdown(text: str, expected_keys: List[str]) -> dict:
    """
    Parse a JSON string from a Markdown string and check that it
    contains the expected keys.

    Args:
        text: The Markdown string.
        expected_keys: The expected keys in the JSON string.

    Returns:
        The parsed JSON object as a Python dictionary.
    """
    try:
        json_obj = parse_json_markdown(text)
    except json.JSONDecodeError as e:
        raise OutputParserException(f"Got invalid JSON object. Error: {e}")
    for key in expected_keys:
        if key not in json_obj:
            raise OutputParserException(
                f"Got invalid return object. Expected key `{key}` "
                f"to be present, but got {json_obj}"
            )
    return json_obj


class JsonOutputParser(BaseCumulativeTransformOutputParser[Any]):
    """Parse the output of an LLM call to a JSON object.

    When used in streaming mode, it will yield partial JSON objects containing
    all the keys that have been returned so far.

    In streaming, if `diff` is set to `True`, yields JSONPatch operations
    describing the difference between the previous and the current object.
    """

    pydantic_object: Optional[Type[BaseModel]] = None

    def _diff(self, prev: Optional[Any], next: Any) -> Any:
        return jsonpatch.make_patch(prev, next).patch

    def parse_result(self, result: List[Generation], *, partial: bool = False) -> Any:
        text = result[0].text
        text = text.strip()
        if partial:
            try:
                return parse_json_markdown(text)
            except JSONDecodeError:
                return None
        else:
            try:
                return parse_json_markdown(text)
            except JSONDecodeError as e:
                msg = f"Invalid json output: {text}"
                raise OutputParserException(msg, llm_output=text) from e

    def parse(self, text: str) -> Any:
        return self.parse_result([Generation(text=text)])

    def get_format_instructions(self) -> str:
        if self.pydantic_object is None:
            return "Return a JSON object."
        else:
            # Copy schema to avoid altering original Pydantic schema.
            schema = {k: v for k, v in self.pydantic_object.schema().items()}

            # Remove extraneous fields.
            reduced_schema = schema
            if "title" in reduced_schema:
                del reduced_schema["title"]
            if "type" in reduced_schema:
                del reduced_schema["type"]
            # Ensure json in context is well-formed with double quotes.
            schema_str = json.dumps(reduced_schema)
            return JSON_FORMAT_INSTRUCTIONS.format(schema=schema_str)

    @property
    def _type(self) -> str:
        return "simple_json_output_parser"


# For backwards compatibility
SimpleJsonOutputParser = JsonOutputParser
