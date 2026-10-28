---
name: bdd-test
description: >
  Execute BDD tests from generated .feature files. Detects application type
  (frontend/backend/API) and uses appropriate test runner. Supports Playwright
  (frontend), SpecFlow (.NET backend), and Cucumber/REST frameworks.
  Use when user says "run feature tests", "execute BDD tests", "test this spec",
  or invokes /bdd-test.
user_invocable: true
---

# /bdd-test — BDD Feature File Test Runner

You are a test automation agent. You execute BDD tests generated in `.feature` files (Gherkin format), automatically detecting the application type and selecting the appropriate test runner.

## Process

### Step 1: Identify Feature Files

If the user specifies a feature specification or directory, use that. Otherwise, find the most recent feature specification:

```bash
ls -t docs/tasks/*_feature-spec.md 2>/dev/null | head -1
```

Extract the feature files directory from the specification:
- **Location pattern:** `docs/tasks/features/NNN_[slug]/`
- All `.feature` files in this directory are the test suite

If no feature files exist, stop and ask the user to create a feature specification first (use `/feature-spec`).

### Step 2: Detect Application Type

Based on the repository structure and feature file content, determine the application type:

#### Frontend Web Application (React, Vue, Angular, etc.)
**Detection:**
- Feature files contain references to UI elements, pages, buttons, forms
- Keywords: "I see", "I click", "I fill", "I navigate", "page", "user interface"
- `src/frontend/` or similar directory exists with `.tsx`, `.jsx`, `.ts`, `.js`, `.vue`, etc.
- Frontend dev server is running or can be started

**Test Runner:** `Playwright` + `@cucumber/cucumber` or similar BDD adapter
**Implementation:** TypeScript/JavaScript Cucumber steps with Playwright page interaction

#### Backend API / .NET Service
**Detection:**
- Feature files contain references to API endpoints, requests, responses, database state
- Keywords: "API", "POST", "GET", "endpoint", "response", "database"
- `src/backend/` with `.csproj` files exists
- Primary language: C# / .NET

**Test Runner:** `SpecFlow` (Gherkin for .NET) or `BDDfy`
**Implementation:** C# step definitions with HTTP client / API mocking

#### Python Backend
**Detection:**
- `pyproject.toml` or `requirements.txt` exists
- Primary language: Python
- Feature files reference REST endpoints or service behavior

**Test Runner:** `pytest-bdd` or `Behave`
**Implementation:** Python step definitions with requests/httpx libraries

#### Generic / Unknown
**Default approach:** Suggest Playwright for web testing; ask user for clarification on backend

### Step 3: Report Current State

Before running tests, report:
- Number of feature files found
- Detected application type(s)
- Test runner tool(s) that will be used
- Any prerequisites (dev server, database, API running)
- Ask user for confirmation to proceed

### Step 4: Set Up Test Environment

#### Frontend (Playwright + Cucumber)

1. **Check dependencies** — in `src/frontend/`:
   ```bash
   npm list @playwright/test @cucumber/cucumber
   ```
   If missing, suggest:
   ```bash
   npm install --save-dev @playwright/test @cucumber/cucumber @cucumber/cucumber-expressions
   ```

2. **Check dev server** — verify React dev server is running:
   ```bash
   lsof -i :5173  # macOS/Linux
   netstat -ano | findstr :5173  # Windows
   ```
   If not running, ask user to start it or offer to run `npm run dev` in `src/frontend/`

3. **Create step definitions** (if not present) at `src/frontend/features/steps.ts`:
   - Import `.feature` files from `docs/tasks/features/`
   - Define step matchers (Given, When, Then) using Playwright
   - Each step interacts with page elements via Playwright locators

4. **Create test config** (if not present) at `src/frontend/cucumber.js`:
   ```javascript
   module.exports = {
     default: {
       require: ['features/steps.ts'],
       requireModule: ['ts-node/register'],
       format: ['progress', 'json:reports/cucumber-report.json'],
       formatOptions: { snippetInterface: 'async-await' },
     },
   };
   ```

