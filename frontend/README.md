# Daily Briefing Dashboard (frontend)

Next.js + TypeScript + Tailwind + shadcn/ui + Lucide. **All data is live** from your AWS account. There is no mock data.

## Run
1. Deploy the agent first (`../scripts/deploy.sh`).
2. Give the machine running the dashboard AWS credentials (never in the browser):
   ```bash
   aws configure            # or export AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION
   npm install && npm run dev      # http://localhost:3000
   ```
   The IAM user needs: `ssm:GetParameter/PutParameter`, `scheduler:GetSchedule/UpdateSchedule` (+ `iam:PassRole` for the scheduler role), `lambda:InvokeFunction/GetFunctionConfiguration`, `sns:ListSubscriptionsByTopic/Subscribe`, `dynamodb:Query`.

## What is real
| Dashboard part | Source |
|---|---|
| Settings (name, city, timezone, topics, prefs) | SSM Parameter Store `/daily-briefing/settings`, read by the Lambda on every run |
| Delivery time, timezone, on/off | EventBridge Scheduler schedule |
| Email address | SNS email subscription (AWS sends a confirmation mail) |
| Generate briefing now | Invokes the real Lambda; the real email is sent |
| Execution history and briefing preview | DynamoDB table `daily-briefing-runs` (written by the Lambda, kept 30 days) |
| System health | Live checks: schedule state, Lambda state and last run, Open-Meteo ping, last Bedrock outcome, SNS subscription status |
| Workflow diagram | Built from what the latest run really did (which sources failed, whether the AI summary or email step failed) |
| City search and weather card | Open-Meteo (free, no key) |

Notification preferences work: with "Email me the briefing every day" off, runs are generated and stored but not emailed; with "Email me if a run fails" on, a failed run sends an alert email.

Server code: `src/server/aws.ts` and `src/app/api/*`. Client calls: `src/services/briefingApi.ts`.

## Security
No login: run it only on your own computer. Mutating routes reject cross-site requests, but do not expose the app to the internet without adding authentication.

## Structure
`src/components/dashboard/`: WeatherCard, BriefingCard, ScheduleCard, TopicSelector, WorkflowStatus, ExecutionHistory, SettingsPanel, NotificationStatus, SystemHealth, CitySearch, and `states.tsx` (LoadingState, ErrorState, EmptyState).
