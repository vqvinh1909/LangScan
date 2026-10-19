# LangScan — bôi đen là tra từ: Trung · Nhật · Hàn · Anh

> **Chỉ chạy trên Windows 10/11** (cần Python 3.9+). Chưa hỗ trợ macOS và Linux.

Bôi đen chữ ở bất kỳ đâu trên Windows (PDF, trình duyệt, Word, Zalo…), bấm **Ctrl+Alt+D** → popup hiện ngay cạnh con trỏ. App tự nhận ra đó là tiếng Trung, Nhật, Hàn hay Anh rồi tra đúng từ điển.

| | Phiên âm | Nghĩa | Cấp độ | Đưa về dạng gốc |
|---|---|---|---|---|
| **Trung** | pinyin có dấu thanh, tô màu theo thanh | **tiếng Việt** + tiếng Anh | HSK 1–6 | tách từ |
| **Nhật** | kana + romaji | tiếng Anh + **dịch Việt online** | JLPT N5–N1 | 食べました → 食べる |
| **Hàn** | phiên âm Latin | tiếng Anh + **dịch Việt online** | — | 일해요 → 일하다 |
| **Anh** | IPA | **tiếng Việt** (118.000 từ, offline) | CEFR A1–C2 · **IT** | studying → study |

Kèm theo: nút ▶ phát âm từng từ và cả câu, nghĩa từng chữ Hán trong từ tiếng Nhật, câu ví dụ cho từ tiếng Anh, và với tiếng Hàn thì hiện luôn phần Hán tự cùng nghĩa tiếng Việt của nó — 은행 → 銀行 → ngân hàng.

---

## Vì sao Trung/Anh có nghĩa Việt offline mà Nhật/Hàn thì không

Tiếng Trung có CVDICT (119.000 mục Trung–Việt) và tiếng Anh có bộ dữ liệu 118.000 từ Anh–Việt, đều giấy phép mở, nên tra offline được. Nhật và Hàn không có bộ tương đương chất lượng, nên app dùng:

- **Nghĩa tiếng Anh offline** — hiện ngay lập tức, chính xác, từ JMdict (Nhật) và kengdic (Hàn)
- **Một dòng tiếng Việt dịch online** — tự động lưu cache vào `data/vi_cache.db`, nên từ nào tra rồi thì lần sau hiện ngay cả khi mất mạng

Cơ chế dịch online này cũng đỡ cho tiếng Anh: từ điển Anh–Việt offline dựa trên nguồn khá cũ nên thiếu thuật ngữ IT hiện đại. Từ nào không có, app tự dịch online rồi cache lại.

### Từ điển thuật ngữ IT

Dịch máy xử lý thuật ngữ chuyên ngành rất tệ — nó dịch `offline` thành "ngoại tuyến", đúng từ điển nhưng sai ngữ cảnh nghề. Nên `data/it_terms.tsv` chứa hơn 250 thuật ngữ Linux / mạng / bảo mật / cloud / DevOps / Active Directory với giải thích tiếng Việt đúng cách dân trong ngành nói, **được ưu tiên hơn từ điển thường** và có huy hiệu `IT`:

```
offline        → không kết nối mạng; ở chế độ rời mạng
load balancer  → bộ cân bằng tải - chia lưu lượng cho nhiều máy chủ
idempotent     → gọi nhiều lần cho kết quả như gọi một lần
```

Bắt được cả cụm nhiều từ (`load balancer`, `high availability`, `infrastructure as code`). Muốn thêm từ thì mở `data/it_terms.tsv` bằng Notepad, viết thêm một dòng theo dạng `thuật_ngữ<Tab>nghĩa<Tab>ghi chú`, lưu lại rồi khởi động lại app.

Không thích dòng dịch máy thì mở `langscan.py` sửa `TRANSLATE_VI = False`.

---

## Cài đặt (làm 1 lần)

