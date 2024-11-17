# Config3

## Инструмент командной строки для учебного конфигурационного языка

Этот инструмент преобразует JSON-конфигурации в упрощенный конфигурационный язык, выполняя вычисления констант и выражений.

## Описание задачи

Разработать инструмент командной строки, который преобразует входной текст в формате JSON в выходной текст на учебном конфигурационном языке. Инструмент должен обрабатывать синтаксические ошибки и выдавать сообщения об ошибках.


**Поддерживаемые операции и функции:**

1. Сложение (`+`)
2. Вычитание (`-`)
3. Умножение (`*`)
4. Деление (`/`)
5. Сортировка (`sort`)


## Реализация

Код написан на Python и использует стандартные библиотеки (`json`, `sys`, `re`, `unittest`).

**Основные функции:**

* `reformat_expr(expr, constants)`: Вычисляет значение выражения.
* `reformat_operand(operand, constants)`: Обрабатывает отдельный операнд.
* `preprocess(input_string, constants)`:  Предобрабатывает входную строку JSON, вычисляя константы и выражения.
* `format_value(val)`: Форматирует значение для вывода.
* `read_json(data, constants)`:  Читает JSON данные и преобразует их в выходной формат.
* `parse_json(json_data, constants)`: Разбирает JSON строку.


**Тестирование:**

Все функции покрыты тестами, которые можно запустить из командной строки:

```bash
python JSONcon.py test

**Работа программы:**
Для запуска прогррамы введите в командной строке python JSONcon.py < название_вашего_файла.json > output.conf