#### Backend (.NET + SpecFlow)

1. **Check SpecFlow NuGet package** — in backend `.csproj`:
   ```bash
   cd src/backend
   dotnet list package | grep -i specflow
   ```
   If missing, suggest:
   ```bash
   dotnet add [ProjectName].csproj package SpecFlow --version 3.9.*
   dotnet add [ProjectName].csproj package SpecFlow.Tools.MsBuild.Generation --version 3.9.*
   ```

2. **Check API is running** — verify backend API is accessible:
   ```bash
   curl https://localhost:7000/swagger  # or appropriate health endpoint
   ```
   If not running, ask user to run `dotnet run --project DVTk.DefBuilder.Api`

3. **Create step definitions** (if not present) — map feature files to C# step classes:
   - Create `src/backend/[TestProject]/Features/` mirror of `docs/tasks/features/`
   - Copy `.feature` files here
   - Create `StepDefinitions/` directory with C# classes implementing steps

4. **Create test project** (if needed):
   ```bash
   cd src/backend
   dotnet new nunit -n DVTk.DefBuilder.Tests
   cd DVTk.DefBuilder.Tests
   dotnet add package SpecFlow --version 3.9.*
   dotnet add package SpecFlow.NUnit --version 3.9.*
   ```

#### Python Backend (pytest-bdd)

1. **Check pytest-bdd** — in project root:
   ```bash
   pip list | grep pytest-bdd
   ```
   If missing:
   ```bash
   pip install pytest-bdd requests pytest
   ```

2. **Create conftest.py** and step definitions mapping feature files to Python functions

### Step 5: Run Tests

#### Frontend (Playwright + Cucumber)

```bash
cd src/frontend
npm run test:bdd  # or npx cucumber-js docs/tasks/features/**/*.feature
```

Expected output:
- ✓ PASSED / ✗ FAILED per scenario
- Summary: X scenarios passed, Y failed
- HTML/JSON report at `reports/`

#### Backend (.NET + SpecFlow)

```bash
cd src/backend
dotnet test DVTk.DefBuilder.Tests --logger "console;verbosity=detailed"
```

Expected output:
- ✓ PASSED / ✗ FAILED per scenario
- Test Results Summary

#### Python Backend (pytest-bdd)

```bash
cd .  # project root
pytest docs/tasks/features/ --gherkin-terminal-reporter -v
```

### Step 6: Parse and Report Results

After test execution:

1. **Capture output** — save test results to a report file
2. **Parse results** — extract:
   - Total scenarios / features
   - Passed / failed / skipped counts
   - Failed scenario names and error messages
   - Execution time
3. **Report to user**:
   - Summary table (passed/failed/total)
   - Failed scenarios (if any) with error messages
   - Link to detailed test report
   - Suggestion: "All tests passed! ✓" or "X tests failed. See details above."

### Step 7: Interactive Failure Response

If tests fail:

1. **Analyze failures** — for each failed scenario:
   - Identify the step that failed (Given/When/Then)
   - Extract error message or assertion failure
   - Suggest likely causes

2. **Ask user**:
   - "Would you like me to debug this failure?"
   - Options: "Re-run with verbose output", "Update step definitions", "Update feature file", "Cancel"

3. **Debug mode** (if user chooses):
   - Re-run with debug output (e.g., `--debug` flag)
   - Log step inputs/outputs
   - Capture screenshots (Playwright) or request payloads (API testing)

### Step 8: Generate Test Coverage Report

After all tests run:

1. **Coverage detection** — check if coverage tool is available:
   - **Frontend:** Playwright native coverage or `nyc`
   - **Backend (.NET):** `coverlet` NuGet package
   - **Python:** `coverage.py` package

2. **Generate coverage report** (if tool available):
   ```bash
   # Frontend
   npm run test:bdd:coverage

   # Backend
   dotnet test DVTk.DefBuilder.Tests /p:CollectCoverage=true

   # Python
   pytest --cov docs/tasks/features/ --cov-report html
   ```

3. **Report coverage** — summarize code coverage % by component

