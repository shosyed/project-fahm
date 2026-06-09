# Data Attributions

This file documents the license and attribution requirements for every data asset bundled in project-fahm.

**Last reviewed:** 2026-06-08

All confirmed sources below are either in the public domain or freely redistributable for non-commercial use with attribution. No all-rights-reserved or no-derivatives content is bundled.

---

## Arabic Text

| Field | Value |
|-------|-------|
| Source | Tanzil.net |
| Text variant | Uthmani (with full tashkeel / diacritics) |
| URL | https://tanzil.net/download/ |
| Version | 1.1 (released February 2021) |
| License | Custom — non-commercial redistribution permitted with attribution |
| Redistribution conditions | May be redistributed verbatim (unmodified) in websites and applications. Modification of the text is prohibited. When 3 or more translations are bundled alongside the text, a hyperlink to tanzil.net must be included to help users access updates. |
| Attribution required | Yes — "Source: Tanzil Project (tanzil.net)" must be clearly visible in the application |
| Non-commercial restriction | Yes — the Tanzil download page states translations are for non-commercial purposes; project-fahm is non-commercial and satisfies this condition |
| Notes | The Quran text itself (as divine revelation) is in the public domain. Tanzil's specific encoded/verified Unicode rendering is a curated dataset they license under these non-commercial terms. No restriction on use alongside AI summarization is stated. |

---

## Translations

### Yusuf Ali (1934)

| Field | Value |
|-------|-------|
| Source | Tanzil.net (en.yusufali) and QUL (TarteelAI/quranic-universal-library) |
| Author | Abdullah Yusuf Ali (1872–1953) |
| Title | "The Holy Quran: Translation and Commentary" |
| First published | 1934 |
| URL | https://tanzil.net/trans/ |
| UK copyright status | Public domain — Yusuf Ali died 1953; UK 70-year rule means copyright expired 2023 |
| US copyright status | REQUIRES FURTHER REVIEW — Works published 1924–1963 in the US required renewal to remain protected. Fewer than 7% of books were renewed. No renewal record has been positively confirmed or ruled out for the 1934 edition. If unrenewed, it is public domain in the US; if renewed, protection extends to 2029. The translation is widely distributed on Tanzil, QUL, and other open platforms without copyright restriction, suggesting non-renewal, but a formal renewal search at https://copyright.gov/records/ or Stanford Copyright Renewal Database should be completed before production release. |
| Redistribution conditions | Tanzil states translations are for non-commercial purposes and requires attribution to Tanzil as source. QUL (MIT-licensed platform) lists this translation without additional copyright notice. |
| Attribution required | Yes — credit Abdullah Yusuf Ali as translator; link to tanzil.net |
| Non-commercial restriction | Yes (per Tanzil terms) — project-fahm is non-commercial |
| Notes | Use ONLY the translation text from the 1934 original by Yusuf Ali himself. Many later editions (e.g. IFTA/Saudi editions) include commentary added by other editors and may carry separate copyright. The QUL and Tanzil datasets contain only the original translation text. |

### Pickthall (1930)

| Field | Value |
|-------|-------|
| Source | Tanzil.net (en.pickthall) and QUL (TarteelAI/quranic-universal-library) |
| Author | Marmaduke William Pickthall (1875–1936) |
| Title | "The Meaning of the Glorious Koran" |
| First published | 1930 |
| URL | https://tanzil.net/trans/ and https://www.gutenberg.org/ebooks/16955 |
| UK copyright status | Public domain — Pickthall died 1936; UK 70-year rule means copyright expired 2006 |
| US copyright status | Public domain — confirmed. Project Gutenberg lists the work as "Public domain in the USA." Works published 1924–1963 required renewal; the renewal rate for books was under 7% and no renewal for the 1930 Pickthall edition is recorded. The work appears at https://www.gutenberg.org/ebooks/16955 as public domain. |
| Redistribution conditions | Public domain — no restrictions. Tanzil additionally requires attribution to Tanzil as source for translations served through their download. |
| Attribution required | Credit Marmaduke Pickthall as translator; link to tanzil.net if served from Tanzil data |
| Non-commercial restriction | No — public domain imposes no commercial restrictions, though Tanzil's non-commercial term applies to files downloaded from their platform |
| Notes | This is the standard translation text. No commentary is bundled — only the translation itself. |