1. Cài Python 3.9+ : https://www.python.org/downloads/ — nhớ tick **"Add Python to PATH"**
2. Nháy đúp **`setup.bat`**, trả lời 3 câu hỏi:
   - Cài từ điển tiếng Nhật? → `y` nếu bạn học tiếng Nhật (tải ~75MB, một lần duy nhất)
   - jieba → cứ để nó chạy, lỗi cũng không sao
   - Bật khởi động cùng Windows? → tuỳ bạn

Từ điển Trung, Hàn và Anh đã kèm sẵn trong `data/`. Riêng từ điển Nhật nằm trong gói pip `jamdict-data` nên phải cài qua mạng.

Cài tiếng Nhật sau cũng được — nháy đúp **`caidat_tiengnhat.bat`**. Nó tải ~54MB rồi giải nén thành ~310MB trong `data/jamdict.db`.

**Vì sao có file cài riêng:** gói `jamdict-data` trên PyPI bị lỗi khi cài bằng pip trên Windows — nó tự giải nén file `.db` ngay trong lúc pip đang đọc gói, rồi báo `WinError 32: file đang bị tiến trình khác dùng`. Lỗi của gói đó, không phải của máy bạn. File `caidat_tiengnhat.bat` đi vòng: tải thẳng gói về, rút file `.db` ra, giải nén vào `data/`.

## Chạy

| File | Kiểu chạy |
|---|---|
| **`run_hidden.bat`** | Chạy ngầm, không cửa sổ nào. Dùng hằng ngày. |
| `run.bat` | Có console để xem log khi nghi có lỗi. |

Có **icon 語 ở khay hệ thống** (góc phải taskbar, có thể phải bấm mũi tên `^`). Chuột phải để tra từ, bật/tắt autostart, mở thư mục, xem log, thoát.

| Phím tắt | Tác dụng |
|---|---|
| `Ctrl+Alt+D` | Tra phần bôi đen, **tự nhận diện ngôn ngữ** |
| `Ctrl+Alt+C` | Ép tra tiếng Trung |
| `Ctrl+Alt+J` | Ép tra tiếng Nhật |
| `Ctrl+Alt+K` | Ép tra tiếng Hàn |
| `Ctrl+Alt+E` | Ép tra tiếng Anh |
| **Nhấn đúp `Ctrl`** | **Mở cửa sổ gõ tay để tra từ** (hai chiều) |
| `Ctrl+Alt+S` | Cũng mở cửa sổ đó — giữ làm đường dự phòng |
| `Ctrl+Alt+X` | **Chụp một vùng màn hình rồi đọc chữ** (OCR) |
| `Esc` | Đóng popup |
| `Ctrl+Alt+Q` | Thoát chương trình |

**Vì sao cần phím ép:** chữ Hangul và kana thì máy nhận ra chắc chắn, nhưng một cụm **toàn Kanji** như 日本語 thì tiếng Trung và tiếng Nhật viết giống hệt nhau. App mặc định đoán là tiếng Trung; gặp câu tiếng Nhật toàn Kanji thì bấm `Ctrl+Alt+J`.

## Cửa sổ tra từ hai chiều

Không phải lúc nào cũng có sẵn chữ để bôi đen. **Nhấn phím `Ctrl` hai lần liên tiếp** (kiểu Google Dịch trên máy tính) để mở ô gõ tay — hoặc `Ctrl+Alt+S`, hoặc chuột phải icon khay → "Cua so tra tu".

Nhấn đúp Ctrl **không đụng** vào các thao tác quen thuộc: Ctrl+C rồi Ctrl+V liên tiếp sẽ không làm cửa sổ nhảy ra, vì app chỉ tính khi Ctrl được bấm **một mình**, không kèm phím nào khác. Hai lần bấm phải cách nhau dưới 0,4 giây.

Thấy vướng thì mở `langscan.py` sửa `DOUBLE_CTRL_SEARCH = False`, lúc đó chỉ còn `Ctrl+Alt+S`. Muốn chỉnh độ nhạy thì sửa `DOUBLE_TAP_GAP`. Ngay dưới ô nhập có thanh chọn **ngôn ngữ nguồn ⇄ ngôn ngữ đích**, kiểu Google Dịch:

