---
name: migrating-zep-v3-to-v4
description: >-
  Procedure for a coding agent that migrates an application from the Zep V3
  API and SDKs to V4. The procedure reads the V4 migration guide, finds each
  V3 call in the codebase, maps it to its V4 replacement, moves the
  application to Zep-generated UUIDs in the documented order, and verifies
  each step. Use when a user asks to "migrate to Zep v4", "upgrade zep-cloud
  to v4", "port my Zep code from v3", or "what breaks when I move to Zep v4".
  Use together with the building-with-zep skill from the same plugin.
  Activate that skill first if it is not active yet.
---

# Migrating from Zep V3 to V4

**Required: use this skill together with the building-with-zep skill from
the same plugin.** If that skill is not active, activate it now, before you
continue. If your runtime cannot activate skills, read
[`../building-with-zep/SKILL.md`](../building-with-zep/SKILL.md). Use the
Documentation index and the source rules of the building-with-zep skill.

## Source of truth

The migration guide is the source of truth for every method name, field,
and behavior change. This skill tells you how to apply the guide. It does not
repeat the guide.

1. Read the guide through the `zep-docs` MCP server. Search for "Migrating
   from v3", or read the resource `zep-docs://migrating-from-v3`.
2. If the MCP server is not available, read
   [Migrating from v3](https://help.getzep.com/migrating-from-v3) at
   `https://help.getzep.com/migrating-from-v3.md`.
3. Read the whole guide before you change code. Read these sections first:
   "Migration steps", "Pagination", and "Deletes". These changes cause most of
   the work.

If the guide and this skill do not agree, obey the guide.

## Procedure

### Step 1. Make an inventory of the V3 usage

- Find each Zep SDK import and each Zep SDK call in the codebase, in each
  language. Include tests, scripts, background jobs, and infrastructure code.
- Record the SDK version that each service uses now. The method map of the
  guide matches one V3 SDK version. If the application uses an older V3 SDK,
  tell the user before you continue.
- For each call, record the method, the file, and the identifier that the
  call uses (`user_id`, `thread_id`, `graph_id`, or a UUID).
- Find each place where the application stores or makes a Zep identifier.

### Step 2. Classify each call

Use the "Method map" of the guide for each call. Put each call in one of these
groups:

- A rename: the V4 method has the same behavior.
- A change that needs more than a rename: the call is in a section of
  "Changes that need more than a rename", for example pagination, deletes,
  instruction updates, list filters, or errors.
- No V4 equivalent: the call is in "What has no v4 equivalent". Tell the user
  about each of these calls before you change code. Do not make a replacement
  that the guide does not give.

Show the classified inventory to the user before you start Step 3.

### Step 3. Plan the identifier migration

V4 addresses each user, thread, and graph by a UUID that Zep generates. This
is the largest part of the migration. Follow the five steps in "Migration
steps" of the guide, in their order. Do not combine or skip a step.

- The UUID columns are a change to the database of the user. Show the schema
  change to the user, and get approval before you write the database
  migration.
- Use `lookup` only in the one backfill job of the guide. The application
  code must never call `lookup`, also not as a fallback, because `lookup`
  will become deprecated.
- Move resource creation to V4 only after no V3 read or write remains. The V3
  API cannot address a resource that V4 created.
- The application uses both SDKs during the migration. Read the note in
  "Migration steps" for each language before you change the dependencies.
  Some languages cannot load both SDKs in one process.

### Step 4. Change the code

- Make one migration step of the guide per change, so that the user can
  deploy and verify each step. Open one PR for each step. Start the next step
  only after the user has merged and deployed the PR before it.
- Get each V4 method name and argument from the method map and the V4 SDK
  reference of the installed SDK version. Do not guess a name from the V3
  name.
- Use the SDKs. Do not call the Zep API over raw HTTP.
- Read each "Changes that need more than a rename" section that applies to a
  call before you change that call. A change that compiles can still have
  different behavior. For example, the type checker does not find a loop that
  reads only the first page of a list, or code that expects a delete to be
  complete when the call returns.

### Step 5. Verify

- Run the type checker, the linter, and the tests after each step.
- Search the codebase again for V3 imports and for `lookup` calls. After the
  last step, no V3 import remains, and only the backfill job calls `lookup`.
- Test each changed path against a Zep project that is not production. Use the
  test project that the user gives you.
- Tell the user which calls you could not test.

## Report

When you finish each step, tell the user:

- The calls that you changed, by group (Step 2).
- The calls that have no V4 equivalent, and what the user must decide for each.
- The database changes and the backfill status.
- The checks that passed, and the paths that you did not test.
