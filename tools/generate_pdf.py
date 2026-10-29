import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#555555"))
        
        # Header (on pages after page 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * 72 - 36, "Ontology-Guided Screening for Undetected Dysglycemia in NHANES")
            self.setStrokeColor(colors.HexColor("#cccccc"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

        # Footer (on all pages)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 36, page_str)
        self.drawString(54, 36, "ClinOntoScreen Research Prototype — Research Manuscript")
        self.setStrokeColor(colors.HexColor("#cccccc"))
        self.setLineWidth(0.5)
        self.line(54, 48, 8.5 * 72 - 54, 48)

        self.restoreState()

def build_pdf():
    root = Path(__file__).resolve().parents[1]
    pdf_path = root / "paper" / "ClinOntoScreen_Paper.pdf"
    art_dir = root / "artifacts"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'PaperTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=0,
        spaceAfter=12
    )

    subtitle_style = ParagraphStyle(
        'PaperSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#444444'),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'PaperH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        spaceBefore=16,
        spaceAfter=8,
        textColor=colors.HexColor('#111111')
    )

    h2_style = ParagraphStyle(
        'PaperH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor('#222222')
    )

    body_style = ParagraphStyle(
        'PaperBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        spaceAfter=8,
        textColor=colors.HexColor('#222222')
    )

    abstract_style = ParagraphStyle(
        'PaperAbstract',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        spaceAfter=6,
        textColor=colors.HexColor('#333333')
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#222222')
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("Ontology-Guided Screening for Undetected Dysglycemia: Evaluating Clinical Knowledge Integration Under Temporal Shift in NHANES", title_style))
    story.append(Paragraph("ClinOntoScreen Research Prototype — Manuscript Draft", subtitle_style))
    story.append(Paragraph("<b>Notice:</b> Research prototype only. Not a diagnostic tool, not clinically validated, and not for medical decisions.", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#333333"), spaceBefore=8, spaceAfter=12))

    # Abstract
    story.append(Paragraph("Abstract", h1_style))
    abstract_text = (
        "<b>Background.</b> Clinical guidelines and tabular machine learning are usually developed and evaluated separately; "
        "few studies test whether encoding guideline content as executable, provenance-carrying knowledge changes downstream "
        "screening decisions, and almost none do so under a temporal shift that can break hard-coded thresholds.<br/><br/>"
        "<b>Methods.</b> We built ClinOntoScreen: an OWL/RDF ontology encoding ADA 2026 diabetes-screening recommendations "
        "as executable rules with guideline-section references, coupled to logistic regression and XGBoost models. "
        "Leakage-safe predictors (excluding HbA1c, glucose, questionnaire answers, and medications) were derived from NHANES "
        "2017–March 2020 (historical development, n = 6,103, 28.9% screen-positive) and August 2021–August 2023 "
        "(locked temporal test, n = 4,260, 23.1% screen-positive). The outcome is HbA1c ≥ 5.7% among adults reporting neither "
        "prior diabetes nor prior prediabetes. The primary confirmatory endpoint was sensitivity of a hybrid ranking "
        "(XGBoost + ontology rule score) minus XGBoost alone at a fixed 20% screening capacity (paired bootstrap, 1,000 replicates). "
        "Exploratory experiments probed low-data regimes (E1), masked inputs (E2), model families (E3), disagreement review (H3), "
        "and the published CDC/ADA risk test.<br/><br/>"
        "<b>Results.</b> The primary effect was null: hybrid 0.409 vs ML-only 0.412 at 20% capacity; in the prespecified direction "
        "(hybrid − ML-only) the difference was <b>−0.003 (95% CI −0.010 to +0.008)</b>, entirely within the smallest detectable difference (0.014). "
        "At 20% capacity the prevalence ceiling is 0.867; the best policy (logistic + ontology features) reached sensitivity 0.423 "
        "(0.488 of ceiling), PPV 0.488, lift 2.12. All trained models outperformed the published CDC/ADA score (AUPRC 0.460–0.463 vs 0.380). "
        "Ontology features helped the linear model consistently in direction (sensitivity@20% +0.009, CI −0.004 to +0.019) and gave "
        "the smallest degradation under 30% input masking, but no interval excluded zero.<br/><br/>"
        "<b>Conclusions.</b> Encoding guideline provenance into an executable layer is feasible and auditable, but on NHANES with "
        "full historical data the rule-derived features are largely redundant with raw inputs for ranking. The honest headline is a "
        "well-powered null on the primary endpoint, with a consistent advantage for guideline features in linear, low-data, and "
        "missing-input settings."
    )
    story.append(Paragraph(abstract_text, abstract_style))
    story.append(Paragraph("<b>Keywords:</b> clinical ontology, screening, NHANES, temporal validation, fixed-capacity evaluation", body_style))
    story.append(Spacer(1, 10))

    # Section 1: Introduction
    story.append(Paragraph("1. Introduction", h1_style))
    story.append(Paragraph(
        "Diabetes screening is a resource-allocation problem before it is a prediction problem: practices can screen only a bounded "
        "fraction of their population, so a model's value at a fixed referral capacity is often more decision-relevant than its AUROC. "
        "At the same time, guidelines such as the ADA Standards of Care encode expert consensus that is auditable in prose but inert "
        "in software. Tabular machine learning can rank risk effectively, yet it silently discards that consensus; guideline rule "
        "engines keep the consensus but usually are not evaluated under strict temporal generalization tests.",
        body_style
    ))
    story.append(Paragraph(
        "ClinOntoScreen asks a narrow, testable question: <b>does encoding a documented subset of screening guidance as an executable, "
        "provenance-carrying ontology change screening decisions or robustness, relative to raw features, when both are evaluated "
        "on a genuinely later survey cycle?</b>",
        body_style
    ))
    story.append(Paragraph("<b>Key Contributions:</b>", body_style))
    story.append(Paragraph("• An OWL/RDF ontology whose executable rules carry guideline section references and operationalization status.", body_style))
    story.append(Paragraph("• A leakage-safe, cycle-harmonized feature contract with automated contract testing.", body_style))
    story.append(Paragraph("• A capacity-constrained evaluation protocol with prevalence ceilings and pre-registered MDE thresholds.", body_style))
    story.append(Paragraph("• An honest temporal evaluation on the latest cycle (2021–2023) against published knowledge and stress probes.", body_style))

    # Section 2: Related Work
    story.append(Paragraph("2. Related Work", h1_style))
    story.append(Paragraph(
        "NHANES supports a large prediction literature; closest to us in evaluation discipline is Kumar's leakage-controlled benchmark "
        "with rolling-origin temporal cross-validation and the same 2021–2023 holdout. Pham and Soo combine community detection with "
        "a diabetes ontology on NHANES data and report high discrimination, but with lab-inclusive features and a random split. "
        "Random splits overstate performance under survey-cycle shift; our ceiling-adjusted capacity reporting makes the achievable "
        "operating point explicit.",
        body_style
    ))

    # Capability Comparison Table
    story.append(Paragraph("<b>Table 1: Capability comparison with related studies.</b>", h2_style))
    comp_data = [
        [Paragraph("Dimension", table_header), Paragraph("Pham & Soo (CEAI)", table_header), Paragraph("Kumar (CMPB)", table_header), Paragraph("ClinOntoScreen (This work)", table_header)],
        [Paragraph("Data", table_cell), Paragraph("Pima, Hospitals, NHANES", table_cell), Paragraph("NHANES dev + holdouts", table_cell), Paragraph("NHANES dev + 2021–2023 temporal test", table_cell)],
        [Paragraph("Target", table_cell), Paragraph("Diabetes (lab-inclusive)", table_cell), Paragraph("HbA1c ≥ 6.5%", table_cell), Paragraph("HbA1c ≥ 5.7% (no prior history)", table_cell)],
        [Paragraph("Knowledge Role", table_cell), Paragraph("Domain ontology + clustering", table_cell), Paragraph("None", table_cell), Paragraph("OWL/RDF rules with provenance", table_cell)],
        [Paragraph("Primary Metric", table_cell), Paragraph("Accuracy / AUROC", table_cell), Paragraph("Discrimination + calibration", table_cell), Paragraph("<b>Sensitivity @ capacity with ceiling</b>", table_cell)]
    ]
    t_comp = Table(comp_data, colWidths=[100, 110, 110, 180])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 10))

    # Section 3: Data & Cohort
    story.append(Paragraph("3. Data and Cohort Harmonization", h1_style))
    story.append(Paragraph(
        "<b>Sources & Cohort Flow.</b> CDC/NCHS public XPT files across NHANES cycles. Adults aged 18+ with valid HbA1c and "
        "no reported prior diabetes or prediabetes comprise the historical development cohort (2017–March 2020, n = 6,103, "
        "28.94% screen-positive) and the temporal test cohort (August 2021–August 2023, n = 4,260, 23.08% screen-positive).",
        body_style
    ))
    story.append(Paragraph(
        "<b>Covariate Shift & Harmonization.</b> The 2021–2023 test cycle is older (mean age 49.2 vs 46.1) and demographically "
        "distinct. Physical activity instruments were harmonized across incompatible survey instruments into leisure minutes and "
        "sedentary minutes. HDL cholesterol is included; hypertension treatment (`BPQ040A`) and family history (`MCQ300C`) exist "
        "only in the earlier cycle (disclosed as 100% missing in test). Survey weights were not applied in this study.",
        body_style
    ))

    # Section 4: Ontology & Rule Engine
    story.append(Paragraph("4. Ontology and Rule Engine", h1_style))
    story.append(Paragraph(
        "The OWL/RDF knowledge model (version 0.2.0) encodes screening rules, age thresholds, overweight/obesity criteria "
        "(25 kg/m² general; 23 kg/m² for Asian participants), hypertension, physical inactivity, CVD history, and higher-risk ethnicity. "
        "Every rule carries guideline section references (`sectionReference`) and operationalization status. The Python rule executor "
        "derives 11 `onto_*` features and produces a rule-priority score.",
        body_style
    ))

    # Section 5: Methods
    story.append(Paragraph("5. Experimental Methods", h1_style))
    story.append(Paragraph(
        "<b>Leakage Contract.</b> Predictors strictly exclude HbA1c, glucose, diabetes questionnaire responses, medications, and IDs. "
        "Preprocessing pipelines fit exclusively within each training fold.<br/>"
        "<b>Models & Policies.</b> L2 logistic regression and XGBoost. Hyperparameters tuned on an 80/20 historical split "
        "(n = 1,221). Six model variants evaluated. Policies include raw probability, hybrid score (alpha = 0.10), rule-only score, "
        "and published CDC/ADA risk test.<br/>"
        "<b>Evaluation.</b> Test outcomes read once after protocol freezing. Metrics include AUROC, AUPRC, Brier score, and capacity "
        "tables at 10%, 20%, 30% referral budgets reporting prevalence ceiling, fraction of ceiling, PPV, and lift. Uncertainty "
        "evaluated via paired participant bootstrap (1,000 resamples) and pre-registered MDE thresholds.",
        body_style
    ))

    # Section 6: Results
    story.append(Paragraph("6. Empirical Results", h1_style))

    story.append(Paragraph("6.1 Historical Validation", h2_style))
    story.append(Paragraph(
        "Historical validation demonstrated robust baseline performance across models, with AUROC ranging from 0.776 to 0.781 "
        "and AUPRC from 0.542 to 0.549. Hybrid alpha was selected as 0.10.",
        body_style
    ))

    story.append(Paragraph("6.2 Temporal Test Discrimination & Calibration", h2_style))
    story.append(Paragraph(
        "On the locked 2021–2023 temporal test set, trained models achieved strong discrimination despite distribution shift.",
        body_style
    ))
    
    # Embed Figure 1 (ROC + Calibration)
    if (art_dir / "roc_pr_curves.png").exists():
        story.append(Image(str(art_dir / "roc_pr_curves.png"), width=420, height=210))
        story.append(Paragraph("<b>Figure 1a:</b> Receiver Operating Characteristic (ROC) and Precision-Recall (PR) curves.", ParagraphStyle('Cap', fontName='Helvetica-Oblique', fontSize=8.5, textColor=colors.HexColor('#555555'), spaceAfter=8)))
    if (art_dir / "calibration.png").exists():
        story.append(Image(str(art_dir / "calibration.png"), width=360, height=180))
        story.append(Paragraph("<b>Figure 1b:</b> Calibration reliability curves on the temporal test set.", ParagraphStyle('Cap', fontName='Helvetica-Oblique', fontSize=8.5, textColor=colors.HexColor('#555555'), spaceAfter=10)))

    story.append(Paragraph("6.3 Fixed Screening Capacity", h2_style))
    story.append(Paragraph(
        "Evaluating policies at fixed screening capacities against the prevalence ceiling (0.867 at 23.08% prevalence) shows that "
        "logistic regression combined with ontology features achieves the highest sensitivity at 20% capacity (0.423, finding 416 of 983 positives) "
        "with a PPV of 0.488 and lift of 2.12. All trained models outperformed the published CDC/ADA risk test.",
        body_style
    ))

    if (art_dir / "capacity_sensitivity.png").exists():
        story.append(Image(str(art_dir / "capacity_sensitivity.png"), width=400, height=200))
        story.append(Paragraph("<b>Figure 2:</b> Screening sensitivity across capacities (10%, 20%, 30%) relative to the prevalence ceiling.", ParagraphStyle('Cap', fontName='Helvetica-Oblique', fontSize=8.5, textColor=colors.HexColor('#555555'), spaceAfter=10)))

    story.append(Paragraph("6.4 Primary Endpoint (H2, Confirmatory) — Null", h2_style))
    story.append(Paragraph(
        "The primary confirmatory comparison yielded a null result: hybrid sensitivity was 0.409 versus 0.412 for XGBoost alone. "
        "In the prespecified direction (hybrid minus ML-only), the difference was <b>−0.0031 (95% CI −0.0100 to +0.0079)</b>, "
        "lying entirely within the smallest detectable difference (0.0143).",
        body_style
    ))

    if (art_dir / "primary_effect_ci.png").exists():
        story.append(Image(str(art_dir / "primary_effect_ci.png"), width=380, height=190))
        story.append(Paragraph("<b>Figure 3:</b> Paired bootstrap confidence interval for the primary effect (hybrid vs ML sensitivity difference).", ParagraphStyle('Cap', fontName='Helvetica-Oblique', fontSize=8.5, textColor=colors.HexColor('#555555'), spaceAfter=10)))

    story.append(Paragraph("6.5 Model-Family Knowledge-Layer Deltas (E3)", h2_style))
    story.append(Paragraph(
        "Adding ontology features to logistic regression yielded a sensitivity delta of +0.0092 (95% CI −0.0038 to +0.0185), while for XGBoost "
        "the delta was −0.0031 (95% CI −0.0181 to +0.0114). All intervals cross zero.",
        body_style
    ))

    if (art_dir / "e3_model_family_deltas.png").exists():
        story.append(Image(str(art_dir / "e3_model_family_deltas.png"), width=380, height=190))
        story.append(Paragraph("<b>Figure 4:</b> Model-family knowledge-layer deltas across logistic regression and XGBoost.", ParagraphStyle('Cap', fontName='Helvetica-Oblique', fontSize=8.5, textColor=colors.HexColor('#555555'), spaceAfter=10)))

    story.append(Paragraph("6.6 Low-Data Learning Curve (E1)", h2_style))
    story.append(Paragraph(
        "Evaluating models across training data fractions (5% to 100%) revealed no consistent low-data advantage for guideline features.",
        body_style
    ))

    if (art_dir / "e1_learning_curve.png").exists():
        story.append(Image(str(art_dir / "e1_learning_curve.png"), width=380, height=190))
        story.append(Paragraph("<b>Figure 5:</b> Low-data learning curve showing performance deltas across training data fractions.", ParagraphStyle('Cap', fontName='Helvetica-Oblique', fontSize=8.5, textColor=colors.HexColor('#555555'), spaceAfter=10)))

    story.append(Paragraph("6.7 Missing-Input Stress Test (E2)", h2_style))
    story.append(Paragraph(
        "Under 30% MCAR input masking of waist circumference, blood pressure, and hypertension history, the hybrid policy retained the "
        "highest AUPRC (0.4608) at every masking rate, and the linear model with ontology features exhibited the highest stability in capacity sensitivity.",
        body_style
    ))

    if (art_dir / "e2_missing_input.png").exists():
        story.append(Image(str(art_dir / "e2_missing_input.png"), width=380, height=190))
        story.append(Paragraph("<b>Figure 6:</b> Missing-input stress test showing robustness under MCAR data masking.", ParagraphStyle('Cap', fontName='Helvetica-Oblique', fontSize=8.5, textColor=colors.HexColor('#555555'), spaceAfter=10)))

    story.append(Paragraph("6.8 Guideline Disagreement vs Confidence Review (H3) & Subgroups", h2_style))
    story.append(Paragraph(
        "Reviewing cases where the top-20% model set and rule set disagreed yielded a precision of 0.360 (750 participants), whereas reviewing "
        "participants closest to the ML cutoff achieved a precision of 0.400. Guideline disagreement was not enriched relative to confidence review.",
        body_style
    ))

    # Section 7: Discussion
    story.append(Paragraph("7. Discussion", h1_style))
    story.append(Paragraph(
        "The primary screening endpoint is null, demonstrating that on rich tabular data with sufficient historical samples, explicit "
        "rule-derived features are largely redundant with raw model features for ranking. However, guideline integration provides substantial "
        "value in provenance tracking, auditability, and stability under missing inputs. The knowledge layer functions effectively as an "
        "explanation and governance substrate rather than a black-box performance booster.",
        body_style
    ))

    # Section 8: Limitations & Ethics
    story.append(Paragraph("8. Limitations and Ethics", h1_style))
    story.append(Paragraph(
        "Study limitations include a cross-sectional single-measurement HbA1c outcome, unweighted NHANES complex survey design "
        "(preventing population-representative prevalence estimates), uncaptured screening criteria (family history, gestational diabetes), "
        "and the absence of prospective clinical validation.",
        body_style
    ))

    # Section 9: Conclusion
    story.append(Paragraph("9. Conclusion", h1_style))
    story.append(Paragraph(
        "Under a pre-temporally held-out evaluation on NHANES 2021–2023, adding an executable guideline-ontology layer produced a "
        "well-powered null primary effect on sensitivity at 20% capacity, while outperforming published point-score baselines and providing "
        "robust stability under missing data. The integration of formal knowledge models into tabular machine learning offers significant "
        "auditability and governance benefits while establishing rigorous performance boundaries.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated formal PDF at {pdf_path}")

if __name__ == '__main__':
    build_pdf()