| Cặp | Gõ vào | Ra |
|---|---|---|
| `Việt → Trung` | `chào` | 你好, 招呼, 施礼 |
| `Việt → Anh` | `ngân hàng` | bank, banking |
| `Trung → Việt` | `银行` hoặc `yinhang` | ngân hàng |
| `Nhật → Việt` | `食べる` | to eat + dịch Việt |
| `Hàn → Việt` | `일해요` | 일하다 - to work |
| `Anh → Việt` | `deploy` | triển khai |
| `Trung → Việt` | `wo shi xuesheng` | 我 · 是 · 学生 (tách câu pinyin) |
| `Nhật → Việt` | `tabemashita`, `tokyo` | 食べる, 東京 (gõ romaji) |
| `Hàn → Việt` | `annyeonghaseyo` | 안녕하세요 (gõ phiên âm Latin) |

**Gõ phiên âm thay cho chữ gốc**: chọn nguồn Trung / Nhật / Hàn rồi gõ pinyin, romaji hay phiên âm Latin tiếng Hàn đều được. Để nguồn **Tự động** thì app chỉ thử đọc như romaji / phiên âm Hàn khi chữ đó không phải từ tiếng Anh. Romaji bỏ trường âm vẫn nhận (`tokyo`, `gakko`); phiên âm Hàn nhận cả kiểu chuẩn (`gamsahamnida`) lẫn kiểu cũ (`kamsahamnida`).

**Di chuyển và chỉnh cỡ popup**: giữ chuột vào chỗ trống ở thanh trên, thanh chọn ngôn ngữ hoặc dòng chữ nhỏ dưới cùng rồi kéo để di chuyển. Kéo góc **◢** ở dưới bên phải để phóng to, thu nhỏ. Cỡ đã chỉnh được nhớ cho các lần sau (lưu ở `data/popup.json`, xoá file này để về cỡ mặc định).

**Dán cả câu thì nó dịch cả câu**, rồi bên dưới vẫn tách ra từng từ để bạn học. Ô nhập cao 2 dòng, Shift+Enter xuống dòng, Enter là dịch.

```
我每天在银行工作，也学习汉语。
→ DỊCH CẢ CÂU: Tôi làm việc ở ngân hàng mỗi ngày và cũng học tiếng Trung.
→ NGHĨA TỪNG TỪ: 我 · 每天 · 在 · 银行 · 工作 · 学习 · 汉语
```

Phần dịch câu **cần mạng** (dùng API dịch máy) và được cache lại. Phần tra từ vẫn offline như cũ. Dịch sang đúng ngôn ngữ bạn chọn ở ô đích — chọn `Việt → Trung` rồi gõ câu tiếng Việt thì ra câu tiếng Trung.

Ô đích quyết định kết quả ra thứ tiếng nào, kể cả khi nguồn để **Tự động**. Gõ `chào` với đích `Anh` ra `hello, greet`; đổi đích sang `Trung` thì ra `你好, 招呼`.

Nút **⇄** ở giữa đảo chiều. Đổi ngôn ngữ là tra lại ngay, không cần bấm Enter. Cặp đang chọn được nhớ cho lần mở sau.

Để nguồn là **Tự động** thì app tự đoán — dùng hằng ngày là đủ. Chọn tay khi nó đoán sai, hay gặp nhất với mấy từ nằm giữa hai thứ tiếng: `chào` vừa là tiếng Việt vừa đọc được như pinyin `chao`; `song`, `ban`, `dang` vừa là từ tiếng Anh vừa là pinyin.

Tra ngược (Việt → tiếng khác) quét thẳng phần nghĩa tiếng Việt có sẵn trong từ điển nên **chạy offline**. Gõ không dấu cũng được: `ngan hang`, `tuong lua`, `may chu`. Pinyin thì gõ kiểu nào cũng nhận — liền, cách, có số thanh điệu hay có dấu; gõ dở `yinh` cũng gợi ý.