---

## Tafsirs

### Tafsir al-Jalalayn (Arabic text)

| Field | Value |
|-------|-------|
| Source | QUL — TarteelAI/quranic-universal-library |
| Authors | Jalal al-Din al-Mahalli (d. 1459 CE) and Jalal al-Din al-Suyuti (d. 1505 CE) |
| Language | Arabic |
| Original composition | 15th century (written c. 1463–1505) |
| Copyright status of original text | Public domain worldwide — both authors died over 500 years ago, far beyond any copyright term in any jurisdiction |
| Data source URL | https://qul.tarteel.ai/resources/tafsir |
| QUL repo URL | https://github.com/TarteelAI/quranic-universal-library |
| QUL repo commit (reviewed) | af69a2b7e9e2b48c8df2e97364e8ee48d347576d (2026-06-07) |
| QUL code license | MIT License — Copyright (c) 2024-present Tarteel, Inc |
| Data license | The QUL repo LICENSE file (MIT) covers the codebase. Per the QUL FAQ: "Check repository license terms and dataset-specific licensing details before production use." Individual resources carry per-resource permission flags in the QUL data model. The Arabic text of al-Jalalayn is itself public domain; QUL's curation is MIT-licensed. No separate restrictive data license is documented for this dataset. REQUIRES FURTHER REVIEW: confirm per-resource permission_to_share status via https://qul.tarteel.ai/resources/tafsir before production data download. |
| Attribution required | Credit "Tafsir al-Jalalayn, curated by Tarteel AI / Quranic Universal Library (qul.tarteel.ai)" |
| Non-commercial restriction | No restriction on the original classical text; QUL MIT license imposes none |
| Notes | Only the Arabic tafsir text is bundled. The app's AI layer will generate English summaries referencing this text. No English translation of al-Jalalayn is bundled (various English translations have their own copyright status). |

### Tafsir Ibn Kathir (Arabic text)

| Field | Value |
|-------|-------|
| Source | QUL — TarteelAI/quranic-universal-library |
| Author | Ismail ibn Kathir (d. 1373 CE) |
| Title | "Tafsir al-Qur'an al-Azim" |
| Language | Arabic |
| Original composition | 14th century (written c. 1370) |
| Copyright status of original text | Public domain worldwide — author died over 600 years ago, far beyond any copyright term in any jurisdiction |
| Data source URL | https://qul.tarteel.ai/resources/tafsir |
| QUL repo URL | https://github.com/TarteelAI/quranic-universal-library |
| QUL repo commit (reviewed) | af69a2b7e9e2b48c8df2e97364e8ee48d347576d (2026-06-07) |
| QUL code license | MIT License — Copyright (c) 2024-present Tarteel, Inc |
| Data license | Same as al-Jalalayn above. The original Arabic text is public domain; QUL's curation is MIT-licensed. REQUIRES FURTHER REVIEW: confirm per-resource permission_to_share status via https://qul.tarteel.ai/resources/tafsir before production data download. |
| Attribution required | Credit "Tafsir Ibn Kathir, curated by Tarteel AI / Quranic Universal Library (qul.tarteel.ai)" |
| Non-commercial restriction | No restriction on the original classical text; QUL MIT license imposes none |
| Notes | Only the Arabic tafsir text is bundled. English summaries will be AI-generated at runtime. No English translation of Ibn Kathir is bundled. |

---

## Cross-reference Datasets

All four datasets below are sourced from the Quranic Universal Library (QUL) by Tarteel AI. The repository's code and data are published under the MIT License. The QUL FAQ notes users should verify "dataset-specific licensing details" for production use, and the data model includes a per-resource `permission_to_share` flag. Based on the MIT license of the repository and the open download model (no API key, no paywall), redistribution for non-commercial use is consistent with the stated MIT terms, but the REQUIRES FURTHER REVIEW flag is applied pending confirmation of per-resource permission status.

