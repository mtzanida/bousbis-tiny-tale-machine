# Setting Up Your Own AWS Project Felt Big — Until I Actually Did It

I work with AWS, Spacelift, and GitHub every day at work. I help teams manage infrastructure, automate deployments, review Terraform. And yet, when I thought about setting up a personal project on AWS — something small, just mine — it felt like a bigger deal than it should have.

It wasn't.

It turned out to be straightforward, free, and genuinely useful to have done. Not just because I built something I care about, but because I now have something real to talk about in interviews. Not "I've worked with Terraform" — but "here's exactly what I provisioned, with what permissions, and why."

This article is about the flow. How you get from an empty AWS account and a local folder to a live app, with Terraform managing the infrastructure and GitHub handling everything else. The project I used as the vehicle doesn't matter — what matters is how the pieces connect.

---

## The pieces

- **AWS Lambda** — runs your backend code, only when called, scales to zero
- **Lambda Function URL** — gives Lambda a direct public HTTPS endpoint, no API Gateway needed
- **IAM** — controls what your Lambda is allowed to do (spoiler: almost nothing)
- **CloudWatch Logs** — captures what your Lambda did
- **Terraform** — creates and manages all of the above from your terminal
- **GitHub Pages** — hosts your frontend for free
- **GitHub Actions** — redeploys your frontend automatically on every push

Total cost for a personal project or demo: **€0**.

---

## How Terraform actually creates things in AWS

This is the part that clicked everything into place for me.

Terraform talks to AWS using the AWS CLI credentials on your machine. When you run `terraform apply`, Terraform calls the AWS APIs on your behalf — the same APIs the console uses when you click around — but it does it programmatically, in the right order, and it remembers what it created.

The flow looks like this:

```
terraform apply
    ↓
Terraform reads your .tf files
    ↓
Calls AWS APIs (CreateRole, CreateFunction, CreateLogGroup...)
    ↓
AWS creates the resources in your account
    ↓
Terraform saves the result in terraform.tfstate
```

