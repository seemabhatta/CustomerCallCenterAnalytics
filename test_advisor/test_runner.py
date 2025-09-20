"""
Automated test harness for advisor agent API.
Tests → Analyzes → Creates Issues → Fixes → Retests

This harness continuously tests the advisor agent by:
1. Testing scenarios via API calls
2. Using LLM to analyze responses for bugs
3. Creating GitHub issues automatically
4. Generating fix suggestions
5. Generating new test scenarios based on findings
"""

import asyncio
import aiohttp
import yaml
import json
import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

# Add the parent directory to sys.path to import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.llm.llm_client_v2 import LLMClientV2, RequestOptions


class AdvisorTestHarness:
    """Automated test harness for the advisor agent API."""

    def __init__(self):
        """Initialize the test harness."""
        self.llm = LLMClientV2()
        self.api_url = "http://localhost:8000/api/v1/advisor/chat"
        self.test_results = []
        self.scenarios_file = Path(__file__).parent / "test_scenarios.yaml"

    async def run(self):
        """Main test loop - runs continuously."""
        iteration = 0

        print("🚀 Starting Automated Advisor Test Harness")
        print(f"API URL: {self.api_url}")
        print(f"Scenarios: {self.scenarios_file}")
        print("="*80)

        while True:
            iteration += 1
            print(f"\n{'='*80}")
            print(f"🔄 Test Iteration {iteration} - {datetime.now().strftime('%H:%M:%S')}")
            print('='*80)

            try:
                # 1. Load or generate scenarios
                if iteration == 1:
                    scenarios = self.load_initial_scenarios()
                else:
                    scenarios = await self.generate_scenarios_from_bugs()

                print(f"📋 Testing {len(scenarios)} scenarios")

                # 2. Test each scenario
                for i, scenario in enumerate(scenarios, 1):
                    print(f"\n[{i}/{len(scenarios)}] Testing: {scenario['name']}")
                    bugs = await self.test_scenario(scenario)

                    if bugs:
                        print(f"  🐛 Found {len(bugs)} bugs")

                        # 3. Create GitHub issue
                        issue_id = await self.create_issue(scenario, bugs)
                        if issue_id:
                            print(f"  📝 Created issue #{issue_id}")

                        # 4. Generate fix
                        fix = await self.generate_fix(bugs[0])
                        if fix:
                            print(f"  🔧 Fix suggested for: {fix.get('file', 'unknown')}")
                            print(f"     Change: {fix.get('change', 'See issue')}")
                    else:
                        print("  ✅ All tests passed")

                # 5. Save results
                self.save_test_results(iteration, scenarios)

                # Wait before next iteration
                print(f"\n⏰ Waiting 2 minutes before next iteration...")
                await asyncio.sleep(120)

            except KeyboardInterrupt:
                print("\n\n🛑 Test harness stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Error in iteration {iteration}: {str(e)}")
                print("Continuing in 30 seconds...")
                await asyncio.sleep(30)

    def load_initial_scenarios(self):
        """Load initial test scenarios from YAML file."""
        try:
            with open(self.scenarios_file, 'r') as f:
                data = yaml.safe_load(f)
                return data.get('scenarios', [])
        except FileNotFoundError:
            print(f"⚠️  Scenarios file not found: {self.scenarios_file}")
            return self.get_default_scenarios()
        except Exception as e:
            print(f"⚠️  Error loading scenarios: {e}")
            return self.get_default_scenarios()

    def get_default_scenarios(self):
        """Get default test scenarios if file not found."""
        return [
            {
                "name": "Context-aware analysis request",
                "steps": [
                    {
                        "input": "show me the last call",
                        "expect": ["CALL_", "transcript", "PMI"]
                    },
                    {
                        "input": "show me the analysis for this",
                        "expect": ["sentiment", "risk", "compliance"],
                        "not_expect": ["list", "multiple", "transcripts"]
                    }
                ]
            }
        ]

    async def test_scenario(self, scenario):
        """Test a single scenario and return any bugs found."""
        bugs_found = []

        try:
            # Start session
            session_id = await self.start_session()
            if not session_id:
                return [{"type": "session_error", "description": "Could not start session", "severity": "critical"}]

            context = []

            for step_num, step in enumerate(scenario['steps'], 1):
                print(f"    Step {step_num}: {step['input'][:60]}...")

                # Send message
                response = await self.send_message(step['input'], session_id)
                if response is None:
                    bugs_found.append({
                        "type": "api_error",
                        "description": f"No response for: {step['input']}",
                        "severity": "high"
                    })
                    continue

                # Analyze with LLM
                analysis = await self.analyze_response(
                    step['input'],
                    step.get('expect', []),
                    step.get('not_expect', []),
                    response,
                    context
                )

                if analysis and analysis.get('bugs'):
                    bugs_found.extend(analysis['bugs'])
                    print(f"      ❌ {len(analysis['bugs'])} bugs found:")
                    for bug in analysis['bugs']:
                        print(f"        - {bug['type']}: {bug['description'][:80]}...")
                else:
                    print(f"      ✅ Passed")

                # Add to context
                context.append({
                    'user': step['input'],
                    'agent': response[:200] + "..." if len(response) > 200 else response
                })

        except Exception as e:
            bugs_found.append({
                "type": "test_error",
                "description": f"Test execution failed: {str(e)}",
                "severity": "high"
            })

        return bugs_found

    async def start_session(self):
        """Initialize session via API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json={
                    "advisor_id": "ADV001",
                    "message": "session_init",
                    "session_id": None
                }, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('session_id')
                    else:
                        print(f"      API error: {resp.status}")
                        return None
        except Exception as e:
            print(f"      Session start failed: {str(e)}")
            return None

    async def send_message(self, message, session_id):
        """Send message to API and return response."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json={
                    "advisor_id": "ADV001",
                    "message": message,
                    "session_id": session_id
                }, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('response', data.get('message', ''))
                    else:
                        return f"API Error: {resp.status}"
        except Exception as e:
            return f"Request failed: {str(e)}"

    async def analyze_response(self, input_text, expected, not_expected, response, context):
        """Use LLM to analyze response for bugs."""

        prompt = f"""Analyze this advisor agent response for bugs:

User Input: {input_text}
Expected to contain: {expected}
Should NOT contain: {not_expected}
Conversation Context: {json.dumps(context[-2:], indent=2) if context else "None"}

Agent Response:
{response}

Check for these bugs:
1. Missing expected content
2. Contains forbidden content
3. Asked for IDs when context was available
4. Used wrong tool (should use context-aware tools)
5. Fallback response instead of proper error
6. Not using conversation context intelligently

IMPORTANT: Return ONLY valid JSON, no markdown formatting, no explanations outside JSON:
{{
    "makes_sense": true/false,
    "bugs": [
        {{
            "type": "missing_tool|wrong_tool|context_not_used|fallback|missing_content|forbidden_content",
            "description": "specific description of the bug",
            "severity": "critical|high|medium|low",
            "evidence": "quote from response showing the issue"
        }}
    ],
    "analysis": "brief explanation"
}}"""

        try:
            response_obj = await self.llm.arun(
                messages=[
                    {"role": "system", "content": "You are a test analyzer for an advisor CLI agent. Return ONLY valid JSON. Be strict about detecting bugs."},
                    {"role": "user", "content": prompt}
                ],
                options=RequestOptions(temperature=0.1)
            )

            # Extract JSON from response (handle markdown code blocks)
            response_text = response_obj.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            elif response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```

            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```

            response_text = response_text.strip()

            # Parse the cleaned JSON
            result = json.loads(response_text)

            # Basic validation - check expected content
            if expected:
                found_expected = [e for e in expected if e.lower() in response.lower()]
                missing_expected = [e for e in expected if e.lower() not in response.lower()]

                if missing_expected:
                    # Add bug for missing expected content
                    if 'bugs' not in result:
                        result['bugs'] = []
                    result['bugs'].append({
                        "type": "missing_content",
                        "description": f"Response missing expected content: {missing_expected}",
                        "severity": "high",
                        "evidence": response[:200] + "..." if len(response) > 200 else response
                    })

            # Check forbidden content
            if not_expected:
                found_forbidden = [n for n in not_expected if n.lower() in response.lower()]

                if found_forbidden:
                    # Add bug for forbidden content
                    if 'bugs' not in result:
                        result['bugs'] = []
                    result['bugs'].append({
                        "type": "forbidden_content",
                        "description": f"Response contains forbidden content: {found_forbidden}",
                        "severity": "high",
                        "evidence": response[:200] + "..." if len(response) > 200 else response
                    })

            return result

        except json.JSONDecodeError as e:
            print(f"      ❌ JSON parsing failed: {str(e)}")
            print(f"      Response text: {response_obj.text[:200] if hasattr(locals(), 'response_obj') else 'N/A'}")
            # Return analysis failure as a bug itself
            return {
                "makes_sense": False,
                "bugs": [{
                    "type": "analysis_failure",
                    "description": f"Failed to parse LLM analysis response: {str(e)}",
                    "severity": "critical",
                    "evidence": "Analysis JSON parsing failed"
                }],
                "analysis": f"Analysis error: {str(e)}"
            }
        except Exception as e:
            print(f"      ❌ Analysis failed: {str(e)}")
            # Return analysis failure as a bug itself
            return {
                "makes_sense": False,
                "bugs": [{
                    "type": "analysis_failure",
                    "description": f"Analysis failed: {str(e)}",
                    "severity": "critical",
                    "evidence": "Analysis failed completely"
                }],
                "analysis": f"Analysis error: {str(e)}"
            }

    async def generate_scenarios_from_bugs(self):
        """Generate new test scenarios based on bugs found."""
        if not self.test_results:
            return self.get_default_scenarios()

        prompt = f"""Based on these recent test results and bugs:

{json.dumps(self.test_results[-5:], indent=2)}

Generate 3 new test scenarios that:
1. Stress test the areas where bugs were found
2. Test edge cases not yet covered
3. Test context switching between different topics
4. Test the specific functionality that failed

IMPORTANT: Return ONLY valid JSON array, no markdown formatting:
[
    {{
        "name": "Test scenario name",
        "steps": [
            {{
                "input": "user message",
                "expect": ["keywords", "that should", "appear"],
                "not_expect": ["words", "that shouldnt", "appear"]
            }}
        ]
    }}
]"""

        try:
            response = await self.llm.arun(
                messages=[
                    {"role": "system", "content": "Generate test scenarios to uncover bugs. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                options=RequestOptions(temperature=0.7)
            )

            # Extract JSON from response (handle markdown code blocks)
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            elif response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```

            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```

            scenarios = json.loads(response_text.strip())
            print(f"📝 Generated {len(scenarios)} new scenarios from bug patterns")
            return scenarios

        except Exception as e:
            print(f"⚠️  Scenario generation failed: {str(e)}")
            return self.get_default_scenarios()

    async def create_issue(self, scenario, bugs):
        """Create GitHub issue for bugs found."""
        try:
            bug_summary = "\n".join([f"- **{b['type']}**: {b['description']}" for b in bugs])

            body = f"""## 🤖 Automated Test Failure

### Test Scenario: {scenario['name']}

### Bugs Found:
{bug_summary}

### Test Steps:
```yaml
{yaml.dump(scenario, default_flow_style=False)}
```

### Bug Details:
```json
{json.dumps(bugs, indent=2)}
```

---
*Generated by automated test harness - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

            result = subprocess.run([
                'gh', 'issue', 'create',
                '--title', f"[AUTO-BUG] {bugs[0]['type']}: {scenario['name']}",
                '--body', body,
                '--label', 'bug,automated-test'
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # Extract issue number from output
                output = result.stdout.strip()
                if '/' in output:
                    return output.split('/')[-1]
            else:
                print(f"      GitHub issue creation failed: {result.stderr}")

        except Exception as e:
            print(f"      Issue creation error: {str(e)}")

        return None

    async def generate_fix(self, bug):
        """Generate fix instructions for a bug."""

        prompt = f"""Generate specific fix for this bug in the advisor agent:

Bug Type: {bug['type']}
Description: {bug['description']}
Severity: {bug['severity']}
Evidence: {bug.get('evidence', 'N/A')}

The advisor agent has these components:
- src/agents/advisor_agent/workflow_tools.py (tools like list_workflows, load_transcript_workflows)
- src/agents/advisor_agent/advisor_agent.py (tool mapping)
- prompts/advisor_agent/system_prompt.txt (LLM instructions)

IMPORTANT: Return ONLY valid JSON, no markdown formatting:
{{
    "file": "path/to/file.py",
    "change": "what specifically to change",
    "code": "code snippet to add/modify",
    "explanation": "why this fixes the bug"
}}"""

        try:
            response = await self.llm.arun(
                messages=[
                    {"role": "system", "content": "Generate specific code fixes for bugs. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                options=RequestOptions(temperature=0.1)
            )

            # Extract JSON from response (handle markdown code blocks)
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            elif response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```

            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```

            return json.loads(response_text.strip())

        except Exception as e:
            print(f"      Fix generation failed: {str(e)}")
            return None

    def save_test_results(self, iteration, scenarios):
        """Save test results to file."""
        result = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "scenarios_tested": len(scenarios),
            "scenarios": [s['name'] for s in scenarios]
        }

        self.test_results.append(result)

        # Keep only last 20 results
        if len(self.test_results) > 20:
            self.test_results = self.test_results[-20:]


async def main():
    """Main entry point."""
    harness = AdvisorTestHarness()
    await harness.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test harness stopped")