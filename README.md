# Clipboard Inbox

A **minimal clipboard recording tool** that automatically saves the **text and screenshots you copy** into daily Markdown files.

It helps you keep a **trace of what you learned**, without interrupting your workflow.

Typical use cases:

* Study notes
* Language learning
* Research materials
* Web excerpts
* Screenshots
* Temporary knowledge collection

The design goal is simple:

> **Record first. Organize later.**

---

# Features

* Automatically records copied **text**
* Automatically saves copied **images / screenshots**
* Creates **daily Markdown files**
* Stores images in organized folders
* Filters out useless clipboard noise
* Remembers the last save location
* Works **completely offline**
* Very lightweight
* No login, no cloud, no database

---

# Screenshot

The interface is intentionally simple:

```
Save Folder: [Browse...]

Status: Not running

[Start]   [Stop]   [Exit]
```

---

# How It Works

When the program runs, it monitors your **clipboard**.

Whenever you copy something:

* Text
* Screenshot
* Image

it automatically writes the content into today's Markdown file.

Example workflow:

```
Copy text → saved
Take screenshot → saved
Copy webpage content → saved
```

No manual action required.

---

# Output Structure

The program generates the following structure inside your chosen folder:

```
StudyLog
│
├─ inbox
│   ├─ 2026-03-05.md
│   ├─ 2026-03-06.md
│
└─ assets
    ├─ 2026-03-05
    │   ├─ image_101212.png
    │
    └─ 2026-03-06
        ├─ image_142133.png
```

Explanation:

| Folder | Purpose             |
| ------ | ------------------- |
| inbox  | Daily Markdown logs |
| assets | Stored screenshots  |

---

# Example Record

Each day generates a file like:

```
2026-03-05.md
```

Example content:

```
# Inbox - 2026-03-05

## 10:12:33

This is a copied piece of text.

---

## 10:18:12

![image](assets/2026-03-05/image_101812.png)

---
```

Each entry includes:

* timestamp
* text or image

---

# Why "Inbox"

The tool follows an **Inbox workflow**.

While studying, you **should not interrupt your thinking to organize notes**.

Instead:

```
Copy → Automatically recorded
```

Later you can review and move important content into your real notes.

Works well with:

* Obsidian
* Markdown notebooks
* Notion
* Language study notes
* Research notebooks

---

# Noise Filtering

To keep the log clean, the program automatically ignores:

* very short text
* pure numbers
* symbol-only text
* short file paths
* empty clipboard content

This prevents the log from being filled with useless data.

Example ignored content:

```
1234
!!!
C:\temp
```

The filtering rules are implemented in the code.



---

# Usage

## 1 Download

Download the executable:

```
ClipboardInbox.exe
```

No installation required.

---

## 2 Select a Save Folder

Click:

```
Browse...
```

Choose a directory, for example:

```
D:\StudyLog
```

The program will **remember this location automatically**.

---

## 3 Start Recording

Click:

```
Start
```

The clipboard monitor will start running.

---

## 4 Study Normally

Now simply continue your work:

* copy text
* take screenshots
* copy webpage content

Everything will be automatically recorded.

---

# Performance

The program is designed to be extremely lightweight.

| Resource | Usage      |
| -------- | ---------- |
| CPU      | near zero  |
| Memory   | tens of MB |
| Network  | none       |

It can safely run in the background for long periods.

---

# Privacy

This tool:

* does **not connect to the internet**
* does **not upload any data**
* does **not collect user information**

All data stays **on your local computer**.

---

# Configuration

The program automatically saves the last selected folder.

Configuration file location:

```
Windows
%APPDATA%/ClipboardInbox/clip_inbox_config.json
```

No manual configuration is required.

---

# Dependencies (Development)

The project is written in Python and uses:

* tkinter
* pyperclip
* Pillow

The release version is packaged as a **single executable file**.

---

# Typical Use Cases

This tool is especially useful for:

* language learning
* exam preparation
* programming study
* reading notes
* research material collection
* knowledge tracking

It helps build a **learning trace** of what you interact with every day.
