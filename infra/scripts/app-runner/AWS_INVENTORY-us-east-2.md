# AWS inventory — **us-east-2** (account `726101440593`)

Checked via AWS CLI. Use **`AWS_DEFAULT_REGION=us-east-2`** (or `--region us-east-2`) for App Runner, RDS, and ECR for this project.

## ECR

| Repository | URI | Images |
|------------|-----|--------|
| **bigboy-backend-repo** | `726101440593.dkr.ecr.us-east-2.amazonaws.com/bigboy-backend-repo` | Has tag **`latest`** (and digests without tags) |
| **langgraph-service-repo** | `726101440593.dkr.ecr.us-east-2.amazonaws.com/langgraph-service-repo` | Has tag **`latest`** |

Other repos in the same region (unrelated to bigboy deploy): `n8n-repo`, `ed-donner-repo`.

**App Runner image identifiers (examples):**

- Django: `726101440593.dkr.ecr.us-east-2.amazonaws.com/bigboy-backend-repo:latest`
- LangGraph: `726101440593.dkr.ecr.us-east-2.amazonaws.com/langgraph-service-repo:latest`

## RDS — Aurora PostgreSQL (`bigboy-backend-db`)

| Item | Value |
|------|--------|
| **DB cluster identifier** | `bigboy-backend-db` |
| **Writer instance identifier** | `bigboy-backend-db-instance-1` |
| **Engine** | `aurora-postgresql` 17.x |
| **Status** | `available` |
| **Cluster endpoint (writer)** | `bigboy-backend-db.cluster-cryyqgs6ia1n.us-east-2.rds.amazonaws.com` |
| **Instance endpoint (writer, chosen for Django `DATABASE_HOST`)** | `bigboy-backend-db-instance-1.cryyqgs6ia1n.us-east-2.rds.amazonaws.com` |
| **Reader endpoint** | `bigboy-backend-db.cluster-ro-cryyqgs6ia1n.us-east-2.rds.amazonaws.com` |
| **Port** | `5432` |
| **Master username** | `postgres` |
| **Initial database name** | *null in API* — create a database in the cluster (e.g. `bigboy`) or set `DATABASE_NAME` to whatever you created |
| **Publicly accessible** | `false` — App Runner needs a **VPC connector** into **VPC** `vpc-0a4be47f4ff1903bf` |
| **VPC** | `vpc-0a4be47f4ff1903bf` |
| **RDS VPC security group** | `sg-06cff44e7977b7708` |
| **DB subnet group** | `default-vpc-0a4be47f4ff1903bf` (subnets `subnet-08027401ffb6a1f0b`, `subnet-0ff1ce8ed6d0396ca`, `subnet-0e50b4970fe0e46a3`) |

**Django `DATABASE_HOST`:** use the **instance endpoint** above (your choice), or switch to the **cluster endpoint** later if you want Aurora writer failover without changing the hostname.

## Why us-east-1 looked empty

The same account had different resources per region: **ECR + Aurora for bigboy live in `us-east-2`**, not `us-east-1`.
