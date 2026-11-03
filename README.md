# ตัวจับเวลาฝึกซ้อม (Interval Timer App)

> แอปพลิเคชัน Desktop สำหรับจับเวลาฝึกซ้อมส่วนตัว พัฒนาด้วย Python และ PySide6 (Qt) — รองรับการกำหนดชุด (Sets), เวลาเตรียมตัว (Prep), เวลาทำงาน (Work), เวลาพัก (Rest), โหมดแยกข้างซ้าย-ขวา (/ข้าง), โหมดเช็คเซ็ตสำหรับท่าที่มีน้ำหนัก/จำนวนครั้ง และการจัดกลุ่มโปรแกรมฝึกซ้อมแบบต่อเนื่อง

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/GUI-PySide6%20Qt-41CD52?style=flat&logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat&logo=windows&logoColor=white)

---

## ✨ ฟีเจอร์หลัก

- ⏱ **จับเวลาแบบละเอียด:** กำหนดเวลาเตรียมตัว (Prep), เวลาทำงาน (Work), และเวลาพัก (Rest) ได้ตามต้องการ
- ✅ **โหมดเช็คเซ็ต (Check):** สำหรับท่าที่มีน้ำหนัก/จำนวนครั้ง เช่น Goblet Squat 4 × 10–12 — แสดงช่องเช็คทีละเซ็ต ไม่นับเวลา
- 🔀 **ผสม Timer + Check ใน Group เดียว:** เรียงท่าแบบมีเวลาและท่าแบบเช็คเซ็ตสลับกันได้ใน Session เดียว
- 🌐 **ท่าต่อข้าง:** กำหนดเป้าหมายเป็น “ต่อข้าง” และเช็ค 1 ครั้งต่อเซ็ตเมื่อทำครบทั้งสองข้าง
- 🔄 **โหมดแยกข้าง (/ข้าง):** รองรับท่าฝึกที่ต้องทำสลับข้าง เช่น แขนซ้าย/ขวา พร้อมเวลาสลับข้างอัตโนมัติ
- 📑 **จัดกลุ่มโปรแกรมฝึก (Groups):** นำรายการซ้อมหลายชุดมาเรียงร้อยต่อกันเป็น Session ซ้อมยาวๆ ได้
- 🗓 **แผน 7 วันพร้อมใช้:** โหลดโปรแกรม Boxing Fitness Program (จันทร์–อาทิตย์) จาก `workout.md` เป็น Group เริ่มต้น
- 🔔 **ระบบเสียงแจ้งเตือน:** เสียงดังเต็มระดับ (normalize) พร้อมบีบเตือนนับถอยหลัง 3-2-1 และเสียงต่างกันสำหรับจบเซ็ต/จบโปรแกรม (`bell.wav`, `bell2.wav`)
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
- **winsound / Wave** สำหรับสร้างและเล่นเสียงแจ้งเตือน (ไม่ต้องติดตั้ง Dependency เพิ่ม)

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

> **หมายเหตุ:** เมื่อ build เป็น `.exe` แล้ว ข้อมูลจะถูกเก็บใน `data.json` ที่อยู่ **ข้าง ๆ ไฟล์ exe** (ไม่หายเมื่อปิดโปรแกรม) หากยังไม่มีไฟล์ ระบบจะสร้างจาก `default_data.json` ซึ่งเป็น template แผน 7 วันที่ฝังมากับ exe ให้อัตโนมัติ

---

## 🏋️ โหมดการใช้งาน

### Timer (นับเวลา)
เหมาะกับ rope, shadow boxing, reflex ball, plank, carry และช่วงพัก — ตั้ง Sets / Work / Prep / Rest ตามต้องการ ระบบจะนับถอยหลังและมีเสียงเตือน 3-2-1

### Check (เช็คเซ็ต)
เหมาะกับท่าที่มีน้ำหนักหรือจำนวนครั้ง — ตั้ง Sets, Target (เช่น `10-12 reps`, `8-10 ต่อข้าง`) และ Weight/Equipment ในหน้า Bank จากนั้นใน Overlay จะมีปุ่มเลข 1, 2, 3… ให้กดเช็คทีละเซ็ต เมื่อทำครบให้กด Next เพื่อไปท่าถัดไป

### Group แบบผสม
ในแท็บ Groups สามารถเรียง Timer และ Check สลับกันได้ตามลำดับที่ต้องการ เช่น

```text
Goblet Squat (Check) → Jump Rope (Timer) → DB Floor Press (Check) → Plank (Timer)
```

จุดสีของ Overlay: เหลือง = เตรียมตัว, เขียว = ทำงาน, แดง = พัก, น้ำเงิน = โหมดเช็คเซ็ต

### แผน 7 วันเริ่มต้น
`data.json` มาพร้อม Group จันทร์–อาทิตย์ จากโปรแกรม Boxing Fitness Program:

- **จันทร์:** Strength A (ขา + ดัน + Core)
- **อังคาร:** Boxing Skill + Jump Rope
- **พุธ:** Active Recovery + Mobility + Prehab
- **พฤหัสบดี:** Strength B (หลัง + ดึง + Core)
- **ศุกร์:** Boxing Conditioning + Power
- **เสาร์:** Full-Body Circuit + Reaction
- **อาทิตย์:** พัก + ยืดเหยียดเบา ๆ

แก้ไขลำดับ/จำนวนเซ็ต/น้ำหนักได้จากแท็บ Bank และ Groups ตามต้องการ
