import streamlit as st
from form_agent import run_cover_mode, run_overlay_mode
import json

st.set_page_config(page_title="Medicaid FormAgent", page_icon="🧾", layout="centered")
st.title("Medicaid FormAgent")
st.write("Upload your Excel of providers and your Medicaid packet PDF, then choose how to generate the packets.")

with st.expander("Required Excel columns", expanded=False):
    st.markdown("""
- First Name
- Last Name
- NPI Number (10 digits)
- Medicaid Number (6-12 digits)
- Date (YYYY-MM-DD)
- Phone Number
""")

excel_file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])
pdf_file = st.file_uploader("Upload Medicaid Packet PDF (.pdf)", type=["pdf"])

mode = st.radio("Generation Mode", ["Cover+Append (easiest)", "Overlay (type onto the form)"])

fmap_bytes = None
if mode == "Overlay (type onto the form)":
    fmap_file = st.file_uploader("Upload field_map.json (or use default)", type=["json"])
    use_default = st.checkbox("Use default field_map.json", value=True)
    if use_default and fmap_file is None:
        default_map = {
            "provider_name": {"x": 120, "y": 180, "page": 0, "font_size": 11},
            "npi": {"x": 120, "y": 210, "page": 0, "font_size": 11},
            "medicaid_number": {"x": 120, "y": 240, "page": 0, "font_size": 11},
            "date": {"x": 120, "y": 270, "page": 0, "font_size": 11},
            "phone": {"x": 120, "y": 300, "page": 0, "font_size": 11}
        }
        fmap_bytes = json.dumps(default_map).encode("utf-8")
    elif fmap_file is not None:
        fmap_bytes = fmap_file.read()

if st.button("Generate Packets"):
    if not excel_file or not pdf_file:
        st.error("Please upload both the Excel file and the Medicaid packet PDF.")
    else:
        with st.spinner("Generating packets..."):
            try:
                excel_bytes = excel_file.read()
                pdf_bytes = pdf_file.read()
                if mode.startswith("Cover"):
                    zip_bytes = run_cover_mode(excel_bytes, pdf_bytes)
                else:
                    if fmap_bytes is None:
                        st.error("Overlay mode requires a field map (or select 'Use default field_map.json').")
                        st.stop()
                    zip_bytes = run_overlay_mode(excel_bytes, pdf_bytes, fmap_bytes)
            except Exception as e:
                st.error(f"Error: {e}")
            else:
                st.success("Done! Download below.")
                st.download_button("Download Packets ZIP", data=zip_bytes, file_name="Medicaid_Packets.zip", mime="application/zip")

st.divider()
st.caption("Tip: If the text doesn't align in overlay mode, tweak field_map.json positions and re-run.")