That state file is how Terraform knows what already exists. Run `apply` twice and the second time does nothing — Terraform compares the desired state (your files) against the real state (what's in AWS) and only acts on differences.

---

## The IAM question: who is Terraform running as?

This is the question nobody explains clearly, so let me be direct about it.

When you run `terraform apply`, Terraform uses **your AWS credentials** — whatever is configured in `~/.aws/credentials` or via environment variables. It acts as **you** (or whatever IAM identity you've configured).

For a personal project I created a dedicated IAM user with only the permissions needed for this specific project:

```json
{
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole", "iam:DeleteRole", "iam:GetRole",
        "iam:PassRole", "iam:TagRole", "iam:AttachRolePolicy",
        "iam:DetachRolePolicy", "iam:ListAttachedRolePolicies"
      ],
      "Resource": "arn:aws:iam::ACCOUNT_ID:role/my-project-lambda-role"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction", "lambda:DeleteFunction",
        "lambda:GetFunction", "lambda:UpdateFunctionCode",
        "lambda:CreateFunctionUrlConfig", "lambda:GetFunctionUrlConfig",
        "lambda:ListVersionsByFunction", "lambda:GetFunctionCodeSigningConfig"
      ],
      "Resource": "arn:aws:lambda:eu-central-1:ACCOUNT_ID:function:my-project"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup", "logs:DeleteLogGroup",
        "logs:PutRetentionPolicy", "logs:TagResource"
      ],
      "Resource": "arn:aws:logs:eu-central-1:ACCOUNT_ID:log-group:/aws/lambda/my-project*"
    }
  ]
}
```

Why bother? Two reasons:

1. If those credentials ever leak, the blast radius is limited to this project only — the key can't touch anything else in your account.
2. It's good practice to demonstrate in interviews. "I used a scoped IAM user for Terraform with only the permissions needed for this project" is a better answer than "I used my admin credentials."

Once the IAM user is created, you configure the CLI:

```bash
aws configure --profile myproject
# enter Access Key ID, Secret Access Key, region
aws sts get-caller-identity --profile myproject
# verify: shows your account ID and the IAM user ARN
```

---

## The Terraform files and what they do

I split the configuration across files by responsibility — one file per concern:

```
terraform/
├── versions.tf      # which Terraform version and providers to use
├── main.tf          # the AWS provider + default resource tags
├── iam.tf           # the Lambda execution role
├── cloudwatch.tf    # the CloudWatch log group
├── lambda.tf        # the function itself + the public URL
├── variables.tf     # configurable inputs (region, name, CORS origin)
└── outputs.tf       # what gets printed after apply (the Lambda URL)
```

**versions.tf** pins the Terraform and provider versions so the config behaves the same for everyone:

```hcl
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
```

**main.tf** configures the AWS provider. I use `default_tags` so every resource gets the same tags automatically — no need to add them individually:

```hcl
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "My Project"
      ManagedBy = "Terraform"
    }
  }
}
```

**iam.tf** creates the Lambda execution role — the role that Lambda *assumes at runtime* to do its job. This is different from the Terraform user. Terraform creates the role; Lambda uses it.

```hcl
resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
```

`AWSLambdaBasicExecutionRole` is an AWS-managed policy that only allows writing to CloudWatch Logs. Nothing else. Your Lambda function cannot touch S3, DynamoDB, or anything in your account unless you explicitly add permissions.

**lambda.tf** packages the code and deploys the function:

```hcl
data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/lambda_function.py"
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_lambda_function" "story_generator" {
  filename         = data.archive_file.lambda.output_path
  function_name    = var.project_name
  role             = aws_iam_role.lambda.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.13"
  architectures    = ["arm64"]
  memory_size      = 128
  timeout          = 5
  source_code_hash = data.archive_file.lambda.output_base64sha256
}

resource "aws_lambda_function_url" "story_generator" {
  function_name      = aws_lambda_function.story_generator.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = [var.allowed_origin]
    allow_methods = ["POST"]
    allow_headers = ["content-type"]
  }
}
```

`source_code_hash` is how Terraform detects code changes — if the zip content changes, it redeploys. If it hasn't changed, it skips the update.

**outputs.tf** prints the Lambda URL after a successful apply:

```hcl
output "lambda_function_url" {
  value = aws_lambda_function_url.story_generator.function_url
}
```

---

## The deploy sequence, end to end

```bash
# 1. Tell Terraform to use your project profile
export AWS_PROFILE=myproject

# 2. Download the providers
cd terraform
terraform init

# 3. See exactly what will be created — read this before applying
terraform plan

# 4. Create the resources
terraform apply
# type yes when prompted

# 5. Copy the output URL
# lambda_function_url = "https://xxxxxxxxxxxx.lambda-url.eu-central-1.on.aws/"

# 6. Put the URL in your frontend config
# frontend/config.js → LAMBDA_URL: "https://..."

# 7. Push to GitHub — Actions deploys the frontend automatically

# 8. When you're done with the project
terraform destroy
# type yes — removes everything Terraform created
```

That's the whole flow. Five minutes from `terraform init` to a live URL.

---

## The two IAM roles — don't mix them up

One thing that confused me at first: there are two separate IAM identities in this setup.

| | Who | What for |
|---|---|---|
| **Terraform user** | IAM user you created | Runs `terraform apply` from your laptop. Needs permissions to create AWS resources. |
| **Lambda execution role** | IAM role Terraform creates | Used by Lambda at runtime. Needs permissions to write logs. |

Terraform creates the execution role as part of `apply`. They are separate things with separate permissions. Your Terraform user needs `iam:CreateRole` and `iam:PassRole` to create and assign the execution role — but once that's done, the Lambda function runs as the execution role, not as you.

---

## GitHub Actions for the frontend

The frontend lives on GitHub Pages. A workflow deploys it automatically whenever `frontend/` changes:

```yaml
name: Deploy frontend to GitHub Pages

on:
  push:
    branches: [main]
    paths: [frontend/**]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    environment:
      name: github-pages
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: frontend/
      - uses: actions/deploy-pages@v4
```

Enable it once in **Settings → Pages → Source → GitHub Actions** and it runs automatically from then on. No credentials, no tokens, no S3 buckets — GitHub handles the hosting.

---

## What this gives you in interviews

Having done this yourself means you can answer the questions that actually get asked:

- *"How did you scope the IAM permissions for Terraform?"* — You scoped them to specific resource ARNs, not `*`.
- *"What's the difference between the Terraform identity and the Lambda execution role?"* — You just explained it above.
- *"How do you handle infrastructure changes safely?"* — `terraform plan` before every `apply`, branch protection on main, changes go through PRs.
- *"How would you tear this down?"* — `terraform destroy`. Everything Terraform created, Terraform can remove.

These are not trick questions. They are basic operational questions. Having a project where you made these decisions yourself — even a small one — means you can answer them from experience rather than from memory.

---

Setting this up took an afternoon. It felt bigger than it was. If you work with these tools professionally and haven't built something small for yourself yet, this is the nudge.

---

*Maria Tzanidaki — AWS Community Builder, Serverless*  
*GitHub: [github.com/mtzanida](https://github.com/mtzanida)*
