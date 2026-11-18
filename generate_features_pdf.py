# generate_features_pdf.py
import os
import sys

from build_guides_pdf import build_pdf_from_markdown

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Compile Complete Features Guide PDF
    features_md = os.path.join(base_dir, "SMART_CAMPUS_COMPLETE_FEATURES_GUIDE.md")
    features_pdf = os.path.join(base_dir, "Smart_Campus_Complete_Features_Guide.pdf")
    if os.path.exists(features_md):
        print(f"Generating PDF for {features_md}...")
        build_pdf_from_markdown(
            md_filepath=features_md,
            output_pdf_path=features_pdf,
            doc_title="Smart Campus System - Complete Features & Functional Specification",
        )
        print(f"Generated: {features_pdf}")

    # 2. Compile ML Models & Techniques Specification PDF
    ml_md = os.path.join(base_dir, "SMART_CAMPUS_ML_MODELS_AND_TECHNIQUES_SPECIFICATION.md")
    ml_pdf = os.path.join(base_dir, "Smart_Campus_ML_Models_and_Techniques_Specification.pdf")
    if os.path.exists(ml_md):
        print(f"Generating PDF for {ml_md}...")
        build_pdf_from_markdown(
            md_filepath=ml_md,
            output_pdf_path=ml_pdf,
            doc_title="Smart Campus System - ML Models & Techniques Specification",
        )
        print(f"Generated: {ml_pdf}")

if __name__ == "__main__":
    main()
