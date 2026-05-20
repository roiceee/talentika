# Evaluation of OCR Robustness Against Graphically Complex Résumés

## Background and Rationale

Modern résumés are often heavily designed. They use colored sidebars, full page background fills, circular photo placeholders, multi column layouts, skill bars, timeline infographics, donut charts, and large display typography. These visual treatments are common on Canva, free template galleries, and design centric career sites, which means a non trivial fraction of real applicants submit résumés that look more like marketing collateral than plain text documents.

Our screening pipeline depends on Tesseract OCR to convert the uploaded PDF into the text that the AI then reads. If Tesseract fragments the text or misorders it because of visual complexity, the downstream AI sees a degraded copy of the résumé and can score the applicant unfairly. The purpose of this test is to find out how much visual styling our OCR layer can absorb before the extracted text becomes unreliable, and to confirm that a suitable candidate is not falsely downgraded simply because they used a heavily designed template.

## Experimental Design and Dataset Construction

We created a single dedicated job profile titled "Barista (OCR Robustness Test)" inside the same test organization used by the rest of our seeded data. The profile requires at least three years of barista or café operations experience and lists cash handling and inventory management as preferred skills. Other expected abilities (espresso preparation, customer service, sanitation) are listed as required qualifications. All five résumés in this experiment are submitted to this one profile, so they are evaluated against the same rubric.

Every résumé carries the same factual content, namely the suitable Barista persona (three years at Bo's Coffee, a Hospitality Management degree, supervisory and training experience, explicit cash handling and inventory duties, SCA certifications). The only variable across the five résumés is the visual layout of the PDF. All five layouts are heavily graphical, each chosen to stress a different OCR failure mode. The five layouts are a photo banner with orange and teal accents and horizontal skill bars; a full height dark navy sidebar with white text and dot skill ratings; a large red hero block with color block section headers and a dot skill matrix; a soft peach full page background with a donut chart and a vertical timeline; and a full bleed yellow page background with an off white sidebar, a circular photo placeholder, and a pink cursive style name. Holding content constant while varying only the visual treatment lets us attribute any difference in AI score, classification, or written reasoning purely to the OCR layer.

## Identity Configuration

The five résumés share the same last name (Santos) so they read as the same conceptual candidate, and each first name is set to the name of the layout the résumé uses (Photo Banner, Dark Sidebar, Color Blocks, Timeline Peach, and Yellow Sidebar). This makes it easy for the reviewer to identify which row in the dashboard corresponds to which layout, while the differing first names, emails, and phone numbers keep the duplicate score below the platform's block threshold. The résumé filenames themselves do not contain the layout name, so the AI's view of the file is not influenced by metadata.

## Evaluation Criteria

For each of the five submissions we record the classification the AI assigns and the AI's written reasoning. All five should land in the Suitable tier because the underlying content is identical and clearly meets every required and preferred qualification. The reasoning is also inspected for false negatives, that is, cases where the AI says a qualification is "missing" even though it is present in the source résumé but was lost or mangled during OCR. A pass for this test means all five résumés land in the same classification tier and the AI's reasoning does not cite missing qualifications that are in fact present in the source content.

## Results and Findings

All five submissions were classified as Suitable. The AI extracted the candidate's qualifications correctly across every visual treatment, including the styles with full bleed colored backgrounds and the dark sidebar. This indicates that the OCR layer holds up against heavy graphical design and does not falsely downgrade applicants who submit résumés built from designer templates.

| Applicant | Layout | Actual classification |
|---|---|---|
| Photo Banner Santos | Photo banner | Suitable |
| Dark Sidebar Santos | Dark sidebar | Suitable |
| Color Blocks Santos | Color blocks | Suitable |
| Timeline Peach Santos | Timeline, peach background | Suitable |
| Yellow Sidebar Santos | Yellow page, off white sidebar | Suitable |