### Step 9: Commit Test Results

If all tests pass:

```bash
git add docs/tasks/features/ src/[frontend|backend]/tests/
git commit -m "test: BDD tests for feature specification NNN"
```

If tests fail and user defers fixes:

```bash
git add docs/tasks/features/
git commit -m "test(WIP): BDD tests for feature specification NNN - some failures"
```

## Step Definitions Auto-Generation

If step definitions do not exist for a `.feature` file, suggest auto-generation:

**Frontend (Playwright):**

```typescript
import { Given, When, Then, Before } from '@cucumber/cucumber';
import { expect, Page } from '@playwright/test';
import { chromium } from '@playwright/test';

let page: Page;

Before(async () => {
  const browser = await chromium.launch();
  page = await browser.newPage();
  await page.goto('http://localhost:5173');
});

// Examples (user should fill in actual selectors and logic):
Given('I am on the {string} page', async (pageName: string) => {
  await page.goto(`http://localhost:5173/${pageName}`);
});

When('I click on {string}', async (buttonText: string) => {
  await page.click(`button:has-text("${buttonText}")`);
});

Then('I should see {string}', async (text: string) => {
  await expect(page).toContainText(text);
});
```

**Backend (.NET + SpecFlow):**

```csharp
using TechTalk.SpecFlow;
using NUnit.Framework;
using System.Net.Http;

[Binding]
public class APISteps
{
    private HttpClient _client;
    private HttpResponseMessage _response;

    [Before]
    public void Setup()
    {
        _client = new HttpClient { BaseAddress = new Uri("https://localhost:7000") };
    }

    [Given("the API is running")]
    public void GivenAPIIsRunning()
    {
        var health = _client.GetAsync("/health").Result;
        Assert.That(health.IsSuccessStatusCode, Is.True);
    }

    [When(@"I send a GET request to ""(.*)""")]
    public void WhenISendGET(string endpoint)
    {
        _response = _client.GetAsync(endpoint).Result;
    }

    [Then(@"the response status should be (\d+)")]
    public void ThenResponseStatus(int expectedStatus)
    {
        Assert.That((int)_response.StatusCode, Is.EqualTo(expectedStatus));
    }
}
```

**Python + pytest-bdd:**

```python
import pytest
from pytest_bdd import given, when, then, scenarios
import requests

scenarios('docs/tasks/features')

@given('the API is running')
def api_is_running():
    response = requests.get('http://localhost:8000/health')
    assert response.status_code == 200

@when('I send a GET request to <endpoint>')
def send_get_request(endpoint):
    global response
    response = requests.get(f'http://localhost:8000{endpoint}')

@then('the response status should be <status>')
def check_response_status(status):
    assert response.status_code == int(status)
```

## Rules

#### Automation-First
- Always run tests automatically, don't ask for confirmation after setup is confirmed
- Capture all output for reporting
- If a test framework is missing, install it and proceed

#### Framework Selection Priority
For unknown cases, prioritize in order:
1. Playwright (universal web testing, most portable)
2. SpecFlow or pytest-bdd (language-native Gherkin support)
3. Generic REST client (for API-only testing without Gherkin adapter)

#### Error Handling
- If test runner crashes, capture stderr and report to user
- If a step is undefined, suggest auto-generating it from the `.feature` file
- If a dev server is not running, ask user to start it rather than auto-starting (to avoid surprises)

#### Test Isolation
- Each test run should be independent
- Clean up state (database, file system) between test runs if possible
- Use transactional rollback or test fixtures to isolate data

#### Reporting
- Always provide a summary (pass/fail/skip counts)
- Link to detailed report file if available
- For failures, highlight the first error message
- Do NOT flood the user with full stack traces unless they ask

#### When Stuck
- If test framework setup is too complex, ask the user for:
  - Existing test command they use (e.g., `npm run test`, `dotnet test`)
  - Link to their test configuration file
  - Language / framework preference
- If a specific `.feature` file has ambiguous Gherkin, ask the user to clarify the scenario intent
