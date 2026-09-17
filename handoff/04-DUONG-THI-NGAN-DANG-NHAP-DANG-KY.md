# Bản 04 — Dương Thị Ngân — Đăng nhập/Đăng ký

## 1. Mục tiêu

Thiết kế và hoàn thiện luồng tài khoản để xác định người dùng, vai trò và session trước khi truy cập dữ liệu/draft. Wireframe hiện có hai mode; production phải dùng auth provider và role gate server-side.

## 2. Phạm vi file

- Wireframe hiện tại: `frontend/components/AuthWireframe.tsx`.
- Khi tích hợp thật nên tách:
  - `frontend/app/(auth)/login/page.tsx`
  - `frontend/app/(auth)/register/page.tsx`
  - `frontend/app/(auth)/verify-email/page.tsx`
  - `frontend/components/AuthForm.tsx`
  - `frontend/lib/auth.ts`
- Middleware/session và backend JWT validation cần PR riêng nếu vượt phạm vi wireframe.
- Không đưa secret Supabase/Auth.js vào code.

## 3. Thành phần nhỏ nhất

### 3.1 Login form

- Email.
- Mật khẩu.
- Hiện/ẩn mật khẩu.
- Ghi nhớ đăng nhập nếu auth provider hỗ trợ an toàn.
- Quên mật khẩu.
- Submit/loading/error.

### 3.2 Register form

- Họ tên.
- Email tổ chức.
- Mật khẩu.
- Xác nhận mật khẩu.
- Vai trò yêu cầu: researcher hoặc research_manager.
- Đồng ý điều khoản/quyền riêng tư.

### 3.3 Email verification

- Thông báo đã gửi email.
- Nút gửi lại có cooldown.
- Đổi email.
- Success redirect.

### 3.4 Role approval

- Researcher: có thể dùng sau verify email.
- Research manager: trạng thái `pending_role_approval`.
- Chỉ admin/owner được duyệt manager.
- Nếu yêu cầu manager bị từ chối, tài khoản vẫn có thể là researcher.

### 3.5 Session states

- Authenticated.
- Unauthenticated.
- Loading session.
- Session expired.
- Forbidden role.
- Logout success/failure.

## 4. Luồng chi tiết

### Luồng A — Đăng nhập thành công

1. User mở `/login`.
2. Nhập email và mật khẩu.
3. Client kiểm tra định dạng email và mật khẩu không rỗng.
4. Bấm đăng nhập.
5. Disable toàn form, hiện loading.
6. Auth provider xác minh.
7. Server tạo session cookie HttpOnly/Secure/SameSite.
8. Lấy role từ server-side profile.
9. Redirect về URL trước đó hoặc `/`.
10. Header hiển thị tên/role, không hiển thị token.

### Luồng B — Sai mật khẩu

1. Provider trả invalid credentials.
2. Hiện lỗi chung “Email hoặc mật khẩu chưa đúng”.
3. Không nói email có tồn tại hay không.
4. Xóa field mật khẩu, giữ email.
5. Cho thử lại; áp dụng rate limit.

### Luồng C — Tài khoản chưa xác minh email

1. Credentials đúng nhưng email chưa verify.
2. Không tạo session đầy đủ.
3. Chuyển sang màn verify email.
4. Hiện email đã che một phần.
5. Cho gửi lại sau cooldown.

### Luồng D — Đăng ký thành công researcher

1. Nhập đủ họ tên/email/mật khẩu/xác nhận.
2. Chọn “Nhà nghiên cứu”.
3. Tích đồng ý điều khoản.
4. Validate client.
5. Gửi register request.
6. Provider tạo user chưa verify.
7. Tạo profile role `researcher` ở server.
8. Gửi email xác minh.
9. Chuyển màn verify.
10. Verify thành công → đăng nhập/redirect.

### Luồng E — Đăng ký trùng email

1. Provider phát hiện email tồn tại.
2. Hiện thông báo không tiết lộ quá mức.
3. Đề xuất đăng nhập hoặc quên mật khẩu.
4. Không tạo profile trùng.

### Luồng F — Yêu cầu vai trò manager được chấp nhận

1. User chọn “Quản lý phòng KHCN”.
2. Tài khoản được tạo với role tạm `researcher` và request pending.
3. Admin mở danh sách yêu cầu.
4. Kiểm tra email tổ chức/bằng chứng.
5. Bấm chấp nhận và xác nhận.
6. Server cập nhật role `research_manager`.
7. Audit ghi actor/time/old role/new role.
8. User nhận thông báo và quyền manager ở session kế tiếp.

