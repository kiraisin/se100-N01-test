#!/usr/bin/env python3
"""Kiểm gói nộp SE100 (kiểm thủ tục, không chấm điểm).

Dùng:  python scripts/kiem_goi.py --goi 4 [--kho .] [--ma-nhom N07] [--issues issues.json]
       --goi nhận 2, 3, 4, 5, 6, review-cheo hoặc tên thẻ (goi-3, review-cheo).
       Không có --goi thì lấy từ SE100_GOI hoặc GITHUB_REF_NAME.

Kiểm:
  - báo cáo của gói đúng tên, không còn dòng giữ chỗ `<!-- điền: … -->`;
  - các kiểm của kiem_moc.py ứng với gói (2 = M0 + M1, 3 = M2, 4 = M3, 5 = M4, 6 = M5);
  - Gói 3–6: có ít nhất một hạng mục (Issue) gắn milestone của gói. Issues đọc qua GitHub API
    (GITHUB_TOKEN, GITHUB_REPOSITORY; trong Actions có sẵn). Chạy ở máy không có token thì mục này
    chỉ là cảnh báo. Thử với tệp: --issues <tệp JSON> (mảng Issue theo dạng GitHub API);
  - Gói 4, 5, 6: phiếu thay đổi đợt 1, 2, 3 `phieu-thay-doi/dot<k>_N<xx>_TD-xx.md`, log phiên
    `log-tac-tu/phieu-dot<k>.md` và một ADR trong `adr/` nhắc mã phiếu đó (TD-xx);
  - review-cheo: đủ bốn phần, mỗi phát hiện trỏ tới tệp, dòng hoặc PR và ghi mã người phát hiện;
  - cảnh báo (không đánh trượt): email hoặc dãy 8 chữ số giống MSSV trong tệp .md; hạng mục chưa
    gắn milestone.
Ghi kết quả vào GITHUB_STEP_SUMMARY (nếu có); thoát mã 1 khi có mục chưa đạt.
Bộ thử phần phiếu và hạng mục: python3 scripts/thu_kiem_goi.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kiem_moc  # noqa: E402
from kiem_pr import goi_api  # noqa: E402

BAO_CAO = {
    "2": "bao-cao/goi2-vong1-yeu-cau.md",
    "3": "bao-cao/goi3-dac-ta.md",
    "4": "bao-cao/goi4-mo-hinh.md",
    "5": "bao-cao/goi5-kien-truc.md",
    "6": "bao-cao/goi6-tong-ket.md",
    "review-cheo": "bao-cao/review-cheo.md",
}
MOC = {"2": ["M0", "M1"], "3": ["M2"], "4": ["M3"], "5": ["M4"], "6": ["M5"], "review-cheo": []}
MILESTONE = {"3": "Gói 3", "4": "Gói 4", "5": "Gói 5", "6": "Gói 6"}
DOT_PHIEU = {"4": 1, "5": 2, "6": 3}
MUC_BAT_BUOC = {
    "2": [("Hồi cứu vòng 1", r"^#{1,3}\s.*h[ồo]i\s*c[ứu]u\s*v[òo]ng\s*1")],
    "5": [("Trả lời review chéo", r"^#{1,3}\s.*tr[ảa]\s*l[ờo]i.*review\s*ch[ée]o")],
    "review-cheo": [
        ("1. Phạm vi đã đọc", r"^##\s.*ph[ạa]m\s*vi"),
        ("2. Ba phát hiện", r"^##\s.*ph[áa]t\s*hi[ệe]n"),
        ("3. Một điều làm tốt", r"^##\s.*l[àa]m\s*t[ốo]t"),
        ("4. Đề xuất", r"^##\s.*[đd][ềe]\s*xu[ấa]t"),
    ],
}
TEN_GOI = {"2": "Gói 2 · Vòng 1 và yêu cầu", "3": "Gói 3 · Use case và đặc tả", "4": "Gói 4 · Mô hình miền",
           "5": "Gói 5 · Kiến trúc và dữ liệu", "6": "Gói 6 · Bàn giao và tổng kết",
           "review-cheo": "Báo cáo review chéo"}

GIU_CHO = re.compile(r"<!--\s*điền\s*:", re.IGNORECASE)
MA_NGUOI = re.compile(r"\bN\d\d-[A-Z]\b")
# trỏ tới tệp (có đuôi, có thể kèm :dòng), PR (#12, PR 12), dòng (dòng 40) hoặc commit
TRO_TOI = re.compile(r"[\w./-]+\.[A-Za-z]{1,6}(?!\w)(?::\d+)?|\bPR\s*#?\d+|#\d+\b|\bd[òo]ng\s*\d+|\b[0-9a-f]{7,40}\b",
                     re.IGNORECASE)
MSSV = re.compile(r"(?<![\w,])(?<!\d\.)2\d{7}(?![\w,]|[.,]\d)")
NGAY_8_SO = re.compile(r"^20[2-3]\d(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])$")
TIEN_SAU = re.compile(r"^\s*(?:đ|đồng|vnd|vnđ|triệu|tr)\b", re.IGNORECASE)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
EMAIL_BO_QUA = re.compile(r"noreply|@example\.(com|org|net)$|^git@github\.com$", re.IGNORECASE)
BO_QUA_THU_MUC = {".git", ".github", ".se100", "scripts", "node_modules", ".venv", "venv", "__pycache__",
                  "dist", "build", ".next", "target", "vendor"}


def chuan_goi(g: str | None) -> str:
    g = (g or "").strip().lower()
    if g.startswith("refs/tags/"):
        g = g[len("refs/tags/"):]
    if g in ("review-cheo", "review"):
        return "review-cheo"
    m = re.fullmatch(r"(?:goi-?)?([2-6])", g)
    if not m:
        sys.exit(f"Không nhận ra gói: {g!r}. Dùng --goi 2..6 hoặc review-cheo.")
    return m.group(1)


def doc(kho: str, tep: str) -> str | None:
    try:
        with open(os.path.join(kho, tep), encoding="utf-8") as f:
            return f.read()
    except (FileNotFoundError, UnicodeDecodeError, IsADirectoryError):
        return None


def bo_chu_thich(van_ban: str) -> str:
    return re.sub(r"<!--.*?-->", "", van_ban or "", flags=re.S)


def kiem_bao_cao(kho: str, tep: str) -> tuple[bool, str]:
    nd = doc(kho, tep)
    if nd is None:
        return False, f"Không có `{tep}` (tên tệp phải đúng như vậy)."
    so = len(GIU_CHO.findall(nd))
    if so:
        return False, f"`{tep}` còn {so} dòng giữ chỗ `<!-- điền: … -->`; viết xong mục nào thì xoá dòng đó."
    so_tu = len(bo_chu_thich(nd).split())
    if so_tu < 50:
        return False, f"`{tep}` gần như trống ({so_tu} từ)."
    return True, f"`{tep}` đã điền ({so_tu} từ)."


def tach_muc(nd: str, muc: str) -> str:
    """Nội dung từ tiêu đề khớp `muc` tới tiêu đề cùng cấp hoặc cao hơn kế tiếp."""
    dong = nd.splitlines()
    for i, d in enumerate(dong):
        m = re.match(r"^(#+)\s", d)
        if m and re.search(muc, d, re.IGNORECASE):
            cap = len(m.group(1))
            ra = []
            for d2 in dong[i + 1:]:
                m2 = re.match(r"^(#+)\s", d2)
                if m2 and len(m2.group(1)) <= cap:
                    break
                ra.append(d2)
            return "\n".join(ra)
    return ""


def kiem_review_cheo(nd: str) -> list[tuple[str, bool | None, str]]:
    kq = []
    phat_hien = tach_muc(nd, r"^##\s.*ph[áa]t\s*hi[ệe]n")
    khoi = re.split(r"^###\s.*$", phat_hien, flags=re.M)[1:]
    khoi = [bo_chu_thich(k).strip() for k in khoi]
    khoi = [k for k in khoi if k]
    kq.append(("Review chéo: ba phát hiện", len(khoi) >= 3,
               f"thấy {len(khoi)} phát hiện có nội dung (mỗi phát hiện một tiêu đề `### Phát hiện k`)"))
    for i, k in enumerate(khoi, 1):
        loi = []
        if not TRO_TOI.search(k):
            loi.append("chưa trỏ tới tệp, dòng hoặc PR cụ thể (ví dụ `src/don_hang.py:42`, `PR #12`)")
        if not MA_NGUOI.search(k):
            loi.append("chưa ghi mã người phát hiện (ví dụ N08-C)")
        kq.append((f"Review chéo: phát hiện {i}", not loi, "; ".join(loi) or "có chỗ trỏ tới và mã người phát hiện"))
    return kq


def quet_rieng_tu(kho: str) -> tuple[list[str], list[str]]:
    """Quét các tệp .md: trả về (chỗ có email, chỗ có dãy giống MSSV)."""
    gap_email: list[str] = []
    gap_mssv: list[str] = []
    for goc, thu_muc, tep in os.walk(kho):
        thu_muc[:] = [d for d in thu_muc if d not in BO_QUA_THU_MUC]
        for ten in tep:
            if not ten.lower().endswith(".md"):
                continue
            duong = os.path.join(goc, ten)
            try:
                with open(duong, encoding="utf-8", errors="ignore") as f:
                    nd = f.read()
            except OSError:
                continue
            tuong_doi = os.path.relpath(duong, kho)
            for so_dong, dong in enumerate(nd.splitlines(), 1):
                for m in MSSV.finditer(dong):
                    if not NGAY_8_SO.match(m.group(0)) and not TIEN_SAU.match(dong[m.end():]):
                        gap_mssv.append(f"`{tuong_doi}:{so_dong}`")
                for m in EMAIL.finditer(dong):
                    if not EMAIL_BO_QUA.search(m.group(0)):
                        gap_email.append(f"`{tuong_doi}:{so_dong}`")
    return gap_email, gap_mssv


def gop(ds: list[str], toi_da: int = 15) -> str:
    return ", ".join(ds[:toi_da]) + (f" … và {len(ds) - toi_da} chỗ khác" if len(ds) > toi_da else "")


def chuan(van_ban: str) -> str:
    return unicodedata.normalize("NFC", van_ban or "").strip().casefold()


def repo_tu_git(kho: str) -> str | None:
    """owner/tên kho từ remote origin (github.com), None nếu không đọc được."""
    try:
        url = subprocess.run(["git", "-C", kho, "remote", "get-url", "origin"],
                             capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$", url)
    return m.group(1) if m else None


def lay_issues(kho: str, tep: str | None = None) -> tuple[list | None, str]:
    """(danh sách Issue không gồm PR, ghi chú). None khi không đọc được; ghi chú nói vì sao."""
    if tep:
        try:
            with open(tep, encoding="utf-8") as f:
                ds = json.load(f)
        except (OSError, ValueError) as loi:
            return None, f"Không đọc được `{tep}` ({loi})."
    else:
        repo = os.environ.get("GITHUB_REPOSITORY") or repo_tu_git(kho)
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not repo or not token:
            return None, ("Chạy ở máy, không có token nên chưa đọc được Issues. "
                          "Chạy kiem-goi trên Actions để kiểm mục này.")
        try:
            ds = goi_api(f"repos/{repo}/issues?state=all&per_page=100")
        except Exception as loi:
            return None, f"Không đọc được Issues qua GitHub API ({loi}). Chạy lại kiem-goi sau ít phút."
    return [i for i in ds if isinstance(i, dict) and "pull_request" not in i], ""


def kiem_hang_muc(goi: str, issues: list | None, ghi_chu: str = "") -> list[tuple[str, str, bool | None, str]]:
    """Gói 3–6: ít nhất một hạng mục gắn milestone của gói; cảnh báo hạng mục chưa gắn milestone."""
    if goi not in MILESTONE:
        return []
    ten = MILESTONE[goi]
    muc = f"Có hạng mục gắn milestone {ten}"
    if issues is None:
        return [("Issues", muc, None, ghi_chu or "Chưa đọc được Issues.")]
    co = [i for i in issues if chuan((i.get("milestone") or {}).get("title", "")) == chuan(ten)]
    kq: list[tuple[str, str, bool | None, str]] = [
        ("Issues", muc, bool(co),
         f"{len(co)} hạng mục: " + ", ".join(f"#{i.get('number')}" for i in co[:15]) + (" …" if len(co) > 15 else "")
         if co else f"Chưa có hạng mục nào gắn milestone `{ten}` (tab Issues → hạng mục → Milestone).")]
    khong_ms = [f"#{i.get('number')}" for i in issues if not i.get("milestone")]
    if khong_ms:
        kq.append(("Issues", "Hạng mục chưa gắn milestone", None,
                   ", ".join(khong_ms[:30]) + (" …" if len(khong_ms) > 30 else "")))
    return kq


def ds_tep(kho: str, thu_muc: str) -> list[str]:
    duong = os.path.join(kho, thu_muc)
    return sorted(os.listdir(duong)) if os.path.isdir(duong) else []


def kiem_phieu(kho: str, goi: str, ma_nhom: str | None) -> list[tuple[str, str, bool | None, str]]:
    """Gói 4, 5, 6: phiếu thay đổi của đợt 1, 2, 3, log phiên và ADR nhắc mã phiếu."""
    if goi not in DOT_PHIEU:
        return []
    k = DOT_PHIEU[goi]
    nhom = ma_nhom or r"N\d\d"
    mau = re.compile(rf"^dot{k}_{nhom}_(TD-\d\d)\.md$")
    phieu = [(t, mau.match(t).group(1)) for t in ds_tep(kho, "phieu-thay-doi") if mau.match(t)]
    kq: list[tuple[str, str, bool | None, str]] = [
        ("Phiếu thay đổi", f"Phiếu đợt {k}", bool(phieu),
         ", ".join(f"`phieu-thay-doi/{t}`" for t, _ in phieu) if phieu else
         f"Không có `phieu-thay-doi/dot{k}_{ma_nhom or 'Nxx'}_TD-xx.md`. Chạy agent mô phỏng thay đổi "
         f"(`.se100/01_mo_phong_thay_doi.md`) với mã đợt {k} rồi đưa phiếu vào kho qua PR tài liệu.")]
    log = [t for t in ds_tep(kho, "log-tac-tu") if re.match(rf"^phieu-dot{k}([_.-].*)?\.md$", t)]
    kq.append(("Phiếu thay đổi", f"Log phiên tạo phiếu đợt {k}", bool(log),
               ", ".join(f"`log-tac-tu/{t}`" for t in log) or f"Không có `log-tac-tu/phieu-dot{k}.md`."))
    if not phieu:
        kq.append(("Phiếu thay đổi", f"ADR xử lý phiếu đợt {k}", False, "Chưa có phiếu nên chưa tìm được ADR."))
        return kq
    adr = [t for t in ds_tep(kho, "adr") if t.lower().endswith(".md") and not t.startswith("0000")]
    noi_dung = {t: t + "\n" + bo_chu_thich(doc(kho, f"adr/{t}") or "") for t in adr}
    for _, ma in phieu:
        co = [t for t, nd in noi_dung.items() if re.search(rf"(?<![A-Za-z0-9]){ma}(?!\d)", nd)]
        kq.append(("Phiếu thay đổi", f"ADR xử lý {ma}", bool(co),
                   ", ".join(f"`adr/{t}`" for t in co) if co else
                   f"Không có ADR nào trong `adr/` nhắc `{ma}`. Viết `adr/NNNN-xu-ly-{ma}.md` theo khuôn "
                   "`adr/0000-mau-xu-ly-phieu.md`."))
    return kq


def kiem_goi(kho: str, goi: str, ma_nhom: str | None = None, issues: list | None = None,
             ghi_chu_issues: str = "") -> list[tuple[str, str, bool | None, str]]:
    """Trả về [(nhóm, tên kiểm, True/False/None=cảnh báo, ghi chú)]."""
    kq: list[tuple[str, str, bool | None, str]] = []
    tep = BAO_CAO[goi]

    ok, gc = kiem_bao_cao(kho, tep)
    kq.append(("Báo cáo", "Báo cáo của gói", ok, gc))
    nd = doc(kho, tep) or ""
    for ten, mau in MUC_BAT_BUOC.get(goi, []):
        co = bool(re.search(mau, nd, re.IGNORECASE | re.M))
        kq.append(("Báo cáo", f"Có mục “{ten}”", co, "" if co else f"Không thấy tiêu đề mục “{ten}” trong `{tep}`."))
    if goi == "review-cheo" and nd:
        kq += [("Báo cáo", t, o, g) for t, o, g in kiem_review_cheo(nd)]

    if goi == "2":
        co = doc(kho, "docs/phong-van.md") is not None
        kq.append(("Tệp của gói", "docs/phong-van.md", True if co else None,
                   "Có `docs/phong-van.md`." if co else "Chưa có ghi chép phỏng vấn người dùng thật `docs/phong-van.md`."))

    kq += kiem_hang_muc(goi, issues, ghi_chu_issues)
    kq += kiem_phieu(kho, goi, ma_nhom)

    for moc in MOC[goi]:
        for ok, ten, ct in kiem_moc.chay_moc(moc, kho):
            kq.append((f"Kiểm {moc}", ten, bool(ok), ct if not ok else ""))

    gap_email, gap_mssv = quet_rieng_tu(kho)
    kq.append(("Bút danh", "Không có email trong tệp .md", None if gap_email else True,
               ("Có địa chỉ email ở " + gop(gap_email) + ". Thay bằng mã thành viên.") if gap_email else "Không thấy."))
    kq.append(("Bút danh", "Không có dãy số giống MSSV trong tệp .md", None if gap_mssv else True,
               ("Có dãy 8 chữ số ở " + gop(gap_mssv) + ". Nếu là MSSV thì thay bằng mã thành viên; số khác thì bỏ qua.")
               if gap_mssv else "Không thấy."))
    return kq


def in_ket_qua(goi: str, kq: list[tuple[str, str, bool | None, str]], ma_nhom: str | None) -> str:
    dat = all(ok is not False for _, _, ok, _ in kq)
    so_truot = sum(1 for _, _, ok, _ in kq if ok is False)
    so_canh_bao = sum(1 for _, _, ok, _ in kq if ok is None)
    nhan = {True: "Đạt", False: "Chưa đạt", None: "Cảnh báo"}
    ra = [f"## Kiểm {TEN_GOI[goi]}{' · ' + ma_nhom if ma_nhom else ''}: {'ĐẠT' if dat else 'CÒN MỤC CHƯA ĐẠT'}", "",
          f"{len(kq)} mục kiểm · {so_truot} chưa đạt · {so_canh_bao} cảnh báo. "
          "Đây là kiểm thủ tục, không phải điểm.", "",
          "| Nhóm kiểm | Kiểm tra | Kết quả | Ghi chú |", "|---|---|---|---|"]
    ra += [f"| {n} | {t} | {nhan[ok]} | {g.replace('|', '/').replace(chr(10), ' ')} |" for n, t, ok, g in kq]
    ra.append("")
    if not dat:
        ra.append("Sửa các mục **Chưa đạt** qua PR rồi chạy lại (Actions → kiem-goi → Run workflow). "
                  "Thẻ đã đẩy vẫn được ghi nhận là đã nộp; thẻ không xoá hay dời được.")
    if so_canh_bao:
        ra.append("Mục **Cảnh báo** không làm gói trượt nhưng nên xem lại.")
    return "\n".join(ra) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Kiểm gói nộp SE100.")
    ap.add_argument("--goi", default=os.environ.get("SE100_GOI") or os.environ.get("GITHUB_REF_NAME"))
    ap.add_argument("--kho", default=".")
    ap.add_argument("--ma-nhom", default=None, help="mã nhóm N07; mặc định đọc từ tên kho se100-N07")
    ap.add_argument("--issues", default=None, help="tệp JSON danh sách Issue thay cho GitHub API (để thử)")
    a = ap.parse_args()
    goi = chuan_goi(a.goi)
    kho = os.path.abspath(a.kho)
    m = re.search(r"se100-(N\d\d)", os.environ.get("GITHUB_REPOSITORY") or repo_tu_git(kho) or "", re.IGNORECASE)
    ma_nhom = (a.ma_nhom or (m.group(1) if m else "")).upper() or None

    issues, ghi_chu = lay_issues(kho, a.issues) if goi in MILESTONE else (None, "")
    kq = kiem_goi(kho, goi, ma_nhom, issues, ghi_chu)
    noi_dung = in_ket_qua(goi, kq, ma_nhom)
    tom_tat = os.environ.get("GITHUB_STEP_SUMMARY")
    if tom_tat:
        with open(tom_tat, "a", encoding="utf-8") as f:
            f.write(noi_dung)
    print(noi_dung)
    sys.exit(0 if all(ok is not False for _, _, ok, _ in kq) else 1)


if __name__ == "__main__":
    main()