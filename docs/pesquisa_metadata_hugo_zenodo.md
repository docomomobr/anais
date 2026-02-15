# Metadata Standards, Export Formats, and Discoverability for a Static Scholarly Repository

**Context:** Hugo static site + Zenodo for PDFs/DOIs, hosting ~2,300 conference papers from Brazilian architecture conferences (Docomomo Brasil).

**Existing spec already covers:** Highwire Press/Google Scholar meta tags, Dublin Core, Schema.org/JSON-LD, Open Graph, sitemap, Hugo taxonomies, basic HTML structure.

**This report covers what is MISSING.**

---

## Table of Contents

1. [COinS (Context Objects in Spans)](#1-coins-context-objects-in-spans)
2. [Signposting (FAIR Signposting Profile)](#2-signposting-fair-signposting-profile)
3. [Citation Export Formats](#3-citation-export-formats)
4. [Typed Links in HTML Head](#4-typed-links-in-html-head)
5. [What OJS/DSpace Provide That Static Sites Miss](#5-what-ojsdspace-provide-that-static-sites-miss)
6. [Google Scholar Specific Requirements](#6-google-scholar-specific-requirements)
7. [FAIR Principles](#7-fair-principles)
8. [Accessibility (WCAG)](#8-accessibility-wcag)
9. [Hugo Themes and Tools](#9-hugo-themes-and-tools-for-academic-repositories)
10. [Alternative/Complementary Formats](#10-alternativecomplementary-formats)
11. [Prioritized Implementation Plan](#11-prioritized-implementation-plan)

---

## 1. COinS (Context Objects in Spans)

### What it is

COinS (ContextObjects in Spans) is a method for embedding bibliographic metadata in HTML using invisible `<span>` elements. It encodes OpenURL (NISO Z39.88-2004) key-value pairs in the `title` attribute of a span with `class="Z3988"`. Reference managers like Zotero detect these spans and import citation data directly.

### Why it matters

COinS is one of the most effective methods for Zotero integration because it successfully exposes **genre data**, allowing Zotero to detect the correct item type (conference paper vs. journal article vs. book chapter). This is a critical advantage over Highwire Press meta tags, which do not reliably distinguish between publication types.

### Zotero's translator priority order

Zotero processes metadata sources in this order:
1. **Site-specific translators** (priority ~100) -- e.g., dedicated JSTOR, PubMed translators
2. **unAPI** (priority 300)
3. **Embedded Metadata / Highwire Press** (priority 310)
4. **COinS** (priority 320)
5. **DOI** (priority 330)

Since our site will not have a site-specific Zotero translator, COinS serves as a reliable fallback that correctly types the item. Even though Embedded Metadata (Highwire tags) has higher priority, COinS provides genre information that Highwire tags often lack.

### Is it still relevant in 2025-2026?

Yes. Princeton's Center for Digital Humanities published a guide on COinS for Zotero integration in November 2025, confirming it remains actively used. JSON-LD (Schema.org) is gaining ground but Zotero's JSON-LD support is not yet fully mature. COinS remains the most reliable way to expose genre/type metadata to reference managers.

### Conference paper implementation

For conference papers, COinS uses the `book` matrix format with `genre=proceeding`:

```html
<span class="Z3988" title="ctx_ver=Z39.88-2004&amp;rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&amp;rft.genre=proceeding&amp;rft.atitle=T%C3%ADtulo+do+artigo&amp;rft.btitle=12%C2%BA+Semin%C3%A1rio+Docomomo+Brasil&amp;rft.date=2017&amp;rft.aulast=Cappello&amp;rft.aufirst=Maria+Beatriz&amp;rft.place=Uberl%C3%A2ndia&amp;rft.pub=EDUFU&amp;rft.isbn=978-85-64554-03-0&amp;rft.pages=1-15"></span>
```

Key OpenURL fields for conference papers:

| OpenURL Key | Description | Example |
|-------------|-------------|---------|
| `rft_val_fmt` | Format identifier | `info:ofi/fmt:kev:mtx:book` |
| `rft.genre` | Genre | `proceeding` (triggers conferencePaper in Zotero) |
| `rft.atitle` | Article/paper title | Titulo do artigo |
| `rft.btitle` | Book/proceedings title | 12 Seminario Docomomo Brasil |
| `rft.date` | Publication date | 2017 |
| `rft.aulast` | Author last name | Cappello |
| `rft.aufirst` | Author first name | Maria Beatriz |
| `rft.au` | Full author name (alternative) | Maria Beatriz Cappello |
| `rft.place` | Place of publication | Uberlandia |
| `rft.pub` | Publisher | EDUFU |
| `rft.isbn` | ISBN | 978-85-64554-03-0 |
| `rft.pages` | Pages | 1-15 |

### Hugo template snippet

```html
{{/* COinS for conference paper */}}
<span class="Z3988" title="ctx_ver=Z39.88-2004&amp;rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&amp;rft.genre=proceeding&amp;rft.atitle={{ .Params.title | urlquery }}&amp;rft.btitle={{ .Params.conference_title | urlquery }}&amp;rft.date={{ .Params.year }}&amp;{{ range $i, $a := .Params.authors }}{{ if $i }}&amp;{{ end }}rft.au={{ printf "%s %s" $a.givenname $a.familyname | urlquery }}{{ end }}&amp;rft.place={{ .Params.conference_place | urlquery }}&amp;rft.pub={{ .Params.publisher | urlquery }}{{ with .Params.isbn }}&amp;rft.isbn={{ . }}{{ end }}{{ with .Params.pages }}&amp;rft.pages={{ . }}{{ end }}"></span>
```

### Assessment

**Priority: CRITICAL.** COinS is the primary mechanism by which Zotero correctly identifies conference papers. Without it, papers may be imported as generic "Web Page" items. Implementation is trivial (one span tag per article page) and requires zero server infrastructure.

### Does Zenodo handle this?

Zenodo's landing pages include COinS spans, but our Hugo site is the primary discovery interface. Users browsing our site need COinS on our pages, not just on Zenodo.

---

## 2. Signposting (FAIR Signposting Profile)

### What it is

Signposting is a community-driven approach (not a formal W3C standard, but built on IETF standards) that uses **typed links** (RFC 8288) to help machines navigate scholarly objects on the web. It tells bots: "here is the persistent identifier," "here is the content file," "here is the metadata," "here is the license."

The FAIR Signposting Profile (signposting.org/FAIR/) provides concrete recipes for implementing these patterns, organized in two levels.

### How it works with static sites

Signposting can be implemented via:
1. **HTTP Link headers** -- requires server configuration (nginx/Apache), not ideal for static CDN hosting
2. **HTML `<link>` elements** -- works perfectly with static sites, placed in `<head>`
3. **Linksets** (RFC 9264) -- JSON files that group all typed links (for Level 2)

For a Hugo static site, **HTML `<link>` elements are the recommended approach**. They require no server-side configuration and work on any CDN (Netlify, Cloudflare Pages, GitHub Pages).

### Level 1 (Minimum FAIR Signposting)

Level 1 requires typed links provided **by value** in HTML `<link>` elements on the landing page:

| Link Relation | Points To | Cardinality | Required? |
|---------------|-----------|-------------|-----------|
| `cite-as` | Persistent identifier (DOI) | Exactly 1 | MUST |
| `item` | Content resource (PDF) | 1 or more | SHOULD |
| `describedby` | Metadata resource (JSON-LD, DC XML) | 1 or more | SHOULD |
| `type` | Resource type (schema.org class) | 1 or more | SHOULD |
| `author` | Author identifier (ORCID) | 0 or more | MAY |
| `license` | License URI | 0 or 1 | MAY |
| `collection` | Collection the item belongs to | 0 or more | MAY |

### Level 2 (Comprehensive FAIR Signposting)

Level 2 requires typed links provided **by reference** via a Linkset (a JSON file), discoverable through a `<link rel="linkset">` in the HTML. The Linkset includes all Level 1 relations plus additional metadata about content types and profiles.

### HTML implementation for our use case

```html
<head>
  <!-- Signposting Level 1 -->
  <!-- cite-as: the DOI from Zenodo (persistent identifier) -->
  <link rel="cite-as" href="https://doi.org/10.5281/zenodo.XXXXXXX" />

  <!-- item: link to the PDF on Zenodo -->
  <link rel="item" href="https://zenodo.org/records/XXXXXXX/files/sdbr12-001.pdf"
        type="application/pdf" />

  <!-- describedby: link to machine-readable metadata -->
  <link rel="describedby" href="/artigos/sdbr12-001/metadata.json"
        type="application/ld+json" />

  <!-- type: Schema.org type for a scholarly article -->
  <link rel="type" href="https://schema.org/ScholarlyArticle" />

  <!-- author: ORCID for each author (when available) -->
  <link rel="author" href="https://orcid.org/0000-0001-2345-6789" />

  <!-- license -->
  <link rel="license" href="https://creativecommons.org/licenses/by-nc-nd/4.0/" />

  <!-- Level 2: Linkset -->
  <link rel="linkset" href="/artigos/sdbr12-001/linkset.json"
        type="application/linkset+json" />
</head>
```

### Signmap (augmented sitemap)

Signmap extends standard sitemaps with Signposting links using the ResourceSync Framework. For each URL in the sitemap, you can include typed links:

```xml
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:rs="http://www.openarchives.org/rs/terms/">
  <url>
    <loc>https://anais.docomomobrasil.com/artigos/sdbr12-001/</loc>
    <rs:ln rel="cite-as" href="https://doi.org/10.5281/zenodo.XXXXXXX"/>
    <rs:ln rel="item" href="https://zenodo.org/records/XXXXXXX/files/sdbr12-001.pdf"
           type="application/pdf"/>
    <rs:ln rel="describedby" href="https://anais.docomomobrasil.com/artigos/sdbr12-001/metadata.json"
           type="application/ld+json"/>
  </url>
</urlset>
```

### FAIRiCat (FAIR Interoperability Catalogue)

FAIRiCat is a static JSON file that advertises a repository's interoperability affordances. It tells harvesters: "this site supports Signposting Level 1, provides metadata in JSON-LD and Dublin Core, etc." This is useful for automated FAIR assessment tools.

```json
{
  "linkset": [
    {
      "anchor": "https://anais.docomomobrasil.com/",
      "describedby": [
        {
          "href": "https://anais.docomomobrasil.com/fairicat.json",
          "type": "application/linkset+json"
        }
      ]
    }
  ]
}
```

### Who has adopted Signposting?

As of 2025: DSpace 7.x, DSpace-CRIS, OJS, InvenioRDM (and therefore Zenodo), Dataverse, EPrints, DANS, and many others. COAR (Confederation of Open Access Repositories) actively recommends Signposting adoption.

### Assessment

**Priority: RECOMMENDED.** Signposting Level 1 is straightforward to implement via HTML `<link>` elements in Hugo templates. It significantly improves machine discoverability and FAIR compliance. Level 2 (Linksets) and Signmap are nice-to-have additions that can come later.

### Does Zenodo handle this?

Yes, Zenodo (via InvenioRDM) implements FAIR Signposting on its own landing pages. However, our Hugo site is the primary browsing interface, so implementing Signposting on our pages ensures that bots arriving via our site (not via Zenodo) can also navigate to the DOI, PDF, and metadata.

---

## 3. Citation Export Formats

### Overview

Academic repositories typically offer downloadable citation files in multiple formats. These are static files that can be pre-generated during Hugo's build process, one per article.

### 3.1 BibTeX

The standard format for LaTeX users. For conference papers, use `@inproceedings`:

```bibtex
@inproceedings{sdbr12-001,
  author    = {Cappello, Maria Beatriz Camargo and Camisassa, Maria Marta},
  title     = {Titulo do artigo},
  booktitle = {12{\textdegree} Semin{\'a}rio Docomomo Brasil},
  year      = {2017},
  address   = {Uberl{\^a}ndia},
  publisher = {EDUFU},
  pages     = {1--15},
  isbn      = {978-85-64554-03-0},
  doi       = {10.5281/zenodo.XXXXXXX},
  url       = {https://doi.org/10.5281/zenodo.XXXXXXX}
}
```

Key fields for `@inproceedings`: `author`, `title`, `booktitle`, `year`, `address`, `publisher`, `pages`, `isbn`, `doi`, `url`. Optional: `editor`, `series`, `volume`, `organization`, `month`.

### 3.2 RIS

Widely supported by Mendeley, EndNote, and other reference managers. For conference papers, use `TY - CPAPER`:

```
TY  - CPAPER
AU  - Cappello, Maria Beatriz Camargo
AU  - Camisassa, Maria Marta
TI  - Titulo do artigo
BT  - 12 Seminario Docomomo Brasil
PY  - 2017
CY  - Uberlandia
PB  - EDUFU
SP  - 1
EP  - 15
SN  - 978-85-64554-03-0
DO  - 10.5281/zenodo.XXXXXXX
UR  - https://doi.org/10.5281/zenodo.XXXXXXX
AB  - Resumo do artigo...
KW  - Arquitetura Moderna
KW  - Patrimonio Cultural
LA  - pt
ER  -
```

Key RIS tags for conference papers:

| Tag | Field | Notes |
|-----|-------|-------|
| TY | Type | `CPAPER` for conference paper |
| AU | Author | One per line, "Last, First" format |
| TI | Title | Paper title |
| BT | Book Title | Proceedings/conference title |
| PY | Year | Publication year |
| CY | City | Conference city |
| PB | Publisher | Publisher name |
| SP | Start page | First page |
| EP | End page | Last page |
| SN | ISBN/ISSN | ISBN of proceedings |
| DO | DOI | Without URL prefix |
| UR | URL | Full URL |
| AB | Abstract | Full abstract text |
| KW | Keywords | One per line |
| LA | Language | Language code |
| ER | End of record | Must be last line |

### 3.3 CSL-JSON

The native format for Citation Style Language processors (Zotero, Pandoc/citeproc). Most flexible and modern:

```json
{
  "id": "sdbr12-001",
  "type": "paper-conference",
  "title": "Titulo do artigo",
  "container-title": "12 Seminario Docomomo Brasil",
  "publisher": "EDUFU",
  "publisher-place": "Uberlandia",
  "page": "1-15",
  "ISBN": "978-85-64554-03-0",
  "DOI": "10.5281/zenodo.XXXXXXX",
  "URL": "https://doi.org/10.5281/zenodo.XXXXXXX",
  "language": "pt-BR",
  "author": [
    {"family": "Cappello", "given": "Maria Beatriz Camargo"},
    {"family": "Camisassa", "given": "Maria Marta"}
  ],
  "issued": {"date-parts": [[2017]]},
  "event-title": "12 Seminario Docomomo Brasil",
  "event-place": "Uberlandia, MG",
  "abstract": "Resumo do artigo..."
}
```

Key CSL-JSON fields for `paper-conference`: `type`, `title`, `container-title`, `event-title`, `event-place`, `publisher`, `publisher-place`, `page`, `ISBN`, `DOI`, `URL`, `language`, `author`, `issued`, `abstract`.

### 3.4 Dublin Core RDF/XML

For linked data consumers and library systems:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/"
         xmlns:dcterms="http://purl.org/dc/terms/">
  <rdf:Description rdf:about="https://doi.org/10.5281/zenodo.XXXXXXX">
    <dc:title>Titulo do artigo</dc:title>
    <dc:creator>Maria Beatriz Camargo Cappello</dc:creator>
    <dc:creator>Maria Marta Camisassa</dc:creator>
    <dc:date>2017</dc:date>
    <dc:publisher>EDUFU</dc:publisher>
    <dc:language>pt-BR</dc:language>
    <dc:identifier>doi:10.5281/zenodo.XXXXXXX</dc:identifier>
    <dcterms:isPartOf>12 Seminario Docomomo Brasil</dcterms:isPartOf>
    <dc:type>conferenceObject</dc:type>
    <dc:rights>https://creativecommons.org/licenses/by-nc-nd/4.0/</dc:rights>
  </rdf:Description>
</rdf:RDF>
```

### Can all of these be generated statically?

**Yes, absolutely.** All four formats are plain text files that can be generated during Hugo's build process:

1. Create Hugo output formats for `.bib`, `.ris`, `.json` (CSL), and `.xml` (DC-RDF)
2. Create templates for each format in `layouts/artigo/single.bib`, etc.
3. Hugo generates one file per article during build
4. Link to them from the article page with download buttons

### How OJS and DSpace implement citation export

- **OJS**: Uses the `metadataExport` plugin to provide BibTeX, RIS, MARC XML, and RDF downloads. Shows "Cite" button on article pages.
- **DSpace**: DSpace-CRIS offers BibTeX, RIS, and other formats from the item page and search results. Standard DSpace lacks this feature out of the box.

### Hugo implementation approach

```toml
# config.toml - define custom output formats
[outputFormats.BibTeX]
  mediaType = "application/x-bibtex"
  baseName = "cite"
  isPlainText = true

[outputFormats.RIS]
  mediaType = "application/x-research-info-systems"
  baseName = "cite"
  isPlainText = true

[outputFormats.CSLJSON]
  mediaType = "application/vnd.citationstyles.csl+json"
  baseName = "cite"
  isPlainText = true
```

```html
<!-- Download buttons on article page -->
<div class="citation-exports">
  <span>Exportar citacao:</span>
  <a href="cite.bib" download>BibTeX</a>
  <a href="cite.ris" download>RIS</a>
  <a href="cite.json" download>CSL-JSON</a>
</div>
```

### Assessment

**Priority: CRITICAL (BibTeX + RIS), RECOMMENDED (CSL-JSON), NICE-TO-HAVE (DC RDF/XML).**

BibTeX and RIS are the two formats that every researcher expects to find. CSL-JSON is increasingly important for Zotero/Pandoc workflows. DC RDF/XML is useful for linked data but lower priority.

### Does Zenodo handle this?

Zenodo provides BibTeX, CSL-JSON, DataCite XML, Dublin Core, and other formats via content negotiation on DOI URLs. However, researchers browsing our site need download buttons on our pages, not just on Zenodo. The convenience of one-click export from our browsing interface is the key value add.

---

## 4. Typed Links in HTML Head

### 4.1 `<link rel="cite-as">`

**What it does:** Defined in RFC 8574 (IETF Informational, 2019), this link relation conveys the preferred URI for referencing a resource. For scholarly objects, it points to the DOI.

**Is it a W3C standard?** No, it is an IETF RFC (RFC 8574) and is registered in the IANA Link Relations Registry. It is a recognized standard used by DSpace, InvenioRDM/Zenodo, Dataverse, and other major platforms.

```html
<link rel="cite-as" href="https://doi.org/10.5281/zenodo.XXXXXXX" />
```

**Assessment: CRITICAL.** This is the cornerstone of Signposting and tells machines which DOI to use for citing this work.

### 4.2 `<link rel="item">`

**What it does:** Points from the landing page to the content resource (the PDF file). The `type` attribute specifies the media type.

```html
<link rel="item" href="https://zenodo.org/records/XXXXXXX/files/sdbr12-001.pdf"
      type="application/pdf" />
```

**Assessment: RECOMMENDED.** Helps machines find the actual content without parsing the page.

### 4.3 `<link rel="describedby">`

**What it does:** Points from the landing page to machine-readable metadata about the resource. Can point to multiple metadata formats.

```html
<link rel="describedby" href="/artigos/sdbr12-001/cite.json"
      type="application/vnd.citationstyles.csl+json" />
<link rel="describedby" href="/artigos/sdbr12-001/metadata.json"
      type="application/ld+json" />
```

**Assessment: RECOMMENDED.** Enables automated metadata harvesting without scraping HTML.

### 4.4 `<link rel="license">`

**What it does:** Points to the license that governs the resource. This is part of the ccREL (Creative Commons Rights Expression Language) standard and is recognized by search engines for license discovery.

```html
<link rel="license" href="https://creativecommons.org/licenses/by-nc-nd/4.0/" />
```

**Assessment: RECOMMENDED.** Machine-readable license declaration. Critical for reuse and FAIR compliance.

### 4.5 `<link rel="author">`

**What it does:** In Signposting context, points to author identifiers (ORCID URIs). Standard HTML already supports this for linking to author pages.

```html
<link rel="author" href="https://orcid.org/0009-0008-4670-9812" />
```

**Assessment: NICE-TO-HAVE.** Useful for Signposting completeness but not widely consumed yet.

### 4.6 OpenURL / Link Resolvers

Static sites do not need to implement OpenURL resolver functionality. COinS (Section 1) handles the OpenURL embedding. Library link resolvers will pick up COinS spans automatically.

**Assessment: NOT NEEDED.** COinS covers this.

### Combined Hugo template for typed links

```html
{{/* Typed links in <head> */}}
{{ with .Params.doi }}
<link rel="cite-as" href="https://doi.org/{{ . }}" />
{{ end }}

{{ with .Params.zenodo_pdf_url }}
<link rel="item" href="{{ . }}" type="application/pdf" />
{{ end }}

<link rel="describedby" href="{{ .RelPermalink }}cite.json"
      type="application/vnd.citationstyles.csl+json" />

{{ with .Params.license_url }}
<link rel="license" href="{{ . }}" />
{{ end }}

{{ range .Params.authors }}
  {{ with .orcid }}
<link rel="author" href="https://orcid.org/{{ . }}" />
  {{ end }}
{{ end }}

<link rel="type" href="https://schema.org/ScholarlyArticle" />
```

---

## 5. What OJS/DSpace Provide That Static Sites Typically Miss

### 5.1 OAI-PMH

**What it is:** The Open Archives Initiative Protocol for Metadata Harvesting is the standard protocol for metadata harvesting used by aggregators (DOAJ, BASE, OpenAIRE, Google Scholar).

**Can a static site provide OAI-PMH?**

Yes, via the **OAI-PMH Static Repository** specification (openarchives.org/OAI/2.0/guidelines-static-repository.htm). A Static Repository is a single XML file hosted at a persistent URL that contains all metadata records. It does not need to respond to OAI-PMH requests dynamically -- instead, a third-party **Static Repository Gateway** intermediates between harvesters and the static XML file.

Limitations of static repositories:
- No sets support
- No deleted records
- No resumptionTokens
- Granularity limited to YYYY-MM-DD

For our ~2,300 records, the XML file would be manageable (estimated ~5-10 MB).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Repository xmlns="http://www.openarchives.org/OAI/2.0/static-repository"
            xmlns:oai="http://www.openarchives.org/OAI/2.0/"
            xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
            xmlns:dc="http://purl.org/dc/elements/1.1/">
  <Identify>
    <oai:repositoryName>Anais Docomomo Brasil</oai:repositoryName>
    <oai:baseURL>https://anais.docomomobrasil.com/oai-static.xml</oai:baseURL>
    <oai:protocolVersion>2.0</oai:protocolVersion>
    <oai:adminEmail>admin@docomomobrasil.com</oai:adminEmail>
    <oai:earliestDatestamp>1995-01-01</oai:earliestDatestamp>
    <oai:deletedRecord>no</oai:deletedRecord>
    <oai:granularity>YYYY-MM-DD</oai:granularity>
  </Identify>
  <ListMetadataFormats>
    <oai:metadataFormat>
      <oai:metadataPrefix>oai_dc</oai:metadataPrefix>
      <oai:schema>http://www.openarchives.org/OAI/2.0/oai_dc.xsd</oai:schema>
      <oai:metadataNamespace>http://www.openarchives.org/OAI/2.0/oai_dc/</oai:metadataNamespace>
    </oai:metadataFormat>
  </ListMetadataFormats>
  <ListRecords metadataPrefix="oai_dc">
    <oai:record>
      <oai:header>
        <oai:identifier>oai:anais.docomomobrasil.com:sdbr12-001</oai:identifier>
        <oai:datestamp>2017-11-24</oai:datestamp>
      </oai:header>
      <oai:metadata>
        <oai_dc:dc>
          <dc:title>Titulo do artigo</dc:title>
          <dc:creator>Cappello, Maria Beatriz Camargo</dc:creator>
          <dc:date>2017</dc:date>
          <dc:type>conferenceObject</dc:type>
          <dc:identifier>https://doi.org/10.5281/zenodo.XXXXXXX</dc:identifier>
          <dc:language>pt</dc:language>
        </oai_dc:dc>
      </oai:metadata>
    </oai:record>
    <!-- ... more records ... -->
  </ListRecords>
</Repository>
```

This XML can be generated during Hugo build from the same data source.

**Assessment: RECOMMENDED.** Generating a static OAI-PMH XML file is feasible and would enable harvesting by aggregators like BASE and OpenAIRE. However, finding an active Static Repository Gateway is the challenge -- the infrastructure is not widely maintained. An alternative is to register the OJS instance (which already has OAI-PMH) as the harvesting endpoint and use the Hugo site for human browsing only.

**Practical recommendation:** Since OJS already provides OAI-PMH for the same content, and Zenodo provides DataCite harvesting, generating a static OAI-PMH file is **nice-to-have** rather than critical. The content is already harvestable through OJS.

### 5.2 SWORD Protocol

**What it is:** Simple Web-service Offering Repository Deposit. Allows automated deposit of content into repositories.

**Assessment: NOT NEEDED.** SWORD is for accepting deposits. Our site is read-only. Zenodo handles deposits via its API.

### 5.3 Machine-Readable License Declarations

**What OJS/DSpace do:** Include license metadata in OAI-PMH records, HTML meta tags, and API responses.

**What we need:** `<link rel="license">` in HTML head (covered in Section 4.4), plus license in Schema.org JSON-LD, Dublin Core meta tags, and Signposting. Also include `<meta name="DC.rights" content="...">` and the `license` field in CSL-JSON exports.

**Assessment: CRITICAL.** Must be implemented consistently across all metadata channels.

### 5.4 Usage Statistics

**What OJS/DSpace do:** Track downloads and views, often COUNTER-compliant. OJS has built-in statistics; DSpace integrates with usage tracking.

**Alternatives for static sites:**
- **Plausible Analytics** -- lightweight, privacy-friendly, GDPR-compliant, hosted or self-hosted. ~1KB script. $9/month hosted.
- **GoatCounter** -- open source, cookieless, no personal data collected. Free hosted tier for non-commercial use. 2.3KB script.
- **Umami** -- open source, self-hosted. Feature-rich dashboard.
- **Cloudflare Web Analytics** -- free if using Cloudflare, no cookies, privacy-first.

None of these are COUNTER-compliant, but COUNTER compliance is not required for conference proceedings repositories. COUNTER is primarily for journal subscriptions.

**Practical recommendation:** GoatCounter for free tier, or Plausible for a polished dashboard. Implement as a simple script tag.

**Assessment: RECOMMENDED.** Basic analytics help demonstrate impact. GoatCounter or Plausible is sufficient.

### 5.5 Author Pages with Aggregated Metrics

**What OJS/DSpace do:** OJS has author browse pages; DSpace-CRIS has rich author profiles.

**What we can do:** Hugo taxonomy pages for authors (already in the spec). To add metrics, we could:
- Display article count per author
- Link to ORCID profiles (we have 1107 authors with ORCIDs)
- Link to Google Scholar profiles where available
- Show co-authorship network (static, pre-generated)

**Assessment: NICE-TO-HAVE.** Author taxonomy pages with ORCID links are sufficient. Rich metrics can come later.

### 5.6 "Cited By" Functionality

**What OJS/DSpace do:** Some installations show citing articles via Crossref Cited-by or Dimensions.

**Alternatives for static sites:**
- **OpenCitations API (COCI)**: Query `https://api.opencitations.net/index/v1/citations/{doi}` for open citation data. Returns JSON.
- **Crossref Cited-by**: If DOIs are registered with Crossref (via ABEC), the Crossref API provides cited-by data.
- **Dimensions Badge**: JavaScript widget that shows citation count.
- **Semantic Scholar API**: Free academic API for citation data.

Implementation approaches:
1. **Build-time**: Query APIs during Hugo build, embed counts in pages (stale but fast)
2. **Client-side**: JavaScript widget that queries API on page load (always current but requires API call)
3. **Hybrid**: Build-time counts with a "Check for updates" client-side button

**Assessment: NICE-TO-HAVE.** Most of our conference papers may have few citations. Can be added later when DOIs are registered.

### 5.7 Social Sharing Metadata

**What it covers:** Open Graph (og:), Twitter Cards, and general social sharing previews.

**Assessment: Already in the existing spec** (Open Graph mentioned). Ensure full implementation:

```html
<!-- Open Graph -->
<meta property="og:title" content="{{ .Title }}" />
<meta property="og:type" content="article" />
<meta property="og:url" content="{{ .Permalink }}" />
<meta property="og:description" content="{{ .Params.abstract | truncate 200 }}" />
<meta property="og:site_name" content="Anais Docomomo Brasil" />
{{ with .Params.thumbnail }}
<meta property="og:image" content="{{ . | absURL }}" />
{{ end }}

<!-- Twitter Card -->
<meta name="twitter:card" content="summary" />
<meta name="twitter:title" content="{{ .Title }}" />
<meta name="twitter:description" content="{{ .Params.abstract | truncate 200 }}" />
```

---

## 6. Google Scholar Specific Requirements

### 6.1 Official Requirements (from scholar.google.com/intl/en/scholar/inclusion.html)

1. **File format**: HTML or PDF. Each file must not exceed **5 MB**.
2. **One article per file**: Each article and each abstract must be in a separate HTML or PDF file.
3. **Crawlable URLs**: Robots must be able to discover and fetch all article URLs. A "browse" interface (table of contents, index page) is necessary.
4. **Meta tags**: Must include `citation_title` at minimum. For conference papers, include `citation_conference_title`, `citation_author`, `citation_publication_date`, `citation_pdf_url`, and `citation_firstpage`.
5. **Abstract visible**: The abstract must be visible to all users without login.
6. **PDF link**: The `citation_pdf_url` meta tag must point to a directly accessible PDF (no login walls).

### 6.2 Does Google Scholar require the PDF to be directly hosted?

Google Scholar **does not require** that the PDF be on the same server. The `citation_pdf_url` can point to an external URL (e.g., Zenodo). However:

- The PDF must be **directly accessible** without login
- The URL should resolve to the actual PDF (not an interstitial page)
- Zenodo's direct file URLs (e.g., `https://zenodo.org/records/XXXXXXX/files/paper.pdf`) work correctly
- DOI redirect URLs (e.g., `https://doi.org/10.5281/...`) should **not** be used as `citation_pdf_url` because they redirect to a landing page, not the PDF itself

### 6.3 Does Google Scholar index static sites?

**Yes.** Google Scholar indexes any publicly accessible site with proper meta tags. There is no requirement to use OJS, DSpace, or any specific platform. The key requirements are:

- Proper Highwire Press meta tags
- Crawlable URL structure
- Browse interface for discovery
- Publicly accessible content

### 6.4 Indexing timeline

- **Initial indexing**: 6-9 months after request/discovery
- **Subsequent updates**: Every few weeks once the site is trusted
- **Submission**: Use the [Google Scholar inclusion request form](https://partnerdash.google.com/partnerdash/d/scholarinclusions) to request indexing

### 6.5 Complete meta tags for conference papers

```html
<!-- Required -->
<meta name="citation_title" content="Titulo do artigo" />
<meta name="citation_author" content="Cappello, Maria Beatriz Camargo" />
<meta name="citation_author" content="Camisassa, Maria Marta" />
<meta name="citation_publication_date" content="2017/11/24" />
<meta name="citation_conference_title" content="12 Seminario Docomomo Brasil" />
<meta name="citation_pdf_url" content="https://zenodo.org/records/XXXXXXX/files/sdbr12-001.pdf" />

<!-- Strongly recommended for proper citation matching -->
<meta name="citation_firstpage" content="1" />
<meta name="citation_lastpage" content="15" />
<meta name="citation_isbn" content="978-85-64554-03-0" />

<!-- Optional but helpful -->
<meta name="citation_doi" content="10.5281/zenodo.XXXXXXX" />
<meta name="citation_language" content="pt" />
<meta name="citation_abstract_html_url" content="{{ .Permalink }}" />
<meta name="citation_keywords" content="Arquitetura Moderna; Patrimonio Cultural" />

<!-- Author institutional affiliation (one per author, matching order) -->
<meta name="citation_author_institution" content="EDUFU" />
<meta name="citation_author_institution" content="UFU" />

<!-- Author ORCID -->
<meta name="citation_author_orcid" content="https://orcid.org/0000-0001-2345-6789" />
```

**Important notes:**
- `citation_conference_title` (not `citation_journal_title`) for conference papers
- `citation_publication_date` format: `YYYY/MM/DD` or `YYYY`
- One `citation_author` tag per author, in order
- Tags not in Google's official list (like `citation_doi`, `citation_keywords`) are "undefined" in their documentation but widely used and seemingly processed

### 6.6 File size and structure

- PDFs must not exceed 5 MB for Google Scholar indexing (larger files are only indexed via Google Books)
- Some of our PDFs may exceed this limit -- worth auditing
- PDF text must be searchable (not scanned images without OCR)
- Each article needs its own unique URL

### Assessment

**Priority: CRITICAL.** Google Scholar is the primary discovery mechanism for researchers. The existing spec covers Highwire tags, but we must ensure:

1. `citation_conference_title` (not `citation_journal_title`) is used
2. `citation_pdf_url` points to Zenodo's direct file URL (not DOI URL)
3. Browse pages exist for crawler discovery
4. PDFs are under 5 MB or flagged for OCR split
5. Submit the site for inclusion after launch

### Does Zenodo handle this?

Zenodo is indexed by Google Scholar independently. However, our Hugo site provides a richer browsing experience (by conference, by section, by author) and conference-specific metadata that Zenodo does not have (conference_title, section, etc.). Both should be indexed.

---

## 7. FAIR Principles

### The four principles applied to our static site

| Principle | Requirement | How We Cover It |
|-----------|-------------|-----------------|
| **Findable** | Persistent identifiers | DOIs from Zenodo |
| | Rich metadata | JSON-LD, DC, Highwire tags, COinS |
| | Indexed in searchable resource | Google Scholar, OJS OAI-PMH, Zenodo |
| **Accessible** | Retrievable by identifier | DOI resolves to Zenodo; our site is open |
| | Open protocol (HTTP) | Yes, static site over HTTPS |
| | Metadata available even if data gone | Zenodo guarantees long-term preservation |
| **Interoperable** | Formal metadata schemas | Schema.org, Dublin Core, COinS |
| | FAIR vocabularies | ORCID for authors, DOI for objects |
| | Qualified references | Signposting typed links |
| **Reusable** | Clear license | `<link rel="license">`, DC.rights, JSON-LD |
| | Provenance | Conference metadata, dates, publisher |
| | Community standards | Highwire Press, CSL-JSON, BibTeX, RIS |

### What else is needed?

1. **Signposting** (Section 2) is the primary gap -- it directly addresses the "A" (Accessible) in FAIR by providing machine-navigable typed links.

2. **FAIRiCat** -- a static JSON file advertising interoperability affordances. Helps automated FAIR assessment tools (like F-UJI) evaluate the site.

3. **DataCite metadata linking** -- Zenodo registers metadata with DataCite. From our site, we should link to DataCite's metadata via:
   ```html
   <link rel="describedby"
         href="https://data.crossref.org/10.5281/zenodo.XXXXXXX"
         type="application/vnd.citationstyles.csl+json" />
   ```

4. **Machine-actionable license** -- not just a text mention but a URI in metadata.

### Assessment

**Priority: Signposting is RECOMMENDED; FAIRiCat is NICE-TO-HAVE.**

The existing spec (JSON-LD, DC, DOI from Zenodo) already covers most FAIR requirements. Signposting adds the machine-navigability layer. FAIRiCat advertises these affordances to automated tools.

---

## 8. Accessibility (WCAG)

### Key requirements (WCAG 2.2, Level AA)

WCAG 2.2 is the current standard, with Level AA being the most common compliance target. The US DOJ mandates WCAG 2.1 Level AA by April 2026 for public entities, though this does not directly apply to a Brazilian nonprofit. However, following WCAG best practices is important for inclusivity.

### Requirements for scholarly repository pages

#### Perceivable
- **Text alternatives**: All images (cover thumbnails, figures) must have `alt` text
- **Meaningful sequence**: Reading order must make sense without CSS
- **Contrast**: Text contrast ratio of at least 4.5:1 (3:1 for large text)
- **Resizable text**: Content must be usable at 200% zoom

#### Operable
- **Keyboard navigation**: All interactive elements (search, download buttons, filters) must be keyboard-accessible
- **Skip navigation**: Provide "Skip to content" link
- **Focus indicators**: Visible focus styles on all interactive elements

#### Understandable
- **Language declaration**: `<html lang="pt-BR">` on all pages
- **Consistent navigation**: Same navigation structure across all pages
- **Error handling**: Form validation for search provides clear error messages

#### Robust
- **Valid HTML**: Proper semantic markup
- **ARIA landmarks**: Define page regions

### ARIA landmarks for article pages

```html
<body>
  <header role="banner">
    <nav role="navigation" aria-label="Navegacao principal">...</nav>
  </header>

  <main role="main" id="main-content">
    <article role="article">
      <header>
        <h1>{{ .Title }}</h1>
        <div role="contentinfo" aria-label="Metadados do artigo">
          <span>Autores: ...</span>
          <span>Publicado em: ...</span>
        </div>
      </header>

      <section aria-label="Resumo">
        <h2>Resumo</h2>
        <p>{{ .Params.abstract }}</p>
      </section>

      <section aria-label="Palavras-chave">
        <h2>Palavras-chave</h2>
        <ul>{{ range .Params.keywords }}<li>{{ . }}</li>{{ end }}</ul>
      </section>

      <nav aria-label="Exportar citacao">
        <h2>Exportar citacao</h2>
        <ul>
          <li><a href="cite.bib" download>BibTeX</a></li>
          <li><a href="cite.ris" download>RIS</a></li>
        </ul>
      </nav>
    </article>
  </main>

  <footer role="contentinfo">...</footer>
</body>
```

### Screen reader compatibility with metadata-heavy pages

- **Hidden metadata spans** (COinS, JSON-LD): Already invisible to screen readers since they use `<span>` with no visible text or `<script type="application/ld+json">`
- **Meta tags**: Invisible to screen readers by design
- **Download links**: Use descriptive text ("Baixar citacao em formato BibTeX") rather than just "BibTeX"
- **Author lists**: Use ordered `<ol>` for authors to convey authorship order

### Assessment

**Priority: RECOMMENDED.** WCAG 2.2 Level AA compliance is good practice. Key items: language declaration, ARIA landmarks, keyboard navigation, image alt text, contrast ratios. Most of these are Hugo theme concerns rather than metadata concerns.

---

## 9. Hugo Themes and Tools for Academic Repositories

### 9.1 Existing Hugo themes

No existing Hugo theme is specifically designed for a **scholarly repository** (article hosting with metadata). The closest options are:

- **HugoBlox (formerly Wowchemy/Academic)**: Designed for academic personal sites and lab groups. Has publication listing from BibTeX, but oriented toward a researcher's CV, not a repository. 250,000+ users.
- **PaperMod academic template** (Pascal Michaillat): Minimalist academic personal site. Not repository-oriented.
- **Academia Hugo**: Resume/portfolio theme, not repository.

**Recommendation:** Build a custom Hugo theme or modify an existing minimal theme. None of the existing themes handle the repository use case (browse by conference, section, author; citation exports; scholarly metadata).

### 9.2 Hugo-cite

[Hugo-cite](https://github.com/loup-brun/hugo-cite) is a Hugo module for managing bibliography and in-text citations. It:
- Uses CSL-JSON as input format
- Provides shortcodes for in-text citations
- Generates rich, semantic HTML with embedded microdata
- Supports multiple citation styles

**Relevance for our project:** Limited. Hugo-cite is for **citing references within content**, not for **exposing article metadata to machines**. It could be useful if we display reference lists for articles that have `referencias` fields.

### 9.3 Client-side search

| Tool | Index Size (2300 pages) | Load Time | Features | Recommendation |
|------|-------------------------|-----------|----------|----------------|
| **Pagefind** | ~2-5 MB chunked | Fast (chunks loaded on demand) | Full-text, highlighting, filtering | **Best choice** |
| **Fuse.js** | Full dataset in memory | Slow for 2300 items | Fuzzy matching, simple API | Not suitable at this scale |
| **Lunr.js** | Pre-built index ~5-10 MB | Moderate | Full-text, stemming, 14 languages | Possible but Pagefind is better |
| **FlexSearch** | Compact index | Fast | Memory-efficient, fuzzy matching | Good alternative to Pagefind |

**Pagefind** is the clear winner for our use case:
- Designed specifically for static sites
- Index is split into chunks (only loads what is needed for the query)
- Works with any static site generator
- Index size ~1/1000th of content size
- Supports filtering by data attributes (could filter by conference, year, section)
- No server required
- 1-week cache headers for performance
- Integrates with Hugo via post-build indexing

```bash
# After Hugo build
npx pagefind --site public --glob "artigos/**/*.html"
```

### Assessment

**Priority: Pagefind search is CRITICAL for usability.** For 2,300 articles, client-side search is essential. Pagefind is the recommended solution. No existing Hugo theme fits our needs; a custom theme is required.

---

## 10. Alternative/Complementary Formats

### 10.1 MODS (Metadata Object Description Schema)

**What it is:** Library of Congress standard, a simplified alternative to MARC 21 for digital library objects. XML-based, richer than Dublin Core but simpler than full MARC.

**Needed?** No. MODS is used primarily by digital library systems (Islandora, Fedora) for internal metadata management. Our content is not being ingested into a MODS-based system. Dublin Core and Schema.org cover our needs.

**Assessment: NOT NEEDED.**

### 10.2 MARCXML

**What it is:** XML serialization of MARC 21 (Machine-Readable Cataloging), the standard for library catalogs worldwide.

**Needed?** No. MARCXML is for library catalog systems (OCLC WorldCat, institutional OPACs). If a library wants to catalog our proceedings, they would use WorldCat or their local catalog, not harvest MARCXML from our site. Providing Dublin Core (which is the "lowest common denominator" for OAI-PMH) is sufficient.

**Assessment: NOT NEEDED.**

### 10.3 DataCite Metadata

**What it is:** The metadata schema used by DataCite for DOI registration. Zenodo registers all DOIs with DataCite and provides metadata in DataCite XML and JSON formats.

**How to link from our static site:**

```html
<!-- Link to DataCite metadata for the DOI -->
<link rel="describedby"
      href="https://api.datacite.org/dois/10.5281/zenodo.XXXXXXX"
      type="application/vnd.api+json" />
```

Additionally, DataCite supports content negotiation on DOI URLs:
```
# Get DataCite XML
curl -H "Accept: application/vnd.datacite.datacite+xml" https://doi.org/10.5281/zenodo.XXXXXXX

# Get Schema.org JSON-LD
curl -H "Accept: application/vnd.schemaorg.ld+json" https://doi.org/10.5281/zenodo.XXXXXXX

# Get BibTeX
curl -H "Accept: application/x-bibtex" https://doi.org/10.5281/zenodo.XXXXXXX
```

**Zenodo already handles DataCite registration and metadata provision.** Our site just needs to link to the DOI and optionally to the DataCite API endpoint.

**Assessment: Already handled by Zenodo.** Adding a `<link rel="describedby">` pointing to DataCite is NICE-TO-HAVE.

---

## 11. Prioritized Implementation Plan

### TIER 1: CRITICAL (must have for scholarly discoverability)

These are non-negotiable for a scholarly repository that wants to be taken seriously by researchers and indexed by Google Scholar.

| # | Item | Effort | Section |
|---|------|--------|---------|
| 1 | **Google Scholar meta tags** (Highwire Press) with `citation_conference_title`, correct `citation_pdf_url` pointing to Zenodo direct file URL | Low | 6 |
| 2 | **COinS spans** on every article page (genre=proceeding for Zotero) | Low | 1 |
| 3 | **BibTeX + RIS export files** per article (pre-generated, download buttons) | Medium | 3 |
| 4 | **`<link rel="cite-as">`** pointing to DOI | Low | 4.1 |
| 5 | **`<link rel="license">`** with CC license URI | Low | 4.4 |
| 6 | **Machine-readable license** in JSON-LD, DC meta tags, and export files | Low | 5.3 |
| 7 | **Browse pages** for Google Scholar crawler discovery (by conference, by section) | Medium | 6 |
| 8 | **Pagefind client-side search** | Medium | 9.3 |
| 9 | **Submit to Google Scholar** via inclusion request form after launch | Low | 6.4 |

### TIER 2: RECOMMENDED (significantly improves the site)

These additions substantially improve machine interoperability, FAIR compliance, and researcher experience.

| # | Item | Effort | Section |
|---|------|--------|---------|
| 10 | **Signposting Level 1** (`cite-as`, `item`, `describedby`, `type`, `license` link elements) | Low | 2 |
| 11 | **CSL-JSON export files** per article | Medium | 3.3 |
| 12 | **`<link rel="item">`** pointing to PDF on Zenodo | Low | 4.2 |
| 13 | **`<link rel="describedby">`** pointing to metadata files | Low | 4.3 |
| 14 | **Privacy-friendly analytics** (GoatCounter or Plausible) | Low | 5.4 |
| 15 | **WCAG 2.2 Level AA** compliance (ARIA landmarks, keyboard nav, contrast, alt text) | Medium | 8 |
| 16 | **Signmap** (augmented sitemap with typed links) | Medium | 2 |
| 17 | **OAI-PMH Static Repository XML** (generated at build time) | High | 5.1 |

### TIER 3: NICE-TO-HAVE (can add later)

These are refinements that add polish but are not essential for launch.

| # | Item | Effort | Section |
|---|------|--------|---------|
| 18 | **Dublin Core RDF/XML export** per article | Medium | 3.4 |
| 19 | **Signposting Level 2** (Linksets in JSON) | Medium | 2 |
| 20 | **FAIRiCat** (interoperability catalogue JSON file) | Low | 2 |
| 21 | **`<link rel="author">`** with ORCID URIs | Low | 4.5 |
| 22 | **DataCite API link** in `<link rel="describedby">` | Low | 10.3 |
| 23 | **"Cited by" counts** from OpenCitations or Crossref API | High | 5.6 |
| 24 | **Author pages** with article counts and ORCID links | Medium | 5.5 |
| 25 | **Social sharing preview images** (auto-generated OG images) | Medium | 5.7 |
| 26 | **hugo-cite** integration for reference lists | Low | 9.2 |

### NOT NEEDED

| Item | Reason | Section |
|------|--------|---------|
| SWORD Protocol | Read-only site; deposits via Zenodo | 5.2 |
| MODS | For internal digital library systems; DC suffices | 10.1 |
| MARCXML | For library catalogs; not our concern | 10.2 |
| DataCite metadata generation | Zenodo handles this | 10.3 |
| OpenURL resolver | COinS covers this | 4.6 |
| COUNTER-compliant statistics | For journal subscriptions, not conference proceedings | 5.4 |

---

## Summary of Key Findings

1. **COinS is critical** and often overlooked by static site builders. It is the only reliable way for Zotero to detect conference papers as the correct item type.

2. **Signposting is the emerging standard** for scholarly web interoperability, adopted by all major platforms (DSpace, InvenioRDM/Zenodo, OJS). Implementing Level 1 is straightforward and positions the site as a serious scholarly resource.

3. **Google Scholar will index static sites** -- there is no requirement to use OJS or DSpace. The key is proper Highwire Press meta tags, a crawlable structure, and a direct PDF URL in `citation_pdf_url`.

4. **Citation export files (BibTeX + RIS) are essential**. Every researcher expects a "Cite" button. These can be pre-generated statically during Hugo build.

5. **Zenodo handles DOIs, DataCite registration, OAI-PMH harvesting, and long-term preservation.** The Hugo site's role is to provide the best browsing experience and scholarly metadata for Google Scholar and reference managers.

6. **Pagefind is the recommended search solution** for a 2,300-article static site. It is purpose-built for this use case and outperforms Fuse.js and Lunr.js at this scale.

7. **OAI-PMH Static Repository is feasible** but lower priority since OJS already provides OAI-PMH for the same content.

---

## Sources

### COinS
- [Zotero Documentation: COinS](https://www.zotero.org/support/dev/exposing_metadata/coins)
- [CDH Princeton: Building COinS for Zotero Integration (2025)](https://cdh.princeton.edu/blog/2025/11/11/building-coins-for-zotero-integration/)
- [CDH Princeton: A Guide to Zotero Integration for Academic Websites (2025)](https://cdh.princeton.edu/blog/2025/11/11/making-research-easier-to-save-a-guide-to-zotero-integration-for-academic-websites/)
- [Wikipedia: COinS](https://en.wikipedia.org/wiki/COinS)

### Signposting
- [Signposting the Scholarly Web](https://signposting.org/)
- [FAIR Signposting Profile](https://signposting.org/FAIR/)
- [Signposting Adopters](https://signposting.org/adopters/)
- [FAIRiCat Specification](https://signposting.org/FAIRiCat/)
- [Signmap Specification](https://signposting.org/Signmap/)
- [COAR: Supporting the "A" in FAIR](https://www.coar-repositories.org/news-updates/supporting-the-a-in-fair-improving-machine-access-to-repository-resources-through-the-adoption-of-signposting/)
- [DSpace Signposting Documentation](https://wiki.lyrasis.org/display/DSDOC7x/Signposting)
- [Signposting in InvenioRDM](https://zenodo.org/records/12554416)
- [Introduction to Signposting (2024)](https://s11.no/2024/signposting-intro/)

### Citation Formats
- [BibTeX inproceedings template](https://www.bibtex.com/t/template-inproceedings/)
- [RIS file format (Wikipedia)](https://en.wikipedia.org/wiki/RIS_(file_format))
- [CSL-JSON specification](https://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html)
- [CSL Data Model and Mappings](https://github.com/citation-style-language/schema/wiki/Data-Model-and-Mappings)
- [OJS metadataExport plugin (BibTeX, RIS, MARC XML, RDF)](https://github.com/ojsde/metadataExport)

### Typed Links
- [RFC 8574: cite-as Link Relation](https://www.rfc-editor.org/rfc/rfc8574.html)
- [RFC 8288: Web Linking](https://httpwg.org/specs/rfc8288.html)
- [ccREL: Creative Commons Rights Expression Language](https://opensource.creativecommons.org/ccrel/)
- [Creative Commons: License Properties](https://wiki.creativecommons.org/wiki/License_Properties)

### Google Scholar
- [Google Scholar Inclusion Guidelines](https://scholar.google.com/intl/en/scholar/inclusion.html)
- [Google Scholar Support for Publishers](https://scholar.google.com/intl/en/scholar/publishers.html)
- [DSpace: Google Scholar Metadata Mappings](https://wiki.lyrasis.org/display/DSDOC7x/Google+Scholar+Metadata+Mappings)
- [Greenlane: The Current State of Google Scholar](https://www.greenlanemarketing.com/resources/articles/the-current-state-of-google-scholar)
- [Scholastica: Google Scholar Indexing FAQ](https://blog.scholasticahq.com/post/why-having-your-journal-indexed-in-google-scholar-matters-more-than-ever-and-steps-to-get-started/)

### FAIR Principles
- [GO FAIR Principles](https://www.go-fair.org/fair-principles/)
- [Zenodo FAIR Principles](https://about.zenodo.org/principles/)
- [The FAIR Guiding Principles (Nature, 2016)](https://www.nature.com/articles/sdata201618)

### OAI-PMH
- [OAI-PMH Static Repository Specification](https://www.openarchives.org/OAI/2.0/guidelines-static-repository.htm)
- [OAI-PMH Protocol](https://www.openarchives.org/pmh/)

### COAR
- [COAR Notify Protocol](https://coar-notify.net/)
- [COAR Next Generation Repositories](https://coar-repositories.org/next-generation-repositories/)
- [COAR Strategy 2026-2028](https://coar-repositories.org/wp-content/uploads/2025/12/COAR-Strategy-and-Action-Plan-2026-1.pdf)

### Accessibility
- [WCAG 2.2 Overview (W3C)](https://www.w3.org/WAI/standards-guidelines/wcag/)
- [Federal Accessibility Requirements for Higher Ed (2025)](https://onlinelearningconsortium.org/olc-insights/2025/09/federal-digital-a11y-requirements/)

### Hugo Tools
- [Pagefind: Static search at scale](https://pagefind.app/)
- [Hugo-cite: Bibliography management for Hugo](https://github.com/loup-brun/hugo-cite)
- [HugoBlox (formerly Academic/Wowchemy)](https://hugoblox.com/templates/)

### Analytics
- [GoatCounter](https://www.goatcounter.com)
- [Plausible Analytics](https://plausible.io/)

### Citations
- [OpenCitations API](https://api.opencitations.net/)
- [Initiative for Open Citations (I4OC)](https://i4oc.org/)
- [DataCite Content Negotiation](https://support.datacite.org/docs/datacite-content-resolver)

---

*Pesquisa realizada em 2026-02-13.*
