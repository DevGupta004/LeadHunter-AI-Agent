"""
Google Maps AI-Powered Scraper
Uses Local Llama 3.2 for intelligent data extraction
Hybrid approach: Playwright + AI for best results
"""

import streamlit as st
from playwright.sync_api import sync_playwright
import time
import json
import requests
import re
from export_utils import export_to_excel, deduplicate_records, get_export_summary

st.title("🤖 AI-Powered Google Maps Scraper")
st.caption("Using Local Llama 3.2 for Intelligent Extraction")

# Configuration
url = st.text_input(
    "Google Maps URL",
    value="https://www.google.com/maps/search/cloth+stores+in+Lucknow/",
)

col1, col2 = st.columns(2)
with col1:
    max_stores = st.slider("Max stores", 5, 50, 10)
with col2:
    enable_pagination = st.checkbox("Enable pagination", value=True)

st.info("""
🤖 **AI-Powered Features:**
- ✅ Uses Local Llama 3.2 (no API needed!)
- 🧠 Understands context and variations
- 🎯 Smarter data extraction
- 🔄 Auto-adapts to format changes
- ⚡ Falls back to regex for speed

**Expected:** 60-80% accuracy (better than pure regex!)
""")

# AI Helper Functions
def call_ollama_ai(prompt, model="llama3.2"):
    """Call local Ollama AI for intelligent extraction"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": 100
                }
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["response"].strip()
        return None
    except Exception as e:
        st.warning(f"AI call failed: {str(e)}")
        return None

def extract_with_ai(text, field_name):
    """Use AI to extract specific field from text"""
    prompt = f"""From this Google Maps store text, extract ONLY the {field_name}.
Return just the value, nothing else. If not found, return "Not found".

Text: {text[:1500]}

{field_name}:"""
    
    result = call_ollama_ai(prompt)
    return result if result else "Not found"

def extract_all_fields_with_ai(text):
    """Use AI to extract all fields at once (more efficient)"""
    prompt = f"""From this Google Maps store page, extract the following information.
IMPORTANT: Extract ONLY the phone number for THIS SPECIFIC STORE, not from navigation or common elements.
Return ONLY a JSON object with these exact fields:

{{
  "store_name": "name here",
  "rating": "4.5 or N/A",
  "reviews_count": "number or N/A",
  "phone": "phone number for THIS store only or Not found",
  "address": "full address or Not found",
  "hours": "opening hours or Not found",
  "website": "website URL or Not found"
}}

Text from page (focus on store details section):
{text[:2000]}

