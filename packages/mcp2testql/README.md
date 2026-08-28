# mcp2testql

MCP server for TestQL control (query, patch, validate, DSL).

Query and validation tools remain read-only. Materialization, patching and DSL
execution are disabled unless the server operator explicitly sets
`TESTQL_MCP_ALLOW_MUTATION=1` for trusted MCP clients.
