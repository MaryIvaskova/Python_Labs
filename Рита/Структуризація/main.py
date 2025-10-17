from models import Medicine, Antibiotic, Vitamin, Vaccine

def show_info(items: list[Medicine]):
    for m in items:
        print(m.info())

if __name__ == "__main__":
    meds: list[Medicine] = [
        Antibiotic("Амоксицилін", 20, 89.5),
        Vitamin("Вітамін C", 50, 12),
        Vaccine("Грип-вакцина", 10, 300),
    ]
    show_info(meds)