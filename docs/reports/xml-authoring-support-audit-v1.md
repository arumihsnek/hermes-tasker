# XML authoring support audit V1

Initial audit at `ef6f99e` found 382 action catalog entries, 90 event entries, 52 state entries, and 7 plugin templates. Catalog entries are not evidence of complete XML serialization. The repository has one local Project candidate XML and manifest; the real Pixel export corpus referenced by plugin metadata is absent from this checkout.

| kind | identifier | renderer | validator | fixture | contract | roundtrip | runtime | proposed level | action |
|---|---|---|---|---|---|---|---|---|---|
| action | catalog (382 entries) | generic catalog handler | catalog checks | none | none | none | none | catalog_only | reject authoring until exact shape evidence |
| event/state | catalog (142 entries) | context handlers | catalog checks | none local | none | none | none | catalog_only | reject authoring until exact shape evidence |
| plugin | 7 template IDs | exact template clone | template signature | referenced but absent | template embedded | none local | none | fixture_backed, not renderer_golden | preserve template-only policy |
| project | project-renderer-gate-v1 | root-sibling renderer | graph/XML validators | candidate XML | project contract | parallel branch only | none | unsupported in this foundation | integration contract required |

False positives identified: catalog entry plus renderer acceptance without a local exact export/contract/golden; plugin fixture paths without files in this checkout; historical documentation claiming supported contexts without immutable local provenance. This mission therefore starts with an empty authorization matrix. No historical fixture was edited and no new XML support is inferred.
