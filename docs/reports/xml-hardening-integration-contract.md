# XML hardening integration contract

Checkpoint at initial HEAD `ef6f99e` and XML branch HEAD after foundation commits.

| Hot file | Changed in parallel | Change needed here | Strategy |
|---|---|---|---|
| renderer | no | deferred | narrow adapter after parallel review |
| validator | no | deferred | symmetric matrix/contract lookup after renderer boundary |
| common | no | no | independent loader accepts stable dictionaries |
| existing tests | no | no | additive tests only |
| CI | no | deferred | separate command once foundation is stable |
| hermes-android | prohibited | no | never modify |

The roundtrip/runtime branches currently add candidate/comparator/roundtrip artifacts only. Their Typed IR and runtime work is not duplicated here. If their renderer changes land first, re-read the new HEAD and apply only a narrow adapter; otherwise integrate this additive foundation first and keep renderer/validator changes as separate commits.
