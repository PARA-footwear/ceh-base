import os
from pathlib import Path
from PIL import Image, ImageOps
import openpyxl

# ================= НАСТРОЙКИ =================
SOURCE_DIR = r"G:\Other computers\My Laptop\Google Drive\Work\models"      # <-- Укажи путь к твоей папке с моделями
OUTPUT_DIR = r"D:\Обувь\ceh_base"    # <-- Сюда скрипт сложит готовое
MAX_PHOTOS_PER_MODEL = 5             # Сколько фото брать на одну модель
MAX_SIZE = 800                       # Размер по длинной стороне в пикселях
JPEG_QUALITY = 80                    # Качество сжатия (оптимально для телефона)
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# Стоп-слова в названии файла или подпапки (регистр не важен) — такие файлы пропускаем
IGNORE_KEYWORDS = {
    "gemini_generated",
    "generated",
    "nano_banana",
    "banana",
    "midjourney",
    "chatgpt",
    "dalle"
}
# =============================================


def is_ai_generated(file_path: Path) -> bool:
    """Проверяет, есть ли стоп-слова в имени файла или родительских папок."""
    full_name_lower = file_path.name.lower()
    return any(kw in full_name_lower for kw in IGNORE_KEYWORDS)


def process_models():
    src_path = Path(SOURCE_DIR)
    out_path = Path(OUTPUT_DIR)
    photos_dir = out_path / "photos"
    photos_dir.mkdir(parents=True, exist_ok=True)

    if not src_path.exists():
        print(f"Ошибка: папка {SOURCE_DIR} не найдена!")
        return

    models_data = []

    # Проходим по всем папкам моделей
    for folder in sorted(src_path.iterdir()):
        if not folder.is_dir():
            continue

        article = folder.name.strip()

        # Ищем только реальные фотки (игнорируем видео, RAW и ИИ-генерации)
        images = [
            f for f in folder.rglob("*")
            if f.is_file()
            and f.suffix.lower() in VALID_EXTS
            and not is_ai_generated(f)
        ]
        images.sort(key=lambda x: x.name.lower())

        saved_count = 0
        for idx, img_path in enumerate(images[:MAX_PHOTOS_PER_MODEL], start=1):
            dest_file = photos_dir / f"{article}_{idx}.jpg"

            # Если файл уже сжат ранее — пропускаем (экономит время при обновлениях)
            if not dest_file.exists():
                try:
                    with Image.open(img_path) as img:
                        img = ImageOps.exif_transpose(img)  # Учитываем поворот с камеры
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        img.thumbnail((MAX_SIZE, MAX_SIZE), Image.Resampling.LANCZOS)
                        img.save(dest_file, "JPEG", quality=JPEG_QUALITY, optimize=True)
                except Exception as e:
                    print(f"Ошибка с файлом {img_path.name}: {e}")
                    continue
            saved_count += 1

        models_data.append({
            "article": article,
            "photos_count": saved_count
        })
        print(f"[OK] {article} — фото: {saved_count}")

    # Работа с Excel-таблицей (создание или безопасное обновление)
    excel_path = out_path / "models.xlsx"
    headers = [
        "Артикул", "Кол-во фото", "Колодка",
        "Верх (Кожа/Замша)", "Подкладка", "Подошва",
        "Фурнитура / Нитки", "Примечания по пошиву"
    ]

    try:
        if excel_path.exists():
            wb = openpyxl.load_workbook(excel_path)
            ws = wb.active

            existing_rows = {}
            for row_idx in range(2, ws.max_row + 1):
                art_val = ws.cell(row=row_idx, column=1).value
                if art_val:
                    existing_rows[str(art_val).strip()] = row_idx

            for item in models_data:
                art = item["article"]
                if art in existing_rows:
                    ws.cell(row=existing_rows[art], column=2, value=item["photos_count"])
                else:
                    ws.append([art, item["photos_count"], "", "", "", "", "", ""])

            print(f"\nГотово! Фотки обновлены, столбец 'Кол-во фото' в {excel_path} актуализирован.")
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Техкарты"
            ws.append(headers)
            for item in models_data:
                ws.append([item["article"], item["photos_count"], "", "", "", "", "", ""])
            print(f"\nГотово! Создана новая таблица: {excel_path}")

        wb.save(excel_path)

    except PermissionError:
        print(f"\nОШИБКА: Закрой файл {excel_path} в Excel и запусти скрипт ещё раз!")


if __name__ == "__main__":
    process_models()