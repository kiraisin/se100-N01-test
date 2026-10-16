#!/usr/bin/env python3
"""Bộ thử cho kiem_pr.py, chạy trên dữ liệu giả, không gọi GitHub.

Dùng khi sửa kiem_pr.py. Nhóm không cần chạy tệp này.
    python3 scripts/thu_kiem_pr.py          (in ĐẠT ở cuối nếu mọi ca đạt)

Mỗi ca dựng một sự kiện pull_request giả (GITHUB_EVENT_PATH) và danh sách tệp giả
(SE100_DU_LIEU_THU/pr_files.json), chạy kiem_pr.py như trong Actions, rồi đọc mã thoát
và bảng kết quả.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

KIEM_PR = Path(__file__).resolve().parent / "kiem_pr.py"
MAU_PR = Path(__file__).resolve().parent.parent / ".github" / "pull_request_template.md"

DONG_DAU_TAY = "Agent: không · Điều khiển: N07-B · Review: N07-A"
DONG_DAU_AGENT = "Agent: Claude Code · Điều khiển: N07-B · Review: N07-A"


def than_pr(dong_dau: str, tra_loi: str | None = "", ngay_duoi: bool = False, dong: str | None = "Đóng #5") -> str:
    """Thân PR theo mẫu. tra_loi=None: bỏ hẳn dòng "Sửa hoặc xoá test đã có?" (mẫu PR cũ).
    dong=None: không có dòng "Đóng #"."""
    phan = [dong_dau] + ([dong] if dong is not None else []) + [
        "", "### Mô tả ngắn", "", "Chuyển luật huỷ đơn vào Don.huy (UC-03, BR-03).", ""]
    if tra_loi is not None:
        phan += ["### Test", ""]
        if ngay_duoi:
            phan += ["Sửa hoặc xoá test đã có? Vì sao:", tra_loi]
        else:
            phan += [f"Sửa hoặc xoá test đã có? Vì sao: {tra_loi}".rstrip()]
        phan += ["", "<!-- Để trống nếu PR không sửa test đã có. -->", ""]
    phan += ["### Mục kiểm", "", "- [x] Người review đã đọc diff và chạy thử trên máy mình"]
    return "\n".join(phan)


def chay(than: str, tep: list[dict], so_pr: int = 12, nhanh: str = "") -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tm:
        su_kien = Path(tm) / "event.json"
        su_kien.write_text(json.dumps({"pull_request": {"number": so_pr, "body": than, "head": {"ref": nhanh}}}),
                           encoding="utf-8")
        (Path(tm) / "pr_files.json").write_text(json.dumps(tep), encoding="utf-8")
        tom_tat = Path(tm) / "summary.md"
        env = dict(os.environ, GITHUB_EVENT_PATH=str(su_kien), SE100_DU_LIEU_THU=tm,
                   GITHUB_REPOSITORY="uit-se100-2026-hk1/se100-N07", GITHUB_STEP_SUMMARY=str(tom_tat))
        env.pop("GITHUB_TOKEN", None)
        env.pop("GITHUB_HEAD_REF", None)
        ra = subprocess.run([sys.executable, str(KIEM_PR)], env=env, capture_output=True, text=True)
        tt = tom_tat.read_text(encoding="utf-8") if tom_tat.exists() else ""
        return ra.returncode, tt


def dong(bang: str, ten: str) -> str | None:
    """Dòng của một mục kiểm trong bảng kết quả, None nếu không có."""
    for d in bang.splitlines():
        if d.startswith(f"| {ten} |"):
            return d
    return None


SUA_TEST = [{"filename": "src/domain/don.py", "status": "modified"},
            {"filename": "tests/luat/test_huy_don.py", "status": "modified"}]

CA: list[tuple[str, object]] = []


def ca(ten):
    def boc(ham):
        CA.append((ten, ham))
        return ham
    return boc


@ca("Sửa test đã có, dòng Vì sao để trống: cảnh báo, PR vẫn đạt")
def _():
    ma, bang = chay(than_pr(DONG_DAU_TAY, ""), SUA_TEST)
    d = dong(bang, "Sửa test đã có")
    assert ma == 0, bang
    assert d and "| Cảnh báo |" in d and "tests/luat/test_huy_don.py" in d, bang
    assert "ĐẠT" in bang


@ca("Ghi lý do cùng dòng: đạt, lý do hiện trong bảng")
def _():
    ma, bang = chay(than_pr(DONG_DAU_TAY, "đổi tên lớp Don thành DonHang, chỉ sửa import"), SUA_TEST)
    d = dong(bang, "Sửa test đã có")
    assert ma == 0 and d and "| Đạt |" in d and "DonHang" in d, bang


@ca("Ghi lý do ở dòng ngay dưới: đạt")
def _():
    ma, bang = chay(than_pr(DONG_DAU_TAY, "test cũ gọi setTrangThai, nay đi qua huy()", ngay_duoi=True), SUA_TEST)
    d = dong(bang, "Sửa test đã có")
    assert ma == 0 and d and "| Đạt |" in d and "huy()" in d, bang


@ca("Lý do chỉ nằm trong chú thích HTML: coi như trống")
def _():
    ma, bang = chay(than_pr(DONG_DAU_TAY, "<!-- sẽ ghi sau -->"), SUA_TEST)
    assert ma == 0 and "| Cảnh báo |" in (dong(bang, "Sửa test đã có") or ""), bang


@ca("Ghi \"không\" mà vẫn sửa test: cảnh báo")
def _():
    ma, bang = chay(than_pr(DONG_DAU_TAY, "Không."), SUA_TEST)
    assert ma == 0 and "| Cảnh báo |" in (dong(bang, "Sửa test đã có") or ""), bang


@ca("Mẫu PR cũ, không có dòng Vì sao, PR xoá test: cảnh báo")
def _():
    tep = [{"filename": "tests/luat/test_huy_don.py", "status": "removed"},
           {"filename": "src/domain/don.py", "status": "modified"}]
    ma, bang = chay(than_pr(DONG_DAU_TAY, None), tep)
    assert ma == 0 and "| Cảnh báo |" in (dong(bang, "Sửa test đã có") or ""), bang


@ca("Đổi tên tệp test đã có: cảnh báo, ghi cả tên cũ và mới")
def _():
    tep = [{"filename": "tests/luat/test_don.py", "status": "renamed",
            "previous_filename": "tests/luat/test_huy.py"}]
    ma, bang = chay(than_pr(DONG_DAU_TAY, ""), tep)
    d = dong(bang, "Sửa test đã có") or ""
    assert ma == 0 and "| Cảnh báo |" in d and "test_huy.py → tests/luat/test_don.py" in d, bang


@ca("Chỉ thêm test mới: không có dòng Sửa test đã có")
def _():
    tep = [{"filename": "tests/luat/test_moi.py", "status": "added"},
           {"filename": "src/domain/don.py", "status": "modified"}]
    ma, bang = chay(than_pr(DONG_DAU_TAY, ""), tep)
    assert ma == 0 and dong(bang, "Sửa test đã có") is None, bang


@ca("Chuyển tệp từ ngoài vào tests/: không tính là test đã có")
def _():
    tep = [{"filename": "tests/luat/test_don.py", "status": "renamed", "previous_filename": "src/don_test.py"}]
    ma, bang = chay(than_pr(DONG_DAU_TAY, ""), tep)
    assert ma == 0 and dong(bang, "Sửa test đã có") is None, bang


@ca("Sửa tệp ngoài tests/: không có dòng Sửa test đã có")
def _():
    tep = [{"filename": "src/tests_helper.py", "status": "modified"},
           {"filename": "src/domain/don.py", "status": "modified"}]
    ma, bang = chay(than_pr(DONG_DAU_TAY, ""), tep)
    assert ma == 0 and dong(bang, "Sửa test đã có") is None, bang


@ca("Có mục chưa đạt khác: PR trượt vì mục đó, cảnh báo test vẫn hiện")
def _():
    than = than_pr("Agent: không · Điều khiển: N07-B · Review: N07-B", "")
    ma, bang = chay(than, SUA_TEST)
    assert ma == 1 and "| Người review khác người điều khiển | Chưa đạt |" in bang, bang
    assert "| Cảnh báo |" in (dong(bang, "Sửa test đã có") or ""), bang


@ca("PR agent có log, sửa test có lý do: đạt")
def _():
    tep = SUA_TEST + [{"filename": "log-tac-tu/PR-12.md", "status": "added"}]
    ma, bang = chay(than_pr(DONG_DAU_AGENT, "đổi tên lớp Don thành DonHang"), tep)
    assert ma == 0 and "| Đạt |" in (dong(bang, "Sửa test đã có") or ""), bang


@ca("Viết \"xóa\", chữ hoa, dấu tổ hợp (NFD): vẫn nhận ra dòng")
def _():
    than = unicodedata.normalize("NFD", than_pr(DONG_DAU_TAY, "đổi tên lớp").replace(
        "Sửa hoặc xoá test đã có? Vì sao:", "SỬA HOẶC XÓA TEST ĐÃ CÓ? VÌ SAO:"))
    ma, bang = chay(than, SUA_TEST)
    assert ma == 0 and "| Đạt |" in (dong(bang, "Sửa test đã có") or ""), bang


@ca("Mẫu PR trong kho có dòng Vì sao mà kiem_pr đọc được")
def _():
    mau = MAU_PR.read_text(encoding="utf-8").replace(
        'Agent: <công cụ hoặc "không"> · Điều khiển: N07-B · Review: N07-A', DONG_DAU_TAY)
    ma, bang = chay(mau, SUA_TEST)
    assert ma == 1 and "| Hạng mục đóng | Chưa đạt |" in bang, bang   # mẫu để trống số hạng mục
    mau = mau.replace("Đóng #\n", "Đóng #5\n", 1)
    ma, bang = chay(mau, SUA_TEST)
    assert ma == 0 and "| Cảnh báo |" in (dong(bang, "Sửa test đã có") or ""), bang
    sua = mau.replace("Sửa hoặc xoá test đã có? Vì sao:", "Sửa hoặc xoá test đã có? Vì sao: đổi tên lớp")
    ma, bang = chay(sua, SUA_TEST)
    assert ma == 0 and "| Đạt |" in (dong(bang, "Sửa test đã có") or ""), bang


# ---------------------------------------------------------------- Đóng # và PR tài liệu
MA_NGUON = [{"filename": "src/domain/don.py", "status": "modified"}]


@ca("PR thường thiếu dòng Đóng #: chưa đạt")
def _():
    ma, bang = chay(than_pr(DONG_DAU_TAY, dong=None), MA_NGUON)
    assert ma == 1 and "| Hạng mục đóng | Chưa đạt |" in bang, bang


@ca("PR thường có dòng Đóng # nhưng chưa ghi số: chưa đạt")
def _():
    ma, bang = chay(than_pr(DONG_DAU_TAY, dong="Đóng #"), MA_NGUON)
    assert ma == 1 and "| Hạng mục đóng | Chưa đạt |" in bang, bang


@ca("PR thường đóng hai hạng mục (hai dòng hoặc một dòng hai số): chưa đạt")
def _():
    for dong in ("Đóng #5\nĐóng #6", "Đóng #5, #6"):
        ma, bang = chay(than_pr(DONG_DAU_TAY, dong=dong), MA_NGUON)
        assert ma == 1 and "| Hạng mục đóng | Chưa đạt |" in bang and "#6" in bang, bang


@ca("PR thường đúng một Đóng # (chữ thường, không dấu, ghi lặp cùng số): đạt")
def _():
    for dong in ("Đóng #5", "đóng #5", "Dong #5", "Đóng #5\n\nĐóng #5"):
        ma, bang = chay(than_pr(DONG_DAU_TAY, dong=dong), MA_NGUON)
        assert ma == 0 and "| Hạng mục đóng | Đạt | Đóng #5 |" in bang, (dong, bang)


@ca("Đóng # chỉ nằm trong chú thích HTML: coi như thiếu")
def _():
    ma, bang = chay(than_pr(DONG_DAU_TAY, dong="<!-- Đóng #5 -->"), MA_NGUON)
    assert ma == 1 and "| Hạng mục đóng | Chưa đạt |" in bang, bang


@ca("PR tài liệu (bao-cao/, docs/, diagrams/, adr/, .md ở gốc) không có Đóng #: đạt")
def _():
    tep = [{"filename": f, "status": "modified"} for f in (
        "bao-cao/goi4-mo-hinh.md", "docs/dac-ta-UC-03.md", "diagrams/class.mmd", "adr/0002-xu-ly-TD-04.md",
        "README.md", "AGENTS.md")]
    ma, bang = chay(than_pr(DONG_DAU_TAY, dong=None), tep)
    assert ma == 0 and "PR tài liệu" in (dong(bang, "Loại PR") or "") and dong(bang, "Hạng mục đóng") is None, bang


@ca("PR đưa phiếu thay đổi vào kho, dùng agent, kèm log phiên phieu-dot1.md: đạt")
def _():
    tep = [{"filename": "phieu-thay-doi/dot1_N07_TD-04.md", "status": "added"},
           {"filename": "log-tac-tu/phieu-dot1.md", "status": "added"}]
    ma, bang = chay(than_pr(DONG_DAU_AGENT, dong=None), tep)
    assert ma == 0 and "| Log agent | Đạt |" in bang and "phieu-dot1.md" in bang, bang


@ca("PR tài liệu dùng agent, không có log nào: chưa đạt")
def _():
    tep = [{"filename": "phieu-thay-doi/dot2_N07_TD-09.md", "status": "added"}]
    ma, bang = chay(than_pr(DONG_DAU_AGENT, dong=None), tep)
    assert ma == 1 and "| Log agent | Chưa đạt |" in bang, bang


@ca("PR tài liệu dùng agent, có log-tac-tu/PR-<số>.md: đạt")
def _():
    tep = [{"filename": "adr/0003-xu-ly-TD-09.md", "status": "added"},
           {"filename": "log-tac-tu/PR-12.md", "status": "added"}]
    ma, bang = chay(than_pr(DONG_DAU_AGENT, dong=None), tep)
    assert ma == 0 and "| Log agent | Đạt |" in bang and "PR tài liệu" in bang, bang


@ca("PR sửa mã kèm log phiên phieu-dot1.md, không có PR-<số>.md: chưa đạt (không phải PR tài liệu)")
def _():
    tep = MA_NGUON + [{"filename": "log-tac-tu/phieu-dot1.md", "status": "added"}]
    ma, bang = chay(than_pr(DONG_DAU_AGENT), tep)
    assert ma == 1 and "| Log agent | Chưa đạt |" in bang and dong(bang, "Hạng mục đóng"), bang


@ca("PR có cả tài liệu và mã: là PR thường, cần Đóng #")
def _():
    tep = [{"filename": "docs/yeu-cau.md", "status": "modified"}] + MA_NGUON
    ma, bang = chay(than_pr(DONG_DAU_TAY, dong=None), tep)
    assert ma == 1 and "| Hạng mục đóng | Chưa đạt |" in bang, bang


@ca("Tệp .md trong thư mục khác (src/, tests/) không làm PR thành PR tài liệu")
def _():
    tep = [{"filename": "src/README.md", "status": "modified"}]
    ma, bang = chay(than_pr(DONG_DAU_TAY, dong=None), tep)
    assert ma == 1 and "| Hạng mục đóng | Chưa đạt |" in bang, bang


@ca("PR chỉ sửa THANH-VIEN.md: chưa đạt, không tính là PR tài liệu")
def _():
    tep = [{"filename": "THANH-VIEN.md", "status": "modified"}]
    ma, bang = chay(than_pr(DONG_DAU_TAY, dong=None), tep)
    assert ma == 1 and "| THANH-VIEN.md | Chưa đạt |" in bang and "PR tài liệu" not in bang, bang


@ca("Năm chuyển tiếp: PR từ nhánh kho-mau đưa kho mẫu vào, không cần Đóng #")
def _():
    tep = [{"filename": ".github/workflows/kiem-pr.yml", "status": "added"},
           {"filename": "scripts/kiem_pr.py", "status": "added"}, {"filename": ".se100/README.md", "status": "added"}]
    ma, bang = chay(than_pr(DONG_DAU_TAY, dong=None), tep, nhanh="kho-mau")
    assert ma == 0 and "PR đưa kho mẫu" in bang and dong(bang, "Hạng mục đóng") is None, bang


@ca("Cùng các tệp đó từ nhánh khác: vẫn cần Đóng #")
def _():
    tep = [{"filename": "scripts/kiem_pr.py", "status": "modified"}]
    ma, bang = chay(than_pr(DONG_DAU_TAY, dong=None), tep, nhanh="sua-kiem")
    assert ma == 1 and "| Hạng mục đóng | Chưa đạt |" in bang, bang


def main() -> None:
    hong = 0
    for ten, ham in CA:
        try:
            ham()
            print(f"  đạt   {ten}")
        except AssertionError as loi:
            hong += 1
            print(f"  HỎNG  {ten}\n{loi}")
    print(f"\n{len(CA) - hong}/{len(CA)} ca đạt")
    print("ĐẠT" if hong == 0 else "HỎNG")
    sys.exit(1 if hong else 0)


if __name__ == "__main__":
    main()