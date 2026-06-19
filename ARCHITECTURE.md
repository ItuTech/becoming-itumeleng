# Becoming Itumeleng: Architecture, Troubleshooting and Technical Deep Dive

**Author:** Itumeleng Mokgako  
**Date:** June 2026  
**Status:** Work in Progress — I am actively refining and documenting this as I go  
**This document was inspired by a challenge from:** Craig M. (Solutions Architect, AWS)

---

## Why I wrote this document

Craig challenged me to do three things after I shared my demo with him:

1. Figure out what was wrong with the Bedrock chat, fix it, and document the process
2. Build a high-level architecture diagram showing how my AWS services connect
3. Explain each service at L100 (why I chose it), L200 (what I am using it for), and L300 (how it actually works technically)

This document is my response to that challenge. It covers my thought process, the bugs I found, how I fixed them, and everything I learned along the way. I am writing it in a way that I can share back with Craig and also use as a reference for myself as the project grows.

---

## Project Overview

"Becoming Itumeleng" is a personal AI platform I built for myself. Not a tutorial project. Not a generic demo. A real system built around my actual life. My goals, my wardrobe, my academic marks, my personal brand, and my daily habits.

I wanted to answer one question: what if I could code the woman I am becoming?

That question turned into this platform. It runs entirely on AWS, is powered by Amazon Bedrock and Claude Sonnet 4, and exposes six core capabilities through a React web interface.

| Capability | What it does for me |
|---|---|
| Chat with Itu | A conversational AI agent that knows who I am and can help me with anything |
| Goal Tracker | I set goals, update their status, and add progress notes over time |
| Habit Tracker | I track my daily habits and watch my streaks grow |
| Style Curator | AI outfit recommendations pulled from my actual wardrobe inventory |
| Brand Guide | AI content guidance that keeps my voice consistent across YouTube, LinkedIn and Medium |
| BSc Academics | My real semester marks, exam targets, and the calculations I need to hit distinctions |

---

## Part 1: The Bedrock Chat — Troubleshooting

### What the chat is supposed to do

When I type a message in the "Chat with Itu" section, I want to have a real conversation with an AI agent that knows me. It should be able to:

- Answer questions about my goals and habits
- Recommend outfits from my wardrobe
- Help me write content for my platforms
- Hype me up before a recording or an event
- Give me honest accountability when I need it

The agent uses my real data (wardrobe, goals, brand guidelines) as context and has tools it can call depending on what I ask.

### What was happening

Every single message I sent came back with this:

> "Hmm, something went wrong on my end. Give me a sec and try again?"

And when I tried again, same thing. The Style Curator and Brand Guide had the exact same problem. Something was clearly breaking between the frontend and Bedrock but I had no idea what because the error message told me nothing.

### How I investigated

The first thing I did was look at the actual route handler that processes chat messages. This is what it looked like before I fixed it:

```python
# BEFORE — no error handling at all
@router.post("")
async def chat(body: ChatRequest) -> ChatResponse:
    ag = create_agent()
    result = ag(body.message)
    return ChatResponse(reply=str(result))
```

The problem was obvious once I saw it. There was no `try/except` anywhere. When the Strands agent tried to call Amazon Bedrock and something failed, the exception had nowhere to go. It just crashed the entire request and the frontend received a raw 500 error with no useful information. The frontend then caught it generically and showed the same message every time, regardless of what actually went wrong.

I had essentially built a car with no dashboard warning lights. It was failing but not telling me why.

### The possible root causes

I identified four possible reasons the Bedrock call could be failing:

**1. AWS credentials not configured**

The Strands SDK uses `boto3` under the hood to talk to Bedrock. If my AWS credentials are not configured on the machine running the backend, every single Bedrock call will fail with a `NoCredentialsError` before it even reaches AWS.

I can verify this by running:
```bash
aws sts get-caller-identity
```
If it returns my account ID and user ARN, my credentials are working. If it fails, I need to run `aws configure` and enter my access key and secret key.

**2. Wrong AWS region**

The model ID I am using starts with `us.` which means it is a cross-region inference profile for US regions. If my AWS CLI is configured for a non-US region, Bedrock will reject the call because that model profile is not available there.

