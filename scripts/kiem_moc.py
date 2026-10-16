#!/usr/bin/env python3
"""
Kiểm nội dung theo mốc M0–M5 — SE100.

Chạy tay:  python scripts/kiem_moc.py M3            (kiểm kho hiện tại)
           python scripts/kiem_moc.py M3 <thư mục>  (kiểm kho khác)

Kiểm gói (scripts/kiem_goi.py) gọi hàm chay_moc() cho các mốc ứng với gói:
Gói 2 = M0 + M1, Gói 3 = M2, Gói 4 = M3, Gói 5 = M4, Gói 6 = M5.

Mọi kiểm tra là tất định, không dùng AI. Đầu ra: danh sách ✅/❌ và exit code
0 nếu tất cả ✅.
"""
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
KQ = []  # (ok: bool, ten: str, chi_tiet: str)


def ghi(ok, ten, chi_tiet=""):
    KQ.append((ok, ten, chi_tiet))


# ---------- tiện ích ----------

def doc(path):
    p = GOC / path
    return p.read_text(encoding="utf-8") if p.exists() else None


def ton_tai(path, ten=None):
    ok = (GOC / path).exists()
    ghi(ok, ten or f"Tệp {path} tồn tại", "" if ok else f"không thấy {path}")
    return ok


def git(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=GOC, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return ""


def so_thanh_vien():
    """Số dòng thành viên (mã Nxx-X) trong THANH-VIEN.md; 0 nếu chưa có."""
    tv = doc("THANH-VIEN.md") or ""
    return len(set(re.findall(r"^\|\s*(N\d\d-[A-Z])\s*\|", tv, re.M)))


def ten_lop_trong_class_mmd(text):
    return set(re.findall(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)", text, re.M))


def phuong_thuc_trong_class_mmd(text):
    """{ten_lop: {ten_phuong_thuc}} — đọc các dòng dạng +ten(...) trong khối class X { }"""
    kq = {}
    for m in re.finditer(r"class\s+(\w+)\s*\{(.*?)\}", text, re.S):
        lop, than = m.group(1), m.group(2)
        kq[lop] = set(re.findall(r"[+\-#~]?\s*(\w+)\s*\(", than))
    # dạng ngoài khối: Lop : +ten()
    for lop, pt in re.findall(r"^\s*(\w+)\s*:\s*[+\-#~]?\s*(\w+)\s*\(", text, re.M):
        kq.setdefault(lop, set()).add(pt)
    return kq


def participant_trong_seq(text):
    """Mọi bên tham gia là LỚP: khai báo bằng participant, hoặc xuất hiện trong
    thông điệp mà không được khai báo là actor. Mermaid tự tạo participant từ
    thông điệp nên phải quét cả dòng thông điệp."""
    actors = set(re.findall(r"^\s*actor\s+(\w+)", text, re.M))
    ps = set(re.findall(r"^\s*participant\s+(\w+)", text, re.M))
    for nguon, dich, _ in loi_goi_trong_seq(text):
        ps.add(nguon); ps.add(dich)
    for nguon, dich in re.findall(r"^\s*(\w+)\s*-{1,2}>>?\s*(\w+)\s*:", text, re.M):
        ps.add(nguon); ps.add(dich)
    return ps - actors


def loi_goi_trong_seq(text):
    """[(nguon, dich, phuong_thuc)] từ dòng A->>B: ten(...)"""
    return re.findall(r"^\s*(\w+)\s*-{1,2}>>?\s*(\w+)\s*:\s*(?:new\s+)?(\w+)\s*\(", text, re.M)


def _kiem_so_bo(p):
    dong = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and not l.strip().startswith("%%") and not l.strip().startswith("---")]
    dau = (dong or [""])[0]
    ok = bool(re.match(r"^(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram|C4Context|C4Container|erDiagram)", dau))
    return ok, "" if ok else f"dòng đầu không phải loại sơ đồ Mermaid: '{dau[:40]}'"


def mermaid_parse_duoc(path):
    """Kiểm cú pháp Mermaid bằng mmdc nếu chạy được; nếu mmdc không có hoặc
    không mở được trình duyệt (thiếu Chromium) thì kiểm sơ bộ theo dòng đầu."""
    p = GOC / path
    if not p.exists():
        return False, "không thấy tệp"
    mmdc = os.environ.get("MMDC", "mmdc")
    try:
        subprocess.run(
            [mmdc, "-i", str(p), "-o", "/tmp/_kiem.svg", "-q"],
            check=True, capture_output=True, timeout=120,
        )
        return True, ""
    except FileNotFoundError:
        return _kiem_so_bo(p)
    except subprocess.TimeoutExpired:
        return _kiem_so_bo(p)
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"").decode(errors="ignore")
        # lỗi hạ tầng (không phải lỗi cú pháp) → không phạt sinh viên
        if re.search(r"puppeteer|chrom|browser|launch|ENOENT|libnss|libatk", err, re.I):
            return _kiem_so_bo(p)
        # lỗi cú pháp thật: lấy dòng có ích nhất
        dong = [d for d in err.splitlines() if re.search(r"Parse error|Syntax error|Expecting|Lexical", d)]
        return False, (dong[0] if dong else err.strip().splitlines()[-1] if err.strip() else "mmdc báo lỗi")[:200]


