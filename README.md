# 🤖 AI-DEV-Module-Odoo17

> **AI-Powered Odoo 17 Module Development**
> เขียน module ทั้งหมดด้วย AI Agent — ตั้งแต่ design ถึง deploy

---

## 📌 เกี่ยวกับโปรเจกต์

โปรเจกต์นี้ใช้ **AI Agent** ในการพัฒนา Odoo 17 modules ทั้งหมด ตั้งแต่:

- 🧠 **วิเคราะห์ Business Logic** — ออกแบบระบบก่อนเขียน code
- ✍️ **เขียน Module Code** — Models, Views, Security, Reports
- 🔍 **Self-Review** — ตรวจสอบคุณภาพ code อัตโนมัติ
- 📦 **Deploy & Push** — Commit, Push, Create PR อัตโนมัติ

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│              🧠 Human (Ball)                 │
│         กำหนด Requirement & Review           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│          🤖 AI Orchestrator (Manao)          │
│     วิเคราะห์ · วางแผน · จัดการ workflow      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│           💻 AI Code Agent                   │
│   เขียน Code · Self-Review · Commit · Push    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│          📦 GitHub Repository                │
│         AI-DEV-Module-Odoo17                 │
└─────────────────────────────────────────────┘
```

---

## 🔄 Workflow

```
Requirement → Business Logic Plan → Design → Implement → Self-Review → PR
     1              2                 3          4            5         6
```

| Step | Description | Tool |
|------|-------------|------|
| 1 | กำหนดความต้องการ | Human |
| 2 | วิเคราะห์ Business Logic | AI Orchestrator |
| 3 | ออกแบบ Data Model & Views | AI Code Agent |
| 4 | เขียน Module Code | AI Code Agent |
| 5 | ตรวจสอบคุณภาพ | AI Self-Review |
| 6 | Push & Create PR | AI Code Agent |

---

## 📁 Project Structure

```
AI-DEV-Module-Odoo17/
├── README.md              # ไฟล์นี้
├── modules/               # Odoo 17 modules
│   └── <module_name>/
│       ├── __init__.py
│       ├── __manifest__.py
│       ├── models/
│       ├── views/
│       ├── security/
│       ├── data/
│       └── static/
├── docs/                  # Documentation & Plans
│   └── plans/
└── scripts/               # Automation scripts
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **ERP** | Odoo 17 |
| **AI Orchestrator** | Hermes Agent (มะนาว) |
| **AI Code Agent** | DeepSeek / Claude / GPT |
| **Language** | Python, XML, JavaScript |
| **Version Control** | Git + GitHub |
| **Note System** | Obsidian Vault |

---

## 🚀 Getting Started

### Prerequisites

- Odoo 17 instance
- Python 3.10+
- Git
- GitHub account

### Clone

```bash
git clone https://github.com/apcball/AI-DEV-Module-Odoo17.git
cd AI-DEV-Module-Odoo17
```

### Install Module

```bash
# Copy module to Odoo addons path
cp -r modules/<module_name> /path/to/odoo/addons/

# Restart Odoo
service odoo restart

# Install module via Odoo UI or CLI
./odoo-bin -c odoo.conf -i <module_name> --stop-after-init
```

---

## 📋 Module Checklist

ทุก module ที่สร้างต้องผ่าน checklist นี้:

- [ ] `__manifest__.py` ครบถ้วน
- [ ] Models ถูกต้องตาม Odoo 17 conventions
- [ ] Views ใช้ syntax ใหม่ (ไม่มี `attrs=`)
- [ ] Security (`ir.model.access.csv`) ครบ
- [ ] ไม่มี hardcoded values
- [ ] Comments อธิบายชัดเจน
- [ ] Self-review ผ่าน

---

## 📊 Status

| Module | Status | Description |
|--------|--------|-------------|
| _Coming soon..._ | ⏳ | รอ Ball สั่งสร้าง |

---

## 🤝 Contributing

โปรเจกต์นี้พัฒนาด้วย **AI Agent ทั้งหมด** แต่ Human review เป็นขั้นตอนสุดท้ายเสมอ

1. Ball กำหนด requirement
2. AI วิเคราะห์ + เขียน code
3. AI Self-review
4. Ball ตรวจสอบ + approve
5. AI Push + Create PR

---

## 📄 License

MIT License

---

## 👤 Author

**Ball (Apichart)** — Project Owner
**Manao (มะนาว)** — AI Orchestrator 🍋

---

> *"AI writes the code. Human approves the vision."*
