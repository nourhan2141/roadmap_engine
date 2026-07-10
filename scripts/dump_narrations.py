from roadmap_engine import engine, llm
import json

def extract():
    with open('outputs/scenario1_output.json', encoding='utf-8') as f:
        d = json.load(f)
    
    with open('outputs/narration_dump_with_topics.txt', 'w', encoding='utf-8') as out:
        for w in d.get("weeks", []):
            out.write(f"WEEK {w['week_number']}\n")
            
            # Gather all titles
            titles = []
            for item in w.get("items", []):
                if item.get("type") == "choice_group":
                    for opt in item.get("options", []):
                        titles.append(opt.get("title"))
                else:
                    titles.append(item.get("title"))
                    
            out.write(f"Topics Provided:\n  • " + "\n  • ".join(titles) + "\n\n")
            out.write(f"Generated Narration:\n  Intro: {w.get('intro', 'MISSING')}\n")
            out.write(f"  Milestone: {w.get('milestone', 'MISSING')}\n")
            out.write("-" * 80 + "\n\n")

if __name__ == '__main__':
    extract()
