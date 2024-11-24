import json
import sys
import re
import unittest


def reformat_expr(expr, constants):
    if expr.startswith("sort "):
        array_expr = expr[5:].strip()
        arr = reformat_operand(array_expr, constants)
        if not isinstance(arr, list):
            raise ValueError(f"Sort requires a list, got {type(arr)}.")
        return sorted(arr)

    tokens = expr.split()
    operator = tokens[0]
    operands = tokens[1:]

    evaluated_operands = [reformat_operand(op, constants) for op in operands]

    if operator == '+':
        return sum(evaluated_operands)
    elif operator == '-':
        if len(evaluated_operands) == 1:
            return -evaluated_operands[0]
        return evaluated_operands[0] - sum(evaluated_operands[1:])
    elif operator == '*':
        result = 1
        for op in evaluated_operands:
            result *= op
        return result
    elif operator == '/':
        if len(evaluated_operands) != 2:
            raise ValueError("Division requires two operands.")
        return evaluated_operands[0] / evaluated_operands[1]
    else:
        raise ValueError(f"Unsupported operator: {operator}")


def reformat_operand(operand, constants):
    if operand.isdigit() or (operand[0] == '-' and operand[1:].isdigit()):
        return int(operand)
    elif operand.replace('.', '', 1).isdigit():
        return float(operand)
    elif operand in constants:
        return constants[operand]
    elif operand.startswith(".[") and operand.endswith("]."):
        expr = operand[2:-2]
        return reformat_expr(expr, constants)
    elif operand.startswith("[") and operand.endswith("]"):
        elements = operand[1:-1].split(",")
        return [reformat_operand(elem.strip(), constants) for elem in elements]
    elif operand.startswith("{") and operand.endswith("}"):
        elements = operand[1:-1].split(",")
        return [reformat_operand(elem.strip(), constants) for elem in elements]
    else:
        raise ValueError(f"Unknown operand: {operand}")


def format_value(val):
    if isinstance(val, list):
        elements = ", ".join(format_value(elem) for elem in val)
        return f"{{{elements}}}"
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, str):
        return f'"{val}"'
    else:
        raise ValueError(f"Unsupported value type: {type(val)}")


def collect_configurations(data, parent_key="", configurations=None):
    if configurations is None:
        configurations = []
    for key, value in data.items():
        if not re.match(r'^[_a-zA-Z]+$', key):
            raise ValueError(f"Invalid key name: {key}")
        if isinstance(value, dict):
            new_key = f"{parent_key}.{key}" if parent_key else key
            collect_configurations(value, new_key, configurations)
        else:
            final_key = f"{parent_key}.{key}" if parent_key else key
            configurations.append((final_key, value))
    return configurations


def resolve_expressions(data, constants):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                resolve_expressions(value, constants)
            elif isinstance(value, str) and value.startswith(".[") and value.endswith("]."):
                expr = value[2:-2]
                try:
                    data[key] = reformat_expr(expr, constants)
                except Exception as e:
                    raise ValueError(f"Error evaluating expression for {key}: {e}")
    elif isinstance(data, list):
        for i, value in enumerate(data):
            if isinstance(value, dict):
                resolve_expressions(value, constants)
            elif isinstance(value, str) and value.startswith(".[") and value.endswith("]."):
                expr = value[2:-2]
                try:
                    data[i] = reformat_expr(expr, constants)
                except Exception as e:
                    raise ValueError(f"Error evaluating expression in list: {e}")


def preprocess(input_data, constants):
    data = json.loads(input_data)
    if "constants" in data:
        constants_data = data["constants"]
        for name, value in constants_data.items():
            if isinstance(value, str) and value.startswith(".[") and value.endswith("]."):
                expr = value[2:-2]
                try:
                    constants[name] = reformat_expr(expr, constants)
                except Exception as e:
                    raise ValueError(f"Error evaluating constant {name}: {e}")
            else:
                constants[name] = value
        del data["constants"]
    resolve_expressions(data, constants)
    configurations = collect_configurations(data)
    output_lines = []
    for name, value in constants.items():
        output_lines.append(f"{name} is {format_value(value)};")
    for key, value in configurations:
        output_lines.append(f"{key} {format_value(value)};")
    return output_lines


class TestJsonParser(unittest.TestCase):
    def test_reformat_expr_operations(self):
        constants = {"a": 5, "b": 10}
        self.assertEqual(reformat_expr("+ a b", constants), 15)
        self.assertEqual(reformat_expr("- b a", constants), 5)
        self.assertEqual(reformat_expr("* a 3", constants), 15)
        self.assertEqual(reformat_expr("/ b a", constants), 2)
        self.assertEqual(reformat_expr("sort {3, 1, 2}", constants), [1, 2, 3])



    def test_sort_with_expressions(self):
        constants = {"a": 5, "b": 10}
        expr = "sort {.[+ a 2]., b, .[- b a].}"
        self.assertEqual(reformat_expr(expr, constants), [5, 7, 10])

    def test_invalid_key_names(self):
        json_string = '{"1key": "value"}'
        constants = {}
        with self.assertRaisesRegex(ValueError, "Invalid key name"):
            preprocess(json_string, constants)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        del sys.argv[1]
        unittest.main()
    else:
        if len(sys.argv) > 1:
            for file_path in sys.argv[1:]:
                try:
                    with open(file_path, 'r') as file:
                        json_input = file.read()
                    constants = {}
                    output_lines = preprocess(json_input, constants)
                    for line in output_lines:
                        print(line)
                except FileNotFoundError:
                    print(f"Error: File not found - {file_path}", file=sys.stderr)
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in file - {file_path}: {e}", file=sys.stderr)
                except Exception as e:
                    print(f"Error processing file - {file_path}: {e}", file=sys.stderr)
        else:
            try:
                json_input = sys.stdin.read()
                constants = {}
                output_lines = preprocess(json_input, constants)
                for line in output_lines:
                    print(line)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON input - {e}", file=sys.stderr)
            except Exception as e:
                print(f"Error processing input: {e}", file=sys.stderr)