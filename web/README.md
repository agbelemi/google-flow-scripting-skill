# Flow Scripting Studio (web app)

Web app chạy trên **Cloudflare Workers**, dùng **Gemini API** để tạo bộ prompt sản xuất (ảnh tham chiếu, storyboard, video) cho Google Flow theo đúng quy trình của Skill trong repo này. Bạn sao chép từng prompt và dán vào Flow.

Unofficial; not affiliated with Google.

## App làm gì

1. Bạn nhập ý tưởng và thông số (nền tảng, model video, chế độ, độ dài đoạn, tỉ lệ, thể loại, âm thanh, chữ trong hình).
2. Worker ghép nguyên văn các file của Skill (`SKILL.md`, `core/`, `formats/`, `reference/`, `prompts/`, ví dụ) thành system instruction và gọi Gemini để viết bộ prompt hoàn chỉnh.
3. Kết quả được kiểm tra bằng `src/validator.ts`, bản TypeScript của `scripts/validate.py`. `test/parity.test.ts` chạy cả hai bản trên mọi fixture và nhiều cấu hình, và kết quả phải giống hệt nhau.
4. Nếu còn lỗi, nút **AI sửa lỗi** gửi danh sách lỗi cho Gemini để viết lại bản đầy đủ.

Vì các file Markdown của Skill được đóng gói lúc build, mỗi lần cập nhật Skill rồi deploy lại thì app tự dùng quy tắc mới.

## Gemini API key

Mở **Cài đặt** trong app và dán key lấy từ <https://aistudio.google.com/apikey>.

- Key được lưu trong `localStorage` của trình duyệt và gửi kèm mỗi yêu cầu qua header `X-Gemini-Key`. Worker chỉ chuyển tiếp key tới Gemini, không lưu và không ghi log.
- Mỗi người dùng app sẽ dùng key và quota của chính họ.
- Model mặc định là `gemini-3-flash-preview`. Bấm **Tải danh sách** để chọn model khác mà key của bạn dùng được.

## Chạy trên máy

Cần Node.js 22.18 trở lên.

```bash
cd web
npm install
npm run dev        # http://localhost:8787
```

## Deploy lên Cloudflare

### Cách 1: dòng lệnh

```bash
cd web
npm install
npx wrangler login
npm run deploy
```

Wrangler in ra địa chỉ dạng `https://flow-scripting-studio.<tên-tài-khoản>.workers.dev`.

### Cách 2: nối GitHub trong Cloudflare dashboard

1. Cloudflare dashboard, vào **Workers & Pages**, chọn **Create**, rồi **Import a repository** và chọn repo này.
2. **Root directory**: `web`
3. **Build command**: `npm install`
4. **Deploy command**: `npx wrangler deploy`

Từ đó mỗi lần push lên nhánh chính, Cloudflare sẽ tự deploy lại.

## Kiểm tra trước khi deploy

```bash
cd web
npm run check      # typecheck, so sánh với validate.py, build thử Worker
```

`npm test` cần `python3` để chạy `scripts/validate.py` làm chuẩn so sánh.

## Cấu trúc

| Đường dẫn | Vai trò |
|---|---|
| `src/worker.ts` | Worker: phục vụ giao diện, các API `/api/generate` (stream từ Gemini), `/api/validate`, `/api/models` |
| `src/skill.ts` | Ghép các file Skill thành system instruction, thêm hợp đồng định dạng đầu ra cho app |
| `src/validator.ts` | Bản TypeScript của `scripts/validate.py` |
| `public/` | Giao diện (HTML, CSS, JS thuần, không cần build) |
| `test/parity.test.ts` | So sánh kết quả với `scripts/validate.py` |

Thư mục `web/` không thuộc gói Skill: trình cài đặt, bản phát hành và `MANIFEST.json` đều bỏ qua nó.

## Giới hạn

- App chỉ tạo **văn bản prompt**. Việc tạo ảnh và video vẫn làm trong Google Flow.
- Chất lượng kịch bản phụ thuộc vào model Gemini đã chọn. Bộ kiểm tra chỉ phát hiện lỗi máy móc, bạn vẫn cần tự xem lại tính liên tục giữa các cảnh.
- Video càng dài thì kết quả càng dài. Nếu bị cắt (MAX_TOKENS), hãy giảm tổng thời lượng hoặc chia dự án thành nhiều phần.
