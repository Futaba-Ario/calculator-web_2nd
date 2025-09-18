from calc.logic import CalculatorEngine


def press(engine: CalculatorEngine, sequence: str) -> CalculatorEngine:
    for key in sequence:
        engine.process(key)
    return engine


def test_addition() -> None:
    engine = CalculatorEngine()
    press(engine, "12+3=")
    assert engine.state.current == "15"


def test_decimal_multiplication() -> None:
    engine = CalculatorEngine()
    press(engine, "0.5*8=")
    assert engine.state.current == "4"


def test_percent_with_base() -> None:
    engine = CalculatorEngine()
    press(engine, "200+10%=")
    assert engine.state.current == "220"


def test_clear_entry() -> None:
    engine = CalculatorEngine()
    press(engine, "56")
    engine.process("CE")
    engine.process("7")
    engine.process("=")
    assert engine.state.current == "7"


def test_divide_by_zero_error() -> None:
    engine = CalculatorEngine()
    press(engine, "8/0=")
    expression, current, error = engine.get_display()
    assert error == "ゼロ除算エラー"
    assert current == "0"
    assert expression == ""
