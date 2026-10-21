# Nhật ký thay đổi

## 2.0.0 — 2026-10-21

Bản đầu tiên có file cài đặt — người dùng không cần cài Python.

### Cài đặt và giao diện
- **File cài đặt `LangScan-Setup-2.0.0.exe`**: bấm Next là xong, không cần Python, không cần quyền admin. Đã gói sẵn từ điển cả 4 thứ tiếng (kể cả tiếng Nhật) và bộ đọc chữ tiếng Việt. Gỡ cài đặt sạch, không đụng vào chế độ khởi động cùng Windows của bản chạy bằng Python.
- **Logo mới**: chữ ký "Vinh" trên nền tre xanh (cỡ nhỏ là chữ V).
- **Popup mới**: giao diện sáng màu xanh tre, bo góc, nút ✕ ở góc; **kéo để di chuyển**, kéo góc ◢ để **chỉnh to nhỏ** (nhớ cho lần sau). Popup tự co theo nội dung, chiều cao đã kéo là mức tối đa. Đổi lại giao diện tối: `THEME = "toi"`.
- Toàn bộ chữ trên giao diện có dấu tiếng Việt; bỏ phần hiện thừa (từ tiếng Anh phổ biến không kèm "đọc như pinyin" nữa).
- Menu khay hiện số phiên bản.

### Tra từ
- **Tiếng Hàn**: tra được động từ, tính từ bất quy tắc (갔습니다 → 가다, 예뻐요 → 예쁘다, 추워요 → 춥다, 불렀어요 → 부르다…).
- **Gõ phiên âm thay chữ gốc**: pinyin (`wo shi xuesheng` → 我 · 是 · 学生, tách câu pinyin), romaji (`tabemashita` → 食べる, `tokyo` → 東京), phiên âm Latin tiếng Hàn (`annyeonghaseyo` → 안녕하세요).
- **Chữ phồn thể** tách từ đúng (臺灣, 為什麼).
- **Tiếng Anh**: phiên âm IPA đúng dạng chia (went /wɛnt/ chứ không phải /ɡoʊ/ của go).
- **Thuật ngữ chuyên ngành** 4 thứ tiếng (~257 mục, `data/terms/`): IT, Kinh tế – tài chính, Y khoa, Kỹ thuật – sản xuất. Thẻ có nhãn ngành, kèm từ tương đương ở các thứ tiếng kia; tra ngược từ tiếng Việt. *Bản khởi đầu do máy soạn — nên nhờ người trong ngành rà lại.*
- Tiếng Việt **gõ không dấu** (`toi di hoc`, `ngan hang`) được nhận là tiếng Việt.

### Dịch cả câu
- **Phiên âm Latin** dưới câu tiếng Trung / Nhật / Hàn (pinyin, romaji, phiên âm Hàn); nút **▶ Câu gốc** và **▶ Câu dịch** để nghe.
- **Làm sạch câu trước khi dịch**: nối chữ gạch nối và dòng bị ngắt, sửa dấu câu, hạ chữ IN HOA ("COMPASS AI DOANH NGHIỆP" → "La bàn AI doanh nghiệp…").
- **Ép đúng thuật ngữ** khi dịch máy dịch sai ("offline" → "không kết nối mạng" thay vì "ngoại tuyến"); từ nhiều nghĩa chỉ ép khi câu có ngữ cảnh chuyên ngành.
- Đoạn dài được chia theo câu để dịch.
- **Dịch offline khi mất mạng** (Argos Translate, Anh / Trung / Nhật / Hàn → Việt): tải qua menu khay → *Tải bộ dịch offline* (~380MB). Kém Google, chỉ để nắm ý.
- Câu tiếng Việt được đọc bằng giọng Việt (trước bị đọc giọng Trung); âm thanh đã nghe được lưu lại đúng cách.

### Chụp màn hình (OCR)
- **Đọc chữ tiếng Việt có dấu** (Tesseract): "Dasta:" → "Đã sửa:". Bỏ chữ rác ở vùng bị cắt ngang; tách chữ dính ("từcó" → "từ có"); sửa chữ kiểu code bị đọc nhầm ("Ctr1+A1t+Q" → "Ctrl+Alt+Q").
- **`Ctrl+Alt+Z`: chụp lại đúng vùng vừa khoanh** — đọc phụ đề video, game, tài liệu cuộn.
- Nối dòng bị ngắt giữa câu (tiêu đề in hoa không còn mỗi từ một dòng).
- Sửa: OCR Trung / Anh hỏng do xung đột DLL giữa `winrt` và `onnxruntime`; chữ Nhật bị đọc thành tiếng Trung; đo tỉ lệ màn hình 125% sai khi chụp.

### Sửa lỗi khác
- Ô nhập thiếu mất dòng cuối (bôi đen 2 dòng chỉ hiện 1).
- Tra tiếng Nhật từ luồng nền luôn ra rỗng (cả tra ngược Việt → Nhật).
- `setup.bat` cài tiếng Nhật qua đường bị lỗi `WinError 32`.

### Cho người phát triển
- Có git và 246 test tự động (`python -m pytest tests`).
- Đóng gói: `python build.py` (PyInstaller + Inno Setup); số phiên bản ở `version.py`.
- `LangScan.exe --selftest` tự kiểm tra 4 thứ tiếng, OCR, dịch offline → `data/selftest.txt`.

## 1.0.0 — 2026-10-19

Bản đầu tiên: bôi đen / chụp màn hình để tra từ Trung · Nhật · Hàn · Anh, nghĩa tiếng Việt, phiên âm, cấp độ HSK / JLPT / CEFR, tra ngược Việt → ngoại ngữ, dịch cả câu qua mạng, từ điển thuật ngữ IT tiếng Anh. Chạy bằng Python.
