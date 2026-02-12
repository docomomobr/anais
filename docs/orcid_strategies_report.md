# ORCID Integration Strategies: Evaluation Report

**Project:** Anais Docomomo Brasil
**Date:** 2026-02-11
**Context:** 2108 authors, 751 with ORCIDs (35.6%), ~1357 remaining

---

## Current State

The existing script (`scripts/fetch_orcid.py`) searches the ORCID Public API v3.0 using `family-name` + `given-names` (first real name), then validates results by checking employments for Brazilian affiliations. Results from a complete run:

| Category | Count | Description |
|----------|-------|-------------|
| confirmed | 264 | Single BR match, auto-applied |
| candidates | 616 | Ambiguous, need manual review |
| not_found | 424 | No API results |
| too_many | 638 | >20 results, search too broad |
| skipped | 3 | Initials only or API error |

**Key bottleneck:** 638 authors (33% of total without ORCID) return too many results with name-only search. Of these, only 107 have affiliation data in our database that could be used as an additional filter. The remaining 531 have no affiliation to narrow the search.

**Articles with DOIs in database:** Only 3 articles have DOIs, all sandbox DOIs (`10.5072/zenodo.*`) from sdnne08 testing. These are not real DOIs and are not findable in ORCID or Crossref.

**sdbr15 and sdnne10:** These two seminars (101 + 85 = 186 articles, ~318 unique authors) have Even3/Crossref DOIs (prefix `10.29327`), but the DOIs are not stored in our `anais.db`. They exist in the Even3 platform and Crossref. A search of the ORCID API for `digital-object-ids:10.29327` returns 7,255 results, suggesting some Even3 authors have added these publications to their ORCID records.

---

## Strategy 1: ORCID API with Solr Syntax (Affiliation Fields)

### What it is

Enhance the current `fetch_orcid.py` to use additional ORCID search fields beyond `family-name` + `given-names`:

- `affiliation-org-name:"Universidade Federal do Rio Grande do Sul"` (free-text org name)
- `grid-org-id:grid.11899.38` (GRID identifier, legacy but well-populated)
- `ror-org-id:036rp1748` (ROR identifier, current standard but sparse in ORCID)
- `ringgold-org-id:NNNNN` (deprecated since August 2023, still indexed)

### Live API tests performed

| Query | Results |
|-------|---------|
| `affiliation-org-name:"Universidade de Sao Paulo"` | 62,209 |
| `affiliation-org-name:"Universidade Federal do Rio Grande do Sul"` | 18,623 |
| `affiliation-org-name:"Universidade Federal da Bahia"` | 13,449 |
| `grid-org-id:grid.11899.38` (USP GRID) | 4,225 |
| `ror-org-id:036rp1748` (USP ROR) | 0 |
| `affiliation-org-name:"Universidade Federal do Rio Grande do Sul" AND family-name:Comas` | 1 |

**Key findings:**

- `affiliation-org-name` works well for Brazilian universities -- returns thousands of results. Combined with `family-name`, it narrows to precise matches.
- `grid-org-id` works but returns fewer results (4,225 vs 62,209 for USP) because only affiliations registered via institutional integration use GRID.
- `ror-org-id` returns **zero** results for USP. ROR adoption in ORCID is still extremely low. ORCID switched from Ringgold to ROR in August 2023, but existing records were not retroactively updated.
- The combined query `affiliation-org-name + family-name` is the most promising approach, as demonstrated by the Comas test returning exactly 1 result.

### Expected yield

- **107 "too_many" authors with affiliation:** Adding `affiliation-org-name` could resolve many of these 107 cases where name search returns >20 results but we know the institution.
- **109 "candidate" authors with affiliation:** Could disambiguate some of these ambiguous matches.
- **Additional "not_found" recoveries:** Some of the 424 not-found authors might be findable if their ORCID profile has a different spelling but the same affiliation.
- **Estimated new ORCIDs:** 30--80 (conservative), mainly from the 107 too_many + 109 candidates with affiliation data.
- **Limitation:** 531 too_many authors and 507 candidates have NO affiliation in our database, so this strategy cannot help them.

