from __future__ import annotations

import ast
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, getcontext
from typing import List, Optional, Tuple

getcontext().prec = 28

OPERATORS = {"+", "-", "*", "/"}


def _format_decimal(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in {"", "-"}:
        return "0"
    if text == "-0":
        return "0"
    return text


def _sanitize_number(text: str) -> str:
    try:
        value = Decimal(text)
    except InvalidOperation as err:
        raise ValueError("数値の解析に失敗しました") from err
    return _format_decimal(value)


class _SafeEvaluator(ast.NodeVisitor):
    def visit(self, node):
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        if isinstance(node, ast.BinOp):
            left = self.visit(node.left)
            right = self.visit(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    raise ZeroDivisionError
                return left / right
            raise ValueError("未対応の演算子です")
        if isinstance(node, ast.UnaryOp):
            operand = self.visit(node.operand)
            if isinstance(node.op, ast.UAdd):
                return operand
            if isinstance(node.op, ast.USub):
                return -operand
            raise ValueError("未対応の単項演算子です")
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return Decimal(str(node.value))
            raise ValueError("未対応の定数が含まれています")
        raise ValueError("不正な式が検出されました")


def safe_calculate(expression: str) -> Decimal:
    expression = expression.strip()
    if not expression:
        return Decimal("0")
    tree = ast.parse(expression, mode="eval")
    evaluator = _SafeEvaluator()
    result = evaluator.visit(tree)
    if not isinstance(result, Decimal):
        return Decimal(result)
    return result


@dataclass
class CalculatorState:
    tokens: List[str] = field(default_factory=list)
    current: str = "0"
    overwrite: bool = True
    error: Optional[str] = None

    @property
    def expression_text(self) -> str:
        return " ".join(self.tokens)


class CalculatorEngine:
    def __init__(self) -> None:
        self.state = CalculatorState()

    def process(self, command: str) -> Tuple[str, str, Optional[str]]:
        dispatcher = {
            "C": self._clear_all,
            "CE": self._clear_entry,
            "=": self._calculate_result,
            "%": self._percent,
            "+/-": self._toggle_sign,
            "±": self._toggle_sign,
            "⌫": self._backspace,
            "Backspace": self._backspace,
        }
        if command in "0123456789":
            self._input_digit(command)
        elif command == ".":
            self._input_decimal_point()
        elif command in OPERATORS:
            self._apply_operator(command)
        elif command in dispatcher:
            dispatcher[command]()
        else:
            return self.get_display()
        return self.get_display()

    def get_display(self) -> Tuple[str, str, Optional[str]]:
        return self.state.expression_text, self.state.current, self.state.error

    def _reset_on_error(self) -> None:
        if self.state.error:
            self.state = CalculatorState()

    def _input_digit(self, digit: str) -> None:
        self._reset_on_error()
        if self.state.overwrite:
            self.state.current = digit
            self.state.overwrite = False
            return
        if self.state.current == "0":
            self.state.current = digit
        else:
            self.state.current += digit

    def _input_decimal_point(self) -> None:
        self._reset_on_error()
        if self.state.overwrite:
            self.state.current = "0."
            self.state.overwrite = False
            return
        if "." not in self.state.current:
            self.state.current += "."

    def _apply_operator(self, operator: str) -> None:
        self._reset_on_error()
        self._commit_current()
        if self.state.tokens and self.state.tokens[-1] in OPERATORS:
            self.state.tokens[-1] = operator
        else:
            self.state.tokens.append(operator)
        self.state.overwrite = True

    def _commit_current(self) -> None:
        value = _sanitize_number(self.state.current)
        if self.state.tokens:
            if self.state.tokens[-1] in OPERATORS:
                self.state.tokens.append(value)
            else:
                self.state.tokens[-1] = value
        else:
            self.state.tokens.append(value)

    def _calculate_result(self) -> None:
        self._reset_on_error()
        tokens = list(self.state.tokens)
        if not tokens:
            try:
                result = _sanitize_number(self.state.current)
            except ValueError:
                self._set_error("数値の解析に失敗しました")
                return
            self.state.current = result
            self.state.overwrite = True
            return
        if not self.state.overwrite or (tokens and tokens[-1] in OPERATORS):
            try:
                current_value = _sanitize_number(self.state.current)
            except ValueError:
                self._set_error("数値の解析に失敗しました")
                return
            if tokens and tokens[-1] in OPERATORS:
                tokens.append(current_value)
            else:
                tokens[-1] = current_value
        elif tokens and tokens[-1] in OPERATORS:
            tokens.pop()
        expression = " ".join(tokens)
        try:
            result_decimal = safe_calculate(expression)
        except ZeroDivisionError:
            self._set_error("ゼロ除算エラー")
            return
        except (InvalidOperation, ValueError):
            self._set_error("式の解析に失敗しました")
            return
        self.state.current = _format_decimal(result_decimal)
        self.state.tokens.clear()
        self.state.overwrite = True
        self.state.error = None

    def _clear_all(self) -> None:
        self.state = CalculatorState()

    def _clear_entry(self) -> None:
        self._reset_on_error()
        self.state.current = "0"
        self.state.overwrite = True

    def _toggle_sign(self) -> None:
        self._reset_on_error()
        try:
            value = Decimal(self.state.current) * Decimal("-1")
        except InvalidOperation:
            self._set_error("数値の解析に失敗しました")
            return
        self.state.current = _format_decimal(value)
        self.state.overwrite = False

    def _percent(self) -> None:
        self._reset_on_error()
        try:
            current_value = Decimal(self.state.current)
        except InvalidOperation:
            self._set_error("数値の解析に失敗しました")
            return
        if len(self.state.tokens) >= 2 and self.state.tokens[-1] in OPERATORS:
            try:
                base = Decimal(self.state.tokens[-2])
            except InvalidOperation:
                base = Decimal("0")
            current_value = base * current_value / Decimal("100")
        else:
            current_value = current_value / Decimal("100")
        self.state.current = _format_decimal(current_value)
        self.state.overwrite = False

    def _backspace(self) -> None:
        self._reset_on_error()
        if self.state.overwrite:
            self.state.current = "0"
            return
        if len(self.state.current) > 1:
            self.state.current = self.state.current[:-1]
            if self.state.current in {"-", "-0"}:
                self.state.current = "0"
                self.state.overwrite = True
        else:
            self.state.current = "0"
            self.state.overwrite = True

    def _set_error(self, message: str) -> None:
        self.state.error = message
        self.state.tokens.clear()
        self.state.current = "0"
        self.state.overwrite = True
