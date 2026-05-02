"""Safe expression evaluator using AST parsing.

Evaluates arithmetic expressions without using eval() by walking the AST
and only allowing whitelisted operations and math functions. Also provides
statistical computation and base conversion modes.
"""

import argparse
import ast
import cmath
import decimal
import fractions
import math
import operator
import statistics
import sys

from withpy.commands.shared import read_input_text


_BINARY_OPS: dict[type, object] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.BitAnd: operator.and_,
    ast.BitOr: operator.or_,
    ast.BitXor: operator.xor,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
}

_UNARY_OPS: dict[type, object] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Invert: operator.invert,
}

_MATH_FUNCS: dict[str, object] = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "log": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "exp": math.exp,
    "ceil": math.ceil,
    "floor": math.floor,
    "factorial": math.factorial,
    "gcd": math.gcd,
    "radians": math.radians,
    "degrees": math.degrees,
    "hypot": math.hypot,
}

_CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "inf": math.inf,
}


def _eval_node(node: ast.expr) -> int | float | complex | decimal.Decimal | fractions.Fraction:
    """Recursively evaluate an AST expression node.

    Args:
        node: An AST expression node.

    Returns:
        The computed numeric value.

    Raises:
        ValueError: If the node type is not allowed.
    """
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, complex)):
            return node.value
        raise ValueError(f"unsupported constant type: {type(node.value).__name__}")
    if isinstance(node, ast.Name):
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise ValueError(f"unknown variable: {node.id}")
    if isinstance(node, ast.BinOp):
        op_func = _BINARY_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"unsupported operator: {type(node.op).__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return op_func(left, right)
    if isinstance(node, ast.UnaryOp):
        op_func = _UNARY_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"unsupported unary operator: {type(node.op).__name__}")
        operand = _eval_node(node.operand)
        return op_func(operand)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("only simple function calls are allowed")
        func_name = node.func.id
        if func_name not in _MATH_FUNCS:
            raise ValueError(f"function not allowed: {func_name}")
        func = _MATH_FUNCS[func_name]
        eval_args = [_eval_node(arg) for arg in node.args]
        return func(*eval_args)
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


def _eval_expr(expression: str) -> int | float | complex | decimal.Decimal | fractions.Fraction:
    """Safely evaluate an arithmetic expression.

    Args:
        expression: The expression string to evaluate.

    Returns:
        The computed result.

    Raises:
        ValueError: If the expression contains disallowed constructs.
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"syntax error: {e}") from e
    return _eval_node(tree.body)


def _format_result(value: int | float | complex, precision: int | None, base: str) -> str:
    """Format a numeric result for output.

    Args:
        value: The computed value.
        precision: Decimal places, or None for auto.
        base: Output base (dec, hex, oct, bin).

    Returns:
        Formatted string representation.
    """
    if isinstance(value, complex):
        return str(value)
    if isinstance(value, float):
        if precision is not None:
            value_str = f"{value:.{precision}f}"
        elif value == int(value) and abs(value) < 2**53:
            value_str = str(int(value))
        else:
            value_str = str(value)
        if base == "dec":
            return value_str
    if isinstance(value, int) or (isinstance(value, float) and value == int(value)):
        int_val = int(value)
        match base:
            case "hex":
                return hex(int_val)
            case "oct":
                return oct(int_val)
            case "bin":
                return bin(int_val)
            case _:
                if precision is not None:
                    return f"{value:.{precision}f}"
                return str(int_val)
    if precision is not None:
        return f"{value:.{precision}f}"
    return str(value)


def _compute_stats(numbers: list[float]) -> str:
    """Compute statistical measures of a number list.

    Args:
        numbers: List of numeric values.

    Returns:
        Formatted statistics string.
    """
    if not numbers:
        return "error: no numbers provided"
    lines: list[str] = [
        f"count:  {len(numbers)}",
        f"sum:    {sum(numbers)}",
        f"mean:   {statistics.mean(numbers)}",
        f"median: {statistics.median(numbers)}",
        f"min:    {min(numbers)}",
        f"max:    {max(numbers)}",
    ]
    if len(numbers) >= 2:
        lines.append(f"stdev:  {statistics.stdev(numbers):.6f}")
    return "\n".join(lines)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the calc subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("calc", help="Safe expression evaluator (no eval)")
    p.add_argument("--mode", "-m", default="expr", choices=["expr", "stats"], help="Operation mode (default: expr)")
    p.add_argument("--precision", type=int, default=None, help="Decimal places for output")
    p.add_argument("--base", default="dec", choices=["dec", "hex", "oct", "bin"], help="Output base (default: dec)")
    p.add_argument("expression", nargs="*", help="Expression or numbers")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the calc subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    match args.mode:
        case "expr":
            expr_str = " ".join(args.expression) if args.expression else read_input_text(None).strip()
            if not expr_str:
                print("error: no expression provided", file=sys.stderr)
                return 1
            try:
                result = _eval_expr(expr_str)
                print(_format_result(result, args.precision, args.base))
                return 0
            except (ValueError, TypeError, ZeroDivisionError, OverflowError) as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
        case "stats":
            if args.expression:
                raw = args.expression
            else:
                raw = read_input_text(None).split()
            try:
                numbers = [float(x.strip(",")) for x in raw if x.strip(",")]
            except ValueError as e:
                print(f"error: invalid number: {e}", file=sys.stderr)
                return 1
            print(_compute_stats(numbers))
            return 0
        case _:
            print(f"error: unknown mode: {args.mode}", file=sys.stderr)
            return 1
