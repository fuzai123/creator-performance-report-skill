# Creator Performance Report Skill

A portable `SKILL.md` for source-backed affiliate and content-performance
reporting. It contains **no source links, credentials, real creator data,
fees, reports, or brand assets**. The user supplies access and inputs in their
own environment; the agent reads source pages directly and does not download
intermediate documents during a reporting or refresh run.

## Install

Place this repository directory, including `SKILL.md`, in the skill folder of
your agent. For Codex, use `~/.codex/skills/creator-performance-report/`.
For WorkBuddy/CodeBuddy, use `~/.codebuddy/skills/creator-performance-report/`
or the product's Skill import UI. Installation is a one-time setup; the
no-download rule applies to all subsequent data-source reading and refreshes.
The skill has no runtime package dependencies. Python 3 is only needed for
the optional local validators.

Ask your agent to use `creator-performance-report` to build or refresh a
creator performance report, PDF, or interactive site. Provide your authorized
source pages/connections, creator roster and account mappings, fees, brand
guide, desired output location, and publication audience. Never paste a
password or API key into a public prompt or repository.

The skill cannot make a private source publicly accessible or turn a browser
login into a durable cloud connection. A scheduled refresh must verify access
at run time and preserve the last published version when it cannot read or
validate the sources.
