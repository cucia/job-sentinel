# Using the Multi-Agent System - Step by Step

## Step 1: Configure AI

Set cloud AI in [configs/settings.yaml](../../configs/settings.yaml):

```yaml
ai:
  use_agents: true
  use_multi_agent: true
  use_cloud: true
  provider: groq
  model: llama-3.1-8b-instant
```

## Step 2: Start Services

```bash
docker compose up -d
```

## Step 3: Test the Agents

The agents run through the existing controller and dashboard flows. Use the dashboard to:
- configure profile details
- add search keywords
- enable platforms
- review outcomes and logs

## Notes

- Agent reasoning uses the configured cloud provider.
- If agents are disabled, the system falls back to heuristic evaluation.