**3. Model access not enabled in Bedrock console**

AWS Bedrock requires me to explicitly request access to each model before I can use it. Even if my credentials are valid and my region is correct, if I never went into the Bedrock console and requested access to Claude Sonnet 4, every call will return an `AccessDeniedException`.

To fix this: AWS Bedrock console → Model access → Request access for Anthropic Claude Sonnet 4.

**4. Model ID mismatch**

The model ID I am using is:
```
us.anthropic.claude-sonnet-4-20250514-v1:0
```

This is the cross-region inference profile ID. It is different from the direct regional model ID. Some versions of the Strands SDK or boto3 may not support cross-region inference profiles. If that is the case, I need to use the direct regional ID:
```
anthropic.claude-sonnet-4-20250514-v1:0
```

### The fix I applied

I updated all three agent-calling routes (chat, style, brand) with proper exception handling. Here is what the chat route looks like now:

```python
# AFTER — structured error handling with logging
@router.post("")
async def chat(body: ChatRequest) -> ChatResponse:
    try:
        ag = create_agent()
        result = ag(body.message)
        return ChatResponse(reply=str(result))
    except Exception as e:
        logger.error(f"Chat agent error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail={
                "error": type(e).__name__,
                "message": str(e),
                "hint": "Check AWS credentials, Bedrock region, and model access.",
            },
        )
```

Now when something fails:
1. The real error is logged to the server with a full traceback (visible in the uvicorn terminal)
2. The frontend receives a structured error response with the exception type, the actual message, and a hint
3. The chat window displays the real error instead of the generic fallback

I also updated the frontend to extract and display the structured error from the API response so I can see exactly what is failing without having to check the server logs every time.

### How to verify the fix is working

1. Restart the backend: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
2. Send a message in the chat
3. Watch the uvicorn terminal — the real error will now print with a full traceback
4. The chat window will show the actual exception type and message

### What I want to improve next (the rabbit hole)

Right now I am creating a new agent instance on every single request. This means:

- The agent has no memory of what I said in previous messages
- There is no streaming — I have to wait for the full response before anything appears
- Every request pays the full cold-start cost of initialising the agent

These are the improvements I am planning to investigate:

| Improvement | Why I want it | Complexity |
|---|---|---|
| Conversation history | So the agent remembers what we talked about in the same session | Medium |
| Response streaming | So I see words appearing as they are generated, not all at once | Medium |
| Session persistence with DynamoDB | So conversation history survives page refreshes | High |
| Bedrock Knowledge Base with RAG | Store my data in a proper knowledge base for smarter retrieval | High |
| Native Bedrock Agents | Replace Strands SDK with AWS-managed agent orchestration | High |

---

## Part 2: The Architecture

### High Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              ME                                          │
│                    (Browser on my laptop or phone)                       │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTPS
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          AWS Cloud                                       │
│                                                                          │
│  ┌─────────────────┐      ┌──────────────┐      ┌────────────────────┐  │
│  │   AWS Amplify   │      │  API Gateway │      │   AWS Lambda       │  │
│  │  (React SPA)    │─────▶│  HTTP API    │─────▶│  (FastAPI +        │  │
│  │  CDN + Hosting  │      │  (REST layer)│      │   Mangum adapter)  │  │
│  └─────────────────┘      └──────────────┘      └─────────┬──────────┘  │
│                                                            │             │
│                          ┌─────────────────────────────────┤             │
│                          │                                 │             │
│                 ┌────────▼────────┐             ┌──────────▼──────────┐  │
│                 │    Amazon S3    │             │  Amazon Bedrock     │  │
│                 │  (YAML data     │             │  Claude Sonnet 4    │  │
│                 │   files)        │             │  (via Strands SDK)  │  │
│                 └─────────────────┘             └─────────────────────┘  │
│                                                                          │
│  ┌─────────────────┐                                                     │
│  │   AWS CDK       │  (Infrastructure as Code — how I deploy all of it) │
│  └─────────────────┘                                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### How a request flows end to end

When I type a message in the chat, here is exactly what happens:

