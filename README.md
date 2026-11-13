# Kora Framework txAdmin Recipe

[![Validate recipe](https://github.com/KoraFiveM/txAdminRecipe/actions/workflows/validate-recipe.yml/badge.svg)](https://github.com/KoraFiveM/txAdminRecipe/actions/workflows/validate-recipe.yml) [![Check resources](https://github.com/KoraFiveM/txAdminRecipe/actions/workflows/check-resources.yml/badge.svg)](https://github.com/KoraFiveM/txAdminRecipe/actions/workflows/check-resources.yml)


> **⚠️ THIS IS UNDER CONSTRUCTION - MAY NOT WORK**

The official txAdmin deployment recipe for **Kora Framework Alpha**.

## Installation

1. Open txAdmin's deployment wizard.
2. Choose **Remote URL Template**.
3. Paste the following recipe URL:

```text
https://raw.githubusercontent.com/KoraFiveM/txAdminRecipe/main/recipe.yaml
```

4. Supply your Cfx.re license and MariaDB/MySQL connection details.
5. Deploy, review `server.cfg`, and start your server.

## Default settings

- OneSync on
- Game build 3751
- 48 slots by txAdmin's default, configurable during deployment
- Kora and QBCore compatibility ACE permissions
- txAdmin imports `kora.sql` to create the selected database only, with no tables; `kora_sql` handles tables on startup.

## Important alpha limitations

- **All referenced repositories must be public** for a public txAdmin deployment.
- The release still needs a full live deployment test before being called production-ready.
- The recipe downloads source repositories from `main`. Source-only resources with UI compilation steps may require prebuilt release packages to work in-game.
- `kora_sql` needs permission to create its tables and will do this at server start.

## Structure deployed on server

```text
server.cfg
permissions.cfg
resources/
  [cfx-default]/
  [default-maps]/
  [pre]/
    kora_lib/
    kora_sql/
    kora_inventory/
    kora_core/
  [compat]/
    PolyZone/
    qb-core/
    oxmysql/
    mysql-async/
  [kora]/
  [standalone]/
```

## Database setup

The recipe connects using txAdmin's database settings, downloads `kora.sql`, replaces the default database name with `{{dbName}}`, then executes the SQL using `query_database`. The SQL only creates and selects the database; it does not create tables. The database account needs `CREATE DATABASE` privileges if the database does not already exist.
\n## Expanded server configuration\n\nThe root `server.cfg` includes networking, discovery, game build, database, locale, dependency startup order, security guidance, and txAdmin owner principal insertion. Edit `sets locale` for your deployment. Only documented convars are active; optional examples are commented out.\n
## Configuration documentation

Each active setting and major optional setting in `server.cfg` now has an explanation and a documentation URL. Official FiveM docs cover engine settings; project-specific Kora repository links identify Kora resources. Voice options are commented out because legacy voice convars are not supported on GTAV Enhanced.

- [FiveM server commands](https://docs.fivem.net/docs/server-manual/server-commands/)
- [FiveM server security](https://docs.fivem.net/docs/developers/server-security/)
- [FiveM voice](https://docs.fivem.net/docs/scripting-manual/voice/)
- [txAdmin recipe specification](https://github.com/citizenfx/txAdmin/blob/master/docs/recipe.md)
- [FiveManage documentation](https://docs.fivemanage.com/)


## Server listing metadata (Cfx Portal)

Configure the public server name, project name and description, locale, tags, banners, and icon at https://portal.cfx.re/servers. These listing settings are deliberately **not** configured in `server.cfg`, following the Cfx Portal migration notice.

## GitHub Actions checks

- **Validate recipe:** YAML syntax, txAdmin placeholders, SQL database-only creation, Cfx Portal-managed listing settings, duplicate downloads, and Kora startup prerequisites. Runs on pushes and pull requests.
- **Check resource repositories:** Queries the GitHub API for every repository and branch referenced in `recipe.yaml`. Runs when resource-related files change and can also be run manually. A missing/private repository will fail the check, which is expected until all dependencies are publicly available.

Both workflows are read-only and do not deploy servers, publish releases, or require custom secrets. These checks do not replace an actual txAdmin installation test.
