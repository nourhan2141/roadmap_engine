import json
from groq import Groq
from .config import settings

def generate_narration(plan_payload: dict, max_retries: int = 2) -> dict:
    if not settings.groq_api_key or settings.groq_api_key == "placeholder_key":
        print("Warning: GROQ_API_KEY is not set. Skipping narration.")
        return plan_payload
        
    client = Groq(api_key=settings.groq_api_key)
    
    schema = {
        "type": "object",
        "properties": {
            "overall_intro": {"type": "string"},
            "week_narratives": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "week_number": {"type": "integer"},
                        "intro": {"type": "string"},
                        "milestone": {"type": "string"}
                    },
                    "required": ["week_number", "intro", "milestone"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["overall_intro", "week_narratives"],
        "additionalProperties": False
    }

    # Build the prompt payload without resources or ids
    weeks_summary = []
    week_title_sets = {}
    for week in plan_payload.get("weeks", []):
        week_num = week.get("week_number")
        items = []
        titles = set()
        for item in week.get("items", []):
            if item.get("type") == "choice_group":
                options = [opt.get("title") for opt in item.get("options", [])]
                items.append(f"Choice Group: {item.get('title')} (Options: {', '.join(options)})")
                titles.add(item.get("title"))
                for opt in item.get("options", []):
                    titles.add(opt.get("title"))
            else:
                items.append(item.get("title"))
                titles.add(item.get("title"))
        weeks_summary.append({"week_number": week_num, "topics": items})
        week_title_sets[week_num] = titles
        
    system_prompt = """You are writing short motivational and orienting narration ONLY. You will be given a structured weekly plan for a learning roadmap. For each week, write a 1-2 sentence intro connecting that week's topics, and a 1-sentence milestone description of what the learner will be able to do after that week.

CRITICAL RULES:
1. Do NOT mention any URL, link, or resource by name.
2. Do NOT invent additional topics, tools, or technologies not present in the provided plan. Write only about what is explicitly listed.
3. Write only short, direct narration."""

    user_content = f"Here is the weekly plan:\n{json.dumps(weeks_summary, indent=2)}"
    
    retry_prompt_additions = ""
    
    for attempt in range(max_retries + 1):
        try:
            completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content + retry_prompt_additions}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "narration",
                        "strict": True,
                        "schema": schema
                    }
                }
            )
            
            raw_response = completion.choices[0].message.content
            if attempt == 0:
                print(f"=== ATTEMPT 0 RAW TEXT ===\n{raw_response}\n========================")
            parsed = json.loads(raw_response)
            
            # Faithfulness Check
            strings_to_check = [parsed.get("overall_intro", "")]
            for w in parsed.get("week_narratives", []):
                strings_to_check.append(w.get("intro", ""))
                strings_to_check.append(w.get("milestone", ""))
                
            has_url = any("http://" in s or "https://" in s for s in strings_to_check)
            
            valid_weeks = {w["week_number"] for w in plan_payload.get("weeks", [])}
            generated_weeks = {w["week_number"] for w in parsed.get("week_narratives", [])}
            has_invalid_weeks = not generated_weeks.issubset(valid_weeks)
            
            # Cross-week leakage check
            import re
            
            # Common dictionary words that appear as standalone titles
            stoplist = {"testing", "base", "internet", "hosting", "dns", "api", "apis", "git", "go", "php"}
            
            leaked_titles = []
            for w in parsed.get("week_narratives", []):
                wn = w.get("week_number")
                if wn not in week_title_sets:
                    continue
                narration_text = (w.get("intro", "") + " " + w.get("milestone", "")).lower()
                
                blocklist = set()
                for other_wn, other_titles in week_title_sets.items():
                    if other_wn != wn:
                        blocklist.update(other_titles)
                        
                # Remove titles that are valid for this week
                blocklist -= week_title_sets[wn]
                
                for b in blocklist:
                    if len(b) >= 4 and b.lower() not in stoplist:
                        # Use word boundary matching to avoid "base" triggering on "database"
                        pattern = r'\b' + re.escape(b.lower()) + r'\b'
                        if re.search(pattern, narration_text):
                            leaked_titles.append(f"'{b}' leaked into Week {wn}")
            
            has_leakage = len(leaked_titles) > 0
            
            if has_url or has_invalid_weeks or has_leakage:
                violation_msg = "\n\nCRITICAL ERROR IN PREVIOUS ATTEMPT:"
                if has_url:
                    violation_msg += "\nYou included a URL (http:// or https://). You MUST NOT include URLs."
                if has_invalid_weeks:
                    violation_msg += f"\nYou generated narratives for week numbers {generated_weeks} but the valid weeks are only {valid_weeks}."
                if has_leakage:
                    violation_msg += f"\nYou hallucinated topics into the wrong weeks: {', '.join(leaked_titles)}. You MUST NOT mention topics from other weeks."
                
                retry_prompt_additions += violation_msg
                if has_leakage:
                    print(f"[LLM] Faithfulness check failed (Attempt {attempt}): {', '.join(leaked_titles)}")
                else:
                    print(f"[LLM] Faithfulness check failed (Attempt {attempt})")
                continue # Retry
                
            # Success! Merge into payload
            merged_payload = dict(plan_payload)
            merged_payload["overall_intro"] = parsed.get("overall_intro")
            
            # Create a lookup for week narratives
            narratives_by_week = {w["week_number"]: w for w in parsed.get("week_narratives", [])}
            
            for week in merged_payload.get("weeks", []):
                wn = week["week_number"]
                if wn in narratives_by_week:
                    week["intro"] = narratives_by_week[wn]["intro"]
                    week["milestone"] = narratives_by_week[wn]["milestone"]
                    
            print(f"[LLM] Narration succeeded after {attempt} retries.")
            return merged_payload
            
        except Exception as e:
            print(f"[LLM] Exception during generation (attempt {attempt}): {e}")
            
    # If we exhaust retries or fail repeatedly
    print(f"[LLM] Narration failed after {max_retries} retries.")
    merged_payload = dict(plan_payload)
    merged_payload["narration_failed"] = True
    return merged_payload
