# ตัวจับเวลาฝึกซ้อม (Interval Timer App)

> แอปพลิเคชัน Desktop สำหรับจับเวลาฝึกซ้อมส่วนตัว พัฒนาด้วย Python และ PySide6 (Qt) — รองรับการกำหนดชุด (Sets), เวลาเตรียมตัว (Prep), เวลาทำงาน (Work), เวลาพัก (Rest), โหมดแยกข้างซ้าย-ขวา (/ข้าง) รวมถึงจัดกลุ่มโปรแกรมฝึกซ้อมแบบต่อเนื่อง

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/GUI-PySide6%20Qt-41CD52?style=flat&logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat&logo=windows&logoColor=white)

---

## ✨ ฟีเจอร์หลัก

- ⏱ **จับเวลาแบบละเอียด:** กำหนดเวลาเตรียมตัว (Prep), เวลาทำงาน (Work), และเวลาพัก (Rest) ได้ตามต้องการ
- 🔄 **โหมดแยกข้าง (/ข้าง):** รองรับท่าฝึกที่ต้องทำสลับข้าง เช่น แขนซ้าย/ขวา พร้อมเวลาสลับข้างอัตโนมัติ
- 📑 **จัดกลุ่มโปรแกรมฝึก (Groups):** นำรายการซ้อมหลายชุดมาเรียงร้อยต่อกันเป็น Session ซ้อมยาวๆ ได้
- 🔔 **ระบบเสียงแจ้งเตือน:** มีเสียงแจ้งเตือนจังหวะเปลี่ยนช่วงและจบเซ็ต (`bell.wav`, `bell2.wav`)
- 🖥 **หน้าต่าง Overlay:** หน้าต่างแสดงตัวเลขนับถอยหลังขนาดใหญ่ ชัดเจน มองเห็นง่ายขณะออกกำลังกาย
- 💾 **บันทึกข้อมูลอัตโนมัติ:** บันทึกรายการที่ตั้งไว้ลงในเครื่องอัตโนมัติ เรียกใช้ต่อได้ทันที

---

## 📁 โครงสร้างโปรเจกต์

```text
timer_app/
├── ui/
│   ├── main_window.py   # หน้าต่างหลักของแอปพลิเคชัน
│   ├── objects_tab.py   # แท็บจัดการรายการฝึกเดี่ยว (Objects)
│   ├── groups_tab.py    # แท็บจัดการกลุ่มโปรแกรมฝึก (Groups)
│   └── overlay.py       # หน้าต่าง Overlay แสดงเวลานับถอยหลัง
├── audio.py             # โมดูลเล่นเสียงแจ้งเตือน
├── controller.py        # ตัวควบคุมประสานงานระหว่าง UI และ Engine
├── engine.py            # ตรรกะการนับเวลา (Timer Engine)
├── models.py            # โครงสร้างข้อมูลและ Data Models
├── main.py              # จุดเริ่มต้นการรันโปรแกรม (Entry point)
├── bell.wav / bell2.wav # ไฟล์เสียงแจ้งเตือน
├── icon.ico / icon.png  # ไอคอนโปรแกรม
├── requirements.txt     # รายการ Dependencies
└── .gitignore           # กำหนดไฟล์ที่ไม่ต้อง push ขึ้น Git
```

---

## ⚙️ เทคโนโลยีที่ใช้

- **Python 3.10+**
- **PySide6** (Qt for Python) สำหรับทำ GUI และ Overlay
- **Pygame / Wave / Sound APIs** สำหรับเล่นเสียงแจ้งเตือน

---

## 📥 วิธีติดตั้งและรัน

1. **Clone repository:**
   ```bash
   git clone https://github.com/fiwflash/timer-app.git
   cd timer-app
   ```

2. **สร้างและเปิดใช้งาน Virtual Environment (แนะนำ):**
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # Windows (CMD):
   .venv\Scripts\activate.bat
   ```

3. **ติดตั้ง Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **รันโปรแกรม:**
   ```bash
   python main.py
   ```
