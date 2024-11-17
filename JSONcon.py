import json
import sys
import re
import unittest

def reformat_expr(expr, constants):
    if expr.startswith("sort "):
        array_expr = expr[5:].strip()
        arr = reformat_operand(array_expr, constants)
        if not isinstance(arr, list):
            raise ValueError(f"Sort работает только с массивами но получила {type(arr)}.")
        return sorted(arr)

    tokens = expr.split()
    operator = tokens[0]
    operands = tokens[1:]

    if operator == '+':
        return sum(reformat_operand(op, constants) for op in operands)
    elif operator == '-':
        if len(operands) == 1:
            return -reformat_operand(operands[0], constants)
        return reformat_operand(operands[0], constants) - sum(reformat_operand(op, constants) for op in operands[1:])
    elif operator == '*':
        result = 1
        for op in operands:
            result *= reformat_operand(op, constants)
        return result
    elif operator == '/':
        if len(operands) != 2:
            raise ValueError("Деление требует двух операндов!")
        return reformat_operand(operands[0], constants) / reformat_operand(operands[1], constants)

    raise ValueError(f"Неподдерживаемый оператор: {operator}")


def reformat_operand(operand, constant):
    if operand.isdigit() or (operand[0] == '-' and operand[1:].isdigit()):
        return int(operand)
    elif operand.replace('.','',1).isdigit():
        return float(operand)
    elif operand in constant:
        return constant[operand]
    elif operand.startswith('[') and operand.endswith(']'):
        element = operand[1:-1].split(',')
        elements = [reformat_operand(elem.strip(),constant) for elem in element]
        return elements
    elif operand.startswith('{') and operand.endswith('}'):
        element = operand[1:-1].split(',')
        elements = [reformat_operand(elem.strip(),constant) for elem in element]
        return elements
    else:
        raise ValueError(f"Неизвестный операнд: {operand}")


def preprocess(input_string, constants):
    lines = input_string.split('\n')
    processed_lines = []
    for line in lines:
        match_expression = re.findall(r'\.\\[(.+?)\\]\.', line)
        for expression in match_expression:
            try:
                result = reformat_expr(expression, constants)
                line = line.replace(f'.[{expression}].', json.dumps(result))
            except (ValueError, TypeError) as e:
                raise ValueError(f"Ошибка вычисления выражения вне JSON: {e}")
        processed_lines.append(line)

    processed_string = "\n".join(processed_lines)

    data = json.loads(processed_string)
    if "constants" in data:
        for name, value_str in data["constants"].items():
            if isinstance(value_str, str) and value_str.startswith(".["):
                try:
                    value = reformat_expr(value_str[2:-2], constants)
                    constants[name] = value
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Ошибка вычисления константного выражения: {e}")
            else:
                constants[name] = value_str

        del data["constants"]

    return json.dumps(data), constants

def format_value(val):
    if isinstance(val, list):
        return json.dumps(val)
    elif isinstance(val, (int,float)):
        return str(val)
    elif isinstance(val, str):
        return f'"{val}"'
    else:
        raise ValueError(f"Недопустимый тип значения: {type(val)}")

def read_json(data, constants):
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            nested_lines = read_json(value, constants)
            lines.extend(nested_lines)
        elif key in constants:
            continue
        elif isinstance(value, list):
            lines.append(f"{key} {format_value(value)};")
        elif isinstance(value, (int, float)):
            lines.append(f"{key} {value};")
        else:
            lines.append(f"{key} \"{value}\";")
    return lines


def parse_json(json_data, constants):
    try:
        data = json.loads(json_data)
        if isinstance(data, dict):
            return read_json(data, constants)
        else:
            raise ValueError("Входные данные должны быть JSON-объектом.")

    except json.JSONDecodeError as x:
        raise ValueError(f"Некорректный JSON: {x}")


##Отсюда идут тесты
class TestJsonParser(unittest.TestCase):

    def test_reformat_expr(self):
        constants = {"a": 5, "b": 2}
        self.assertEqual(reformat_expr("+ 1 2 3", constants), 6)
        self.assertEqual(reformat_expr("- 5 2", constants), 3)
        self.assertEqual(reformat_expr("- 5", constants), -5)
        self.assertEqual(reformat_expr("* 2 3", constants), 6)
        self.assertEqual(reformat_expr("/ 6 2", constants), 3)
        self.assertEqual(reformat_expr("sort [3 1 2]", constants), [1, 2, 3])
        self.assertEqual(reformat_expr("+ a b", constants), 7)
        with self.assertRaisesRegex(ValueError, "Sort работает только с"):
            reformat_expr("sort 5", constants)
        with self.assertRaisesRegex(ValueError, "Деление требует двух"):
            reformat_expr("/", constants)


    def test_reformat_operand(self):
        constants = {"a": 5}
        self.assertEqual(reformat_operand("1", constants), 1)
        self.assertEqual(reformat_operand("3.14", constants), 3.14)
        self.assertEqual(reformat_operand("-2", constants), -2)
        self.assertEqual(reformat_operand("a", constants), 5)
        self.assertEqual(reformat_operand("[1, 2, 3]", constants), [1, 2, 3])
        with self.assertRaisesRegex(ValueError, "Неизвестный операнд"):
            reformat_operand("b", constants)




    def test_preprocess(self):
        constants = {}
        input_string = '{"a": .[1+2]. , "b": .[4/2].,"c":".[sort [3,1,2]]."}'
        result, constants = preprocess(input_string, constants)
        self.assertEqual(json.loads(result), {"a": 3, "b": 2, "c": [1, 2, 3]})


        input_string = '{"constants": {"c": .[5*2].}, "a": .[c+1].}'
        result, constants = preprocess(input_string, constants)
        self.assertEqual(json.loads(result), {"a": 11})



    def test_parse_json(self):
        constants = {"PI": 3.14159}
        json_string = '{"name": "Booba", "age": 30, "PI": 3.14, "city":"Moscow"}'
        result = parse_json(json_string, constants)
        self.assertEqual(result, ['name "Booba";', 'age 30;', 'city "Moscow";'])

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        del sys.argv[1]
        unittest.main()
    else:
        json_input = sys.stdin.read()
        constants = {}

        try:
            preprocessed_json, constants = preprocess(json_input, constants)
            output_lines = parse_json(preprocessed_json, constants)

            for key, value in constants.items():
                print(f"{key} is {format_value(value)};")

            for line in output_lines:
                print(line)

        except (ValueError, json.JSONDecodeError) as x:
            print(f"Ошибка: {x}", file=sys.stderr)