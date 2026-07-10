import streamlit as st
import requests

# Set page config
st.set_page_config(page_title="Roadmap Generator", page_icon="🗺️", layout="wide")

st.title("🗺️ Personalized Roadmap Generator")

# Sidebar for config
with st.sidebar:
    st.header("Configuration")
    API_BASE_URL = st.text_input("API Base URL", value="http://localhost:8000")

def get_api(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the API at {API_BASE_URL}{endpoint} — is the FastAPI server running?")
        st.stop()

def post_api(endpoint, payload):
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=payload)
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the API at {API_BASE_URL}{endpoint} — is the FastAPI server running?")
        st.stop()

# --- Step 2: Roadmap Selection ---
st.header("1. Select a Roadmap")
roadmaps = get_api("/roadmaps")
# Convert list of dicts to a dict mapping title/id to id
roadmap_options = {r["title"]: r["id"] for r in roadmaps}
selected_roadmap_title = st.selectbox("Roadmap", options=list(roadmap_options.keys()))

if selected_roadmap_title:
    selected_roadmap_id = roadmap_options[selected_roadmap_title]
    
    # Reset downstream topics if roadmap changes
    if st.session_state.get("current_roadmap_id") != selected_roadmap_id:
        st.session_state["current_roadmap_id"] = selected_roadmap_id
        for key in list(st.session_state.keys()):
            if key.startswith("topic_") or key.startswith("subtopic_"):
                del st.session_state[key]

    # --- Step 3: Known Topics Picker ---
    st.header("2. What do you already know?")
    st.write("Check the topics and subtopics you have already mastered.")
    topics_data = get_api(f"/roadmaps/{selected_roadmap_id}/topics")
    
    # Group topics
    top_level = [t for t in topics_data if t.get("parent_topic_id") is None]
    subtopics = {t["id"]: [] for t in top_level}
    
    for item in topics_data:
        parent_id = item.get("parent_topic_id")
        if parent_id and parent_id in subtopics:
            subtopics[parent_id].append(item)
            
    for topic in top_level:
        with st.expander(topic["title"]):
            st.checkbox("I already know this whole topic", key=f"topic_{topic['id']}")
            for subtopic in subtopics.get(topic["id"], []):
                st.checkbox(subtopic["title"], key=f"subtopic_{subtopic['id']}")
                
    # --- Step 4: Duration Inputs ---
    st.header("3. How much time do you have?")
    col1, col2 = st.columns(2)
    with col1:
        duration_weeks = st.number_input("Duration (weeks)", min_value=1, value=8, step=1)
    with col2:
        hours_per_week = st.number_input("Hours per week", min_value=0.5, value=10.0, step=0.5)

    # --- Step 5: Generate ---
    if st.button("Generate My Roadmap", type="primary"):
        # Calculate known_node_ids directly from session state
        known_node_ids = []
        for key, value in st.session_state.items():
            if (key.startswith("topic_") or key.startswith("subtopic_")) and value is True:
                # Extract the ID by removing the prefix
                node_id = key.split("_", 1)[1]
                known_node_ids.append(node_id)
                
        payload = {
            "roadmap_id": selected_roadmap_id,
            "known_node_ids": known_node_ids,
            "duration_weeks": duration_weeks,
            "hours_per_week": hours_per_week
        }
        
        with st.spinner("Generating your personalized roadmap..."):
            response = post_api("/generate", payload)
            
            if response.status_code == 200:
                st.session_state["generated_plan"] = response.json()
            else:
                try:
                    error_detail = response.json().get("detail", response.text)
                except Exception:
                    error_detail = response.text
                st.error(f"API Error ({response.status_code}): {error_detail}")

# --- Step 6: Render the Plan ---
if "generated_plan" in st.session_state:
    st.divider()
    plan = st.session_state["generated_plan"]
    
    st.header("Your Personalized Roadmap")
    if plan.get("overall_intro"):
        st.caption(plan["overall_intro"])
        
    if plan.get("narration_failed"):
        st.warning("AI narration wasn't available for this plan — showing the structured schedule only.")
        
    for week in plan.get("weeks", []):
        st.subheader(f"Week {week['week_number']}")
        
        if not plan.get("narration_failed"):
            if week.get("intro"):
                st.write(week["intro"])
            if week.get("milestone"):
                st.info(week["milestone"])
                
        for item in week.get("items", []):
            if item["type"] in ["topic_overview", "subtopic"]:
                st.markdown(f"**{item['title']}**")
                
                # We can use expander for description if it's long, or just render it. Let's do expander if there is a description.
                has_desc = bool(item.get("description"))
                has_res = bool(item.get("resources"))
                
                if has_desc or has_res:
                    with st.expander("View Details"):
                        if has_desc:
                            st.markdown(item["description"])
                        if has_res:
                            st.markdown("**Resources:**")
                            for res in item["resources"]:
                                st.markdown(f"- [{res['title']}]({res['url']})")
            
            elif item["type"] == "choice_group":
                st.markdown("🔀 **Choose one:**")
                for option in item.get("options", []):
                    title = f"⭐ Recommended: {option['title']}" if option.get("status") == "personal_recommendation" else option['title']
                    with st.expander(title):
                        if option.get("description"):
                            st.markdown(option["description"])
                        if option.get("resources"):
                            st.markdown("**Resources:**")
                            for res in option["resources"]:
                                st.markdown(f"- [{res['title']}]({res['url']})")
                                
    if plan.get("stretch_goals"):
        st.divider()
        st.header("Stretch Goals (if you have extra time)")
        for item in plan["stretch_goals"]:
            st.markdown(f"**{item['title']}**")
            has_desc = bool(item.get("description"))
            has_res = bool(item.get("resources"))
            if has_desc or has_res:
                with st.expander("View Details"):
                    if has_desc:
                        st.markdown(item["description"])
                    if has_res:
                        st.markdown("**Resources:**")
                        for res in item["resources"]:
                            st.markdown(f"- [{res['title']}]({res['url']})")

    # --- Step 7: Staleness Check ---
    st.divider()
    if st.button("Check for roadmap updates"):
        staleness_payload = {
            "roadmap_id": plan["roadmap_id"],
            "version_generated_against": plan["version_generated_against"],
            "node_ids_used": plan["node_ids_used"]
        }
        with st.spinner("Checking for updates..."):
            stale_res = post_api("/check-staleness", staleness_payload)
            if stale_res.status_code == 200:
                stale_data = stale_res.json()
                if not stale_data.get("stale"):
                    st.success("Your plan is up to date")
                else:
                    changed_nodes = stale_data.get("changed_nodes", [])
                    st.warning("Your plan is stale. The following nodes have changed: " + ", ".join([f"{n['title']} ({n['id']})" for n in changed_nodes]))
            else:
                st.error("Failed to check staleness.")