1. I open my browser and the React app loads from AWS Amplify
2. I type a message and click send
3. React sends a POST to `/api/v1/chat` via Axios
4. API Gateway HTTP API receives the request and triggers the Lambda function
5. Lambda runs my FastAPI application (via Mangum, which translates Lambda events to ASGI)
6. FastAPI routes the request to my chat handler
7. My chat handler calls `create_agent()` which sets up the Strands agent
8. Strands sends the system prompt, my tools, and my message to Amazon Bedrock
9. Bedrock runs Claude Sonnet 4 which decides whether to answer directly or call a tool
10. If it needs a tool (e.g. `check_goals`), Strands calls that Python function which reads from S3
11. The tool result goes back to Claude, Claude formulates a response
12. The response travels back through Lambda → API Gateway → React → my screen

---

## Part 3: The L100 / L200 / L300 Breakdown

### AWS Amplify

**L100 — Why I chose it:**  
I chose Amplify to host my React frontend because it connects directly to my GitHub repository and handles everything automatically. Every time I push a commit to `main`, Amplify rebuilds and redeploys my site. I did not want to manually manage an S3 bucket for static hosting, configure CloudFront distributions, or set up a deployment pipeline from scratch. As a solo developer building in public, I needed something that gets out of my way and just works.

**L200 — What I am using it for:**  
I am using Amplify for:
- Hosting with a managed CDN (CloudFront is running under the hood, I just do not have to configure it)
- Automatic builds triggered from GitHub on every push to `main`
- Environment variable injection at build time so my React app knows the API Gateway URL without me hardcoding it

**L300 — How it works technically:**  
The Amplify build spec defines two phases. `preBuild` runs `npm ci` which installs my exact package versions from `package-lock.json` for reproducible builds. `build` runs `npm run build` which calls Vite to bundle my React application into static HTML, CSS and JavaScript. The `VITE_API_URL` environment variable is set in the Amplify console and injected at build time. Vite bakes it into the JavaScript bundle via `import.meta.env.VITE_API_URL`. The output lands in `frontend/dist` and Amplify serves it from its CDN globally.

---

### API Gateway (HTTP API)

**L100 — Why I chose it:**  
I needed something between the internet and my Lambda function. API Gateway handles TLS, request routing, CORS, and throttling so my Lambda does not have to worry about any of that. I chose HTTP API over REST API specifically because HTTP API has lower latency and lower cost for simple proxy integrations, which is exactly what I need here.

**L200 — What I am using it for:**  
- A single catch-all route `/{proxy+}` that forwards every request to my Lambda function
- CORS preflight configuration at the gateway level so my Amplify frontend can make cross-origin requests to the API
- Lambda proxy integration which passes the full HTTP request through to my FastAPI application

**L300 — How it works technically:**  
When a request hits API Gateway, it constructs a Lambda proxy event: a JSON object with the HTTP method, path, headers, query string, and body. This goes to my Lambda handler. Mangum (my ASGI adapter) receives this event and translates it into an ASGI-compatible scope that FastAPI understands. FastAPI then routes the request to the correct handler based on path and method, processes it, and returns a response. Mangum translates that back into the Lambda response format which API Gateway returns to the client.

---

### AWS Lambda

**L100 — Why I chose it:**  
My application is request-driven. When nobody is using it, nothing needs to run. Lambda is the perfect fit because it scales from zero and costs nothing at idle. I did not need a persistent server, background jobs, or long-lived connections. Lambda let me focus on my application code instead of managing infrastructure.

**L200 — What I am using it for:**  
- Running my entire FastAPI backend as a serverless function
- I deployed it as a Docker container image (not a ZIP package) because the Strands Agents SDK with all its dependencies is larger than Lambda's 250MB ZIP limit
- Memory is set to 1024MB and timeout to 120 seconds to give Bedrock inference enough room
- Environment variables configure the S3 bucket name, Bedrock model ID, and CORS origins
- The Lambda execution IAM role grants it permission to call Bedrock and read/write S3

**L300 — How it works technically:**  
My Docker image is built from `public.ecr.aws/lambda/python:3.12`. I install `requirements.txt` and copy my application code into the Lambda task root. The `CMD` is `main.handler` — that is the Mangum-wrapped FastAPI app. When Lambda receives an invocation from API Gateway, it calls this handler with the event and context objects. Mangum translates the Lambda invocation model into the ASGI protocol. FastAPI processes the request, my route handlers run, and the response goes back through Mangum to Lambda to API Gateway to the browser.