Kết quả xếp theo độ phổ biến: từ có trong HSK/CEFR lên trước, chữ đơn hiếm đẩy xuống cuối. Nên `chào → 你好` chứ không phải mấy chữ cổ như 匑, 喏.

### Việt → Nhật / Hàn (đi đường vòng)

Không tồn tại từ điển Việt–Nhật hay Việt–Hàn mã nguồn mở đủ tốt. Nên app bắc hai cây cầu:

1. **Qua Hán tự** — `ngân hàng` → 银行 (Trung) → 銀行 (Nhật) / 은행 (Hàn). Đây là đường chính xác nhất, ăn đứt dịch máy, và chỉ chạy được vì bạn học cả ba thứ tiếng cùng lúc.
2. **Qua tiếng Anh** — `ngân hàng` → `bank` → 銀行 / 은행. Dùng cho từ thuần, không có Hán tự.

Mỗi kết quả ghi rõ nó đến qua cầu nào. Kết quả có Hán tự trùng với từ tiếng Trung được xếp lên đầu vì đó là tín hiệu chắc chắn nhất.

Từ Hán–Việt (`ngân hàng`, `thư viện`, `cảm ơn`, `máy tính`) ra rất chuẩn. Từ thuần Việt (`nước`, `ăn`) thì kém hơn — phải đi qua tiếng Anh, mà tiếng Anh lại đa nghĩa. Nên coi đây là gợi ý để tra tiếp, đừng tin tuyệt đối.

Lần tra ngược **đầu tiên** mất khoảng 10 giây để dựng chỉ mục (thanh trạng thái sẽ báo). Chỉ mục lưu vào `data/reverse_*.pickle`, những lần sau tra tức thì.

## Chụp màn hình rồi tra (OCR)

Bấm **Ctrl+Alt+X**, màn hình mờ đi, kéo chuột khoanh vùng có chữ. Thả chuột là app đọc chữ trong đó rồi hiện popup y như khi bôi đen.

Dùng cho chỗ không bôi đen được: **ảnh, PDF scan, video, game, phần mềm vẽ giao diện bằng đồ hoạ**. Đây chính là lỗ hổng còn lại của cách bôi đen — giờ bịt được.

Có hai cách cài, chọn một:

| | Cài gì | Mất bao lâu | Đọc được |
|---|---|---|---|
| **`caidat_ocr_nhanh.bat`** | gói pip RapidOCR, ~36MB | **~1 phút**, không cần quyền admin | Trung + Anh |
| `caidat_ocr.bat` | gói ngôn ngữ của Windows | 10–20 phút, cần quyền admin | Trung + Nhật + Hàn + Anh |

Học tiếng Trung là chính thì dùng bản nhanh là đủ. Cần đọc chữ Nhật/Hàn trong ảnh mới phải chờ bản đầy đủ.

Cài cả hai cũng được — app ưu tiên RapidOCR cho Trung/Anh (nhanh hơn) và dùng OCR của Windows cho Nhật/Hàn.

Kiểm tra sau đó: `python ocr.py` in ra những thứ tiếng đọc được.

App tự đoán vùng chụp là tiếng gì: nó thử đọc bằng từng thứ tiếng rồi chọn kết quả nào ra đúng loại chữ nhất. Chụp chữ Hán thì thử tiếng Trung và Nhật, xem bên nào ra nhiều chữ hợp lý hơn.

Nếu máy bạn đã cài sẵn Tesseract thì app cũng dùng được, coi như phương án dự phòng thứ ba.

Chụp một vùng mất khoảng 2 giây để đọc chữ. Vùng càng nhỏ càng nhanh — khoanh đúng câu cần tra, đừng chụp cả màn hình. Vùng chữ nhỏ thì app tự phóng to trước khi đọc, nên chụp chữ bé vẫn ra.