**QUL repo:** https://github.com/TarteelAI/quranic-universal-library  
**QUL commit reviewed:** af69a2b7e9e2b48c8df2e97364e8ee48d347576d (2026-06-07)  
**QUL data download URL:** https://qul.tarteel.ai/resources

### QUL — Similar Ayahs

| Field | Value |
|-------|-------|
| Source | QUL — TarteelAI/quranic-universal-library |
| Dataset | Similar Ayah (~4,001 ayah-pair records) |
| URL | https://qul.tarteel.ai/resources/similar-ayah |
| License | MIT License (repository) — Copyright (c) 2024-present Tarteel, Inc |
| Redistribution conditions | MIT — free to use, modify, and redistribute with attribution |
| Attribution required | "Similar Ayahs dataset from Quranic Universal Library by Tarteel AI (github.com/TarteelAI/quranic-universal-library)" |
| Non-commercial restriction | None under MIT |
| Notes | REQUIRES FURTHER REVIEW — Verify per-resource `permission_to_share` flag at https://qul.tarteel.ai/resources/similar-ayah before production data download. Fields: verse_key, matched_ayah_key, matched_words_count, coverage, score, match_words_range. |

### QUL — Mutashabihat

| Field | Value |
|-------|-------|
| Source | QUL — TarteelAI/quranic-universal-library |
| Dataset | Mutashabihat ul Quran (~5,277 records of textual similarities) |
| URL | https://qul.tarteel.ai/resources/mutashabihat |
| License | MIT License (repository) — Copyright (c) 2024-present Tarteel, Inc |
| Redistribution conditions | MIT — free to use, modify, and redistribute with attribution |
| Attribution required | "Mutashabihat dataset from Quranic Universal Library by Tarteel AI (github.com/TarteelAI/quranic-universal-library)" |
| Non-commercial restriction | None under MIT |
| Notes | REQUIRES FURTHER REVIEW — Verify per-resource `permission_to_share` flag at https://qul.tarteel.ai/resources/mutashabihat before production data download. |

### QUL — Ayah Topics

| Field | Value |
|-------|-------|
| Source | QUL — TarteelAI/quranic-universal-library |
| Dataset | Ayah Topics (~2,512 key concepts with semantic relations) |
| URL | https://qul.tarteel.ai/resources/ayah-topics |
| License | MIT License (repository) — Copyright (c) 2024-present Tarteel, Inc |
| Redistribution conditions | MIT — free to use, modify, and redistribute with attribution |
| Attribution required | "Ayah Topics dataset from Quranic Universal Library by Tarteel AI (github.com/TarteelAI/quranic-universal-library)" |
| Non-commercial restriction | None under MIT |
| Notes | REQUIRES FURTHER REVIEW — Verify per-resource `permission_to_share` flag at https://qul.tarteel.ai/resources/ayah-topics before production data download. |

### QUL — Ayah Themes

| Field | Value |
|-------|-------|
| Source | QUL — TarteelAI/quranic-universal-library |
| Dataset | Ayah Themes (~1,049 core themes per verse) |
| URL | https://qul.tarteel.ai/resources/ayah-theme |
| License | MIT License (repository) — Copyright (c) 2024-present Tarteel, Inc |
| Redistribution conditions | MIT — free to use, modify, and redistribute with attribution |
| Attribution required | "Ayah Themes dataset from Quranic Universal Library by Tarteel AI (github.com/TarteelAI/quranic-universal-library)" |
| Non-commercial restriction | None under MIT |
| Notes | REQUIRES FURTHER REVIEW — Verify per-resource `permission_to_share` flag at https://qul.tarteel.ai/resources/ayah-theme before production data download. |

---

## AI Model (in-browser, not redistributed)