# ---------- từng mốc ----------

def kiem_M0():
    readme = doc("README.md") or ""
    # phần mô tả hệ thống: từ đầu tệp tới tiêu đề "## " đầu tiên
    dau = re.split(r"^## ", readme, maxsplit=1, flags=re.M)[0]
    dong = [d for d in dau.splitlines() if d.strip() and not d.strip().startswith(("#", "|", ">", "-", "`"))]
    ghi(len(dong) >= 5, "README có ≥ 5 dòng mô tả hệ thống (trước tiêu đề ## đầu tiên)", f"hiện {len(dong)} dòng văn xuôi")
    ghi("Xoá dòng này" not in readme, "README đã xoá hướng dẫn mẫu", "")

    can = so_thanh_vien() or 4
    tac_gia = set(a.strip().lower() for a in git("log", "--format=%ae").splitlines() if a.strip())
    ghi(len(tac_gia) >= can, f"Đủ {can} thành viên có commit (thấy {len(tac_gia)} tài khoản tác giả)",
        "" if len(tac_gia) >= can else "mỗi người phải tự commit ít nhất một lần bằng tài khoản của mình")

    ton_tai("docs/cau-hoi-khach-hang.md", "Có 3 câu hỏi cho khách hàng")
    ch = doc("docs/cau-hoi-khach-hang.md") or ""
    so_cau = len(re.findall(r"\?", ch))
    ghi(so_cau >= 3, "Ít nhất 3 câu hỏi (đếm dấu ?)", f"thấy {so_cau}")


def kiem_M1():
    yc = doc("docs/yeu-cau.md")
    if yc is None:
        ghi(False, "docs/yeu-cau.md tồn tại"); return

    # bảng NFR: các dòng bắt đầu bằng | NFR-
    nfr = [d for d in yc.splitlines() if re.match(r"^\|\s*NFR-\d+", d)]
    ghi(len(nfr) >= 3, f"Có ≥ 3 yêu cầu phi chức năng (thấy {len(nfr)})")
    # mỗi NFR phải có số + đơn vị
    don_vi = r"(ms|s|giây|phút|giờ|ngày|%|người|req|yêu cầu|MB|GB|KB|TPS|rps|/s|/giây|lần|lượt|bước|thao tác|bản ghi|dòng|đồng)"
    thieu = []
    for d in nfr:
        o = [x.strip() for x in d.strip("|").split("|")]
        noi_dung = " ".join(o[1:4])
        if not re.search(r"\d+[\d.,]*\s*" + don_vi, noi_dung, re.I):
            thieu.append(o[0] if o else d[:20])
    ghi(not thieu, "Mỗi NFR có con số kèm đơn vị",
        "" if not thieu else f"thiếu số/đơn vị ở: {', '.join(thieu)} — 'nhanh', 'ổn định' không tính")

    fr = [d for d in yc.splitlines() if re.match(r"^\|\s*FR-\d+", d)]
    ghi(len(fr) >= 6, f"Có ≥ 6 yêu cầu chức năng (thấy {len(fr)})")
    br = [d for d in yc.splitlines() if re.match(r"^\|\s*BR-\d+", d)]
    ghi(len(br) >= 1, f"Có ≥ 1 ràng buộc nghiệp vụ (thấy {len(br)})")
    tn = len(re.findall(r"^\|\s*[^|\-#]+\|[^|]+\|[^|]+\|\s*$", yc.split("## Yêu cầu chức năng")[0], re.M))
    ghi(tn >= 3 + 1, "Có ≥ 3 tác nhân", f"đếm được {max(tn-1,0)} dòng trong bảng tác nhân")


