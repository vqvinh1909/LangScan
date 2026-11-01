# Hướng dẫn tạo app LangScan — từ con số 0

Tài liệu này để **tự học lại cách LangScan được làm ra**: từng mảnh ghép, thư viện nào,
và quan trọng nhất là **tại sao lại chọn cách đó** — cách khác hỏng ở đâu. Phần lớn
các "tại sao" ở đây đến từ lỗi có thật đã gặp khi làm app (xem `CHANGELOG.md`). Các so sánh
với công cụ khác (janome và MeCab, `onefile` và `onedir`…) là kiến thức chung, chưa đo trên app này.

Cách đọc gợi ý: đọc lần lượt từ Bước 0 đến Bước 11. Mỗi bước có
**Làm gì** → **Tại sao** → **Code thật nằm ở đâu** để mở ra đọc.

---

## Mục lục

0. [Bức tranh tổng thể](#0-bức-tranh-tổng-thể)
1. [Chọn ngôn ngữ và công cụ](#1-chọn-ngôn-ngữ-và-công-cụ)
2. [Phím tắt toàn hệ thống](#2-phím-tắt-toàn-hệ-thống)
3. [Lấy đoạn chữ đang bôi đen](#3-lấy-đoạn-chữ-đang-bôi-đen)
4. [Giao diện popup và chuyện luồng (thread)](#4-giao-diện-popup-và-chuyện-luồng-thread)
5. [Nhận diện ngôn ngữ](#5-nhận-diện-ngôn-ngữ)
6. [Từ điển và tách từ](#6-từ-điển-và-tách-từ)
7. [Dịch cả câu: online, cache, offline](#7-dịch-cả-câu-online-cache-offline)
8. [Thuật ngữ chuyên ngành và ép thuật ngữ](#8-thuật-ngữ-chuyên-ngành-và-ép-thuật-ngữ)
9. [Chụp màn hình và OCR](#9-chụp-màn-hình-và-ocr)
10. [Phát âm, icon khay, khởi động cùng Windows](#10-phát-âm-icon-khay-khởi-động-cùng-windows)
11. [Kiểm thử và đóng gói .exe](#11-kiểm-thử-và-đóng-gói-exe)
12. [Bản "mini LangScan" 90 dòng để tự gõ lại](#12-bản-mini-langscan-90-dòng-để-tự-gõ-lại)
13. [Những cái bẫy đã gặp](#13-những-cái-bẫy-đã-gặp)
14. [Bài tập tự làm](#14-bài-tập-tự-làm)

---

## 0. Bức tranh tổng thể

```
 Người dùng bôi đen chữ, bấm Ctrl+Alt+D
            │
            ▼
 [luồng thư viện keyboard]  bắt phím tắt ──► mở luồng phụ
            │
            ▼
 [luồng phụ]  giả lập Ctrl+C ─► đọc clipboard ─► trả clipboard cũ
            │                         (langscan.py: grab_selection)
            ▼  đẩy chữ vào hàng đợi (queue)
 [luồng giao diện / Tk]  rút hàng đợi ─► Popup.show(chữ)
            │
            ├─► langs.detect()       đoán Trung / Nhật / Hàn / Anh / Việt
            ├─► langs.Analyzer.analyze()  tách từ + tra từ điển ─► danh sách Card
            │       ├─ dictionary.py  (Trung)   ├─ japanese.py (Nhật)
            │       ├─ korean.py      (Hàn)     └─ english.py  (Anh)
            │       └─ terms.py  gắn nhãn thuật ngữ chuyên ngành
            │
            └─► [luồng phụ] translate.py dịch cả câu
                    cache SQLite ─► Google ─► nguồn dự phòng ─► dịch offline
                    langs.enforce_terms() sửa thuật ngữ dịch sai
                    ─► ui_call() đẩy kết quả về luồng giao diện để hiện
```

Ý tưởng cốt lõi: **mỗi việc một file, file nào cũng chạy riêng được**
(`python dictionary.py 我在银行工作`). Nhờ vậy sửa tiếng Hàn không làm hỏng tiếng Trung,
và test được từng phần mà không cần mở giao diện.

---

## 1. Chọn ngôn ngữ và công cụ

| Chọn | Thay vì | Tại sao |
|---|---|---|
| **Python** | C#, C++, Electron | Mọi thư viện ngôn ngữ học tốt nhất đều có cho Python: `jieba` (tách từ Trung), `janome` (Nhật), `jamdict` (JMdict), cùng các bộ từ điển mở có sẵn công cụ đọc. Viết bằng C# phải tự làm lại hết. Đổi lại Python chậm khởi động và đóng gói nặng — chấp nhận được với app chạy ngầm. |
| **Tkinter** | PyQt, Electron, web | Có sẵn trong Python, không phải cài thêm, nhẹ. Popup chỉ cần chữ + nút, không cần giao diện phức tạp. Nhược điểm: trông cũ → phải tự bo góc, tự tô màu (Bước 4). |
| **Từ điển offline** (file trong `data/`) | Gọi API từ điển online | Tra từ phải **tức thì** (< 0,1 giây) và chạy được khi mất mạng. API online chậm 0,5–2 giây, có giới hạn lượt, có thể đóng cửa bất cứ lúc nào. |
| **Dịch câu online** (Google) | Chỉ dùng offline | Dịch cả câu thì mô hình offline kém Google rất xa. Nên: tra từ = offline, dịch câu = online, mất mạng thì mới dùng offline (Bước 7). |
| **Thư viện chuẩn** (`urllib`, `sqlite3`, `json`) | `requests`, ORM | Ít phụ thuộc = ít thứ hỏng khi đóng gói, ít MB. `urllib` đủ cho vài lệnh GET. |

**Môi trường:**

```bash
python -m venv .venv
```

```bash
.venv\Scripts\pip install -r requirements.txt
```

`venv` để thư viện của app không lẫn với thư viện của dự án khác — và để PyInstaller
(Bước 11) chỉ gói đúng những gì app cần.

---

## 2. Phím tắt toàn hệ thống

**Làm gì:** bấm `Ctrl+Alt+D` ở **bất kỳ cửa sổ nào** (Chrome, Word, game) thì app nhận được.

```python
import keyboard
keyboard.add_hotkey("ctrl+alt+d", lambda: print("bấm rồi"))
keyboard.wait()
```

**Tại sao dùng thư viện `keyboard`:**
- Tkinter chỉ bắt được phím khi **cửa sổ của nó đang được chọn**. App tra từ thì cửa sổ
  đang chọn là của người khác → cần "móc" (hook) vào bàn phím của cả hệ thống.
  `keyboard` làm việc đó bằng `SetWindowsHookEx` của Windows.
- Thay thế: `pynput` (cũng được), `RegisterHotKey` qua `ctypes` (phải tự viết vòng lặp
  thông điệp Windows). `keyboard` gọn nhất và còn bắt được kiểu "bấm Ctrl hai lần".

**Tại sao chọn tổ hợp `Ctrl+Alt+chữ`:** `Ctrl+chữ` đã bị mọi app dùng (Ctrl+D = bookmark
trong Chrome). `Ctrl+Alt` hầu như còn trống. Riêng `Ctrl+Alt+C/J/K/E` để **ép** ngôn ngữ, vì
chữ Hán thuần không phân biệt được Trung hay Nhật (Bước 5).

**Bấm Ctrl hai lần** (`langscan.py: DoubleTap`): chỉ tính khi Ctrl bấm **một mình**.
Nếu không có điều kiện "dirty" này, người dùng Ctrl+C rồi Ctrl+V nhanh cũng bị tính là
bấm hai lần → popup nhảy ra lung tung. Logic tách riêng thành hàm `feed(name, is_down, now)`
nhận thời gian làm tham số → **test được** mà không cần bấm phím thật
(hiện chưa có test cho phần này — xem bài tập 7).

**Bẫy:** hàm gọi lại của `keyboard` chạy trên **luồng riêng của thư viện**. Không được
làm việc lâu hay đụng vào Tkinter ở đó (xem Bước 4) → `on_hotkey` chỉ mở luồng phụ rồi
thoát ngay.

---

## 3. Lấy đoạn chữ đang bôi đen

**Làm gì** (`langscan.py: grab_selection`):
1. Cất nội dung clipboard hiện tại.
2. Ghi một "dấu hiệu" lạ vào clipboard (`"\x00__scan__\x00"`).
3. Nhả các phím đang giữ (Ctrl, Alt, D…), rồi giả lập bấm `Ctrl+C`.
4. Chờ tối đa ~1 giây xem clipboard có đổi khác dấu hiệu không.
5. Trả clipboard cũ lại như chưa có gì.

**Tại sao lại vòng vèo qua clipboard?**
- Windows **không có** cách chung để hỏi "chữ nào đang được bôi đen?". Có API
  UI Automation nhưng mỗi app hỗ trợ một kiểu, Chrome/Electron/game thường không trả về.
  `Ctrl+C` thì app nào cũng hiểu.
- **Tại sao cần dấu hiệu:** nếu chỉ so "clipboard có đổi không" thì khi người dùng bôi
  đen đúng đoạn đang có sẵn trong clipboard, app tưởng là chưa copy được. Ghi một chuỗi
  không ai gõ ra được rồi chờ nó bị thay → biết chắc Ctrl+C đã chạy.
- **Tại sao phải nhả phím trước:** người dùng vẫn đang giữ `Ctrl+Alt+D`. Gửi `Ctrl+C`
  lúc đó thực chất thành `Ctrl+Alt+C` → app khác không copy. Nhả rồi chờ 50ms là hết.
- **Tại sao chờ vòng lặp chứ không `sleep(0.3)` một lần:** có app copy mất 20ms, có app
  (Word nặng) mất 500ms. Hỏi lại mỗi 50ms vừa nhanh với app nhanh vừa đủ lâu với app chậm.
- **Tại sao trả clipboard cũ:** người dùng vừa copy một đoạn để dán mà tra từ xong
  bị mất là rất khó chịu.

---

## 4. Giao diện popup và chuyện luồng (thread)

### 4.1 Quy tắc vàng: Tkinter chỉ được đụng từ **một luồng**

Tkinter không an toàn khi gọi từ nhiều luồng — gọi từ luồng phụ có lúc chạy, có lúc treo
cứng hoặc văng lỗi `RuntimeError: main thread is not in main loop`, rất khó tái hiện.
Trong khi đó việc chậm (copy, dịch qua mạng, OCR) **bắt buộc** chạy ở luồng phụ, nếu
không popup đứng hình 1–2 giây.

**Giải pháp:** hàng đợi (`queue.Queue`) + "bơm" định kỳ.

```python
UI_QUEUE = queue.Queue()

def ui_call(fn):            # gọi được từ BẤT KỲ luồng nào
    UI_QUEUE.put(fn)

def pump():                 # chỉ chạy trên luồng Tk
    while not UI_QUEUE.empty():
        UI_QUEUE.get_nowait()()
    root.after(60, pump)    # 60ms sau rút tiếp
```

Luồng phụ dịch xong thì `ui_call(lambda: label.config(text=ban_dich))`. Tk tự gọi lại
`pump` mỗi 60ms trong vòng `mainloop()` của nó.
**Tại sao 60ms:** dưới 100ms mắt người không thấy trễ; nhỏ quá (1ms) thì tốn CPU khi
app chạy ngầm cả ngày.

**Đây là mẫu quan trọng nhất của cả app.** Hiểu nó là hiểu `_fill_async`, `Snipper`,
`download_offline`.

### 4.2 Popup không viền

- `root = tk.Tk(); root.withdraw()` — cửa sổ gốc ẩn đi, popup là `Toplevel`.
  **Tại sao:** đóng popup không được làm tắt app; cửa sổ gốc sống suốt.
- `overrideredirect(True)` bỏ thanh tiêu đề của Windows → trông như popup tooltip.
  Cái giá: mất luôn kéo thả và chỉnh cỡ → phải tự viết (`_draggable`, `_resize_*`).
- `attributes("-topmost", True)` để nổi trên mọi cửa sổ.
- **Bo góc** (`_round_corners`): gọi `DwmSetWindowAttribute` của Windows 11 qua `ctypes`.
  Tk không tự bo góc được; vẽ ảnh bo góc thì viền răng cưa.
- **Vị trí** (`_place`): đặt cạnh con trỏ chuột, nhưng kẹp lại trong màn hình — nếu không,
  bôi đen chữ ở mép phải là popup tràn ra ngoài.
- **Nhớ kích thước** vào `data/popup.json`: JSON vì người đọc/sửa tay được.

### 4.3 Bảng màu dạng hằng số (`THEME`)

Màu khai báo một chỗ ở đầu file thay vì rải trong code → đổi giao diện sáng/tối chỉ
sửa một dòng `THEME = "sang"`.

### 4.4 Chữ có dấu tiếng Việt

File `.py` lưu UTF-8; chuỗi hiển thị có dấu đầy đủ, nhưng **chú thích trong code viết
không dấu**. Đây chỉ là thói quen trong code hiện có, không phải yêu cầu kỹ thuật.

Chữ đưa vào popup được qua `unicodedata.normalize("NFC", ...)` (`Popup.show`): chữ "ệ" có thể là 1 ký tự hoặc
"e + dấu mũ + dấu nặng" (3 ký tự). Copy từ PDF hay Mac thường ra dạng tách → so sánh
chuỗi, tra từ điển đều trượt. Chuẩn hoá NFC đưa về một dạng.

---

## 5. Nhận diện ngôn ngữ

**Làm gì** (`langs.py: detect`): đếm ký tự theo **dải mã Unicode**:

| Dải | Chữ |
|---|---|
| `一-鿿` … | Hán tự / Kanji |
| `぀-ヿ` | Hiragana + Katakana |
| `가-힣` | Hangul |
| `A-Za-z` | Latin |

Thứ tự quyết định: có Hangul → Hàn; có kana → Nhật; có Hán → Trung; chỉ Latin → Anh
(hoặc Việt, xem dưới).

**Tại sao không dùng thư viện đoán ngôn ngữ** (`langdetect`, `fasttext`)? Chúng dựa vào
thống kê nên với đoạn **ngắn** (một từ — đúng việc của app tra từ) thì đoán sai nhiều,
lại thêm vài chục MB. Chữ viết của 4 ngôn ngữ này khác hẳn nhau nên đếm ký tự vừa nhanh
vừa gần như luôn đúng.

**Chỗ không phân biệt được:** `学生` vừa là Trung vừa là Nhật. Không có kana thì không
cách nào biết chắc → mặc định Trung (người dùng chủ yếu học Trung) và có phím ép
`Ctrl+Alt+J`.

**Tiếng Việt:** chữ có dấu (ă â đ ê ô ơ ư + thanh) → chắc chắn Việt. Không dấu
(`toi di hoc`) thì khó vì cũng là chữ Latin → `vietnamese_plain` kiểm tra **từng âm tiết
có đúng cấu trúc âm tiết tiếng Việt không** (`RE_VI_SYLLABLE`) cộng với các dấu hiệu chỉ
tiếng Việt có (`ngh-`, `-nh`, `uoi`…). Tại sao không chỉ tra từ điển Anh: "an", "be",
"me" vừa là Anh vừa là Việt; kiểm tra cả câu thì chắc hơn.

---

## 6. Từ điển và tách từ

### 6.1 Cùng một khuôn "thẻ từ" (`Card`) cho mọi ngôn ngữ

```python
Card(word, reading, badge, vi, en, note, speak, lang, tones)
```

**Tại sao:** popup chỉ cần biết vẽ `Card`; không cần biết thẻ đến từ tiếng Trung hay
tiếng Hàn. Thêm ngôn ngữ thứ năm = viết thêm một module trả về `Card`, không sửa giao diện.
Đây là nguyên tắc **"tách phần dữ liệu khỏi phần hiển thị"**.

`__slots__` để mỗi thẻ tốn ít bộ nhớ hơn (một câu dài có thể ra vài chục thẻ).

### 6.2 Tiếng Trung (`dictionary.py`)

- **Không có dấu cách giữa các từ** → phải tách từ: `jieba`. Tại sao jieba: phổ biến
  nhất, có tần suất từ, cho thêm từ điển riêng được. Tách sai thì tra sai cả câu.
- **Nghĩa:** CVDICT (Trung–Việt) trước, thiếu thì CC-CEDICT (Trung–Anh). Cả hai là file
  văn bản, mỗi dòng một từ — app đọc một lần rồi lưu thành **pickle** để lần sau mở nhanh
  (đọc pickle nhanh hơn phân tích lại file văn bản hàng chục lần).
- **Phồn thể:** CC-CEDICT có cả hai dạng chữ; jieba học trên giản thể nên hay cắt vụn từ
  phồn thể (`臺灣` → `臺` + `灣`). Sau khi jieba tách xong, `_merge_traditional` ghép các
  mảnh liền nhau lại nếu từ ghép có trong từ điển và có chữ phồn thể.
- **HSK** từ file JSON → huy hiệu cấp độ.

### 6.3 Tiếng Nhật (`japanese.py`)

- `janome` tách từ **và đưa về dạng gốc**: `食べました` → `食べる`. Tại sao janome mà không
  MeCab: MeCab nhanh hơn nhưng phải cài thư viện C và từ điển riêng, trên Windows hay lỗi;
  janome thuần Python, `pip install` là xong.
- `jamdict` đọc JMdict (SQLite). **Bẫy:** một kết nối SQLite chỉ dùng được trên luồng đã
  tạo ra nó → tra từ ở luồng phụ ra rỗng. Sửa: mỗi luồng một đối tượng Jamdict
  (`threading.local`).
- Romaji ↔ kana bằng bảng tra (`_KANA_TABLE`), để gõ `tabemashita` cũng tra được.

### 6.4 Tiếng Hàn (`korean.py`)

- Tiếng Hàn **chắp dính** (thêm đuôi vào gốc): `갔습니다` = `가다` + quá khứ + lịch sự.
  Không có thư viện nhẹ nào làm tốt → tự viết: **tách mỗi chữ Hangul thành phụ âm/nguyên
  âm (jamo)** bằng phép toán trên mã Unicode, rồi gỡ dần đuôi và thử các dạng biến âm bất
  quy tắc (`추워요` → `춥다`).
- **Tại sao Hangul tách được bằng toán:** mỗi khối Hangul được xếp theo công thức
  `0xAC00 + (đầu*21 + giữa)*28 + cuối`. Chia lấy dư là ra ba phần.
- Từ điển kengdic (Hàn–Anh).

### 6.5 Tiếng Anh (`english.py`)

- Từ điển Anh–Việt + IPA + CEFR, đều là file mở.
- **Đưa về dạng gốc** (`went` → `go`, `studies` → `study`) bằng bảng động từ bất quy tắc +
  luật bỏ đuôi. IPA lấy của **chính dạng đang gặp** trước (`went` /wɛnt/), không có mới lấy
  của dạng gốc — trước đây lấy dạng gốc nên ra /ɡoʊ/ sai.

### 6.6 Tra ngược Việt → ngoại ngữ (`reverse.py`)

Lật từ điển Trung–Việt thành chỉ mục "chữ Việt → danh sách từ Trung", lưu cache. Tại sao
lưu: lật cả từ điển mất vài giây, không thể làm mỗi lần tra.

---

## 7. Dịch cả câu: online, cache, offline

`translate.py: translate_detail` chạy theo thứ tự:

```
cache SQLite ─có─► trả luôn
   │không
   ▼
Google (translate.googleapis.com, client=gtx)
   │lỗi mạng ─► đánh dấu "mất mạng" 30 giây
   │lỗi khác ─► nguồn tiếp theo (Google dict, MyMemory, Lingva)
   ▼
dịch offline (Argos Translate) — KHÔNG lưu cache
```

**Tại sao từng điểm:**
- **Cache SQLite:** câu đã dịch thì lần sau ra ngay, không tốn mạng, không bị Google chặn
  vì gọi nhiều. SQLite vì có sẵn trong Python, một file, tra theo khoá chính rất nhanh,
  ghi an toàn khi app tắt đột ngột (JSON thì ghi dở là hỏng cả file).
  Có `threading.Lock` vì nhiều luồng dịch cùng lúc.
- **Endpoint `client=gtx` miễn phí:** không cần khoá API, người dùng cài là chạy. Đổi lại:
  là mô hình cũ hơn trang web Google Dịch và không có cam kết — nên có **nhiều nguồn dự
  phòng**. Muốn chất lượng cao hơn thì phải dùng Google Cloud Translation / Gemini có khoá
  API (không nên "cào" endpoint nội bộ của trang web).
- **Chế độ "mất mạng 30 giây":** khi mất mạng, mỗi lần gọi Google phải chờ hết thời gian
  chờ (vài giây) mới biết lỗi. Nhớ "đang mất mạng" 30 giây thì các câu sau đi thẳng sang
  offline, không bắt người dùng chờ lại.
- **Không cache bản offline:** để có mạng lại thì câu đó được dịch lại bằng Google (tốt
  hơn). Nếu lưu, bản kém sẽ "dính" mãi.
- **Chia đoạn dài (`CHUNK = 1500`)** theo câu: URL GET có giới hạn độ dài; cắt giữa câu thì
  dịch sai nghĩa.
- **Argos Translate chạy bằng CTranslate2 + SentencePiece, không cài PyTorch:** PyTorch
  nặng ~2GB; CTranslate2 chạy được cùng mô hình chỉ với vài chục MB. Trung/Nhật/Hàn → Việt
  không có mô hình trực tiếp nên đi vòng qua tiếng Anh (`zh→en→vi`).

### 7.1 Làm sạch câu trước khi dịch (`langs.prepare_for_mt`)

Máy dịch rất kém với chữ "bẩn": nối lại dòng bị ngắt giữa câu, chữ gạch nối cuối dòng
(`trans-\nlation`), dấu câu dính, và **chữ IN HOA** (`COMPASS AI DOANH NGHIỆP` bị dịch
từng chữ như tên riêng). `calm_caps` hạ chữ in hoa về thường nhưng **giữ từ viết tắt**
(AI, IT, CPU). Tại sao làm trước khi dịch: rẻ, chạy offline, cải thiện rõ rệt mà không
cần AI.

---

## 8. Thuật ngữ chuyên ngành và ép thuật ngữ

### 8.1 Dữ liệu dạng TSV (`data/terms/*.tsv`)

```
en	zh	ja	ko	vi	note
firewall	防火墙	ファイアウォール	방화벽	tường lửa
```

**Tại sao TSV mà không JSON/SQLite:** người không biết lập trình mở bằng Excel sửa được;
`git diff` thấy rõ từng dòng thay đổi; dấu phẩy trong nghĩa tiếng Việt không làm vỡ cột
như CSV. Mỗi ngành một file → thêm ngành = thêm file, `build.py` tự gói hết.

### 8.2 Tìm thuật ngữ (`terms.py`)

Khớp **dài nhất trước**: "machine learning" thắng "machine". Chữ Hán cần ≥ 2 chữ (trừ khi
cả câu chỉ có 1 chữ) vì một chữ Hán đơn lẻ khớp vào khắp nơi.

### 8.3 Ép thuật ngữ khi máy dịch sai (`langs.enforce_terms`)

Ví dụ: `The database is offline` → Google: "Cơ sở dữ liệu ngoại tuyến". Muốn: "không kết
nối mạng".

Cách làm:
1. Dịch bình thường.
2. Kiểm tra bản dịch đã có nghĩa đúng chưa. **Gần đúng (≥ 60% số chữ) là để nguyên** —
   câu tự nhiên quan trọng hơn đúng từng chữ.
3. Sai thật thì thay thuật ngữ trong câu gốc bằng mã giữ chỗ `ZQ0`, dịch lại → máy dịch
   giữ nguyên `ZQ0` → điền nghĩa đúng vào.

**Tại sao mã `ZQ0`:** phải là thứ máy dịch không dịch, không tách, không đổi hoa thường.
`ZQ` + số không phải từ của ngôn ngữ nào nên máy dịch thường giữ nguyên, nhưng không có gì
bảo đảm. Vì vậy code luôn kiểm tra lại: nếu bản dịch lại làm mất mã → bỏ, dùng bản đầu (an toàn hơn là ra câu
hỏng).

**Tại sao cần "ngữ cảnh":** từ đơn nhiều nghĩa. `capital` là "vốn" (kinh tế) nhưng
"Hanoi is the capital of Vietnam" phải là "thủ đô". Từng bị ép thành "Hà Nội là vốn của
Việt Nam". Nên: **từ đơn chỉ bị ép khi câu có thêm một thuật ngữ khác cùng ngành**; cụm
nhiều chữ thì ít nhập nhằng nên ép luôn.

---

## 9. Chụp màn hình và OCR

### 9.1 Khoanh vùng (`Snipper`)

Một cửa sổ trong suốt phủ cả màn hình, kéo chuột vẽ hình chữ nhật, thả ra thì chụp vùng đó
bằng `PIL.ImageGrab`.

**Bẫy DPI:** màn hình đặt tỉ lệ 125% thì toạ độ Tk (đơn vị logic) khác toạ độ ảnh chụp
(điểm ảnh thật) → chụp lệch. Phải đo tỉ lệ và nhân vào. Và việc đo này **phải chạy trên
luồng Tk** (gọi Tk từ luồng phụ trả số sai — lại là quy tắc ở Bước 4).

Vùng vừa chụp lưu vào `data/snip.json` để `Ctrl+Alt+Z` chụp lại đúng chỗ (phụ đề video).

### 9.2 Ba bộ OCR, mỗi bộ một việc (`ocr.py`)

| Bộ | Dùng cho | Tại sao |
|---|---|---|
| **RapidOCR** (onnxruntime) | Trung + Anh, chạy đầu tiên | Đọc một lần ra cả chữ Hán lẫn Latin, chính xác, chạy offline. |
| **Windows OCR** (winrt) | Nhật, Hàn | Có sẵn trong Windows, không tốn MB. Nhưng **không hỗ trợ tiếng Việt**. |
| **Tesseract** + `vie` | Tiếng Việt có dấu | Mô hình Latin của RapidOCR không có chữ ư, ơ, đ… → "Đã sửa" ra "Dasta". Tesseract có dữ liệu tiếng Việt thật. |

`read_auto` chạy RapidOCR trước rồi **dựa vào kết quả để quyết định**: ra chữ Hán → đọc lại
bằng Windows OCR tiếng Nhật xem có kana không; ra chữ Latin → đọc lại bằng Tesseract xem có
phải tiếng Việt không. Tại sao: chạy cả ba bộ mỗi lần thì chậm gấp ba.

**Lọc rác:** Tesseract xuất **TSV có điểm tin cậy cho từng chữ**. Vùng chụp cắt ngang chữ
thì ra toàn ký tự vớ vẩn với điểm thấp → bỏ dòng điểm trung bình < 65, bỏ chữ ngắn điểm
< 80. Tại sao không dùng đầu ra văn bản thường: mất thông tin điểm, không lọc được.

**Bẫy DLL:** nạp `winrt` trước rồi mới nạp `onnxruntime` thì lỗi khởi tạo DLL (hai bên
dùng hai phiên bản `msvcp140.dll`). Sửa: luôn nạp RapidOCR trước.

---

## 10. Phát âm, icon khay, khởi động cùng Windows

- **gTTS + pygame:** gTTS lấy giọng đọc Google (tự nhiên hơn giọng Windows, có đủ Trung/
  Nhật/Hàn/Việt mà không cần cài gói giọng). pygame để phát mp3. File âm thanh lưu theo
  `mã ngôn ngữ_md5(chữ).mp3` → nghe lại không tải lại. Dùng md5 vì `hash()` của Python đổi
  kết quả mỗi lần mở app: trước đây dùng `hash()` nên cache âm thanh không bao giờ dùng lại được.
- **pystray:** icon cạnh đồng hồ. Tại sao cần: app chạy ngầm không có cửa sổ — không có
  icon thì người dùng không biết app đang chạy, không có chỗ bấm thoát/cài đặt.
- **Chạy ngầm bằng `pythonw`** (`run_hidden.bat`): `python` mở cửa sổ đen, `pythonw` thì không.
  Hệ quả: `print` không có chỗ ra → ghi log vào file (`setup_logging`).
- **Chỉ chạy một bản** (`already_running`): bấm mở hai lần mà chạy hai bản thì mỗi phím
  tắt mở hai popup.
- **Khởi động cùng Windows bằng Task Scheduler** (`autostart.py`) chứ không phải thư mục
  Startup: task chạy được với **quyền cao nhất** → phím tắt vẫn bắt được khi đang dùng app
  chạy quyền admin (Windows chặn app thường "móc" phím của app admin).

---

## 11. Kiểm thử và đóng gói .exe

### 11.1 Test (`tests/`, chạy `python -m pytest tests`)

- Test **phần logic**, không test giao diện: tách từ, nhận diện ngôn ngữ, ép thuật ngữ,
  lọc OCR, bấm Ctrl hai lần. Tại sao: logic là nơi hay hỏng khi sửa; giao diện thì nhìn là
  thấy.
- Test **không gọi mạng**: thay hàm dịch thật bằng hàm giả (`monkeypatch`). Tại sao: test
  phải chạy nhanh, offline, và cho cùng kết quả mỗi lần.
- Mỗi lỗi đã sửa thêm một test → lỗi đó không quay lại được mà không ai biết.

### 11.2 PyInstaller (`build.py`)

Gói Python + thư viện + code thành `dist/LangScan/LangScan.exe`.

- **`onedir` chứ không `onefile`:** `onefile` mỗi lần mở phải giải nén hàng trăm MB vào thư
  mục tạm (chậm 5–10 giây) và hay bị phần mềm diệt virus nghi ngờ.
- **`COLLECT_ALL`**: jieba, janome, jamdict… có file dữ liệu đi kèm mà PyInstaller không tự
  thấy → phải chỉ định gói hết.
- **`paths.py`:** khi chạy bằng .exe, `__file__` trỏ vào thư mục `_internal` của
  PyInstaller → `data/` phải tính theo vị trí file .exe. Mọi module lấy đường dẫn từ đây,
  không tự tính.
- **Tesseract tối giản:** chỉ chép đúng các DLL mà `tesseract.exe` thật sự cần (đọc bảng
  import bằng `pefile`) và bỏ thông tin debug → nhỏ đi nhiều lần.

### 11.3 Inno Setup (`installer.iss`)

Biến thư mục `dist/LangScan` thành một file `LangScan-Setup-x.y.z.exe`.

- **Cài vào `%LOCALAPPDATA%\Programs`, `PrivilegesRequired=lowest`:** không cần quyền admin,
  và thư mục `data/` ghi được (cache, log). Cài vào `Program Files` thì app không ghi được
  vào thư mục của chính nó.
- **`lzma2/max` + `LZMAUseSeparateProcess`:** nén mạnh; `ultra64` thì trình dịch Inno (32-bit)
  hết bộ nhớ với ~760MB dữ liệu.
- **Số phiên bản ở một chỗ** (`version.py`), `build.py` truyền vào Inno — tránh hai nơi ghi
  hai số khác nhau.
- **`--selftest`**: người dùng khác cài xong bấm một lối tắt là biết thiếu gì
  (`data/selftest.txt`) — dễ hỗ trợ từ xa.

---

## 12. Bản "mini LangScan" 90 dòng để tự gõ lại

Gõ lại file này (đừng copy) là cách nhanh nhất để hiểu Bước 2–5 và 7. Cần
`pip install keyboard pyperclip`.

```python
# mini_langscan.py - boi den chu, bam Ctrl+Alt+D -> popup ban dich tieng Viet
import json, queue, re, threading, time, urllib.parse, urllib.request
import tkinter as tk
import keyboard, pyperclip

Q = queue.Queue()                     # luong phu -> luong giao dien

def grab_selection():
    old = pyperclip.paste()
    for k in ("ctrl", "alt", "d"):    # nha phim dang giu cua to hop
        keyboard.release(k)
    time.sleep(0.05)
    marker = "\x00mini\x00"
    pyperclip.copy(marker)
    keyboard.send("ctrl+c")
    text = ""
    for _ in range(20):               # cho toi da 1 giay
        time.sleep(0.05)
        cur = pyperclip.paste()
        if cur != marker:
            text = cur
            break
    pyperclip.copy(old)               # tra clipboard ve nhu cu
    return text.strip()

def detect(text):
    if re.search(r"[가-힣]", text): return "ko"
    if re.search(r"[぀-ヿ]", text): return "ja"
    if re.search(r"[一-鿿]", text): return "zh-CN"
    if re.search(r"[A-Za-z]", text):        return "en"
    return None

def translate(text, src):
    url = ("https://translate.googleapis.com/translate_a/single"
           "?client=gtx&sl={}&tl=vi&dt=t&q={}".format(src, urllib.parse.quote(text)))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=8).read().decode("utf-8"))
    return "".join(p[0] for p in data[0] if p and p[0])

def worker():                         # chay o luong phu: duoc phep cham
    text = grab_selection()
    lang = detect(text) if text else None
    if not lang:
        return
    try:
        out = translate(text, lang)
    except Exception as e:
        out = "Lỗi dịch: {}".format(e)
    Q.put((text, out))

def show_popup(root, text, out):      # chi chay o luong giao dien
    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg="#f4f8f1")
    tk.Label(win, text=text, bg="#f4f8f1", fg="#2f5d2a", wraplength=360,
             justify="left", font=("Segoe UI", 12, "bold")).pack(padx=12, pady=(10, 4), anchor="w")
    tk.Label(win, text=out, bg="#f4f8f1", wraplength=360,
             justify="left", font=("Segoe UI", 11)).pack(padx=12, pady=(0, 10), anchor="w")
    x, y = root.winfo_pointerx() + 12, root.winfo_pointery() + 16
    win.geometry("+{}+{}".format(x, y))
    win.bind("<Button-1>", lambda e: win.destroy())    # bam vao de dong
    win.after(15000, win.destroy)

def pump(root):
    while not Q.empty():
        item = Q.get_nowait()
        if item is None:              # tin hieu thoat
            root.quit()
            return
        show_popup(root, *item)
    root.after(60, pump, root)

def main():
    root = tk.Tk()
    root.withdraw()                   # cua so goc an, chi hien popup
    keyboard.add_hotkey("ctrl+alt+d",
                        lambda: threading.Thread(target=worker, daemon=True).start())
    # Thoat cung di qua hang doi: khong goi root.quit() tu luong cua keyboard
    keyboard.add_hotkey("ctrl+alt+q", lambda: Q.put(None))
    print("Bôi đen chữ rồi bấm Ctrl+Alt+D. Thoát: Ctrl+Alt+Q")
    pump(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

Sau đó so với bản thật để thấy bản thật thêm gì và **vì sao**:
cache (Bước 7), tra từ điển thay vì chỉ dịch (Bước 6), xử lý khi mất mạng, nhớ vị trí và
kích thước popup, phát âm…

> Để ý phím thoát: nó cũng chỉ đẩy `None` vào hàng đợi chứ không tự gọi `root.quit()`,
> vì hàm đó chạy trên luồng của `keyboard` — đúng quy tắc ở Bước 4.

---

## 13. Những cái bẫy đã gặp

| Triệu chứng | Nguyên nhân | Cách sửa | Bài học |
|---|---|---|---|
| App treo / lỗi ngẫu nhiên khi hiện popup | Gọi Tk từ luồng phụ | Hàng đợi + `after()` | Giao diện chỉ một luồng |
| Tra tiếng Nhật ở luồng phụ ra rỗng | Kết nối SQLite gắn với luồng tạo ra nó | `threading.local()` | Tài nguyên có "chủ" là luồng |
| OCR Trung/Anh hỏng hẳn | `winrt` và `onnxruntime` tranh DLL | Nạp RapidOCR trước | Thứ tự import có thể quan trọng |
| Chụp lệch vùng ở màn 125% | Toạ độ logic ≠ điểm ảnh thật; đo từ luồng phụ | Đo tỉ lệ trên luồng Tk | Luôn thử ở nhiều mức DPI |
| Ô nhập thiếu dòng cuối | Tk `count -displaylines` đếm số **chỗ xuống dòng**, không phải số dòng | `+ 1` | Đọc kỹ tài liệu, đừng đoán theo tên |
| "Hà Nội là vốn của Việt Nam" | Ép thuật ngữ không xét ngữ cảnh | Chỉ ép từ đơn khi có thuật ngữ cùng ngành | Sửa máy dịch phải cẩn thận hơn máy dịch |
| Bản dịch offline có ký tự `▁` | SentencePiece đánh dấu khoảng trắng bằng `▁` | Ghép mảnh rồi thay `▁` bằng dấu cách | Hiểu định dạng đầu ra của mô hình |
| Inno Setup hết bộ nhớ | Nén `ultra64` nhiều luồng trên trình 32-bit | `max` + tiến trình nén riêng | Mặc định "mạnh nhất" chưa chắc chạy được |
| Hướng dẫn cài OCR tiếng Việt báo thành công nhưng không chạy | Windows OCR không có tiếng Việt — giả định sai từ đầu | Chuyển sang Tesseract | **Kiểm chứng trước khi tin** |

---

## 14. Bài tập tự làm

Xếp từ dễ đến khó, mỗi bài chạm vào một phần của app:

1. **Bản mini:** thêm cache SQLite cho `translate()` (gợi ý: copy ý tưởng `cached`/`remember`
   trong `translate.py`).
2. **Phím tắt:** đổi `HOTKEY_LOOKUP` trong `langscan.py` sang tổ hợp khác, chạy lại.
3. **Thuật ngữ:** thêm 5 thuật ngữ ngành bạn biết vào một file `data/terms/*.tsv`
   (chỉ cần cột `en`, `zh`, `vi`), viết một test trong `tests/test_terms.py` kiểm tra nó.
4. **Nhận diện:** viết test cho `langs.detect` với chữ Hán + kana lẫn lộn.
5. **Giao diện:** thêm một bảng màu thứ ba vào `THEME`.
6. **Dịch:** thêm một nguồn dịch mới vào `PROVIDERS` trong `translate.py` và xem thứ tự
   dự phòng hoạt động thế nào khi tắt mạng.
7. **Khó:** viết lại `DoubleTap` cho phím Shift, kèm test bằng `feed()`.

### Đọc code theo thứ tự nào

1. `paths.py`, `version.py` — 20 dòng, hiểu chỗ để dữ liệu.
2. `langs.py` — `detect`, `Card`, `Analyzer.analyze`: trái tim của tra từ.
3. `dictionary.py` — module ngôn ngữ đơn giản nhất.
4. `translate.py` — dịch, cache, dự phòng.
5. `langscan.py` — đọc `App.run` trước, rồi `grab_selection`, `ui_call`, cuối cùng `Popup`.
6. `ocr.py`, `korean.py`, `offline_mt.py`, `build.py` — khi đã vững phần trên.

Mỗi file đều chạy riêng được — vừa đọc vừa chạy thử là nhanh hiểu nhất:

```bash
python dictionary.py 我在银行工作
```

```bash
python translate.py "The database is offline" en
```