### Luồng G — Yêu cầu manager bị từ chối

1. Admin bấm từ chối.
2. Bắt buộc nhập lý do.
3. Role vẫn là `researcher`.
4. Không khóa toàn bộ tài khoản nếu researcher hợp lệ.
5. User thấy thông báo và hướng dẫn bổ sung bằng chứng.
6. Lưu audit; không xóa request cũ.

### Luồng H — User truy cập route không đủ quyền

1. Researcher gọi endpoint manager.
2. Backend trả 403.
3. UI hiện “Anh không có quyền thực hiện hành động này”.
4. Không redirect vòng lặp.
5. Không chỉ ẩn nút; server vẫn phải chặn.

### Luồng I — Quên mật khẩu

1. Nhập email.
2. Luôn hiện thông báo chung để tránh dò email.
3. Provider gửi link có hạn dùng.
4. User đặt mật khẩu mới theo policy.
5. Revoke session cũ nếu cấu hình.
6. Redirect đăng nhập.

### Luồng J — Session hết hạn

1. API trả 401.
2. Hiện modal “Phiên đăng nhập đã hết hạn”.
3. Lưu draft local an toàn nếu có.
4. Chuyển login với `returnTo`.
5. Login lại thành công → quay về đúng màn.
6. Không tự lặp request 401 vô hạn.

### Luồng K — Đăng xuất

1. User bấm đăng xuất.
2. Hiện xác nhận nếu đang có thay đổi chưa lưu.
3. Gọi sign-out server.
4. Xóa session cookie.
5. Xóa state nhạy cảm ở client.
6. Redirect login.

### Luồng L — Provider/auth network lỗi

1. Giữ dữ liệu không nhạy cảm trong form.
2. Xóa mật khẩu khỏi state sau lỗi.
3. Hiện lỗi dịch vụ tạm thời và nút thử lại.
4. Không fallback sang đăng nhập giả trong production.

## 5. Validation tối thiểu

- Email đúng định dạng.
- Mật khẩu tối thiểu 8 ký tự; production theo policy provider.
- Confirm password phải khớp.
- Họ tên không chỉ chứa khoảng trắng.
- Phải chọn role.
- Phải đồng ý điều khoản khi đăng ký.
- Không log mật khẩu, token hoặc session cookie.

## 6. Test case bắt buộc

1. Login đúng.
2. Sai mật khẩu.
3. Email sai định dạng.
4. Email chưa verify.
5. Register researcher thành công.
6. Register trùng email.
7. Password và confirm không khớp.
8. Manager request accepted.
9. Manager request rejected có lý do.
10. Researcher gọi manager API → 403.
11. Session expired → returnTo đúng.
12. Forgot password không làm lộ email tồn tại.
13. Logout xóa session.
14. Provider lỗi → không tạo session giả.
15. Keyboard/screen reader đọc đúng label và lỗi.

## 7. Definition of Done

- [ ] Login/register là route rõ ràng hoặc mode rõ ràng.
- [ ] Field có label, autocomplete phù hợp và error text.
- [ ] Password không xuất hiện trong log.
- [ ] Có loading và chống double submit.
- [ ] Có email verification flow.
- [ ] Có forgot/reset password flow.
- [ ] Có manager role approval.
- [ ] Manager reject bắt buộc lý do.
- [ ] 401 và 403 có UX riêng.
- [ ] Server kiểm tra role; không chỉ ẩn nút frontend.
- [ ] Session dùng cookie bảo mật khi tích hợp thật.
- [ ] Wireframe ghi rõ phần nào mock.
- [ ] Responsive 390/768/1440.
- [ ] Typecheck/lint/build pass.
- [ ] Có ảnh login, register, verify và role rejected.

## 8. Các bước làm nhỏ nhất

1. Tạo branch `feature/ngan-auth-wireframe`.
2. Tách LoginForm/RegisterForm.
3. Thêm show/hide password.
4. Thêm validation theo field.
5. Thêm loading/error/success.
6. Dựng verify email.
7. Dựng forgot password.
8. Dựng role pending/accepted/rejected.
9. Dựng 401/403/session expired.
10. Kiểm tra accessibility.
11. Kiểm tra responsive.
12. Chụp bốn ảnh.
13. Commit và push.

```powershell
git checkout -b feature/ngan-auth-wireframe
cd frontend
pnpm typecheck
pnpm lint
pnpm build
cd ..
git add frontend/components/AuthWireframe.tsx frontend/app
git commit -m "feat: complete authentication and role wireframes"
git push -u origin feature/ngan-auth-wireframe
```