---

### Amazon S3

**L100 — Why I chose it:**  
I needed somewhere to store my data (goals, habits, wardrobe, brand guidelines, academic marks). All of it is YAML files. The total data volume is kilobytes. A full relational database would be massively over-engineered and expensive for this. S3 is durable, secure, versioned, and costs essentially nothing at my scale. It was the obvious choice.

**L200 — What I am using it for:**  
- Storing five YAML files: `goals.yaml`, `habits.yaml`, `wardrobe.yaml`, `brand.yaml`, `academics.yaml`
- Bucket versioning is on so I can recover previous versions of my data if I accidentally overwrite something
- SSE-S3 encryption is enabled
- Public access is fully blocked — only my Lambda function can read and write these files via IAM

**L300 — How it works technically:**  
I built a `storage.py` module that checks for the `DATA_BUCKET` environment variable at runtime. In production on Lambda, this is set to my S3 bucket name. The module calls `boto3.client("s3").get_object()` to read files and `put_object()` to write them. In local development, `DATA_BUCKET` is not set, so the module falls back to reading from my local `data/` directory. This means I can develop and test locally without touching S3, and the same code runs in both environments without any changes.

---

### Amazon Bedrock

**L100 — Why I chose it:**  
Bedrock gives me access to Claude Sonnet 4 without having to run any model infrastructure myself. I do not need to provision GPUs, manage model weights, or handle scaling. Everything is API-driven and fully managed by AWS. Claude Sonnet 4 is one of the most capable conversational models available and it handles tool use really well, which is critical for my agentic use case. Using Bedrock also keeps my entire stack inside AWS, which felt right for a project that is supposed to demonstrate AWS expertise.

**L200 — What I am using it for:**  
- The Strands Agents SDK manages the agentic loop: call the model, parse tool requests, execute tools, return results to the model, repeat until a final response is ready
- The model is `us.anthropic.claude-sonnet-4-20250514-v1:0` which is a cross-region inference profile
- I configured a detailed system prompt that defines my personality, values, capabilities, and context
- I registered nine tools: `style_curator`, `brand_guide`, `check_goals`, `update_goal`, `add_goal`, `check_habits`, `log_habit`, `hype_me_up`, `celebrate_win`

**L300 — How it works technically:**  
When I call `agent(user_message)`, Strands sends the system prompt, conversation context, tool schemas (as JSON Schema), and my message to Bedrock's `InvokeModel` API. Claude reads everything and decides whether to respond directly or invoke a tool. If it wants a tool, it returns a structured tool use block with the tool name and parameters. Strands parses this, calls the corresponding Python function, collects the return value, and sends it back to Claude as a tool result message. This loop runs until Claude produces a final text response with no more tool calls. That final response comes back to my FastAPI handler as a string.

---

### AWS CDK (Infrastructure as Code)

**L100 — Why I chose it:**  
I wanted my infrastructure to be code. Not a list of console steps that I have to remember and repeat. With CDK, everything is defined in Python and version controlled in my repository. I can spin up the entire stack in a new AWS account with one command. Given that I have 13 AWS certifications and understand cloud architecture, it felt wrong to not use IaC from the start.

**L200 — What I am using it for:**  
My `infra/stack.py` defines the entire platform:
- S3 bucket with versioning and encryption
- Lambda IAM execution role with Bedrock and S3 permissions
- Lambda Docker image function with environment variables
- API Gateway HTTP API with CORS and Lambda integration
- Amplify app connected to GitHub with build spec and environment variable injection

**L300 — How it works technically:**  
CDK synthesises my Python construct definitions into CloudFormation templates. When I run `cdk deploy`, it builds my Docker image locally, pushes it to ECR (Elastic Container Registry), and then deploys the CloudFormation stack which creates or updates all my resources in the correct dependency order. Stack outputs (my API URL, Amplify app ID, S3 bucket name) are exported as CloudFormation outputs. I can query these with the AWS CLI to wire up environment variables without hardcoding anything.

---

