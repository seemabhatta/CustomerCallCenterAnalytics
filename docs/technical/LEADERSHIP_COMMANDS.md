  📝 Leadership Insights CLI Commands to Try

  1. Strategic Questions for Different Executive Roles

  For Chief Compliance Officer (CCO):
  python cli.py leadership chat "What are our top compliance risks this week?" --exec-id "john.doe" --role "CCO"

  python cli.py leadership chat "Show me all FDCPA violations in the last 30 days" --exec-id "john.doe" --role "CCO"

  python cli.py leadership chat "Which customer interactions had compliance issues?" --exec-id "john.doe" --role "CCO"

  For VP of Operations:
  python cli.py leadership chat "What is our workflow approval backlog?" --exec-id "jane.smith" --role "VP"

  python cli.py leadership chat "How many high-risk workflows are pending?" --exec-id "jane.smith" --role "VP"

  python cli.py leadership chat "What's our execution success rate this month?" --exec-id "jane.smith" --role "VP"

  For Call Center Manager:
  python cli.py leadership chat "What are the main customer complaint topics?" --exec-id "mike.jones" --role "Manager"

  python cli.py leadership chat "Show me sentiment analysis for this week's calls" --exec-id "mike.jones" --role "Manager"

  python cli.py leadership chat "Which topics are causing the most escalations?" --exec-id "mike.jones" --role "Manager"

  2. Session Management Commands

  Create and continue conversations:
  # Start a new conversation
  python cli.py leadership chat "What are our operational metrics?" --exec-id "john.doe" --role "CCO"

  # List your sessions to get the session ID
  python cli.py leadership sessions --exec-id "john.doe"

  # Continue the conversation using session ID (replace SESSION_ID with actual ID)
  python cli.py leadership chat "Can you drill down on the compliance metrics?" --exec-id "john.doe" --role "CCO" --session "SESSION_ID"

  # View the full conversation history
  python cli.py leadership history SESSION_ID

  3. Dashboard and Analytics Commands

  Different dashboard views:
  # General dashboard
  python cli.py leadership dashboard

  # Role-specific dashboard (if implemented)
  python cli.py leadership dashboard --role "CCO"
  python cli.py leadership dashboard --role "VP"
  python cli.py leadership dashboard --role "Manager"

  4. Data-Specific Queries

  Time-based queries:
  python cli.py leadership chat "What happened in the last 24 hours?" --exec-id "john.doe" --role "VP"

  python cli.py leadership chat "Show me this week's performance metrics" --exec-id "john.doe" --role "Manager"

  python cli.py leadership chat "Compare this week to last week's compliance issues" --exec-id "john.doe" --role "CCO"

  Risk-focused queries:
  python cli.py leadership chat "What are our highest risk areas?" --exec-id "jane.smith" --role "VP"

  python cli.py leadership chat "Show me all high-risk workflows" --exec-id "jane.smith" --role "VP"

  python cli.py leadership chat "Which customers are at risk of churn?" --exec-id "mike.jones" --role "Manager"

  5. Performance and Efficiency Queries

  python cli.py leadership chat "What's our average resolution time?" --exec-id "mike.jones" --role "Manager"

  python cli.py leadership chat "How many workflows are stuck in approval?" --exec-id "jane.smith" --role "VP"

  python cli.py leadership chat "What's causing delays in our processes?" --exec-id "jane.smith" --role "VP"

  6. System Status and Monitoring

  # Check service health
  python cli.py leadership status

  # View cache performance after multiple queries
  python cli.py leadership dashboard

  # Check how many sessions you have
  python cli.py leadership sessions --exec-id "john.doe" --limit 20

  7. Complex Multi-Part Queries

  python cli.py leadership chat "Analyze our compliance posture, identify top risks, and recommend immediate actions" --exec-id "john.doe" --role "CCO"

  python cli.py leadership chat "What are our bottlenecks and how can we improve efficiency?" --exec-id "jane.smith" --role "VP"

  python cli.py leadership chat "Give me a comprehensive overview of customer satisfaction issues" --exec-id "mike.jones" --role "Manager"

  💡 Pro Tips:

  1. Use session continuity - Start a conversation and continue it with follow-up questions using --session
  2. Try different roles - CCO, VP, Manager get different perspectives
  3. Watch the cache - Second identical query should be faster (cache hit)
  4. Check the dashboard - After several queries, see the learning patterns build up