### Implementation effort

**Low-medium.** Modify `orcid_search()` in `fetch_orcid.py`:

1. Build a mapping from our affiliation siglas (FAU-USP, PROPAR-UFRGS, etc.) to full university names for `affiliation-org-name` queries. The existing `SIGLA_KEYWORDS` dict already has partial coverage.
2. For authors in the "too_many" category who have affiliation data, retry the search with `family-name + given-names + affiliation-org-name`.
3. Optionally look up GRID IDs for each university via the ROR API (which provides GRID cross-references) for an additional search path.

**Estimated time:** 1--2 days of scripting + 1 day of review.

### Prerequisites / blockers

- ORCID Public API rate limit: 24 requests/second (generous). Our 0.5s delay is conservative.
- Starting February 2025, ORCID began implementing daily usage quotas for Public API. Monitor for any new restrictions.
- Requires a mapping table: our 136 unique affiliation siglas to full Portuguese university names. The existing `SIGLA_KEYWORDS` dict covers ~50 institutions.
- `affiliation-org-name` is free-text and depends on how authors entered their affiliation in ORCID. Variations ("Universidade de Sao Paulo" vs "University of Sao Paulo" vs "USP") may require multiple queries per institution.

### Recommendation

**Do this first.** It is the natural extension of the existing approach, requires minimal new code, and targets the most accessible low-hanging fruit (107 "too_many" + 109 "candidates" with affiliations).

---

## Strategy 2: DOI Cross-Validation (OpenCitations Approach)

### What it is

