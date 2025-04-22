#!/bin/bash

# Переменная для хранения имени выходного файла
OUTPUT_FILE="directory_structure.txt"

# Вывод структуры текущей директории с помощью ls -a и tree -a
{
  echo "=== Структура каталога (ls -a) ==="
  ls -a
  echo ""
  
  echo "=== Структура каталога (tree -a) ==="
  tree -a
  echo ""
} > "$OUTPUT_FILE"

# Рекурсивный проход по всем файлам и каталогам в текущей директории
find "$(pwd)" -type f | while read -r file; do
  # Проверяем, является ли файл небинарным
  if file "$file" | grep -q "text"; then
    {
      echo "=== Содержимое файла: $file ==="
      cat "$file"
      echo ""
    } >> "$OUTPUT_FILE"
  fi
done

echo "Результат записан в файл $OUTPUT_FILE"
