#!/usr/bin/env python3
"""Bộ thử cho phần hạng mục (Issues) và phiếu thay đổi của kiem_goi.py, chạy trên dữ liệu giả.

Dùng khi sửa kiem_goi.py. Nhóm không cần chạy tệp này.
    python3 scripts/thu_kiem_goi.py          (in ĐẠT ở cuối nếu mọi ca đạt)

Mỗi ca dựng một kho giả trong thư mục tạm (phieu-thay-doi/, log-tac-tu/, adr/) và một danh sách
Issue giả, gọi hàm của kiem_goi.py hoặc chạy kiem_goi.py như trong Actions. Không gọi GitHub.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

THU_MUC = Path(__file__).resolve().parent
sys.path.insert(0, str(THU_MUC))
import kiem_goi  # noqa: E402

KIEM_GOI = THU_MUC / "kiem_goi.py"
CA: list[tuple[str, object]] = []


def ca(ten):
    def boc(ham):
        CA.append((ten, ham))
        return ham
    return boc


def kho_gia(tep: dict[str, str]) -> tempfile.TemporaryDirectory:
    tm = tempfile.TemporaryDirectory()
    for duong, nd in tep.items():
        p = Path(tm.name) / duong
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(nd, encoding="utf-8")
    return tm


def tim(kq, ten: str):
    """(ok, ghi chú) của mục có tên `ten`; None nếu không có."""
    for _, t, ok, gc in kq:
        if t == ten:
            return ok, gc
    return None


ADR_TD04 = "# ADR-0002 — Xử lý TD-04\n\n## Bảng tác động\n\nLớp LuotDat, Phong.\n"
DU_DOT1 = {
    "phieu-thay-doi/dot1_N07_TD-04.md": "# Phiếu TD-04\n",
    "log-tac-tu/phieu-dot1.md": "# Log phiên\n",
    "adr/0002-xu-ly-TD-04.md": ADR_TD04,
}


def issue(so: int, milestone: str | None, pr: bool = False) -> dict:
    d = {"number": so, "title": f"HM: việc {so}", "milestone": {"title": milestone} if milestone else None}
    if pr:
        d["pull_request"] = {"url": "x"}
    return d


# ---------------------------------------------------------------- phiếu thay đổi
@ca("Gói 4 đủ phiếu đợt 1, log phiên, ADR nhắc mã phiếu: đạt")
def _():
    with kho_gia(DU_DOT1) as k:
        kq = kiem_goi.kiem_phieu(k, "4", "N07")
    assert tim(kq, "Phiếu đợt 1")[0] is True, kq
    assert tim(kq, "Log phiên tạo phiếu đợt 1")[0] is True, kq
    ok, gc = tim(kq, "ADR xử lý TD-04")
    assert ok is True and "0002-xu-ly-TD-04.md" in gc, kq


@ca("Gói 4 không có phiếu: phiếu, log, ADR đều chưa đạt")
def _():
    with kho_gia({"adr/0001-chon-csdl.md": "# ADR-0001\n"}) as k:
        kq = kiem_goi.kiem_phieu(k, "4", "N07")
    assert [x[2] for x in kq] == [False, False, False], kq
    assert "dot1_N07_TD-xx.md" in tim(kq, "Phiếu đợt 1")[1], kq


@ca("Phiếu của đợt khác hoặc nhóm khác không tính")
def _():
    with kho_gia({"phieu-thay-doi/dot2_N07_TD-09.md": "x", "phieu-thay-doi/dot1_N08_TD-03.md": "x",
                  "log-tac-tu/phieu-dot2.md": "x"}) as k:
        kq = kiem_goi.kiem_phieu(k, "4", "N07")
    assert tim(kq, "Phiếu đợt 1")[0] is False and tim(kq, "Log phiên tạo phiếu đợt 1")[0] is False, kq


@ca("Không biết mã nhóm (chạy ở máy): nhận phiếu của bất kỳ mã nhóm nào")
def _():
    with kho_gia(DU_DOT1) as k:
        kq = kiem_goi.kiem_phieu(k, "4", None)
    assert tim(kq, "Phiếu đợt 1")[0] is True and tim(kq, "ADR xử lý TD-04")[0] is True, kq


@ca("ADR không nhắc mã phiếu, hoặc chỉ nhắc trong chú thích HTML, hoặc là khuôn 0000: chưa đạt")
def _():
    du = {k: v for k, v in DU_DOT1.items() if not k.startswith("adr/")}
    du["adr/0002-xu-ly-phieu-dot1.md"] = "# ADR-0002\n<!-- TD-04 -->\nXử lý phiếu đợt 1.\n"
    du["adr/0000-mau-xu-ly-phieu.md"] = "# Khuôn, ví dụ TD-04\n"
    du["adr/0003-xu-ly-TD-14.md"] = "# ADR-0003 — TD-14\n"
    with kho_gia(du) as k:
        kq = kiem_goi.kiem_phieu(k, "4", "N07")
    assert tim(kq, "ADR xử lý TD-04")[0] is False, kq


@ca("ADR nhắc mã phiếu trong tên tệp hoặc trong nội dung đều được")
def _():
    du = {k: v for k, v in DU_DOT1.items() if not k.startswith("adr/")}
    du["adr/0005-tach-thong-bao.md"] = "# ADR-0005 — Tách phần thông báo\n\nPhiếu: phieu-thay-doi/dot1_N07_TD-04.md\n"
    with kho_gia(du) as k:
        kq = kiem_goi.kiem_phieu(k, "4", "N07")
    assert tim(kq, "ADR xử lý TD-04")[0] is True, kq
    du = {k: v for k, v in DU_DOT1.items() if not k.startswith("adr/")}
    du["adr/0005-xu-ly-TD-04.md"] = "# ADR-0005\n"
    with kho_gia(du) as k:
        kq = kiem_goi.kiem_phieu(k, "4", "N07")
    assert tim(kq, "ADR xử lý TD-04")[0] is True, kq


@ca("Gói 5 kiểm đợt 2, Gói 6 kiểm đợt 3; log có hậu tố (phieu-dot3-lan2.md) vẫn nhận")
def _():
    with kho_gia({"phieu-thay-doi/dot2_N07_TD-09.md": "x", "log-tac-tu/phieu-dot2.md": "x",
                  "adr/0004-xu-ly-TD-09.md": "TD-09"}) as k:
        kq = kiem_goi.kiem_phieu(k, "5", "N07")
    assert all(x[2] is True for x in kq) and tim(kq, "ADR xử lý TD-09"), kq
    with kho_gia({"phieu-thay-doi/dot3_N07_TD-13.md": "x", "log-tac-tu/phieu-dot3-lan2.md": "x",
                  "adr/0006-xu-ly-TD-13.md": "TD-13"}) as k:
        kq = kiem_goi.kiem_phieu(k, "6", "N07")
    assert all(x[2] is True for x in kq) and tim(kq, "Log phiên tạo phiếu đợt 3"), kq


@ca("Gói 2, 3 và review chéo không kiểm phiếu")
def _():
    with kho_gia({}) as k:
        assert kiem_goi.kiem_phieu(k, "2", "N07") == []
        assert kiem_goi.kiem_phieu(k, "3", "N07") == []
        assert kiem_goi.kiem_phieu(k, "review-cheo", "N07") == []


# ---------------------------------------------------------------- hạng mục trên Issues
@ca("Gói 3 có hạng mục gắn milestone Gói 3: đạt; PR trong danh sách không tính là hạng mục")
def _():
    ds = [issue(1, "Gói 3"), issue(2, "Gói 4"), issue(3, "Gói 3", pr=True)]
    ds = [i for i in ds if "pull_request" not in i]
    ok, gc = tim(kiem_goi.kiem_hang_muc("3", ds), "Có hạng mục gắn milestone Gói 3")
    assert ok is True and "#1" in gc and "#3" not in gc, gc


@ca("Gói 4 không có hạng mục nào gắn milestone Gói 4: chưa đạt")
def _():
    ok, gc = tim(kiem_goi.kiem_hang_muc("4", [issue(1, "Gói 3")]), "Có hạng mục gắn milestone Gói 4")
    assert ok is False and "Gói 4" in gc, gc


@ca("Hạng mục chưa gắn milestone: cảnh báo, không trượt")
def _():
    kq = kiem_goi.kiem_hang_muc("5", [issue(1, "Gói 5"), issue(7, None)])
    assert tim(kq, "Có hạng mục gắn milestone Gói 5")[0] is True
    ok, gc = tim(kq, "Hạng mục chưa gắn milestone")
    assert ok is None and "#7" in gc, kq


@ca("Không đọc được Issues: chỉ cảnh báo")
def _():
    ok, gc = tim(kiem_goi.kiem_hang_muc("6", None, "không có token"), "Có hạng mục gắn milestone Gói 6")
    assert ok is None and "token" in gc


@ca("Gói 2 và review chéo không kiểm Issues")
def _():
    assert kiem_goi.kiem_hang_muc("2", []) == [] and kiem_goi.kiem_hang_muc("review-cheo", []) == []


@ca("lay_issues: không có token thì trả None kèm lý do; có tệp thì đọc tệp, bỏ PR")
def _():
    with kho_gia({}) as k:
        env = {x: os.environ.pop(x) for x in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_REPOSITORY") if x in os.environ}
        try:
            ds, gc = kiem_goi.lay_issues(k)
            assert ds is None and "token" in gc, gc
            p = Path(k) / "issues.json"
            p.write_text(json.dumps([issue(1, "Gói 3"), issue(2, None, pr=True)]), encoding="utf-8")
            ds, gc = kiem_goi.lay_issues(k, str(p))
            assert [i["number"] for i in ds] == [1] and gc == "", ds
        finally:
            os.environ.update(env)


# ---------------------------------------------------------------- chạy cả kiem_goi.py
def chay(goi: str, tep: dict[str, str], issues: list | None) -> tuple[int, str]:
    with kho_gia(tep) as k:
        lenh = [sys.executable, str(KIEM_GOI), "--goi", goi, "--kho", k]
        if issues is not None:
            (Path(k) / "_issues.json").write_text(json.dumps(issues), encoding="utf-8")
            lenh += ["--issues", str(Path(k) / "_issues.json")]
        env = dict(os.environ, GITHUB_REPOSITORY="uit-se100-2026-hk1/se100-N07")
        for x in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_STEP_SUMMARY"):
            env.pop(x, None)
        ra = subprocess.run(lenh, env=env, capture_output=True, text=True)
        return ra.returncode, ra.stdout + ra.stderr


def dong(bang: str, ten: str) -> str:
    return next((d for d in bang.splitlines() if f"| {ten} |" in d), "")


@ca("kiem_goi.py Gói 4 với tệp Issues: có dòng hạng mục và ba dòng phiếu, đúng mã nhóm từ tên kho")
def _():
    ma, bang = chay("4", DU_DOT1, [issue(3, "Gói 4")])
    assert "| Đạt |" in dong(bang, "Có hạng mục gắn milestone Gói 4"), bang
    assert "| Đạt |" in dong(bang, "Phiếu đợt 1") and "dot1_N07_TD-04" in dong(bang, "Phiếu đợt 1"), bang
    assert "| Đạt |" in dong(bang, "ADR xử lý TD-04"), bang


@ca("kiem_goi.py Gói 4 chạy ở máy không có token: hạng mục là cảnh báo, không có dòng tac-dong")
def _():
    ma, bang = chay("4", DU_DOT1, None)
    assert "| Cảnh báo |" in dong(bang, "Có hạng mục gắn milestone Gói 4"), bang
    assert "tac-dong" not in bang, bang


@ca("kiem_goi.py Gói 5 không còn đòi bảng tác động ba yêu cầu chung")
def _():
    ma, bang = chay("5", {}, [])
    assert "tac-dong" not in bang and dong(bang, "Phiếu đợt 2"), bang


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