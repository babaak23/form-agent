import io, zipfile, json
from datetime import datetime
import pandas as pd
import fitz  # PyMuPDF

def is_valid_npi(s: str) -> bool:
    s = str(s).strip()
    return s.isdigit() and len(s) == 10

def is_valid_medicaid(s: str) -> bool:
    s = str(s).strip()
    return s.isdigit() and 6 <= len(s) <= 12

def is_valid_date(s: str) -> bool:
    try:
        datetime.strptime(str(s), "%Y-%m-%d")
        return True
    except Exception:
        return False

def normalize_phone(s: str) -> str:
    digits = "".join(ch for ch in str(s) if ch.isdigit())
    if len(digits) == 10:
        return f"({digits[0:3]})-{digits[3:6]}-{digits[6:10]}"
    return str(s)

def run_cover_mode(excel_bytes: bytes, form_bytes: bytes):
    df = pd.read_excel(io.BytesIO(excel_bytes))
    base_form = fitz.open(stream=form_bytes, filetype="pdf")
    output = io.BytesIO()
    zf = zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED)
    log_rows = []

    for idx, row in df.iterrows():
        first = str(row.get("First Name","")).strip()
        last = str(row.get("Last Name","")).strip()
        npi = str(row.get("NPI Number","")).strip()
        medicaid = str(row.get("Medicaid Number","")).strip()
        date_str = str(row.get("Date (YYYY-MM-DD)","")).strip()
        phone = normalize_phone(row.get("Phone Number",""))

        reasons = []
        if not first: reasons.append("Missing first name")
        if not last: reasons.append("Missing last name")
        if not is_valid_npi(npi): reasons.append("NPI must be 10 digits")
        if not is_valid_medicaid(medicaid): reasons.append("Medicaid # must be 6-12 digits")
        if not is_valid_date(date_str): reasons.append("Date must be YYYY-MM-DD")

        file_stub = f"{last}_{first}_{date_str}_ETIN".replace(" ", "_")

        if reasons:
            status = "fail"
        else:
            status = "ready"
            doc = fitz.open()
            page = doc.new_page(width=612, height=792)
            page.insert_text((72,72), "NYS Medicaid ETIN / Notary Packet - Cover Sheet", fontsize=16)
            y=120
            for label, value in [
                ("Provider Name", f"{first} {last}"),
                ("NPI Number", npi),
                ("Medicaid Number", medicaid),
                ("Date (YYYY-MM-DD)", date_str),
                ("Phone Number", str(phone)),
            ]:
                page.insert_text((72,y), f"{label}:", fontsize=12)
                page.insert_text((250,y), str(value), fontsize=12)
                y+=26
            page.insert_text((72,y+12), "Following pages: Original packet for signature & notarization.", fontsize=10)
            doc.insert_pdf(base_form)
            buf = io.BytesIO(); doc.save(buf); doc.close()
            zf.writestr(f"{file_stub}.pdf", buf.getvalue())

        log_rows.append({
            "row_index": idx, "first_name": first, "last_name": last, "npi": npi,
            "medicaid_number": medicaid, "date": date_str, "phone": phone,
            "status": status, "reasons": "; ".join(reasons)
        })

    log_df = pd.DataFrame(log_rows); s = io.StringIO()
    log_df.to_csv(s, index=False); zf.writestr("run_log.csv", s.getvalue())
    zf.close(); output.seek(0); return output.getvalue()

def run_overlay_mode(excel_bytes: bytes, form_bytes: bytes, fmap_bytes: bytes):
    df = pd.read_excel(io.BytesIO(excel_bytes))
    base_form = fitz.open(stream=form_bytes, filetype="pdf")
    fmap = json.loads(fmap_bytes.decode("utf-8"))
    output = io.BytesIO()
    zf = zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED)
    log_rows = []

    for idx, row in df.iterrows():
        first = str(row.get("First Name","")).strip()
        last = str(row.get("Last Name","")).strip()
        npi = str(row.get("NPI Number","")).strip()
        medicaid = str(row.get("Medicaid Number","")).strip()
        date_str = str(row.get("Date (YYYY-MM-DD)","")).strip()
        phone = normalize_phone(row.get("Phone Number",""))

        reasons = []
        if not first: reasons.append("Missing first name")
        if not last: reasons.append("Missing last name")
        if not is_valid_npi(npi): reasons.append("NPI must be 10 digits")
        if not is_valid_medicaid(medicaid): reasons.append("Medicaid # must be 6-12 digits")
        if not is_valid_date(date_str): reasons.append("Date must be YYYY-MM-DD")

        file_stub = f"{last}_{first}_{date_str}_ETIN".replace(" ", "_")

        if reasons:
            status = "fail"
        else:
            status = "ready"
            doc = fitz.open(); doc.insert_pdf(base_form)
            values = {
                "provider_name": f"{first} {last}",
                "npi": npi,
                "medicaid_number": medicaid,
                "date": date_str,
                "phone": phone
            }
            for key, val in values.items():
                cfg = fmap.get(key)
                if not cfg: continue
                page = doc.load_page(int(cfg.get("page",0)))
                page.insert_text((float(cfg.get("x",72)), float(cfg.get("y",72))), str(val),
                                 fontsize=float(cfg.get("font_size",10)))
            buf = io.BytesIO(); doc.save(buf); doc.close()
            zf.writestr(f"{file_stub}.pdf", buf.getvalue())

        log_rows.append({
            "row_index": idx, "first_name": first, "last_name": last, "npi": npi,
            "medicaid_number": medicaid, "date": date_str, "phone": phone,
            "status": status, "reasons": "; ".join(reasons)
        })

    log_df = pd.DataFrame(log_rows); s = io.StringIO()
    log_df.to_csv(s, index=False); zf.writestr("run_log.csv", s.getvalue())
    zf.close(); output.seek(0); return output.getvalue()