**Nếu nó đọc nhầm sang chỗ khác trên màn hình:** đó là do tỉ lệ hiển thị của Windows (125%, 150%). tkinter báo toạ độ theo hệ 100% còn ảnh chụp là điểm ảnh thật, nên khoanh một đằng chụp một nẻo. App đo tỉ lệ này lúc chụp lần đầu và bù lại — bản từ 2026-09-10 trở đi đã xử lý.

## Khởi động cùng Windows

Bật: `install_autostart.bat`, hoặc trả lời `y` ở bước 4 của `setup.bat`, hoặc tick trong menu icon khay. Tắt: `uninstall_autostart.bat`.

Cơ chế: tạo task `LangScan` trong Task Scheduler, chạy lúc đăng nhập với **quyền cao nhất** — nhờ vậy phím tắt vẫn ăn khi bạn đang ở trong app chạy quyền admin. Lúc bật/tắt Windows hỏi UAC một lần, bấm Yes.

Bản cũ tên `ChineseScan` sẽ tự được gỡ khi bạn cài autostart lần này.

Kiểm tra trạng thái: `python autostart.py status`

Chỉ một bản chạy tại một thời điểm — mở thêm lần nữa thì bản thứ hai tự thoát.

---

## Khi có gì đó không chạy

Nháy đúp **`chandoan.bat`**. Nó kiểm tra lần lượt: Python, thư viện nào thiếu, file từ điển nào thiếu, thử tra thật bốn thứ tiếng, và thử từng nguồn dịch online. Đọc cột `[OK]` / `[THIEU]` là biết hỏng ở đâu.

Hai lỗi hay gặp nhất:

- **Tiếng Nhật không ra gì** — chưa cài từ điển Nhật. Nháy đúp **`caidat_tiengnhat.bat`**, chờ tải ~54MB, xong thoát app (Ctrl+Alt+Q) và mở lại.
- **Tiếng Nhật/Hàn không có nghĩa tiếng Việt, hoặc không dịch được câu** — hai việc này cần mạng. Mục 5 của `chandoan.bat` cho biết mạng của bạn có chặn các dịch vụ dịch không. Phần tra từ Trung và Anh vẫn chạy offline bình thường.

## Lưu ý

- Cách lấy chữ: app giả lập `Ctrl+C` rồi đọc clipboard, sau đó **trả clipboard về nguyên trạng**. Chỗ nào không copy được (ảnh, PDF scan) thì không tra được — chỗ đó cần OCR.
- Phát âm dùng gTTS (cần mạng), mp3 cache ở `data/audio/`.
- Tiếng Hàn: kengdic là từ điển cộng đồng, nghĩa tiếng Anh đôi khi cộc lốc hoặc viết hoa lộn xộn. Phần chia động từ (`일해요` → `일하다`) dùng quy tắc đơn giản, không phải bộ phân tích hình thái đầy đủ, nên vài trường hợp hiếm sẽ trượt.
- Dòng "Hán tự = …" của tiếng Hàn là **nghĩa** của chữ Hán đó, không phải âm Hán–Việt. Ví dụ 每日 hiện "hàng ngày" chứ không phải "mỗi nhật".
- Tiếng Anh: bôi đen cả câu thì app bỏ qua các từ chức năng (the, of, is…) cho đỡ rối. Bôi đúng một từ trong số đó thì vẫn tra bình thường.
- Dòng nghĩa **không có** huy hiệu cấp độ, loại từ và ví dụ nghĩa là nó đến từ dịch máy online chứ không phải từ điển — nên kiểm chứng lại khi cần chính xác.

## Tuỳ chỉnh

Mở `langscan.py`, sửa mấy dòng đầu file:

