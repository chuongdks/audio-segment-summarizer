# Commit 3.2 files changes:
## base.py holds everything that every style shares — the Ollama HTTP call, httpx.Timeout setup, JSON fence stripping, segment index building, and transcript formatting. Subclasses never need to touch any of that.

## meeting.py and general.py each only implement two methods: build_prompt() (the instruction text) and parse_result() (mapping the JSON dict to MeetingSummary). That's all a new style ever needs.

## __init__.py has the SUMMARIZERS dict — adding a new style in the future is just dropping a new file in the folder and registering it there.

## summarizer.py is now just three lines — it calls get_summarizer(style) and delegates. The function signature stays identical to before so nothing else in the codebase needed to change.

## /summarize now accepts ?style=meeting or ?style=general as a query param. The frontend hook will pass this once we wire up the style selector in the UI — ready for that when you are.