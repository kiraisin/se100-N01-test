# Mượn sách giữa sinh viên — SE100 · Nhóm 01

Hệ thống hỗ trợ sinh viên đăng ký và chia sẻ sách cá nhân để những sinh viên khác có thể tìm kiếm và gửi yêu cầu mượn sách.

Sinh viên có thể đăng ký sách mình đang sở hữu, tìm kiếm sách và gửi yêu cầu mượn sách từ sinh viên khác.

Chủ sở hữu sách có thể xem và xử lý các yêu cầu mượn đối với sách của mình.

Hệ thống hỗ trợ theo dõi trạng thái sách và thông tin liên quan đến việc mượn và trả sách.

Hệ thống không cho phép sinh viên mượn sách đang không khả dụng hoặc thực hiện các thao tác trái với trạng thái hiện tại của sách.

## Thành viên

| Tên                   | GitHub    | Chủ trì mốc     |
| --------------------- | --------- | --------------- |
| Huỳnh Thanh Thiên Kim | kiraisin  | M1: Yêu cầu     |
| Lê Thành Hòa          | lthnoname | M2: Mô hình hoá |
| Đặng Mai Khanh        | kaydag    | M3–M4: Thiết kế |
| Trần Vinh             | TranVinh23521797 | M5: Giao hàng   |

## URL

- Bản chạy: https://se100.pages.dev/
- Pipeline: xem tab Actions

## Cấu trúc repo

```
docs/         yêu cầu, đặc tả use case, phân tích tác vụ
diagrams/     sơ đồ Mermaid (.mmd) — use case, lớp, tuần tự, trạng thái, C4
adr/          quyết định kiến trúc, mỗi quyết định một tệp
phan-tu/      bản phản tư M0–M5 và bảng phản hồi cáo buộc
ai-log/       bản ghi hội thoại với agent, theo mốc
src/          mã nguồn
.github/      workflow kiểm mốc — đừng sửa
AGENTS.md     ràng buộc kiến trúc cho agent đọc — viết ở M4 
```

## Mốc

| Mốc | Hạn        | Nộp gì                                                                                         | CI kiểm thêm                                          |
| --- | ---------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| M0  | CN tuần 2  | README, đề tài, `docs/cau-hoi-khach-hang.md` (≥ 3 câu)                                         | 4 người có commit                                     |
| V1  | CN tuần 4  | Hệ thống chạy, `docs/hoi-cuu-vong1.md`, ai-log                                                 | Giảng viên kiểm tay, không tính điểm                  |
| M1  | CN tuần 5  | `docs/yeu-cau.md`                                                                              | ≥ 3 tác nhân, ≥ 6 FR, ≥ 3 NFR có số, ≥ 1 BR           |
| M2  | CN tuần 7  | `diagrams/use-case.mmd` (≥ 5 UC), `docs/dac-ta-UC-*.md` ×3, `diagrams/seq-*.mmd` ×2            | Mermaid parse được                                    |
| M3  | CN tuần 9  | `diagrams/class.mmd` (≥ 5 lớp), `diagrams/state.mmd`, `docs/tu-danh-gia-M3.md`                 | Đối chiếu chéo lớp ↔ sequence; mọi lớp có trong docs/ |
| M4  | CN tuần 10 | `diagrams/c4-context.mmd`, `c4-container.mmd`, `docs/du-lieu.md`, `adr/0001-*.md`, `AGENTS.md` | ADR có ≥ 2 phương án; AGENTS.md hết comment mẫu       |
| M5  | CN tuần 13 | Pipeline riêng xanh, URL sống, `docs/tac-dong-vong3.md`, `docs/trung-lap.md` có 2 lần đo       | URL trả 200                                           |

Mốc nào cũng kèm `phan-tu/Mn.md` (M0 ≥ 40 từ, còn lại ≥ 120 từ, có mã commit) và một tệp trong `ai-log/`. Từ M2 thêm `phan-tu/Mn-phan-hoi.md`.

## Cách nộp mốc

1. Tạo nhánh `moc/Mn` rồi làm việc trên đó.
2. Mở Pull Request vào `main`, tiêu đề `Mn — [tên nhóm]`.
3. Đợi workflow **Kiểm mốc** chạy. Đỏ thì đọc log, sửa, push lại.
4. Xanh thì merge. Thời điểm merge là thời điểm nộp.
