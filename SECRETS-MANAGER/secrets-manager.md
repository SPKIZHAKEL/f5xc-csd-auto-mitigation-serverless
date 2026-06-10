## Create the Secrets Manager Secret

1. Search for **Secrets Manager** in the AWS Console.
2. Click **Store a new secret**.
3. Select **Other type of secret**.

### Add the Following Key/Value Pairs

| Key | Value |
|------|--------|
| `base_url` | `https://your-tenant.console.ves.volterra.io` |
| `token` | `your-f5-api-token` |
| `namespace` | `your-namespace` |

4. Click **Next**.

### Secret Details

| Field | Value |
|---------|---------|
| Secret name | `f5-csd-soar` |

5. Click **Store**.