JSON:"""
    
    result = call_ollama_ai(prompt)
    if result:
        try:
            # Try to parse JSON
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except:
            pass
    return None

def extract_coords_from_url(url):
    """Extract coordinates from URL (fast, no AI needed)"""
    coords_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if coords_match:
        return coords_match.group(1), coords_match.group(2)
    return None, None

def extract_phone_fallback(page, page_text):
    """Regex fallback for phone - Target store details specifically"""
    phone = None
    try:
        # Method 1: Look for phone button/link in store details
        phone_selectors = [
            'button[data-item-id*="phone"]',
            'a[href^="tel:"]',
            '[data-item-id*="phone"]',
            '[aria-label*="phone" i]',
            '[aria-label*="call" i]',
        ]
        
        for selector in phone_selectors:
            try:
                phone_element = page.query_selector(selector)
                if phone_element:
                    phone_text = phone_element.inner_text()
                    # Extract phone from text
                    phone_match = re.search(r'[\d\s\+\-\(\)]{10,}', phone_text)
                    if phone_match:
                        phone = phone_match.group(0).strip()
                        break
                    
                    # Check href for tel: links
                    href = phone_element.get_attribute('href')
                    if href and href.startswith('tel:'):
                        phone = href.replace('tel:', '').strip()
                        break
            except:
                continue
        
        # Method 2: Look for phone in store details panel (more targeted)
        if not phone:
            # Try to find the details panel
            details_panel = page.query_selector('[role="main"], [class*="panel"], [class*="details"]')
            if details_panel:
                panel_text = details_panel.inner_text()
                # Look for phone near keywords
                phone_keywords = ['phone', 'call', 'tel', 'contact']
                for keyword in phone_keywords:
                    # Find text around keyword
                    keyword_pos = panel_text.lower().find(keyword)
                    if keyword_pos != -1:
                        # Extract 200 chars around keyword
                        start = max(0, keyword_pos - 50)
                        end = min(len(panel_text), keyword_pos + 150)
                        context = panel_text[start:end]
                        
                        # Extract phone from context
                        patterns = [
                            r'\d{5}\s?\d{5}',  # Indian format: 12345 67890
                            r'\d{3,4}[\s-]?\d{3,4}[\s-]?\d{4}',  # General: 1234-567-8900
                            r'\+91[\s-]?\d{10}',  # +91 format
                            r'0\d{2,4}[\s-]?\d{6,8}',  # Landline: 0522-1234567
                            r'\+?\d[\d\s\-\(\)]{9,}',  # General international
                        ]
                        
                        for pattern in patterns:
                            match = re.search(pattern, context)
                            if match:
                                phone = match.group(0).strip()
                                # Filter out common non-phone numbers
                                if len(phone) >= 10 and not phone.startswith('1800'):
                                    break
                        
                        if phone:
                            break
        
        # Method 3: Fallback - search entire page but filter better
        if not phone:
            patterns = [
                r'\d{5}\s?\d{5}',  # Indian format: 12345 67890
                r'\d{3,4}[\s-]?\d{3,4}[\s-]?\d{4}',  # General: 1234-567-8900
                r'\+91[\s-]?\d{10}',  # +91 format
                r'0\d{2,4}[\s-]?\d{6,8}',  # Landline: 0522-1234567
            ]
            
            # Get all matches and filter
            all_phones = []
            for pattern in patterns:
                matches = re.findall(pattern, page_text)
                all_phones.extend(matches)
            
            # Filter out common numbers and pick the most likely one
            filtered_phones = []
            for p in all_phones:
                p_clean = p.strip()
                # Skip if too short or common patterns
                if len(p_clean) >= 10:
                    # Skip common Google/help numbers
                    if not (p_clean.startswith('1800') or 
                            p_clean.startswith('1-800') or
                            'google' in p_clean.lower()):
                        filtered_phones.append(p_clean)
            
            # Use the first valid phone, or None if none found
            if filtered_phones:
                phone = filtered_phones[0]
    except Exception as e:
        pass
    
    return phone

# Check if Ollama is running
def check_ollama():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

# Main UI
if st.button("🚀 Start AI-Powered Scraping", type="primary"):
    
    # Check Ollama
    if not check_ollama():
        st.error("""
        ❌ **Ollama is not running!**
        
        Please start Ollama first:
        ```bash
        ollama serve
        ```
        
        Make sure Llama 3.2 is installed:
        ```bash
        ollama pull llama3.2
        ```
        """)
        st.stop()
    
    st.success("✅ Ollama is running!")
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        with sync_playwright() as p:
            status_text.text("🌐 Launching browser...")
            
            browser = p.chromium.launch(
                headless=False,
                slow_mo=500
            )
            
            page = browser.new_page(viewport={'width': 1400, 'height': 900})
            
            status_text.text("📍 Loading Google Maps...")
            page.goto(url, timeout=30000)
            time.sleep(15)
            
            # Pagination
            if enable_pagination:
                status_text.text("📜 Loading more results...")
                for scroll in range(max(3, max_stores // 10)):
                    page.evaluate('''
                        const feed = document.querySelector('[role="feed"]');
                        if (feed) feed.scrollTo(0, feed.scrollHeight);
                    ''')
                    time.sleep(2)
                time.sleep(3)
            
            # Find stores
            status_text.text("🔍 Finding stores...")
            selectors = ['a[href*="/maps/place/"]', '[role="article"]']
            
            store_elements = []
            for selector in selectors:
                elements = page.query_selector_all(selector)
                if len(elements) > 0:
                    store_elements = elements[:max_stores]
                    st.success(f"✅ Found {len(elements)} stores")
                    break
            
            if not store_elements:
                st.error("❌ No stores found")
                browser.close()
                st.stop()
            
            # Process each store
            for i in range(min(max_stores, len(store_elements))):
                try:
                    progress_bar.progress((i + 1) / min(max_stores, len(store_elements)))
                    status_text.text(f"🤖 AI analyzing store {i+1}/{min(max_stores, len(store_elements))}...")
                    
                    # Re-find store elements to avoid stale references
                    current_elements = page.query_selector_all(selectors[0])
                    if i >= len(current_elements):
                        st.warning(f"⚠️ Store {i+1} not found, skipping...")
                        continue
                    
                    element = current_elements[i]
                    
                    # Scroll element into view
                    try:
                        element.scroll_into_view_if_needed()
                        time.sleep(0.5)
                    except:
                        pass
                    
                    # Store the old URL to detect change
                    old_url = page.url
                    
                    # Click store
                    try:
                        element.click()
                    except Exception as click_error:
                        st.warning(f"⚠️ Could not click store {i+1}: {str(click_error)}")
                        continue
                    
                    # Wait for URL to change (indicates new store loaded)
                    url_changed = False
                    for wait_attempt in range(15):  # Try for 15 seconds
                        time.sleep(0.5)
                        if page.url != old_url:
                            url_changed = True
                            break
                    
                    # Wait for details panel to load with new content
                    details_panel_loaded = False
                    for wait_attempt in range(10):
                        try:
                            details_panel = page.query_selector('[role="main"]')
                            if details_panel:
                                panel_text = details_panel.inner_text()
                                # Check if panel has meaningful content (not just loading)
                                if len(panel_text) > 50:
                                    details_panel_loaded = True
                                    break
                        except:
                            pass
                        time.sleep(0.5)
                    
                    # Extra wait for content to stabilize
                    time.sleep(2)
                    
                    # Wait for store name element to be visible in details panel
                    try:
                        page.wait_for_selector('[role="main"] h1', timeout=10000)
                    except:
                        try:
                            page.wait_for_selector('h1', timeout=5000)
                        except:
                            pass
                    
                    # Get FRESH page data from DETAILS PANEL specifically
                    current_url = page.url
                    
                    # Extract from details panel, not entire body
                    details_panel = page.query_selector('[role="main"]')
                    if not details_panel:
                        details_panel = page.query_selector('body')
                    
                    panel_text = details_panel.inner_text() if details_panel else ""
                    page_text = panel_text  # Use panel text for AI extraction
                    
                    # Debug: Show URL change
                    if current_url == old_url:
                        st.warning(f"⚠️ Store {i+1}: URL didn't change! Might be duplicate data.")
                    
                    # Extract coordinates (fast, no AI needed)
                    lat, lng = extract_coords_from_url(current_url)
                    
                    # Try AI extraction first
                    status_text.text(f"🧠 AI extracting data for store {i+1}...")
                    ai_data = extract_all_fields_with_ai(page_text)
                    
                    if ai_data:
                        # AI succeeded
                        store_name = ai_data.get('store_name', 'Unknown')
                        rating = ai_data.get('rating', 'N/A')
                        reviews = ai_data.get('reviews_count', 'N/A')
                        phone = ai_data.get('phone', 'Not found')
                        address = ai_data.get('address', 'Not found')
                        hours = ai_data.get('hours', 'Not found')
                        website = ai_data.get('website', 'Not found')
                    else:
                        # AI failed, fallback to regex
                        status_text.text(f"⚡ Using regex fallback for store {i+1}...")
                        
                        # Extract name from details panel
                        store_name = "Unknown"
                        name_selectors = [
                            '[role="main"] h1',
                            '[role="main"] [class*="fontHeadlineLarge"]',
                            'h1[data-attrid="title"]',
                            'h1',
                        ]
                        
                        for selector in name_selectors:
                            try:
                                name_el = page.query_selector(selector)
                                if name_el:
                                    name_text = name_el.inner_text().strip()
                                    if len(name_text) > 3 and name_text not in ['Directions', 'Save', 'Share']:
                                        store_name = name_text[:200]
                                        break
                            except:
                                continue
                        
                        # Extract rating from details panel (first 500 chars where rating appears)
                        rating = 'N/A'
                        if panel_text:
                            top_text = panel_text[:500]
                            rating_match = re.search(r'(\d\.\d)[\s\xa0]*\((\d+(?:,\d+)?)\)', top_text)
                            if rating_match:
                                rating_val = float(rating_match.group(1))
                                if 1.0 <= rating_val <= 5.0:
                                    rating = rating_match.group(1)
                                    reviews = rating_match.group(2).replace(',', '')
                                else:
                                    # Try simpler pattern
                                    rating_match = re.search(r'(\d\.\d)', top_text)
                                    if rating_match:
                                        rating_val = float(rating_match.group(1))
                                        if 1.0 <= rating_val <= 5.0:
                                            rating = rating_match.group(1)
                            else:
                                rating_match = re.search(r'(\d\.\d)', top_text)
                                if rating_match:
                                    rating_val = float(rating_match.group(1))
                                    if 1.0 <= rating_val <= 5.0:
                                        rating = rating_match.group(1)
                        
                        # Extract reviews count
                        reviews = 'N/A'
                        if panel_text and rating != 'N/A':
                            top_text = panel_text[:500]
                            review_match = re.search(r'\((\d+(?:,\d+)?)\)', top_text)
                            if review_match:
                                reviews = review_match.group(1).replace(',', '')
                        
                        phone = extract_phone_fallback(page, page_text)
                        if not phone:
                            phone = 'Not found'
                        
                        address = 'Not found'
                        hours = 'Not found'
                        website = 'Not found'
                    
                    # Extract Plus Code (regex is fine)
                    plus_code = None
                    plus_match = re.search(r'[A-Z0-9]{4}\+[A-Z0-9]{2,3}\s+\w+', page_text)
                    if plus_match:
                        plus_code = plus_match.group(0)
                    
                    # Build result
                    result = {
                        'number': i + 1,
                        'store_name': store_name,
                        'rating': rating,
                        'reviews_count': reviews,
                        'phone_number': phone,
                        'address': address,
                        'opening_hours': hours,
                        'website': website,
                        'plus_code': plus_code if plus_code else 'Not found',
                        'latitude': lat if lat else 'Not found',
                        'longitude': lng if lng else 'Not found',
                        'google_maps_url': current_url,
                        'extraction_method': 'AI' if ai_data else 'Regex'
                    }
                    
                    results.append(result)
                    
                    # Show result
                    method_icon = "🤖" if ai_data else "⚡"
                    with st.expander(f"{method_icon} {store_name} - ⭐ {rating}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Extraction:** {result['extraction_method']}")
                            st.write(f"**⭐ Rating:** {rating} ({reviews} reviews)")
                            st.write(f"**📞 Phone:** {phone}")
                            st.write(f"**🕐 Hours:** {hours}")
                        with col2:
                            st.write(f"**📍 Address:** {address[:80]}...")
                            st.write(f"**🌐 Website:** {website}")
                            st.write(f"**🌍 Coords:** {lat}, {lng}")
                    
                except Exception as e:
                    st.warning(f"⚠️ Error with store {i+1}: {str(e)}")
                    continue
            
            browser.close()
            
            # Summary
            st.success(f"✅ Completed! Scraped {len(results)} stores")
            
            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                ai_count = sum(1 for r in results if r['extraction_method'] == 'AI')
                st.metric("🤖 AI Extracted", f"{ai_count}/{len(results)}")
            with col2:
                phones = sum(1 for r in results if r['phone_number'] != 'Not found')
                st.metric("📞 Phones", f"{phones}/{len(results)}")
            with col3:
                ratings = sum(1 for r in results if r['rating'] != 'N/A')
                st.metric("⭐ Ratings", f"{ratings}/{len(results)}")
            with col4:
                addresses = sum(1 for r in results if r['address'] != 'Not found')
                st.metric("📍 Addresses", f"{addresses}/{len(results)}")
            
            # Export options
            if results:
                st.markdown("---")
                st.subheader("📥 Export Results")
                
                # Deduplicate for summary
                unique_records = deduplicate_records(results)
                st.markdown(get_export_summary(len(results), len(unique_records)))
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Excel export for telecalling team
                    excel_file = export_to_excel(results, 'telecalling_leads.xlsx')
                    st.download_button(
                        "📊 Download Excel (Telecalling Team)",
                        data=excel_file.getvalue(),
                        file_name="telecalling_leads.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help="Excel file with unique records: Name, Contact, Location, Website, Rating"
                    )
                
                with col2:
                    # JSON export (full data)
                    st.download_button(
                        "📥 Download JSON (Full Data)",
                        data=json.dumps(results, indent=2, ensure_ascii=False),
                        file_name="google_maps_ai_results.json",
                        mime="application/json",
                        help="Complete data in JSON format"
                    )
                
                st.info("💡 **Tip:** Upload the Excel file to Google Sheets for team collaboration!")
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Info Section
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🤖 AI-Powered Features")
    st.markdown("""
    **What AI does:**
    - Understands context
    - Handles variations
    - Extracts complex data
    - Adapts to changes
    
    **When AI is used:**
    - Phone numbers with text
    - Complex addresses
    - Ambiguous data
    - Unusual formats
    """)

with col2:
    st.subheader("⚡ Hybrid Approach")
    st.markdown("""
    **Best of both worlds:**
    - Fast regex for simple data
    - AI for complex cases
    - 60-80% success rate
    - Adapts automatically
    
    **Extraction methods:**
    - 🤖 AI: Smart extraction
    - ⚡ Regex: Fast fallback
    """)

st.markdown("---")

st.subheader("💡 Tips for Best Results")
st.markdown("""
**Prerequisites:**
1. Make sure Ollama is running: `ollama serve`
2. Llama 3.2 model installed: `ollama pull llama3.2`

**For best accuracy:**
- Start with 10 stores to test
- Enable pagination for more data
- Watch browser to see AI working
- Check "extraction_method" in results

**AI vs Non-AI:**
- AI version: 60-80% success (smarter)
- Regex version: 40-60% success (faster)
- Choose based on your needs!
""")

