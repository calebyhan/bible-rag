# Bible RAG - Data Sources & Licensing

This document outlines all data sources used in the Bible RAG project, their licensing terms, and usage requirements.

## Table of Contents

- [Overview](#overview)
- [Bible Translations](#bible-translations)
- [Original Language Texts](#original-language-texts)
- [Cross-Reference Data](#cross-reference-data)
- [Strong's Concordance](#strongs-concordance)
- [API Sources](#api-sources)
- [Licensing Compliance](#licensing-compliance)
- [Attribution Requirements](#attribution-requirements)

---

## Overview

The Bible RAG system integrates multiple data sources to provide comprehensive Bible study capabilities across English, Korean, and original biblical languages (Hebrew, Greek, Aramaic).

**Data Types:**
- Bible translations (10+ versions)
- Original language manuscripts
- Cross-reference relationships
- Lexical data (Strong's numbers, morphology)

---

## Bible Translations

### English Translations

#### 1. King James Version (KJV)
- **License**: Public Domain
- **Source**: GetBible API (https://api.getbible.net/v2)
- **Language Code**: `en`
- **Notes**: Published 1611, no copyright restrictions
- **Attribution**: Not required, but recommended

#### 2. World English Bible (WEB)
- **License**: Public Domain
- **Source**: GetBible API
- **Language Code**: `en`
- **Notes**: Modern English translation based on ASV 1901
- **Attribution**: Not required

#### 3. New International Version (NIV)
- **License**: **Commercial License Required**
- **Source**: API.Bible (https://scripture.api.bible)
- **Language Code**: `en`
- **Copyright**: © Biblica, Inc.
- **Usage Restrictions**:
  - Requires API key from API.Bible
  - Subject to Biblica's usage guidelines
  - Cannot redistribute raw text
  - Quotations limited to 1,000 verses
- **Attribution Required**: Yes - "Scripture quotations taken from The Holy Bible, New International Version® NIV®. Copyright © 1973, 1978, 1984, 2011 by Biblica, Inc.™"

#### 4. English Standard Version (ESV)
- **License**: **Commercial License Required**
- **Source**: API.Bible
- **Language Code**: `en`
- **Copyright**: © Crossway Bibles
- **Usage Restrictions**:
  - Requires API key
  - Maximum 500 verses per unique work
  - Cannot create derivative Bible versions
- **Attribution Required**: Yes - "Scripture quotations are from the ESV® Bible (The Holy Bible, English Standard Version®), copyright © 2001 by Crossway"

#### 5. New American Standard Bible (NASB)
- **License**: **Commercial License Required**
- **Source**: API.Bible
- **Language Code**: `en`
- **Copyright**: © The Lockman Foundation
- **Usage Restrictions**:
  - Requires API key
  - Quotation limits apply
  - Cannot redistribute
- **Attribution Required**: Yes - "Scripture taken from the NEW AMERICAN STANDARD BIBLE®, Copyright © 1960,1962,1963,1968,1971,1972,1973,1975,1977,1995 by The Lockman Foundation"

---

### Korean Translations (한글 성경)

#### 6. 개역개정 (Revised Korean Version - RKV)
- **License**: Public Domain (verification recommended)
- **Source**: GetBible API / Korean Bible Society
- **Language Code**: `ko`
- **Notes**: Most widely used Korean Protestant translation
- **Attribution**: Recommended - "대한성서공회 개역개정판"

#### 7. 개역한글 (Korean Revised Version - KRV)
- **License**: Public Domain
- **Source**: GetBible API
- **Language Code**: `ko`
- **Notes**: Traditional Korean translation (1961)
- **Attribution**: Recommended

#### 8. 새번역 (New Korean Revised Version - NKRV)
- **License**: **Copyright - Korean Bible Society**
- **Source**: Korean Bible Society
- **Language Code**: `ko`
- **Copyright**: © 대한성서공회
- **Usage Restrictions**: Contact Korean Bible Society for API access
- **Attribution Required**: Yes

#### 9. 공동번역 (Korean Common Bible - KCBS)
- **License**: **Copyright - Joint publication**
- **Source**: Catholic/Protestant joint translation committee
- **Language Code**: `ko`
- **Notes**: Ecumenical translation (1977)
- **Attribution Required**: Yes

---

### Original Language Texts

#### 10. SBL Greek New Testament (SBLGNT)
- **License**: **CC BY 4.0** (Creative Commons Attribution)
- **Source**: Society of Biblical Literature
- **Language Code**: `gr` (Greek)
- **Website**: https://sblgnt.com
- **Attribution Required**: Yes - "The Greek New Testament: SBL Edition. Copyright © 2010 Society of Biblical Literature and Logos Bible Software"
- **Usage**: Free for scholarly and personal use
- **Redistribution**: Allowed with attribution

#### 11. Westminster Leningrad Codex (WLC)
- **License**: **Public Domain**
- **Source**: Westminster Hebrew Institute
- **Language Code**: `he` (Hebrew)
- **Notes**: Hebrew Old Testament based on Leningrad Codex
- **Attribution**: Recommended
- **Website**: http://www.tanach.us/Tanach.xml

---

## Cross-Reference Data

### OpenBible.info Cross-References
- **License**: **CC BY 4.0**
- **Source**: https://github.com/openbibleinfo/Bible-Cross-Reference-JSON
- **Format**: JSON
- **Coverage**: 63,779+ cross-references
- **Attribution Required**: Yes - "Cross-reference data from OpenBible.info, licensed under CC BY 4.0"
- **Types**:
  - Quotation: OT quoted in NT
  - Allusion: Indirect references
  - Parallel: Similar passages
  - Theme: Thematically related verses

### Treasury of Scripture Knowledge
- **License**: Public Domain
- **Source**: Various digitization projects
- **Notes**: 19th-century compilation of cross-references
- **Attribution**: Not required

---

## Strong's Concordance

### Strong's Hebrew and Greek Dictionaries
- **License**: **Public Domain**
- **Source**: James Strong (1890)
- **Coverage**:
  - 8,674 Hebrew/Aramaic entries (H1-H8674)
  - 5,624 Greek entries (G1-G5624)
- **Data Includes**:
  - Strong's numbers
  - Transliterations
  - Definitions
  - Etymology
- **Attribution**: Recommended - "Strong's Exhaustive Concordance (1890)"

### Blue Letter Bible Integration
- **License**: **Free for non-commercial use**
- **Source**: https://www.blueletterbible.org
- **API Access**: Free tier available
- **Data**: Enhanced Strong's data with morphology
- **Attribution Required**: Yes - "Lexical data courtesy of Blue Letter Bible"

---

## API Sources

### 1. GetBible API
- **URL**: https://api.getbible.net/v2
- **License**: Free, public domain texts
- **Rate Limits**: Reasonable use (no official limit)
- **Supported Translations**: KJV, WEB, Korean translations
- **Format**: JSON
- **Usage**: Free for all purposes
- **Attribution**: Not required but appreciated

### 2. API.Bible
- **URL**: https://scripture.api.bible
- **License**: API access free, content licensing varies by translation
- **Rate Limits**:
  - Free tier: 500 requests/day
  - Paid tiers available
- **API Key Required**: Yes
- **Supported Translations**: NIV, ESV, NASB, and 1,600+ more
- **Usage**: Subject to individual translation licenses
- **Registration**: https://scripture.api.bible/signup

### 3. Blue Letter Bible API
- **URL**: https://www.blueletterbible.org/webservices/
- **License**: Free for non-commercial use
- **Rate Limits**: Reasonable use
- **Data**: Lexicons, concordances, commentaries
- **API Key Required**: Yes (free registration)
- **Usage Restrictions**: Non-commercial only

---

## Licensing Compliance

### Public Domain Translations
**Unrestricted Use:**
- KJV
- WEB
- 개역한글 (KRV)
- Westminster Leningrad Codex
- Strong's Concordance

**Best Practices:**
- Provide attribution even when not required
- Maintain text integrity
- Indicate translation used

### Commercial/Licensed Translations
**NIV, ESV, NASB Usage:**
1. **Obtain API Key**: Register with API.Bible or official providers
2. **Display Attribution**: Show required copyright notices in UI
3. **Respect Quotation Limits**:
   - NIV: 1,000 verses per work
   - ESV: 500 verses per work
   - NASB: Follow Lockman Foundation guidelines
4. **No Redistribution**: Cannot provide raw Bible text downloads
5. **No Derivative Works**: Cannot create modified Bible versions

### Korean Translations
**Public Domain (개역한글):**
- Free to use and redistribute
- Attribution recommended

**Licensed (개역개정, 새번역, 공동번역):**
- Contact Korean Bible Society for commercial use
- Non-commercial use generally permitted with attribution
- Verify current licensing status

---

## Attribution Requirements

### In Application UI

**Footer Attribution Example:**
```
Scripture quotations are from:
- The Holy Bible, New International Version® NIV®. Copyright © 1973, 1978, 1984, 2011 by Biblica, Inc.™
- ESV® Bible (The Holy Bible, English Standard Version®), copyright © 2001 by Crossway
- King James Version (Public Domain)
- 개역개정판 © 대한성서공회
- The Greek New Testament: SBL Edition. Copyright © 2010 Society of Biblical Literature
- Cross-reference data from OpenBible.info, licensed under CC BY 4.0
```

### In API Responses

**Include metadata field:**
```json
{
  "verse": {
    "text": "...",
    "translation": "NIV",
    "copyright": "© Biblica, Inc.",
    "attribution": "Scripture taken from The Holy Bible, New International Version® NIV®..."
  }
}
```

### In Documentation

- List all data sources in README.md
- Provide licensing information in this file
- Include attribution in academic papers or publications using the system

---

## Data Update Policy

### Translation Updates
- **Frequency**: Check for translation updates annually
- **Process**: Re-fetch via API, regenerate embeddings
- **Versioning**: Track translation edition/version in database

### Cross-Reference Updates
- **Source**: Monitor OpenBible.info GitHub repository
- **Frequency**: Quarterly checks for updates
- **Process**: Merge new cross-references, update confidence scores

### Strong's Data Updates
- **Source**: Public domain, stable
- **Updates**: Rare, only for corrections
- **Enhanced Data**: Check Blue Letter Bible for morphology updates

---

## Contact Information for Licensing Questions

### English Translations
- **NIV**: Biblica - https://www.biblica.com/bible/permissions
- **ESV**: Crossway - permissions@crossway.org
- **NASB**: Lockman Foundation - https://www.lockman.org

### Korean Translations
- **Korean Bible Society** (대한성서공회): https://www.bskorea.or.kr

### API Providers
- **API.Bible**: support@api.bible
- **Blue Letter Bible**: https://www.blueletterbible.org/contact.cfm

---

## Compliance Checklist

Before deploying to production, verify:

- [ ] All required copyright notices displayed in UI
- [ ] API keys configured for licensed translations
- [ ] Attribution footer included on all pages
- [ ] Quotation limits not exceeded for commercial translations
- [ ] No raw Bible text download functionality (violates licenses)
- [ ] User-generated content (notes, highlights) clearly separated from Bible text
- [ ] License terms reviewed for any new data sources
- [ ] Privacy policy addresses user data handling
- [ ] Terms of service clarify data source licensing

---

## License Summary Table

| Translation | License | Attribution Required | Commercial Use | Redistribution |
|-------------|---------|---------------------|----------------|----------------|
| KJV | Public Domain | No | ✅ Yes | ✅ Yes |
| WEB | Public Domain | No | ✅ Yes | ✅ Yes |
| NIV | © Biblica | **Yes** | ⚠️ Limited | ❌ No |
| ESV | © Crossway | **Yes** | ⚠️ Limited | ❌ No |
| NASB | © Lockman | **Yes** | ⚠️ Limited | ❌ No |
| 개역한글 (KRV) | Public Domain | Recommended | ✅ Yes | ✅ Yes |
| 개역개정 (RKV) | ⚠️ Verify | **Yes** | ⚠️ Contact KBS | ⚠️ Contact KBS |
| SBLGNT | CC BY 4.0 | **Yes** | ✅ Yes | ✅ Yes with attribution |
| WLC | Public Domain | Recommended | ✅ Yes | ✅ Yes |
| Strong's | Public Domain | Recommended | ✅ Yes | ✅ Yes |
| OpenBible Cross-Refs | CC BY 4.0 | **Yes** | ✅ Yes | ✅ Yes with attribution |

---

## Disclaimer

This document provides general information about data sources and licensing. It is not legal advice. For specific licensing questions or commercial use cases, consult with the copyright holders directly or seek legal counsel.

**Last Updated**: 2026-01-13
**Maintained By**: Bible RAG Project Team
**Review Frequency**: Quarterly