def kiem_M2():
    ok, loi = mermaid_parse_duoc("diagrams/use-case.mmd")
    ghi(ok, "diagrams/use-case.mmd parse được", loi)
    uc = doc("diagrams/use-case.mmd") or ""
    # use case dạng UC1(Tên) — loại tác nhân dạng SV([Tên]) và subgraph
    so_uc = len(re.findall(r"^\s*\w+\((?!\[)[^)]+\)\s*$", uc, re.M))
    ghi(so_uc >= 5, f"Sơ đồ use case có ≥ 5 use case (thấy {so_uc})")

    dac_ta = sorted((GOC / "docs").glob("dac-ta-UC-*.md"))
    ghi(len(dac_ta) >= 3, f"Có ≥ 3 đặc tả use case (thấy {len(dac_ta)})")
    for p in dac_ta[:3]:
        t = p.read_text(encoding="utf-8")
        ghi("Luồng thay thế" in t and "Luồng lỗi" in t, f"{p.name} có luồng thay thế và luồng lỗi")

    seqs = sorted((GOC / "diagrams").glob("seq-*.mmd"))
    ghi(len(seqs) >= 2, f"Có ≥ 2 sequence diagram (thấy {len(seqs)})")
    for p in seqs:
        ok, loi = mermaid_parse_duoc(f"diagrams/{p.name}")
        ghi(ok, f"{p.name} parse được", loi)


def doi_chieu_seq_class(lop, pt):
    """ĐỐI CHIẾU CHÉO: lớp trong sequence phải có trong class diagram."""
    seqs = sorted((GOC / "diagrams").glob("seq-*.mmd"))
    thieu_lop, thieu_pt = set(), []
    for p in seqs:
        t = p.read_text(encoding="utf-8")
        for part in participant_trong_seq(t):
            if part not in lop:
                thieu_lop.add(f"{part} ({p.name})")
        for nguon, dich, ph in loi_goi_trong_seq(t):
            if dich in lop and ph not in pt.get(dich, set()) and ph != dich:
                thieu_pt.append(f"{dich}.{ph}() ({p.name})")
    ghi(not thieu_lop, "Mọi participant trong sequence diagram đều là lớp trong class.mmd",
        "" if not thieu_lop else "không có trong sơ đồ lớp: " + ", ".join(sorted(thieu_lop)))
    ghi(not thieu_pt, "Mọi phương thức được gọi trong sequence đều tồn tại trong lớp đích",
        "" if not thieu_pt else "gọi phương thức không tồn tại: " + ", ".join(thieu_pt[:8]))


