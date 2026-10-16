#!/usr/bin/env python3
"""Kiểm thân PR theo mẫu SE100. Chạy trong GitHub Actions (sự kiện pull_request).

Kiểm:
  - dòng ba thông tin `Agent: <công cụ> · Điều khiển: N07-B · Review: N07-A`;
  - mã người đúng dạng N<2 số>-<chữ>, thuộc nhóm của kho (khi biết mã nhóm);
  - người review khác người điều khiển;
  - PR thường (không phải PR tài liệu) có đúng một dòng `Đóng #<số hạng mục>`;
  - PR dùng agent (Agent khác "không") thêm hoặc sửa log-tac-tu/PR-<số PR>.md trong chính PR;
    PR tài liệu dùng agent được thay bằng log-tac-tu/phieu-dot<k>.md (PR đưa phiếu thay đổi vào kho);
  - PR không sửa THANH-VIEN.md (tệp do hệ thống đăng ký ghi);
  - cảnh báo, không chặn: PR sửa, đổi tên hoặc xoá tệp đã có trong tests/ mà dòng
    "Sửa hoặc xoá test đã có? Vì sao:" của mẫu PR để trống; PR sửa tệp của kiểm tra tự động.
PR tài liệu: mọi tệp thay đổi thuộc bao-cao/, docs/, diagrams/, adr/, phieu-thay-doi/,
log-tac-tu/phieu-dot<k>.md hoặc là tệp .md ở gốc kho (trừ THANH-VIEN.md), có thể kèm
log-tac-tu/PR-<số>.md. PR tài liệu không cần `Đóng #`.

Đọc PR từ GITHUB_EVENT_PATH. Danh sách tệp lấy qua GitHub API (GITHUB_TOKEN, GITHUB_REPOSITORY).
Chạy thử: đặt SE100_DU_LIEU_THU = thư mục có pr_files.json (mảng {"filename", "status"},
thêm "previous_filename" khi status là "renamed"). Bộ thử: python3 scripts/thu_kiem_pr.py
Ghi kết quả vào GITHUB_STEP_SUMMARY (nếu có); thoát mã 1 khi có mục chưa đạt.
Chỉ dùng thư viện chuẩn Python 3.10+.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.request

MA_NGUOI = re.compile(r"^N\d\d-[A-Z]$")
DONG_BA_THONG_TIN = re.compile(
    r"Agent\s*:\s*(?P<agent>[^\n]*?)\s*[·|•]\s*[ĐđD]i[ềe]u\s*khi[ểe]n\s*:\s*(?P<dieu_khien>[^\s·|•]*)"
    r"\s*[·|•]\s*Review\s*:\s*(?P<review>[^\s·|•]*)", re.IGNORECASE)
DONG_HANG_MUC = re.compile(r"[ĐđD][óo]ng\s*(#\s*\d+(?:\s*[,;]?\s*#\s*\d+)*)", re.IGNORECASE)
KHONG_DUNG_AGENT = {"không", "khong", "none", "no", "-"}
TEP_HE_THONG = "THANH-VIEN.md"
# Năm chuyển tiếp: PR từ nhánh này đưa tệp kho mẫu vào kho cũ, chưa có hạng mục để đóng.
NHANH_KHO_MAU = "kho-mau"
THU_MUC_TAI_LIEU = ("bao-cao/", "docs/", "diagrams/", "adr/", "phieu-thay-doi/")
LOG_PHIEU = re.compile(r"^log-tac-tu/phieu-dot\d+([_.-][^/]*)?\.md$")
# Test đã có: tệp trong thư mục này mà PR sửa, đổi tên hoặc xoá.
THU_MUC_TEST = "tests/"
TRANG_THAI_SUA = {"modified", "changed", "removed", "renamed"}
DONG_SUA_TEST = re.compile(
    r"S[ửu]a\s+ho[ặa]c\s+x(?:oá|óa|oa)\s+test\s+[đd][ãa]\s+c[óo]\s*\?\s*V[ìi]\s+sao\s*:(?P<sau>[^\n]*)",
    re.IGNORECASE)
TRA_LOI_RONG = {"", "-", "—", "…", "...", "không", "khong", "no", "none", "n/a", "chưa", "chua"}


def bo_chu_thich(van_ban: str) -> str:
    """Bỏ chú thích HTML; chuẩn hoá Unicode về NFC (chữ có dấu gõ hoặc dán từ nhiều nguồn)."""
    return unicodedata.normalize("NFC", re.sub(r"<!--.*?-->", "", van_ban or "", flags=re.S))


def phan_tich(than: str) -> dict | None:
    m = DONG_BA_THONG_TIN.search(bo_chu_thich(than))
    if not m:
        return None
    return {k: (m.group(k) or "").strip().strip("`*") for k in ("agent", "dieu_khien", "review")}


def ly_do_sua_test(than: str) -> str | None:
    """Câu trả lời cho dòng "Sửa hoặc xoá test đã có? Vì sao:"; None nếu không có dòng đó.

    Lấy phần sau dấu hai chấm; trống thì lấy các dòng ngay dưới, tới tiêu đề hoặc mục kiểm kế tiếp.
    """
    van_ban = bo_chu_thich(than)
    m = DONG_SUA_TEST.search(van_ban)
    if not m:
        return None
    phan = [m.group("sau").strip()]
    if not phan[0]:
        for dong in van_ban[m.end():].splitlines()[1:]:
            d = dong.strip()
            if d.startswith("#") or d.startswith("- [") or d.startswith("* ["):
                break
            if d:
                phan.append(d)
    return " ".join(p for p in phan if p).strip()


def test_da_co_bi_sua(ds_tep: list[dict]) -> list[str]:
    """Tệp đã có trong tests/ mà PR sửa, đổi tên hoặc xoá (tệp thêm mới không tính)."""
    kq = []
    for f in ds_tep:
        ten, cu = f.get("filename", ""), f.get("previous_filename") or ""
        if f.get("status") not in TRANG_THAI_SUA:
            continue
        goc = cu if f.get("status") == "renamed" else ten
        if goc.startswith(THU_MUC_TEST):
            kq.append(goc if goc == ten else f"{goc} → {ten}")
    return kq


def la_pr_agent(pt: dict) -> bool:
    return pt["agent"].strip().lower().rstrip(".") not in KHONG_DUNG_AGENT


def hang_muc_dong(than: str) -> list[int]:
    """Số hạng mục ghi ở các dòng `Đóng #<số>` (bỏ chú thích HTML, bỏ số lặp)."""
    kq: list[int] = []
    for m in DONG_HANG_MUC.finditer(bo_chu_thich(than)):
        for so in re.findall(r"#\s*(\d+)", m.group(1)):
            if int(so) not in kq:
                kq.append(int(so))
    return kq


def la_tep_tai_lieu(ten: str) -> bool:
    if ten == TEP_HE_THONG:
        return False
    return (ten.startswith(THU_MUC_TAI_LIEU) or bool(LOG_PHIEU.match(ten))
            or ("/" not in ten and ten.lower().endswith(".md")))


def la_pr_tai_lieu(tep: list[str] | None, so_pr: int) -> bool:
    if not tep:
        return False
    con_lai = [t for t in tep if t != f"log-tac-tu/PR-{so_pr}.md"]
    return bool(con_lai) and all(la_tep_tai_lieu(t) for t in con_lai)


def goi_api(duong: str) -> list:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    goc = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    url = f"{goc}/{duong.lstrip('/')}"
    kq: list = []
    while url:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "se100-kiem-pr",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        })
        with urllib.request.urlopen(req, timeout=60) as r:
            du_lieu = json.loads(r.read().decode("utf-8"))
            lien_ket = r.headers.get("Link", "")
        kq.extend(du_lieu if isinstance(du_lieu, list) else [du_lieu])
        m = re.search(r'<([^>]+)>;\s*rel="next"', lien_ket)
        url = m.group(1) if m else None
    return kq


def tep_cua_pr(so_pr: int, su_kien: dict) -> list[dict] | None:
    """[{filename, status}] của PR; None nếu không lấy được."""
    thu = os.environ.get("SE100_DU_LIEU_THU")
    if thu:
        duong = os.path.join(thu, "pr_files.json")
        if not os.path.exists(duong):
            return []
        with open(duong, encoding="utf-8") as f:
            return json.load(f)
    repo = os.environ.get("GITHUB_REPOSITORY")
    try:
        return goi_api(f"repos/{repo}/pulls/{so_pr}/files?per_page=100")
    except Exception as loi:  # dự phòng: git diff giữa hai commit của PR
        print(f"Không gọi được API ({loi}); thử git diff.", file=sys.stderr)
        pr = su_kien.get("pull_request", {})
        goc, dau = pr.get("base", {}).get("sha"), pr.get("head", {}).get("sha")
        try:
            ra = subprocess.run(["git", "diff", "--name-status", f"{goc}...{dau}"],
                                capture_output=True, text=True, check=True).stdout
            kq = []
            loai = {"A": "added", "D": "removed", "R": "renamed", "C": "copied"}
            for dong in ra.splitlines():
                phan = dong.split("\t")
                if len(phan) >= 2:
                    muc = {"filename": phan[-1], "status": loai.get(phan[0][:1], "modified")}
                    if muc["status"] == "renamed" and len(phan) >= 3:
                        muc["previous_filename"] = phan[1]
                    kq.append(muc)
            return kq
        except Exception:
            return None


def kiem(than: str, so_pr: int, ds_tep: list[dict] | None, repo: str = "",
         nhanh: str = "") -> list[tuple[str, bool | None, str]]:
    """Trả về [(tên kiểm, True/False/None=cảnh báo, ghi chú)]."""
    kq: list[tuple[str, bool | None, str]] = []
    tep_ca_xoa = None if ds_tep is None else [f["filename"] for f in ds_tep]
    tep = None if ds_tep is None else [f["filename"] for f in ds_tep if f.get("status") != "removed"]
    m_nhom = re.search(r"se100-(N\d\d)", repo or "", re.IGNORECASE)
    ma_nhom = m_nhom.group(1).upper() if m_nhom else None

    # 0. THANH-VIEN.md do hệ thống ghi
    if tep_ca_xoa and TEP_HE_THONG in tep_ca_xoa:
        kq.append((TEP_HE_THONG, False, "THANH-VIEN.md do hệ thống đăng ký ghi; bỏ thay đổi tệp này khỏi PR. "
                                        "Cần đổi thành viên thì báo giảng viên."))

    # 1. dòng ba thông tin
    pt = phan_tich(than)
    if pt is None:
        kq.append(("Dòng ba thông tin", False,
                   "Không thấy dòng `Agent: … · Điều khiển: Nxx-X · Review: Nxx-Y` (PR không dùng agent ghi `Agent: không`)."))
        return kq
    loi = []
    if not pt["agent"] or "<" in pt["agent"] or "…" in pt["agent"]:
        loi.append("chưa ghi tên công cụ agent (hoặc `không`)")
    for ten, ma in (("Điều khiển", pt["dieu_khien"]), ("Review", pt["review"])):
        if not MA_NGUOI.match(ma):
            loi.append(f"mã {ten} `{ma or '(trống)'}` không đúng dạng N07-A")
        elif ma_nhom and not ma.startswith(ma_nhom + "-"):
            loi.append(f"mã {ten} `{ma}` không thuộc nhóm {ma_nhom}")
    kq.append(("Dòng ba thông tin", not loi, "; ".join(loi) or
               f"Agent: {pt['agent']} · Điều khiển: {pt['dieu_khien']} · Review: {pt['review']}"))
    if MA_NGUOI.match(pt["dieu_khien"]) and MA_NGUOI.match(pt["review"]):
        khac = pt["dieu_khien"] != pt["review"]
        kq.append(("Người review khác người điều khiển", khac,
                   "" if khac else "Review trùng Điều khiển; nhờ một thành viên khác review."))

    # 2. loại PR, hạng mục đóng, log agent
    agent = la_pr_agent(pt)
    ten_log = f"log-tac-tu/PR-{so_pr}.md"
    tai_lieu = la_pr_tai_lieu(tep, so_pr)
    if nhanh == NHANH_KHO_MAU:
        kq.append(("Loại PR", True, f"PR đưa kho mẫu vào kho cũ (nhánh `{NHANH_KHO_MAU}`, năm chuyển tiếp): "
                   "không cần `Đóng #`"))
    elif tai_lieu:
        kq.append(("Loại PR", True, "PR tài liệu (chỉ sửa bao-cao/, docs/, diagrams/, adr/, phieu-thay-doi/, "
                   "log-tac-tu/phieu-dot<k>.md hoặc .md ở gốc): không cần `Đóng #`"))
    else:
        kq.append(("Loại PR", True, "PR dùng agent" if agent else "PR làm tay (`Agent: không`)"))
        dong = hang_muc_dong(than)
        if len(dong) == 1:
            kq.append(("Hạng mục đóng", True, f"Đóng #{dong[0]}"))
        elif not dong:
            kq.append(("Hạng mục đóng", False, "Thiếu dòng `Đóng #<số hạng mục>` (số của hạng mục trên tab Issues)."))
        else:
            kq.append(("Hạng mục đóng", False, "Mỗi PR ghi đúng một `Đóng #<số>`; đang có: "
                       + ", ".join(f"#{x}" for x in dong) + ". Tách PR, hoặc gộp hạng mục trên Issues."))

    if agent:
        if tep is None:
            kq.append(("Log agent", False, f"Không lấy được danh sách tệp của PR để tìm `{ten_log}`."))
        elif ten_log in tep:
            kq.append(("Log agent", True, f"Có `{ten_log}`"))
        elif tai_lieu and any(LOG_PHIEU.match(t) for t in tep):
            kq.append(("Log agent", True, "Có " + ", ".join(f"`{t}`" for t in tep if LOG_PHIEU.match(t))))
        elif tai_lieu:
            kq.append(("Log agent", False, f"PR tài liệu có dùng agent nhưng chưa thêm `{ten_log}` "
                       "hoặc `log-tac-tu/phieu-dot<k>.md` (khuôn ở `log-tac-tu/README.md`)."))
        else:
            kq.append(("Log agent", False, f"PR dùng agent nhưng chưa thêm `{ten_log}` (khuôn ở `log-tac-tu/README.md`)."))

    # 3. cảnh báo: PR sửa hoặc xoá test đã có mà không nói vì sao
    if ds_tep:
        sua = test_da_co_bi_sua(ds_tep)
        if sua:
            ly_do = ly_do_sua_test(than)
            ds = ", ".join(f"`{t}`" for t in sua[:5]) + (f" và {len(sua) - 5} tệp khác" if len(sua) > 5 else "")
            if ly_do is None or ly_do.lower().rstrip(".") in TRA_LOI_RONG:
                kq.append(("Sửa test đã có", None,
                           f"PR sửa hoặc xoá {ds} nhưng dòng `Sửa hoặc xoá test đã có? Vì sao:` "
                           "trong mô tả PR còn trống. Ghi tệp nào, vì sao; người review đọc diff của tests/ trước."))
            else:
                kq.append(("Sửa test đã có", True, f"{ds}. Vì sao: {ly_do[:200]}"))

    # 4. cảnh báo: PR sửa phần kiểm tra tự động
    if tep_ca_xoa:
        dung_kiem = [t for t in tep_ca_xoa if t.startswith(".github/workflows/kiem-") or t in (
            "scripts/kiem_pr.py", "scripts/kiem_goi.py", "scripts/kiem_moc.py")]
        if dung_kiem:
            kq.append(("Tệp kiểm tra tự động", None,
                       "PR sửa " + ", ".join(f"`{t}`" for t in dung_kiem) + "; các tệp này không được sửa."))
    return kq


def in_ket_qua(so_pr: int, kq: list[tuple[str, bool | None, str]]) -> str:
    dat = all(ok is not False for _, ok, _ in kq)
    nhan = {True: "Đạt", False: "Chưa đạt", None: "Cảnh báo"}
    ra = [f"### Kiểm PR #{so_pr}: {'ĐẠT' if dat else 'CHƯA ĐẠT'}", "",
          "| Kiểm tra | Kết quả | Ghi chú |", "|---|---|---|"]
    ra += [f"| {ten} | {nhan[ok]} | {gc.replace('|', '/')} |" for ten, ok, gc in kq]
    if not dat:
        ra += ["", "Sửa mô tả PR (Edit ở phần mô tả) hoặc đẩy thêm commit chứa log; kiểm tra tự chạy lại."]
    return "\n".join(ra) + "\n"


def main() -> None:
    duong = os.environ.get("GITHUB_EVENT_PATH")
    if not duong:
        sys.exit("Thiếu GITHUB_EVENT_PATH.")
    with open(duong, encoding="utf-8") as f:
        su_kien = json.load(f)
    pr = su_kien.get("pull_request") or {}
    so_pr = pr.get("number") or su_kien.get("number")
    kq = kiem(pr.get("body") or "", so_pr, tep_cua_pr(so_pr, su_kien), os.environ.get("GITHUB_REPOSITORY", ""),
             os.environ.get("GITHUB_HEAD_REF") or pr.get("head", {}).get("ref", ""))
    noi_dung = in_ket_qua(so_pr, kq)
    tom_tat = os.environ.get("GITHUB_STEP_SUMMARY")
    if tom_tat:
        with open(tom_tat, "a", encoding="utf-8") as f:
            f.write(noi_dung)
    print(noi_dung)
    sys.exit(0 if all(ok is not False for _, ok, _ in kq) else 1)


if __name__ == "__main__":
    main()