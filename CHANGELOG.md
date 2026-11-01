# Nhật ký thay đổi

## Chưa phát hành

### Sửa lỗi
- **Dịch cả câu giữ nguyên số, dấu câu, chữ Latin và độ dài.** Trước đây `我有3个苹果` bị dịch mất số 3, và đoạn dài chỉ được dịch phần đầu (120 chữ Hán, 240 ký tự tiếng Anh).
- **Giữ nguyên clipboard**, kể cả ảnh và file; không bôi đen gì thì clipboard không bị đụng tới. App copy chậm không còn ra kết quả rỗng.
- Chặn popup "ma" khi bấm Alt+Tab do thư viện phím bị kẹt trạng thái.
- Bấm nghe lúc mất mạng không còn làm câu đó hỏng âm thanh luôn.
- Một lỗi xử lý không còn làm mọi phím tắt ngừng chạy; chuỗi Latin rất dài không còn gây lỗi đó.
- Lỗi khi chụp màn hình giờ có hiện thông báo.
- Popup hiện đúng màn hình chứa con trỏ; lớp chụp phủ mọi màn hình.

### Bảo mật và riêng tư
- **Khởi động cùng Windows giờ chạy quyền thường**, không còn quyền cao nhất. Phím tắt không ăn trong app chạy quyền admin. Máy đã bật trước đây: tắt rồi bật lại trong menu icon khay để áp dụng.
- Log không còn ghi nội dung chữ OCR. README nói rõ chữ nào được gửi ra dịch vụ ngoài.

### Dọn dẹp
- Bỏ nguồn dịch Lingva; `setup_data.py` chỉ còn kiểm tra từ điển vì dữ liệu đã nằm sẵn trong mã nguồn.

## 2.1.0 — 2026-10-22

### Thuật ngữ chuyên ngành: 257 → 659 mục, 4 → 11 ngành
- **7 ngành mới** (Anh · Trung → Việt): Thể thao – dinh dưỡng – phục hồi, Pháp luật, Xây dựng, Marketing, Logistics – vận tải – xuất nhập khẩu, Giáo dục, Môi trường – năng lượng.
- **Mở rộng 4 ngành cũ**: Y khoa thêm giấc ngủ – nhịp sinh học (circadian rhythm, melatonin, suprachiasmatic nucleus, giấc ngủ REM…) và bệnh lý, chẩn đoán; IT thêm bảo mật, AI; Kinh tế thêm doanh nghiệp, lao động, vĩ mô; Kỹ thuật thêm quản lý sản xuất, điện, an toàn.
- *Vẫn là bản do máy soạn — nên nhờ người trong ngành rà lại.*

### Dịch chính xác hơn
- Ép thuật ngữ thông minh hơn: bản dịch đã gần đúng thì giữ nguyên câu tự nhiên, chỉ sửa thuật ngữ dịch sai hẳn ("Nhân siêu âm" → "Nhân trên giao thoa thị giác"). Từ đơn nhiều nghĩa — kể cả chữ Hán 1–2 chữ như 作业, 模板 — chỉ bị ép khi câu có thuật ngữ cùng ngành.
- Viết hoa lại đầu câu sau khi thay thuật ngữ.

### Sửa lỗi
- Không còn mục "Câu pinyin" rác với từ tiếng Anh ("circadian" → 刺儿 搽 点, "melatonin" → 么 拉 T 哦 您) hay chữ IN HOA.
- Phiên âm thuật ngữ tiếng Anh không còn bị cụt.

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