The OpenCitations approach (documented in their [February 2019 blog post](https://opencitations.wordpress.com/2019/02/16/using-the-orcid-public-api-for-author-disambiguation-in-the-opencitations-corpus/)) works as follows:

1. For a given DOI, retrieve author metadata from Crossref (`family-name`, `given-names`).
2. Search the ORCID API with `doi-self:{DOI} AND family-name:{surname}`.
3. If exactly one result: confirmed match.
4. If multiple results: use additional signals (given-names, affiliation) to disambiguate.

This works because some authors add publications (with DOIs) to their ORCID profiles. The `doi-self` field indexes DOIs from the "works" section of ORCID records.

### Feasibility for our project

**Very limited.** Our articles almost entirely lack DOIs:

| Seminars | Articles | DOIs in database | Real DOIs available |
|----------|----------|------------------|---------------------|
| sdbr01--sdbr14 | 1,073 | 0 | 0 |
| sdbr15 | 101 | 0 (in db) | ~101 Even3/Crossref DOIs (prefix 10.29327) |
| sdnne10 | 85 | 0 (in db) | ~85 Even3/Crossref DOIs (prefix 10.29327) |
| Other regionais | 1,086 | 3 (sandbox) | 0 |
| **Total** | **2,345** | **3 (sandbox)** | **~186** |

- The 3 DOIs in our database are sandbox DOIs (`10.5072/zenodo.*`) from testing -- not real, not indexed anywhere.
- sdbr15 and sdnne10 have Even3/Crossref DOIs, but they are not stored in `anais.db`. They would need to be retrieved from Even3 or Crossref first.
- A test search for `digital-object-ids:10.29327` returns 7,255 results in ORCID, meaning some Even3 content is in ORCID records. However, these are all Even3 publications broadly, not specifically our seminars.
- A targeted search for a specific Even3 DOI (`doi-self:10.29327/2024sdbr.61`) returned 0 results, suggesting that Even3 conference DOIs are rarely added to ORCID profiles.

### Expected yield

- **From Even3 DOIs (sdbr15 + sdnne10):** Likely 0--10 new ORCIDs. Conference paper DOIs are rarely added to ORCID profiles, especially recent Brazilian conference proceedings.
- **From other seminars:** 0 (no DOIs exist).

### Implementation effort

**Medium, but poor ROI.** Steps required:

1. Retrieve Even3 DOIs for sdbr15 and sdnne10 articles (from Even3 API or Crossref).
2. Store DOIs in `anais.db`.
3. For each DOI, search ORCID with `doi-self:{DOI} AND family-name:{surname}`.
4. Validate matches.

**Estimated time:** 2--3 days total, for potentially 0--10 results.

### Prerequisites / blockers

- Even3 DOIs need to be retrieved and matched to our articles first.
- The DOI prefix `10.29327` covers all of Even3, not just Docomomo. Need to verify which specific DOIs correspond to our articles.
- Only 186 of 2,345 articles (~8%) have any DOI at all.
- Conference paper DOIs have very low ORCID profile adoption rates compared to journal article DOIs.

### Recommendation

**Low priority.** The potential yield is too small (0--10) relative to the effort. However, retrieving and storing the Even3 DOIs in `anais.db` is independently useful (for Crossref metadata, citation tracking, etc.) and could be done as a side task. If done, the ORCID cross-validation adds minimal additional effort.

---

## Strategy 3: Public Data File (Offline Bulk Processing)

### What it is

ORCID publishes an annual snapshot of all public registry data on [Figshare](https://orcid.figshare.com/articles/dataset/ORCID_Public_Data_File_2024/27151305). The 2024 edition (snapshot date: September 23, 2024) contains:

| File | Contents | Uncompressed size |
|------|----------|-------------------|
| `ORCID_2024_10_summaries.tar.gz` | Full record summary for each ORCID | ~730 GB |
| `ORCID_2024_10_activities_0.tar.gz` through `..._10.tar.gz` | Works, employments, education, etc. | Multiple TB total |

The summaries file expands to individual XML files organized as `summaries/[checksum]/[ORCID-ID].xml`, one per ORCID record. Each XML contains: name, other names, employment history, education, external identifiers.

### Processing approach

1. Download the summaries tarball (~30--40 GB compressed, ~730 GB uncompressed).
2. Stream through the tar file, parsing each XML for:
   - Family name matching any of our ~1,357 target surnames.
   - Employment/education at a Brazilian institution.
3. Build an offline lookup table: `{familyname, givenname, affiliation} -> ORCID`.
4. Match against our database.

### Expected yield

This approach would cover ALL ORCID holders, not just those findable via the search API. Benefits:

- Catches authors who filled in unusual affiliation spellings that the API text search misses.
- Catches authors with "other names" that differ from their primary display name.
- No API rate limits -- purely offline processing.
- **However:** The "too_many" and "not_found" problems are fundamentally about whether the author HAS an ORCID at all, not about API search limitations. The majority of our 424 "not_found" authors likely do not have ORCID records.

**Estimated new ORCIDs:** 10--40 beyond what Strategy 1 finds. The bulk data lets you discover edge cases (name variants, unusual affiliation entries), but the marginal gain over API search with affiliation is modest for our population.

### Implementation effort

**High.**

1. **Storage:** Need ~730 GB disk space for uncompressed summaries, or stream directly from the tarball (slower but feasible).
2. **Download:** ~30--40 GB download. At 10 MB/s, takes ~1 hour.
3. **Processing:** Parsing ~19 million XML files takes hours even with optimized streaming. A Python script using `tarfile` + `lxml` can process the summaries tarball in ~4--8 hours without full extraction.
4. **Filtering:** Pre-filter by Brazilian institutions to reduce the candidate set dramatically (Brazil has ~500K ORCID records out of ~19M total).
5. **Matching:** Cross-reference against our 1,357 target authors.

**Estimated time:** 3--5 days of development + 1 day of processing + 1 day of review.

### Prerequisites / blockers

- Disk space: 730 GB uncompressed, or ~40 GB for the compressed file if streaming.
- The `/mnt/green` disk (ext4) should have space. Verify with `df -h /mnt/green`.
- Download from Figshare may be slow or have bandwidth limits.
- Amazon S3 sync (real-time updates) requires ORCID Premium membership -- not available to us.
- Data is from September 2024; authors who created ORCIDs since then will not appear.

### Recommendation

**Low priority for now.** The marginal gain over Strategy 1 is likely 10--40 additional ORCIDs, which does not justify 3--5 days of work. Consider this as a future "completeness check" after exhausting API-based strategies. It could also be useful for other projects (e.g., a Brazilian ORCID directory for the entire architecture/urbanism field).

---

## Strategy 4: OJS ORCID OAuth Plugin

### What it is

The [PKP ORCID Profile Plugin](https://github.com/pkp/orcidProfile) integrates ORCID directly into OJS. It provides:

- **3-legged OAuth:** Authors authenticate their ORCID iD during submission or profile creation. This gives a **verified** ORCID (not just claimed by the editor).
- **Automatic profile sync:** With the Member API, accepted publications can be pushed to the author's ORCID record.
- **Author form integration:** ORCID field appears in the submission/profile form.

### Compatibility

| OJS Version | Plugin Status |
|-------------|---------------|
| OJS 3.3.x | Supported (our production is 3.3) |
| OJS 3.4.x | Supported with limitations (author form integration broken) |
| OJS 3.5+ | **Plugin discontinued.** ORCID functionality will be integrated into OJS core |

PKP is a [certified ORCID Service Provider](https://info.orcid.org/implementing-your-orcid-plugin-for-ojs-ops-help-is-here/), so the plugin can use production ORCID API keys directly without sandbox testing.

### API credential types

| Type | Who can get it | Features |
|------|---------------|----------|
| **Public API** | Anyone with an ORCID | Authors authenticate, iD is verified and stored in OJS |
| **Member API** | ORCID member organizations only | All Public API features + push publications to ORCID records |

The Public API credentials are free and can be obtained by any ORCID user via the [ORCID developer tools](https://orcid.org/developer-tools). The Member API requires institutional ORCID membership (e.g., through a university library consortium).

### What it does for us

This plugin addresses a **different problem** than strategies 1--3. It does not help find ORCIDs for historical authors. Instead:

- **Future submissions:** New articles submitted through OJS will have verified author ORCIDs from day one.
- **Author self-identification:** If we send invitations to existing authors, they can authenticate their ORCID via the plugin. However, Docomomo Anais is a retrospective publication (conference proceedings from 1995--2024), so there are no "new submissions" in the traditional sense.
- **Existing articles:** The plugin does NOT retroactively assign ORCIDs to already-published articles.

### Expected yield for existing authors

- **Direct yield: 0.** The plugin does not search for or assign ORCIDs to existing records.
- **Indirect yield (with author outreach):** If we contact authors and ask them to claim their articles via ORCID OAuth, we could get verified ORCIDs. But this is a manual/communication effort, not a technical one. Realistically, response rates for such campaigns are 10--30% at best.

### Implementation effort

**Low (plugin setup), but limited impact for our use case.**

1. Install the ORCID Profile Plugin (included with OJS 3.3).
2. Register for Public API credentials at [ORCID developer tools](https://orcid.org/developer-tools).
3. Configure the plugin with Client ID and Client Secret.
4. Test with a few articles.

**Estimated time:** 1--2 hours for setup. Ongoing maintenance is minimal.

### Prerequisites / blockers

- Requires **Site Admin** or **Journal Manager** role in OJS to install/configure plugins. Our `dmacedo` account is only Editor.
- The server must support HTTPS (it does: `publicacoes.docomomobrasil.com`).
- The OAuth callback URL must be configured in ORCID: `https://publicacoes.docomomobrasil.com/anais/orcid/...`
- For the Member API (which allows pushing publications to ORCID), the organization must be an ORCID member. Docomomo Brasil or a partner university (e.g., via CAPES/CNPq consortium) would need to provide this.

### Recommendation

**Set it up for future use, but it will not solve the current backlog.** The plugin is a best practice for any OJS installation and takes minimal effort to configure. It ensures that any future interactions with authors (corrections, updates, new editions) can capture verified ORCIDs. But for the ~1,357 authors without ORCIDs in our historical data, this plugin is not the solution.

---

## Summary Comparison

| Strategy | Expected yield | Effort | Priority |
|----------|---------------|--------|----------|
| 1. API + Affiliation | 30--80 new ORCIDs | Low-medium (2--3 days) | **HIGH** |
| 2. DOI cross-validation | 0--10 new ORCIDs | Medium (2--3 days) | LOW |
| 3. Public Data File | 10--40 beyond Strategy 1 | High (4--6 days) | LOW |
| 4. OJS OAuth plugin | 0 (retroactive) | Low (2 hours setup) | MEDIUM (future) |

### Recommended action plan

1. **Immediate:** Implement Strategy 1 (affiliation-enhanced API search). Focus on the 107 "too_many" and 109 "candidate" authors who already have affiliation data. Expand the `SIGLA_KEYWORDS` mapping to full institution names.

2. **Short-term:** Set up the OJS ORCID plugin (Strategy 4) with Public API credentials. This is quick and establishes the infrastructure for future ORCID collection.

3. **Optional/later:** If Even3 DOIs are retrieved for other purposes, add the DOI cross-validation (Strategy 2) as a low-effort bonus step.

4. **Deferred:** The Public Data File (Strategy 3) is not cost-effective now. Revisit if the project expands to other publication databases or if a comprehensive Brazilian ORCID directory becomes a goal.

### The bigger picture

With 751 of 2,108 authors (35.6%) already having ORCIDs, and an optimistic additional 80 from Strategy 1, we would reach ~831 authors (~39.4%). The remaining ~1,277 authors likely fall into categories that no automated strategy can resolve:

- **No ORCID exists:** Many conference presenters from 1995--2015 may never have created an ORCID. ORCID adoption in Brazilian humanities/architecture was low before ~2018.
- **No affiliation in our data:** 1,171 authors without ORCID also lack affiliation data, removing the main disambiguation signal.
- **Name too common:** Some authors have names that return hundreds of ORCID results even with affiliation filtering.

For these cases, the only viable approaches are:
- Direct author outreach (email campaigns asking authors to claim their articles).
- Manual web research (Lattes, ResearchGate, university pages).
- The OJS ORCID plugin for any future author interactions.

---

## Technical References

- [ORCID API Tutorial: Searching the Registry](https://info.orcid.org/documentation/api-tutorials/api-tutorial-searching-the-orcid-registry/)
- [ORCID API Search Documentation (GitHub)](https://github.com/ORCID/ORCID-Source/blob/main/orcid-api-web/tutorial/search.md)
- [ORCID Public Data File 2024 (Figshare)](https://orcid.figshare.com/articles/dataset/ORCID_Public_Data_File_2024/27151305)
- [ORCID Public Data File Guide](https://info.orcid.org/documentation/integration-guide/working-with-bulk-data/)
- [PKP ORCID Plugin Setup Guide](https://docs.pkp.sfu.ca/orcid/en/installation-setup.html)
- [PKP ORCID Plugin: How to Use](https://docs.pkp.sfu.ca/orcid/en/using-plugin.html)
- [OpenCitations: Using ORCID API for Author Disambiguation](https://opencitations.wordpress.com/2019/02/16/using-the-orcid-public-api-for-author-disambiguation-in-the-opencitations-corpus/)
- [ORCID API Rate Limit Changes (2025)](https://info.orcid.org/refining-api-traffic-management/)
- [Finding ORCID Holders at Your Institution](https://www.orcidus.lyrasis.org/2019/11/14/finding-orcid-holders-at-your-institution/)
- [ROR Registry](https://ror.org/)