def kiem_M3():
    ok, loi = mermaid_parse_duoc("diagrams/class.mmd")
    ghi(ok, "diagrams/class.mmd parse được", loi)
    ok2, loi2 = mermaid_parse_duoc("diagrams/state.mmd")
    ghi(ok2, "diagrams/state.mmd parse được", loi2)

    cls = doc("diagrams/class.mmd") or ""
    lop = ten_lop_trong_class_mmd(cls)
    ghi(len(lop) >= 5, f"Sơ đồ lớp có ≥ 5 lớp (thấy {len(lop)})")
    pt = phuong_thuc_trong_class_mmd(cls)
    tui_du_lieu = [l for l in lop if not pt.get(l)]
    ghi(len(tui_du_lieu) <= len(lop) // 2,
        "Không quá nửa số lớp là 'túi dữ liệu' không có phương thức",
        "" if len(tui_du_lieu) <= len(lop) // 2 else f"lớp không có hành vi: {', '.join(sorted(tui_du_lieu))}")

    doi_chieu_seq_class(lop, pt)

    # ---- TRUY VẾT: mỗi lớp phải được nhắc trong ít nhất một đặc tả hoặc yêu cầu ----
    van_ban = " ".join((GOC / "docs" / f).read_text(encoding="utf-8")
                       for f in os.listdir(GOC / "docs") if f.endswith(".md")) if (GOC / "docs").exists() else ""
    mo_coi = [l for l in lop if not re.search(r"\b" + re.escape(l) + r"\b", van_ban)]
    ghi(len(mo_coi) == 0, "Mọi lớp được nhắc tới trong docs/ (truy vết về yêu cầu)",
        "" if not mo_coi else "lớp không xuất hiện trong bất kỳ đặc tả/yêu cầu nào: " + ", ".join(sorted(mo_coi)))

    ton_tai("docs/tu-danh-gia-M3.md", "Có bản tự đánh giá cohesion/coupling")


def kiem_M4():
    for f in ("diagrams/c4-context.mmd", "diagrams/c4-container.mmd"):
        ok, loi = mermaid_parse_duoc(f)
        ghi(ok, f"{f} parse được", loi)
    ton_tai("docs/du-lieu.md", "Có tài liệu thiết kế dữ liệu")

    adrs = [p for p in (GOC / "adr").glob("*.md") if not p.name.startswith("0000")]
    ghi(len(adrs) >= 1, f"Có ≥ 1 ADR ngoài mẫu (thấy {len(adrs)})")
    for p in adrs[:3]:
        t = p.read_text(encoding="utf-8")
        ghi("## Các phương án đã cân nhắc" in t and t.count("|") >= 12,
            f"{p.name} có bảng phương án đã cân nhắc (≥ 2 phương án)")

    ag = doc("AGENTS.md") or ""
    kien_truc = ag.split("## Kiến trúc")[1].split("## Kiểm thử")[0] if "## Kiến trúc" in ag else ""
    da_viet = bool(kien_truc.strip()) and "<!--" not in kien_truc
    ghi(da_viet, "AGENTS.md phần Kiến trúc đã viết (không còn comment mẫu)",
        "" if da_viet else "phần '## Kiến trúc' vẫn còn <!-- ví dụ --> — thay bằng ràng buộc thật của nhóm")
    # ràng buộc thật: dòng gạch đầu dòng có chữ "không" bên ngoài tiêu đề
    rang_buoc = [d for d in kien_truc.splitlines() if d.strip().startswith("-") and "không" in d.lower()]
    ghi(len(rang_buoc) >= 1, "AGENTS.md có ít nhất một dòng ràng buộc 'không được'",
        "" if rang_buoc else "cần ít nhất một gạch đầu dòng dạng '- Không ... từ ...'")


def kiem_M5():
    url = None
    readme = doc("README.md") or ""
    m = re.search(r"Bản chạy:\s*(https?://\S+)", readme)
    if m:
        url = m.group(1).rstrip(")")
    if url and url != "https://":
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                ghi(r.status == 200, f"URL deploy trả về 200: {url}", f"mã {r.status}")
        except Exception as e:
            ghi(False, f"URL deploy sống: {url}", str(e)[:120])
    else:
        ghi(False, "README có URL 'Bản chạy:' đã điền", "chưa điền URL")

    wf = list((GOC / ".github" / "workflows").glob("*.yml")) + list((GOC / ".github" / "workflows").glob("*.yaml"))
    co_pipeline_rieng = any(p.stem not in WORKFLOW_CUA_LOP for p in wf)
    ghi(co_pipeline_rieng, "Có workflow CI riêng của nhóm ngoài kiem-pr.yml, kiem-goi.yml",
        "" if co_pipeline_rieng else "thêm ít nhất một workflow: lint / test / build / deploy (mẫu: vi-du-ci.yml.tat)")

    # sơ đồ khớp mã: lớp trong class.mmd có trong src/, participant có trong class.mmd
    cls = doc("diagrams/class.mmd") or ""
    lop = ten_lop_trong_class_mmd(cls)
    ma = van_ban_src()
    if not lop:
        ghi(False, "Mọi lớp trong diagrams/class.mmd có trong src/", "không đọc được lớp nào trong diagrams/class.mmd")
    else:
        vang = sorted(l for l in lop if not re.search(r"\b" + re.escape(l) + r"\b", ma))
        ghi(not vang, "Mọi lớp trong diagrams/class.mmd có trong src/",
            "" if not vang else "không thấy trong mã nguồn: " + ", ".join(vang))
    doi_chieu_seq_class(lop, phuong_thuc_trong_class_mmd(cls))

    tl = doc("docs/trung-lap.md") or ""
    so_do = len(re.findall(r"\d+[.,]?\d*\s*%", tl))
    ghi(so_do >= 2, "docs/trung-lap.md có ít nhất 2 lần đo (% tuần 3 và % tuần 13)",
        "" if so_do >= 2 else f"thấy {so_do} con số % — cần đo lại bằng jscpd và ghi thêm")


WORKFLOW_CUA_LOP = {"kiem-pr", "kiem-goi", "kiem-moc"}
BO_QUA_SRC = {"node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", "target", "vendor"}


def van_ban_src():
    """Gộp nội dung các tệp văn bản trong src/ (bỏ README.md và thư mục phụ thuộc)."""
    goc = GOC / "src"
    phan = []
    if not goc.exists():
        return ""
    for duong, thu_muc, tep in os.walk(goc):
        thu_muc[:] = [d for d in thu_muc if d not in BO_QUA_SRC]
        for ten in tep:
            if ten == "README.md":
                continue
            p = Path(duong) / ten
            try:
                if p.stat().st_size > 1_000_000:
                    continue
                du = p.read_bytes()
            except OSError:
                continue
            if b"\x00" in du[:4096]:
                continue
            phan.append(du.decode("utf-8", errors="ignore"))
    return "\n".join(phan)


# ---------- chạy ----------

KIEM = {"M0": kiem_M0, "M1": kiem_M1, "M2": kiem_M2, "M3": kiem_M3, "M4": kiem_M4, "M5": kiem_M5}


def chay_moc(moc, goc=None):
    """Chạy các kiểm của một mốc, trả về [(ok, ten, chi_tiet)]. Dùng được từ kiem_goi.py."""
    global GOC, KQ
    if goc is not None:
        GOC = Path(goc).resolve()
    KQ = []
    KIEM[moc]()
    return list(KQ)


def main():
    if len(sys.argv) < 2 or sys.argv[1].strip().upper() not in KIEM:
        print("Dùng: python scripts/kiem_moc.py M0|M1|M2|M3|M4|M5 [thư mục kho]")
        sys.exit(2)
    moc = sys.argv[1].strip().upper()
    kq = chay_moc(moc, sys.argv[2] if len(sys.argv) > 2 else None)

    print(f"\n=== KIỂM MỐC {moc} ===\n")
    dat = sum(1 for ok, *_ in kq if ok)
    for ok, ten, ct in kq:
        print(("✅ " if ok else "❌ ") + ten + (f"\n     ↳ {ct}" if ct and not ok else ""))
    print(f"\n{dat}/{len(kq)} đạt.")
    if dat < len(kq):
        print("Còn mục chưa đạt. Sửa các ❌ rồi chạy lại.")
        sys.exit(1)
    print("Đạt các kiểm tự động của mốc này.")


if __name__ == "__main__":
    main()