The models listed here run entirely on the user's device via WebGPU/WebLLM. The app does not host, serve, or redistribute model weights — it references model files that the user's browser downloads directly from Hugging Face at runtime. Attribution and license compliance is still documented here for completeness.

### Qwen2.5-3B-Instruct

| Field | Value |
|-------|-------|
| Provider | Alibaba Cloud |
| Model | Qwen2.5-3B-Instruct |
| Weights URL | https://huggingface.co/Qwen/Qwen2.5-3B-Instruct |
| License | Qwen Research License Agreement (NOT Apache 2.0) — custom proprietary license by Alibaba Cloud, dated September 19, 2024 |
| Commercial use | Non-commercial only by default. The license states use is "FOR NON-COMMERCIAL PURPOSES ONLY." Commercial use requires separate explicit authorization from Alibaba Cloud. |
| Key restrictions | Redistribution requires copy of the agreement; attribution "Qwen is licensed under the Qwen RESEARCH LICENSE AGREEMENT, Copyright (c) Alibaba Cloud" required; export controls apply; derivative AI models must display "Built with Qwen" |
| Non-commercial restriction | Yes — non-commercial only under default research license |
| Status for project-fahm | ACCEPTABLE for non-commercial use. project-fahm is non-commercial and the model is not redistributed — users download directly from Hugging Face. Attribution notice should appear in the app. |
| Notes | Contrary to some secondary sources, this model is NOT licensed under Apache 2.0. The Hugging Face model page shows license: "qwen-research". The full license was verified at https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE. |

### Llama-3.2-3B-Instruct

| Field | Value |
|-------|-------|
| Provider | Meta AI |
| Model | Llama-3.2-3B-Instruct |
| Weights URL | https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct |
| License | Llama 3.2 Community License (custom commercial license by Meta) |
| Commercial use | Permitted with conditions — non-exclusive, royalty-free license for commercial and research use |
| Key restrictions | Must display "Built with Llama" prominently; must include full license agreement with distributions; derivative models must include "Llama" in name; if MAU exceeds 700 million at release date, separate license required from Meta; subject to Meta's Acceptable Use Policy |
| Non-commercial restriction | No — commercial use is permitted |
| Status for project-fahm | ACCEPTABLE. project-fahm does not redistribute weights; users download directly from Hugging Face. "Built with Llama" attribution should appear in the app if this model is selected. |
| Notes | No redistribution of weights occurs in this app architecture, but the Acceptable Use Policy prohibitions (military, CSAM, disinformation, impersonation, malware) remain in force for how the model is used. |

---

## Sources not included (and why)

| Source | Reason excluded |
|--------|----------------|
| Sahih International | All rights reserved — copyright holder (Al-Muntada al-Islami) has not permitted free redistribution or non-commercial use without explicit license grant |
| The Clear Quran (Dr. Mustafa Khattab) | CC-BY-NC-ND — the no-derivatives clause prevents AI summarization and transformation of the text, which is a core feature of this app |
| Any English translation of Ibn Kathir or al-Jalalayn | Modern English translations of classical tafsirs are separately copyrighted. Only the original Arabic text (public domain) is bundled; English summaries are AI-generated at runtime. |

---

## Items Requiring Further Review Before Production

The following items are cleared in principle but require a final manual check before data files are committed:

1. **Yusuf Ali (1934) — US copyright renewal**: Search the Stanford Copyright Renewal Database (https://exhibits.stanford.edu/copyright) and/or the US Copyright Office public records (https://copyright.gov/records/) for any renewal filing on the 1934 edition. If no renewal is found, the work is confirmed public domain in the US.

2. **QUL datasets (all four)**: Visit each resource page on https://qul.tarteel.ai/resources and confirm the `permission_to_share` status shown in the QUL admin interface is "granted" for the specific dataset version being downloaded. The MIT license on the repo covers the platform code; data permissions are tracked per-resource.

3. **QUL tafsirs (al-Jalalayn and Ibn Kathir)**: Same as above — confirm `permission_to_share` is granted for the specific Arabic tafsir resource before bundling.