## Part 4: Issues I Encountered and How I Fixed Them

These are the real problems I hit while building and running this project.

| Issue | Root Cause | How I fixed it |
|---|---|---|
| Chat returning a generic error every time | No exception handling in my route handlers | Added structured `try/except` with `logger.error()` and HTTP 502 responses containing the real error |
| Style Curator failing silently | Same missing error handling | Same fix applied |
| Brand Guide failing silently | Same missing error handling | Same fix applied |
| Frontend showing no useful error detail | Generic `catch {}` block in React | Updated to extract and display the structured error object from the API response |
| YAML files reformatting on save | PyYAML `dump()` reorders keys alphabetically by default | Accepted this as benign — the data is correct even if the key order changes |
| `npm` not found when running the frontend | Node.js was not installed on my machine | Downloaded and installed Node.js LTS from nodejs.org |
| My photo not appearing on the site | I saved the file as `itu.jpeg` but all three components referenced `itu.jpg` | Updated all three component image source paths to use `.jpeg` |

---

## Part 5: What I Am Planning to Improve

These are on my list. I am documenting them here so I can track my progress and show the evolution of the project over time.

### Conversation memory

Right now every message I send starts a fresh conversation. The agent has no idea what I said 30 seconds ago. I want to pass the full conversation history to the agent on each call so it can refer back to earlier messages. This is the most impactful improvement for the user experience.

### Response streaming

I currently wait for the entire response to be generated before I see anything. Bedrock supports streaming via `InvokeModelWithResponseStream`. I want to implement Server-Sent Events on the backend and a streaming reader in React so words appear as they are generated.

### Bedrock Knowledge Base with RAG

Right now my wardrobe and brand data are passed to the agent as raw YAML in the system prompt. This is inefficient and has context length limits. A Bedrock Knowledge Base would store all my data as embeddings and the agent would retrieve only the relevant chunks before answering. This would make responses more accurate and allow me to add much more data.

### Native Bedrock Agents

I would like to explore replacing the Strands SDK agent with a native Amazon Bedrock Agent. This would give me managed agent orchestration inside AWS, native Knowledge Base integration, and better observability through the Bedrock console.

### Authentication

Anyone with the URL can currently access my dashboard. I want to add AWS Cognito with Amplify Auth so the app is protected. Even though I am the only user, unauthenticated access means anyone could trigger Bedrock calls at my expense.

### Observability

I want to add AWS X-Ray distributed tracing so I can see the full request journey from API Gateway through Lambda to Bedrock. I also want a CloudWatch Dashboard showing API latency, error rates, and Bedrock token usage over time.

---

## Part 6: What I Learned

**Error handling is not optional.**  
Three route handlers with no exception handling made the entire AI feature of my application look completely broken. I could have caught this much earlier if I had been logging properly from the start. Now every handler that calls Bedrock has structured error handling and server-side logging.

**Logging is your first debugging tool in distributed systems.**  
My application spans a browser, API Gateway, Lambda, and Bedrock. When something fails in that chain, the only way to find the real problem quickly is to have logs at every layer. Adding `logger.error()` with full tracebacks was the first thing I did once I identified the missing error handling.

**Local development parity matters.**  
The dual-mode storage layer (local filesystem in development, S3 in production) means I can develop and debug locally without touching my AWS environment. Bugs in data handling get caught before they ever reach production.

**IaC from day one saves time later.**  
Starting with CDK meant I never had to document a list of console steps for setting up the infrastructure. The code is the documentation.

**Personal projects teach more than tutorial projects.**  
I understand every AWS service in this stack at a deeper level than I would from any certification question because I had a real reason to choose it, a real problem to solve with it, and a real failure to debug when it did not work as expected. The troubleshooting Craig challenged me to do taught me more about Bedrock, IAM, and agentic architecture in one session than hours of reading docs.

---

## References

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Strands Agents SDK](https://strandsagents.com/)
- [AWS CDK Python Reference](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [Mangum — ASGI adapter for Lambda](https://mangum.fastapiexpert.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode)

---

*This document is a living record of my project. I will keep updating it as I build, break, fix, and improve things.*  
*Learning is the lifestyle. ✨*  
*— Itumeleng Mokgako*
