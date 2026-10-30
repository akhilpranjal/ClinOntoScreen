"""Create an editable manuscript Word file using only the Python standard library."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "ClinOntoScreen_Research_Paper.docx"
IMAGE_FILES = [
    ROOT / "results" / "capacity_sensitivity.png",
    ROOT / "results" / "primary_effect_ci.png",
    ROOT / "results" / "roc_pr_curves.png",
    ROOT / "results" / "calibration.png",
]


def para(text: str, style: str = "Normal") -> str:
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'


def heading(text: str, level: int) -> str:
    return para(text, f"Heading{level}")


def table(rows: list[list[str]], widths: list[int] | None = None) -> str:
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in (widths or [1800] * len(rows[0])))
    body = []
    for row_index, row in enumerate(rows):
        cells = []
        for value in row:
            bold = "<w:b/>" if row_index == 0 else ""
            cells.append(
                '<w:tc><w:tcPr><w:tcBorders><w:top w:val="single" w:sz="4"/>'
                '<w:left w:val="single" w:sz="4"/><w:bottom w:val="single" w:sz="4"/>'
                '<w:right w:val="single" w:sz="4"/></w:tcBorders></w:tcPr>'
                f'<w:p><w:r>{bold}<w:t>{escape(str(value))}</w:t></w:r></w:p></w:tc>'
            )
        body.append("<w:tr>" + "".join(cells) + "</w:tr>")
    return '<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/></w:tblPr><w:tblGrid>' + grid + "</w:tblGrid>" + "".join(body) + "</w:tbl>"


def image_paragraph(rel_id: str, image_id: int, name: str) -> str:
    return (
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        '<wp:extent cx="5486400" cy="3200400"/>'
        f'<wp:docPr id="{image_id}" name="{escape(name)}"/>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="figure.png"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip r:embed="' + rel_id + '"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="5486400" cy="3200400"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
        '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
    )


def build_body() -> str:
    parts: list[str] = []
    parts.append(heading("Do Clinical Rules Improve Fixed-Capacity Dysglycemia Screening?", 1))
    parts.append(para("An Ontology-Ablation Study in NHANES", "Subtitle"))
    parts.append(para("ClinOntoScreen research manuscript draft", "Subtitle"))
    parts.append(para(f"Prepared from the reproducible aggregate study artifacts | {date.today().isoformat()}"))
    parts.append(para("Abstract", "Heading1"))
    parts.append(para(
        "Background: Machine-learning models can help decide who should receive limited screening resources, but they do not automatically explain how clinical guidance was used. We tested whether a small, explicit clinical ontology improved screening prioritization for HbA1c-defined dysglycemia. "
        "Methods: We used NHANES 2017–March 2020 for model development and NHANES August 2021–August 2023 as a locked later-cycle test set. Adults with valid HbA1c who reported neither prior diabetes nor prior prediabetes were included. The primary target was a single HbA1c measurement of at least 5.7%. HbA1c and diabetes questionnaire items were excluded from every model feature set. Logistic Regression and XGBoost were compared with raw features, ontology-derived features, and an ontology-assisted ranking policy. The primary endpoint was sensitivity when 20% of the test cohort was selected for further screening. "
        "Results: The test cohort contained 4,260 participants, including 983 screen-positive research labels. At 20% capacity, XGBoost using the primary non-laboratory feature setting found 396 positives (sensitivity 40.28%), while the ontology-assisted policy found 404 (41.10%). The difference was 0.81 percentage points, with a paired bootstrap 95% confidence interval from −0.43 to 1.84 percentage points. The interval included zero. Adding routine lipids was a post-hoc secondary analysis. Adding fasting plasma glucose in a fasting subsample produced higher sensitivity, as expected for a related glycemic test. "
        "Conclusion: In this study, the ontology layer was reproducible and explainable, but it did not provide a clearly established improvement in the primary fixed-capacity comparison. Its main value may be traceability and explanation rather than a guaranteed increase in predictive performance."
    ))
    parts.append(para("Keywords: dysglycemia; HbA1c; NHANES; clinical ontology; machine learning; screening; fixed capacity; reproducibility"))

    parts.append(heading("1. Introduction", 1))
    parts.append(para(
        "Screening programs often have fewer staff, appointments, or laboratory resources than people who may need assessment. A model that ranks people for follow-up can therefore be judged by how many screen-positive people it finds within a fixed referral budget. This is different from reporting only a probability threshold or a global discrimination measure."
    ))
    parts.append(para(
        "Machine-learning models can use demographic, physical, behavioral, and health-history information to estimate the chance of an elevated HbA1c result. However, a model score alone may not show which clinical ideas were used. A clinical ontology is a formal way to represent concepts, relationships, and rules. When linked to source variables, it can record why a rule was applied and which information was missing."
    ))
    parts.append(para(
        "This study asks a focused question: do clinical rules improve fixed-capacity screening for HbA1c-defined dysglycemia? We compare an XGBoost ranking based on ordinary variables with an ontology-assisted policy on a later NHANES cycle. We also compare ontology-derived features with an equivalent generic feature-engineering control. This comparison tests whether any numerical change comes from the information in the derived features rather than from the use of an ontology file itself."
    ))
    parts.append(para(
        "The primary analysis was defined using non-glycemic, non-laboratory variables. Two additional settings were added after the original primary analysis. They are reported as secondary or exploratory analyses and do not change the primary question."
    ))

    parts.append(heading("2. Related work", 1))
    parts.append(para(
        "Previous NHANES studies have used demographic variables, body measurements, health history, laboratory data, and machine-learning methods to predict diabetes or dysglycemia. Performance depends strongly on the outcome definition, the available laboratory tests, the cohort, and whether the test set is drawn from the same period as model development. Including HbA1c or fasting glucose can produce strong prediction, but those variables are close to the outcome and may answer a different question from no-laboratory screening."
    ))
    parts.append(para(
        "Clinical decision-support research has also examined rule systems and knowledge representations. The present study focuses on a narrow empirical test: whether a bounded, source-linked rule layer changes fixed-capacity ranking performance, while separately recording its provenance and explanations. The ontology is not presented as a complete implementation of clinical guidance."
    ))

    parts.append(heading("3. Materials and methods", 1))
    parts.append(heading("3.1 Study design and data", 2))
    parts.append(para(
        "This was a retrospective analysis of public National Health and Nutrition Examination Survey data. NHANES 2017–March 2020 was used for model development and historical validation. NHANES August 2021–August 2023 was held out as a later-cycle test set. We use the term later-cycle generalization because the survey periods differ in sample design, questionnaires, and examination procedures. We do not interpret the difference as a causal effect of any single event."
    ))
    parts.append(heading("3.2 Cohort and outcome", 2))
    parts.append(para(
        "The primary cohort included adults aged 18 years or older who answered no to prior diabetes and no to prior prediabetes and had a valid HbA1c measurement. The primary target was 1 when HbA1c was at least 5.7% and 0 otherwise. This is a research label based on one measurement, not a confirmed diagnosis. A diabetes-range threshold of 6.5% was retained as a secondary descriptive outcome."
    ))
    parts.append(heading("3.3 Feature settings and leakage control", 2))
    parts.append(para(
        "Setting 1 was the primary setting. It included age, sex, race and ethnicity category, education, income-to-poverty ratio, body mass index, waist circumference, mean systolic and diastolic blood pressure, leisure activity minutes, sedentary minutes, hypertension history, smoking history, and selected cardiovascular history. Setting 2 added HDL and total cholesterol. Setting 3 added fasting plasma glucose and was restricted to participants with non-missing fasting glucose. Settings 1 and 2 were rerun on the same fasting subset."
    ))
    parts.append(para(
        "HbA1c, diabetes questionnaire items, diabetes treatment variables, and participant identifiers were excluded from every feature list. Fasting plasma glucose was treated as a second glycemic test, not as a neutral feature. No fasting-glucose threshold was added to the ontology."
    ))
    parts.append(heading("3.4 Ontology and rule engine", 2))
    parts.append(para(
        "The study ontology is stored as RDF/OWL and links selected screening concepts to source variables and rule descriptions. A deterministic Python rule engine calculates ontology-derived features and explanation fields. The encoded rules cover age-based screening and selected body-size, blood-pressure, cardiovascular-history, activity, and race or ethnicity factors when the required information is available. Missing information is kept as missing rather than treated as a negative response. The race and ethnicity mapping is an approximation to the source guidance and was examined with a higher-risk flag ablation."
    ))
    parts.append(heading("3.5 Models and evaluation", 2))
    parts.append(para(
        "We evaluated Logistic Regression and XGBoost. Each model was run with raw features and with ontology-derived features. We also included an equivalent generic feature-engineering control, an ontology-only rule score, and an ontology-assisted ranking policy. Preprocessing was fitted using historical data only. Model and policy choices were made without using the later-cycle test set. Five seeds were used: 17, 42, 123, 2025, and 2026."
    ))
    parts.append(para(
        "The primary endpoint was sensitivity at 20% screening capacity. We also reported 10% and 30% capacity. Capacity means the fraction of people selected for further screening. The primary uncertainty interval used 1,000 paired participant bootstrap samples. The main analysis was unweighted; therefore, the predictive measures are not automatically nationally representative."
    ))

    parts.append(heading("4. Results", 1))
    parts.append(heading("4.1 Cohort flow", 2))
    parts.append(para("The sequential cohort counts are shown in Table 1. The later-cycle test cohort included 4,260 eligible participants, of whom 983 (23.08%) met the primary research label. The matched fasting test subset contained 2,348 participants and 546 screen-positive labels."))
    parts.append(table([
        ["Cycle", "Merged", "Adults", "Eligible", "Positive", "Negative", "FPG available"],
        ["2017–March 2020", "15,560", "9,693", "6,103", "1,766", "4,337", "2,959"],
        ["August 2021–August 2023", "11,933", "8,153", "4,260", "983", "3,277", "2,348"],
    ], [2400, 1100, 1100, 1100, 1100, 1100, 1400]))
    parts.append(para("Table 1. Cohort counts and target distribution. The target is a single HbA1c measurement of at least 5.7%."))

    parts.append(heading("4.2 Primary fixed-capacity comparison", 2))
    parts.append(para(
        "At 20% capacity, the Setting 1 XGBoost raw ranking selected 852 of 4,260 participants and found 396 positives. The ontology-assisted policy also selected 852 participants and found 404 positives. Sensitivity was 40.28% for the raw ranking and 41.10% for the ontology-assisted policy. Precision was 46.48% and 47.42%, respectively. The difference in sensitivity was 0.81 percentage points, with a 95% bootstrap interval from −0.43 to 1.84 percentage points."
    ))
    parts.append(table([
        ["Capacity", "Raw sensitivity", "Ontology-policy sensitivity", "Raw precision", "Ontology-policy precision"],
        ["10%", "22.38%", "22.79%", "51.61%", "53.29%"],
        ["20%", "40.28%", "41.10%", "46.48%", "47.42%"],
        ["30%", "57.07%", "56.88%", "43.90%", "44.29%"],
    ], [1200, 1800, 2200, 1600, 2200]))
    parts.append(para("Table 2. Primary Setting 1 results on the later-cycle test cohort."))

    parts.append(heading("4.3 Discrimination and calibration", 2))
    parts.append(table([
        ["Variant", "AUROC", "AUPRC", "Brier score"],
        ["Logistic Regression, raw", "0.7650", "0.4436", "0.1529"],
        ["XGBoost, raw", "0.7632", "0.4515", "0.1524"],
        ["Logistic Regression, ontology features", "0.7621", "0.4436", "0.1529"],
        ["XGBoost, ontology features", "0.7634", "0.4526", "0.1518"],
        ["XGBoost, generic equivalent features", "0.7634", "0.4526", "0.1518"],
    ], [3300, 1100, 1100, 1400]))
    parts.append(para("Table 3. Aggregate discrimination and calibration measures on the later-cycle test cohort."))
    parts.append(para(
        "The XGBoost ontology-feature and generic-feature-control results were numerically identical in the committed aggregate output. This supports a cautious interpretation: any small numerical change is associated with the derived information, not with RDF/OWL storage by itself."
    ))

    parts.append(heading("4.4 Secondary feature settings", 2))
    parts.append(para(
        "The secondary analyses were added after the original primary result and are therefore post-hoc. On the full test cohort, Setting 2 increased raw XGBoost sensitivity at 20% capacity from 40.28% to 41.40%. The Setting 2 ontology-feature variant reached 42.42% in the secondary run. In the matched fasting subset, Setting 1 had 39.56% sensitivity, Setting 2 had 39.93%, and Setting 3 reached 44.32% for the ontology-feature variant. The higher Setting 3 result is expected because fasting plasma glucose is closely related to HbA1c. It should not be interpreted as evidence that the ontology itself improved prediction."
    ))
    parts.append(table([
        ["Setting", "Test n", "Positive n", "XGBoost + ontology sensitivity at 20%"],
        ["Setting 1, main cohort", "4,260", "983", "39.78%"],
        ["Setting 2, main cohort", "4,260", "983", "42.42%"],
        ["Setting 1, fasting subset", "2,348", "546", "39.56%"],
        ["Setting 2, fasting subset", "2,348", "546", "39.93%"],
        ["Setting 3, fasting subset", "2,348", "546", "44.32%"],
    ], [3000, 1100, 1200, 2400]))
    parts.append(para("Table 4. Secondary feature-setting results. Settings 2 and 3 were post-hoc; Setting 3 includes fasting plasma glucose."))

    parts.append(heading("4.5 Figures", 2))
    parts.append(para("The following figures are embedded from the committed aggregate results. They are descriptive research outputs and do not establish clinical validity."))
    figure_captions = [
        "Figure 1. Sensitivity at fixed screening capacities for the primary test.",
        "Figure 2. Paired bootstrap uncertainty for the ontology-policy minus raw XGBoost sensitivity difference at 20% capacity.",
        "Figure 3. ROC and precision-recall curves for the evaluated model variants.",
        "Figure 4. Calibration comparison on the later-cycle test cohort.",
    ]
    for index, caption in enumerate(figure_captions, 1):
        parts.append(image_paragraph(f"rId{index}", index, IMAGE_FILES[index - 1].name))
        parts.append(para(caption))

    parts.append(heading("5. Discussion", 1))
    parts.append(para(
        "The primary result does not show a clearly established improvement from adding the ontology-assisted policy. The point estimate favored the ontology policy by 0.81 percentage points at 20% capacity, but the confidence interval included no difference. This means that the observed advantage may reflect sampling variation. The result should therefore be described as a small and uncertain change, not as proof that clinical rules improve screening."
    ))
    parts.append(para(
        "The study still provides a useful result about how clinical knowledge can be added to a screening system. The ontology makes the rule definitions, source variables, missing information, and explanations explicit. This can improve auditability even when the prediction numbers do not improve. The generic-feature control also shows why the representation should not receive credit for information that could be reproduced by ordinary feature engineering."
    ))
    parts.append(para(
        "The secondary feature settings give context for the primary finding. Routine lipids produced modest changes. Fasting plasma glucose produced a larger change, which is expected because it is another glycemic measurement. This comparison reinforces the importance of separating no-laboratory screening from screening that uses a closely related laboratory test."
    ))

    parts.append(heading("6. Limitations and ethics", 1))
    limitations = [
        "The target is one HbA1c measurement and is not a confirmed diagnosis.",
        "The primary analysis is unweighted, so the predictive measures are not automatically national population estimates.",
        "The two NHANES periods differ in survey design, questionnaires, and examination procedures.",
        "The ontology represents only a selected part of clinical screening guidance.",
        "Some risk factors are unavailable or measured through self-report.",
        "The race and ethnicity rule is an approximate mapping and does not constitute a complete fairness analysis.",
        "Settings 2 and 3 were added after the original primary result and are post-hoc.",
        "No prospective study, clinical workflow study, or patient-outcome evaluation was performed.",
        "The software is a research prototype and must not be used to diagnose or treat people.",
    ]
    for item in limitations:
        parts.append(para("• " + item))

    parts.append(heading("7. Conclusion", 1))
    parts.append(para(
        "In a leakage-controlled NHANES analysis, an ontology-assisted policy produced a small point estimate improvement over raw XGBoost ranking at a 20% screening capacity, but the uncertainty interval included zero. The strongest contribution of the ontology in this study is transparent, source-linked rule representation and explanation. Future work should test the approach with survey-weighted analyses, additional cycles, prospective clinical data, and a broader evaluation of fairness and clinical usefulness."
    ))

    parts.append(heading("References", 1))
    refs = [
        "1. Centers for Disease Control and Prevention. National Health and Nutrition Examination Survey 2017–March 2020 data and documentation. https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2017-2020",
        "2. Centers for Disease Control and Prevention. National Health and Nutrition Examination Survey August 2021–August 2023 data and documentation. https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023",
        "3. American Diabetes Association Professional Practice Committee. Diagnosis and Classification of Diabetes: Standards of Care in Diabetes—2026. Diabetes Care. 2026;49(Suppl 1).",
        "4. American Diabetes Association Professional Practice Committee. Prevention or Delay of Diabetes and Associated Comorbidities: Standards of Care in Diabetes—2026. Diabetes Care. 2026;49(Suppl 1).",
        "5. ClinOntoScreen project repository. Ontology-guided screening prioritization for NHANES. https://github.com/akhilpranjal/ClinOntoScreen",
        "6. Karthikeyan S, et al. Machine learning approaches for diabetes prediction using NHANES data. Related work should be verified and cited from the final source selected by the authors.",
        "7. The TRIPOD+AI statement: updated reporting guidance for clinical prediction models using regression or machine learning methods. Use the final published version required by the target journal.",
    ]
    for ref in refs:
        parts.append(para(ref))
    parts.append(heading("Data and code availability", 1))
    parts.append(para(
        "The code, ontology, notebook, protocol configuration, aggregate result tables, figures, checksums, and manuscript-support material are available in the public ClinOntoScreen repository. Raw NHANES files are downloaded from CDC by the notebook and are not redistributed in the repository. Participant-level predictions and model bundles are not included in the public results."
    ))
    return "".join(parts)


def make_docx() -> None:
    body = build_body()
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<w:body>' + body +
        '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>'
        '</w:body></w:document>'
    )
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:docDefaults><w:rPrDefault><w:rPr><w:fonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="22"/></w:rPr></w:rPrDefault>'
        '<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="276"/></w:pPr></w:pPrDefault></w:docDefaults>'
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:b/><w:sz w:val="34"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:rPr><w:i/><w:sz w:val="24"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="Heading 2"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>'
        '</w:styles>'
    )
    rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>',
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image2.png"/>',
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image3.png"/>',
            '<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image4.png"/>']
    document_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/styles.xml"/></Relationships>'
    content_types = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">', '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>', '<Default Extension="xml" ContentType="application/xml"/>', '<Default Extension="png" ContentType="image/png"/>', '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>', '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>', '</Types>']
    with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "".join(content_types))
        z.writestr("_rels/.rels", document_rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", styles)
        z.writestr("word/_rels/document.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + "".join(rels) + "</Relationships>")
        for index, image in enumerate(IMAGE_FILES, 1):
            z.write(image, f"word/media/image{index}.png")
    print(OUT)


if __name__ == "__main__":
    make_docx()