| Biến | Ý nghĩa |
|---|---|
| `HOTKEY_LOOKUP`, `HOTKEY_JA`… | Đổi phím tắt |
| `SHOW_ENGLISH` | `False` = ẩn dòng tiếng Anh |
| `TRANSLATE_VI` | `False` = tắt dịch online (Nhật, Hàn, từ tiếng Anh lạ) |
| `MAX_WORDS` | Số từ tối đa mỗi lần tra |
| `TONE_COLORS` | Màu theo thanh điệu tiếng Trung |

## Cấu trúc

| File | Việc |
|---|---|
| `langscan.py` | App chính: phím tắt, lấy vùng bôi đen, popup, icon khay |
| `langs.py` | Nhận diện chữ viết, lớp thẻ từ chung cho cả 4 ngôn ngữ |
| `dictionary.py` | Tiếng Trung: CVDICT + CC-CEDICT, pinyin, HSK, tách từ |
| `japanese.py` | Tiếng Nhật: JMdict qua jamdict, janome, romaji, JLPT |
| `korean.py` | Tiếng Hàn: kengdic, phiên âm Latin, Hán tự |
| `english.py` | Tiếng Anh: từ điển Anh–Việt, IPA, CEFR, thuật ngữ IT, đưa về dạng gốc |
| `reverse.py` | Tra ngược Việt → Trung/Anh và tra bằng pinyin, có chỉ mục cache |
| `translate.py` | Dịch Việt online + cache SQLite |
| `autostart.py` | Bật/tắt khởi động cùng Windows |
| `setup_data.py` | Tải từ điển về `data/` |
| `caidat_tiengnhat.py` | Cài từ điển tiếng Nhật (đi vòng qua lỗi pip trên Windows) |
| `ocr.py` | Đọc chữ từ ảnh bằng OCR của Windows (hoặc Tesseract) |
| `chandoan.py` | Kiểm tra thiếu gì, hỏng gì |

Mỗi module chạy độc lập được để kiểm tra nhanh, không cần giao diện:

```
python dictionary.py 我在银行工作
python japanese.py   私は毎日日本語を勉強しています
python korean.py     저는 은행에서 일해요
python english.py    "I am deploying a firewall on the server"
python translate.py  食べる ja
python reverse.py    "ngân hàng"
python reverse.py    yinhang
```

Kiểm tra tự động (cần `pip install pytest`, chạy offline, khoảng 3 giây):

```
python -m pytest tests
```

---

## Nguồn dữ liệu & giấy phép

- **CVDICT** — Từ điển Hán Việt của Phong Phan, CC BY-SA 4.0 — https://github.com/ph0ngp/CVDICT
- **CC-CEDICT** — từ điển Trung–Anh, CC BY-SA 4.0 — https://www.mdbg.net/chinese/dictionary?page=cc-cedict
- **HSK 2.0** — https://github.com/glxxyz/hskhsk.com
- **JMdict / KanjiDic2** — EDRDG, CC BY-SA 4.0, qua gói `jamdict-data`
- **kengdic** — Joe Speigle, MPL 2.0 / LGPL — https://github.com/garfieldnate/kengdic
- **JLPT vocab** — https://github.com/jamsinclair/open-anki-jlpt-decks
- **Từ điển Anh–Việt** — minhqnd/dictionary, CC BY-SA 4.0 — https://github.com/minhqnd/dictionary
- **IPA** — open-dict-data/ipa-dict — https://github.com/open-dict-data/ipa-dict
- **CEFR** — CEFR-J + Octanove, https://github.com/openlanguageprofiles/olp-en-cefrj

## Có thể bổ sung sau (chưa làm)

- Lưu từ vào sổ tay + xuất CSV import Anki
- Câu ví dụ cho tiếng Trung, Nhật, Hàn (tiếng Anh đã có)
- Tách từ cho câu tiếng Việt (dán câu Việt hiện mới dịch cả câu, chưa tra từng từ)
- Tra ngược cho tiếng Nhật và Hàn (hai bộ này nghĩa tiếng Anh nên chưa tìm ngược bằng tiếng Việt được)
- Cấp độ TOPIK cho tiếng Hàn (chưa tìm được danh sách mở đủ tốt)
