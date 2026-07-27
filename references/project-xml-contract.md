# Project XML contract

The official source describes `<Project sr="proj0" ve="2">`, `name`, `pids`, and `tids`, plus reference relationships.

## Canonical element order (from real 6.7.6-beta exports)

```xml
<TaskerData sr="" dvi="1" tv="6.7.6-beta">
  <!-- Profiles first (zero or more) -->
  <Profile sr="profN" ve="2">
    <cdate>timestamp_ms</cdate>
    <clp>true</clp>                  <!-- optional -->
    <edate>timestamp_ms</edate>
    <flags>integer</flags>
    <id>integer_profile_id</id>
    <mid0>integer_task_id</mid0>     <!-- entry task reference -->
    <mid1>integer_task_id</mid1>     <!-- exit task reference, optional -->
    <nme>Profile Name</nme>          <!-- optional -->
    <!-- One context: Event, State, Time, Day, Loc, or App -->
    <Event sr="con0" ve="2">
      <code>event_code</code>
      <Str sr="arg0" ve="3">...</Str>
      ...
    </Event>
  </Profile>
  <!-- Project exactly once -->
  <Project sr="proj0" ve="2">
    <cdate>timestamp_ms</cdate>
    <id>uuid-or-timestamp</id>        <!-- String; can be UUID or millisecond timestamp -->
    <name>Project Name</name>
    <pids>profile_id1,profile_id2</pids>   <!-- comma-separated Integer CSV; all root Profiles -->
    <tids>task_id1,task_id2,...</tids>     <!-- comma-separated Integer CSV; all root Tasks -->
  </Project>
  <!-- Tasks follow (zero or more) -->
  <Task sr="taskN">
    <cdate>timestamp_ms</cdate>
    <edate>timestamp_ms</edate>
    <id>integer_task_id</id>
    <nme>Task Name</nme>             <!-- optional; anonymous tasks omit this -->
    <pri>integer</pri>               <!-- optional priority -->
    <Action sr="actN" ve="7">...</Action>
    ...
  </Task>
</TaskerData>
```

## Key rules (from real exports)

- `TaskerData` direct child order is `Profile*`, `Project`, `Task*`. This order is a deterministic compiler rule, not a claimed Tasker semantic requirement.
- `sr="proj0"` is mandatory; Tasker rejects imports with other values.
- `id` is a string; real exports use millisecond timestamps or UUIDs.
- **Root siblings**: Profile, Project, and Task are all direct children of `<TaskerData>`. Project never contains nested Profile or Task elements.
- `pids` and `tids` are comma-separated integer IDs.
- `pids` references only `<Profile>` root siblings; every root Profile must appear exactly once in `pids`.
- `tids` references only `<Task>` root siblings; every root Task must appear exactly once in `tids`.
- `mid0` and `mid1` reference Task IDs (integers). Multiple Profiles may share a Task reference.
- A shared Task is emitted once as a root sibling.
- Tasks may be named (`<nme>`) or anonymous (no `<nme>`).
- Profile and Task integer IDs are separate namespaces — a Profile ID and a Task ID may overlap.
- Static validation (XML catalog check, graph/ID/reference check) does not prove Tasker acceptance.
- Profiles inside a project have the same element order as standalone profiles.

## Optional metadata (unsupported for generation)

Real exports may contain optional elements inside `Project` such as `pc`, `scenes`, `tsort`, `Share`, `Img`, or `ProfileVariable`. These are not supported for fresh generation unless separately evidenced.

## Status

Generation is supported based on `Hermes_Task_Runtime_v2.prj.xml` and `Hermes___Java_Runtime.prj.xml`.
