"""
Simplified Google Maps Scraper - More Reliable
Tries multiple selectors and has better error handling
"""

import streamlit as st
from playwright.sync_api import sync_playwright
import time
import re
import json
from export_utils import export_to_excel, deduplicate_records, get_export_summary

st.title("🗺️ Google Maps Store Scraper")
st.caption("Simplified approach - clicks and extracts visible data")

url = st.text_input(
    "Google Maps URL",
    value="https://www.google.com/maps/search/real+estate+business+in+lucknow",
)

max_stores = st.slider("Max stores to scrape", 10, 100, 20, 
                        help="Set to 100 for all results with pagination")

enable_pagination = st.checkbox("Enable pagination (scroll for more results)", value=True,
                                 help="Automatically scroll to load all stores")

st.info("""
💡 **Enhanced Scraper - Extracts 14 Fields:**
- ✅ Store name
- ⭐ **Rating (out of 5)**
- 📊 **Total ratings count**
- 💬 **Number of reviews**
- ✅ Full address
- ✅ Phone number
- ✅ Opening hours
- ✅ Website
- ✅ Plus code
- ✅ Latitude & Longitude
- ✅ Google Maps URL (CID)
- ✅ Pagination support

**Expected:** 40-70% success rate for ratings, 30-50% for phone numbers
""")

def clean_phone(text):
    """Extract and clean phone number"""
    # Remove common prefixes
    text = text.replace("Phone:", "").replace("Tel:", "").strip()
    # Find phone patterns
    patterns = [
        r'\+?\d[\d\s-]{8,}',  # General phone pattern
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
    return text if len(text) > 5 else None

if st.button("🚀 Start Scraping", type="primary"):
    results = []
    
    with st.spinner("Opening browser..."):
        try:
            with sync_playwright() as p:
                st.info("🌐 Launching Chrome...")
                
                browser = p.chromium.launch(
                    headless=False,
                    slow_mo=1000  # Slow down by 1 second between actions
                )
                
                page = browser.new_page(
                    viewport={'width': 1400, 'height': 900}
                )
                
                st.info("📍 Loading Google Maps...")
                page.goto(url, timeout=30000)
                
                st.info("⏳ Waiting for page to load (15 seconds)...")
                time.sleep(15)  # Give plenty of time
                
                # Take a screenshot for debugging
                page.screenshot(path="debug_screenshot.png")
                st.info("📸 Screenshot saved to debug_screenshot.png")
                
                # Pagination: Scroll to load more results
                if enable_pagination:
                    st.info("📜 Scrolling to load more results...")
                    scroll_attempts = max(3, max_stores // 10)  # More scrolls for more stores
                    
                    for scroll in range(scroll_attempts):
                        page.evaluate('''
                            const feed = document.querySelector('[role="feed"]');
                            if (feed) {
                                feed.scrollTo(0, feed.scrollHeight);
                            }
                        ''')
                        time.sleep(2)
                        st.info(f"Scroll {scroll+1}/{scroll_attempts}")
                    
                    time.sleep(3)  # Final wait after all scrolls
                
                # Try to find stores with multiple selectors
                st.info("🔍 Looking for stores...")
                
                stores_found = False
                selectors_to_try = [
                    'a[href*="/maps/place/"]',  # Store links
                    '[role="article"]',  # Store cards
                    '.Nv2PK',  # Sometimes used class
                    'div[jsaction*="mouseover"]',  # Interactive elements
                ]
                
                store_elements = []
                for selector in selectors_to_try:
                    try:
                        elements = page.query_selector_all(selector)
                        if len(elements) > 0:
                            st.success(f"✅ Found {len(elements)} elements with selector: {selector}")
                            store_elements = elements[:max_stores]
                            stores_found = True
                            break
                    except:
                        continue
                
                if not stores_found:
                    st.error("❌ Could not find store elements with any selector!")
                    st.warning("""
                    **Debug steps:**
                    1. Check the screenshot: debug_screenshot.png
                    2. Make sure stores are visible in the left panel
                    3. Google may have changed their layout
                    4. Try closing and reopening the browser
                    """)
                    browser.close()
                    st.stop()
                
                st.success(f"📊 Processing {len(store_elements)} stores...")
                
                progress_bar = st.progress(0)
                
                for i, element in enumerate(store_elements):
                    try:
                        progress_bar.progress((i + 1) / len(store_elements))
                        st.info(f"🔍 Store {i+1}/{len(store_elements)}")
                        
                        # Store old URL to detect change
                        old_url = page.url
                        
                        # Scroll element into view before clicking
                        try:
                            element.scroll_into_view_if_needed()
                            time.sleep(0.5)
                        except:
                            pass
                        
                        # Click the store
                        try:
                            element.click()
                        except Exception as click_error:
                            st.warning(f"⚠️ Could not click store {i+1}: {str(click_error)}")
                            continue
                        
                        # Wait for URL to change (indicates new store loaded)
                        url_changed = False
                        for wait_attempt in range(10):
                            time.sleep(0.5)
                            if page.url != old_url:
                                url_changed = True
                                break
                        
                        # Debug: Warn if URL didn't change
                        if not url_changed:
                            st.warning(f"⚠️ Store {i+1}: URL didn't change - might be duplicate or same store")
                        
                        # Wait for details panel to load with new content
                        # Look for the details panel specifically
                        details_panel_loaded = False
                        for wait_attempt in range(10):
                            try:
                                # Check if details panel exists and has content
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
                        
                        # Get current URL for coordinates and CID
                        current_url = page.url
                        
                        # Extract data from the DETAILS PANEL specifically, not entire body
                        # This ensures we get the correct store's data
                        details_panel = page.query_selector('[role="main"]')
                        if not details_panel:
                            # Try alternative selectors for details panel
                            details_panel = page.query_selector('[class*="panel"]') or page.query_selector('[class*="details"]')
                        
                        if not details_panel:
                            # Fallback to body if details panel not found
                            details_panel = page.query_selector('body')
                            st.warning(f"⚠️ Store {i+1}: Using body text instead of details panel")
                        
                        panel_text = details_panel.inner_text() if details_panel else ""
                        
                        # Debug: Show if we got meaningful content
                        if len(panel_text) < 50:
                            st.warning(f"⚠️ Store {i+1}: Very little content extracted ({len(panel_text)} chars)")
                        
                        # Extract store name from details panel
                        name = "Unknown Store"
                        try:
                            # Try multiple selectors for store name in details panel
                            name_selectors = [
                                '[role="main"] h1',
                                '[role="main"] [class*="fontHeadlineLarge"]',
                                '[role="main"] [class*="fontHeadline"]',
                                '[data-value="Directions"] + div h1',  # Name near directions button
                                'h1[data-attrid="title"]',
                                'h1',
                            ]
                            
                            for selector in name_selectors:
                                try:
                                    name_element = page.query_selector(selector)
                                    if name_element:
                                        name_text = name_element.inner_text().strip()
                                        # Validate it's a real name (not too short, not common text)
                                        if len(name_text) > 3 and name_text not in ['Directions', 'Save', 'Share']:
                                            name = name_text[:200]
                                            break
                                except:
                                    continue
                            
                            # If still not found, try extracting from panel text
                            if name == "Unknown Store" and panel_text:
                                # Look for text that looks like a business name (first substantial line)
                                lines = panel_text.split('\n')
                                for line in lines[:10]:  # Check first 10 lines
                                    line = line.strip()
                                    if len(line) > 5 and len(line) < 100:
                                        # Skip common UI elements
                                        if line not in ['Directions', 'Save', 'Share', 'Call', 'Website', 'Reviews']:
                                            name = line[:200]
                                            break
                        except Exception as e:
                            st.warning(f"⚠️ Name extraction error: {str(e)}")
                            pass
                        
                        # Extract rating and review count from DETAILS PANEL only
                        rating = None
                        reviews_count = None
                        total_ratings = None
                        try:
                            # First, try to find rating in the details panel specifically
                            # Look for rating elements near the store name
                            rating_selectors = [
                                '[role="main"] [aria-label*="stars"]',
                                '[role="main"] [aria-label*="rating"]',
                                '[role="main"] button[aria-label*="stars"]',
                                '[data-value="Directions"] + div [aria-label*="stars"]',
                            ]
                            
                            for selector in rating_selectors:
                                try:
                                    rating_elements = page.query_selector_all(selector)
                                    if rating_elements:
                                        # Get the first rating element (should be the store's rating)
                                        rating_element = rating_elements[0]
                                        aria_label = rating_element.get_attribute('aria-label')
                                        if aria_label:
                                            # Extract rating from aria-label like "4.5 stars"
                                            rating_match = re.search(r'(\d\.\d)', aria_label)
                                            if rating_match:
                                                rating = rating_match.group(1)
                                                # Try to extract review count from same element or nearby
                                                review_match = re.search(r'(\d+(?:,\d+)?)', aria_label)
                                                if review_match:
                                                    reviews_count = review_match.group(1).replace(',', '')
                                                    total_ratings = reviews_count
                                                break
                                except:
                                    continue
                            
                            # If not found via selectors, search in panel text (but only near the top)
                            if not rating and panel_text:
                                # Extract first 500 chars (where rating usually appears)
                                top_text = panel_text[:500]
                                
                                # Pattern 1: "4.5 (234)" or "4.5(234)" - most common format
                                rating_match = re.search(r'(\d\.\d)[\s\xa0]*\((\d+(?:,\d+)?)\)', top_text)
                                if rating_match:
                                    rating = rating_match.group(1)
                                    reviews_count = rating_match.group(2).replace(',', '')
                                    total_ratings = reviews_count
                                
                                # Pattern 2: "4.5 stars" or "4.5★"
                                if not rating:
                                    rating_match = re.search(r'(\d\.\d)[\s\xa0]*(?:stars?|★)', top_text, re.IGNORECASE)
                                    if rating_match:
                                        rating = rating_match.group(1)
                                
                                # Pattern 3: Look for review count separately near rating
                                if not reviews_count and rating:
                                    # Look in a wider context around the rating
                                    rating_pos = top_text.find(rating)
                                    if rating_pos != -1:
                                        context = top_text[max(0, rating_pos-20):min(len(top_text), rating_pos+100)]
                                        review_match = re.search(r'\((\d+(?:,\d+)?)\)', context)
                                        if review_match:
                                            reviews_count = review_match.group(1).replace(',', '')
                                            total_ratings = reviews_count
                            
                            # Validate rating (should be between 1.0 and 5.0)
                            if rating:
                                try:
                                    rating_val = float(rating)
                                    if rating_val < 1.0 or rating_val > 5.0:
                                        rating = None  # Invalid rating
                                except:
                                    rating = None
                        except Exception as e:
                            st.warning(f"⚠️ Rating extraction error: {str(e)}")
                            pass
                        
                        # Extract phone number - Target store details panel specifically
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
                                # Use the details panel we already have
                                if panel_text:
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
                                            phone_patterns = [
                                                r'\d{5}\s?\d{5}',  # Indian format: 12345 67890
                                                r'\d{3,4}[\s-]?\d{3,4}[\s-]?\d{4}',  # General: 1234-567-8900
                                                r'\+91[\s-]?\d{10}',  # +91 format
                                                r'0\d{2,4}[\s-]?\d{6,8}',  # Landline: 0522-1234567
                                                r'\+?\d[\d\s\-\(\)]{9,}',  # General international
                                            ]
                                            
                                            for pattern in phone_patterns:
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
                                phone_patterns = [
                                    r'\d{5}\s?\d{5}',  # Indian format: 12345 67890
                                    r'\d{3,4}[\s-]?\d{3,4}[\s-]?\d{4}',  # General: 1234-567-8900
                                    r'\+91[\s-]?\d{10}',  # +91 format
                                    r'0\d{2,4}[\s-]?\d{6,8}',  # Landline: 0522-1234567
                                ]
                                
                                # Get all matches and filter
                                all_phones = []
                                for pattern in phone_patterns:
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
                        
                        # Extract address from details panel
                        address = None
                        try:
                            # Look for address in details panel specifically
                            address_selectors = [
                                '[data-item-id*="address"]',
                                '[data-value="Directions"]',
                                'button[data-item-id*="address"]',
                                '[aria-label*="Address"]',
                            ]
                            
                            for selector in address_selectors:
                                try:
                                    address_element = page.query_selector(selector)
                                    if address_element:
                                        address_text = address_element.inner_text().strip()
                                        # Validate it's a real address
                                        if len(address_text) > 10 and len(address_text) < 300:
                                            address = address_text
                                            break
                                except:
                                    continue
                            
                            # Fallback: search in panel text
                            if not address and panel_text:
                                lines = panel_text.split('\n')
                                for line in lines:
                                    line = line.strip()
                                    # Look for address-like text (contains numbers, street names, city)
                                    if (len(line) > 15 and len(line) < 250 and 
                                        (any(char.isdigit() for char in line) or 
                                         any(keyword in line.lower() for keyword in ['street', 'road', 'avenue', 'lucknow', 'nagar']))):
                                        address = line
                                        break
                        except Exception as e:
                            st.warning(f"⚠️ Address extraction error: {str(e)}")
                            pass
                        
                        # Extract website from details panel
                        website = None
                        try:
                            website_selectors = [
                                '[data-item-id*="authority"]',
                                'a[data-item-id*="authority"]',
                                'button[data-item-id*="authority"]',
                            ]
                            
                            for selector in website_selectors:
                                try:
                                    website_element = page.query_selector(selector)
                                    if website_element:
                                        website_text = website_element.inner_text().strip()
                                        # Check if it's a URL
                                        if 'http' in website_text.lower() or 'www.' in website_text.lower():
                                            website = website_text
                                            break
                                        # Check href attribute
                                        href = website_element.get_attribute('href')
                                        if href and ('http' in href or 'www.' in href):
                                            website = href
                                            break
                                except:
                                    continue
                            
                            # Fallback: search in panel text
                            if not website and panel_text:
                                url_match = re.search(r'https?://[^\s]+|www\.[^\s]+', panel_text)
                                if url_match:
                                    website = url_match.group(0)
                        except Exception as e:
                            st.warning(f"⚠️ Website extraction error: {str(e)}")
                            pass
                        
                        # Extract opening hours from details panel
                        opening_hours = None
                        try:
                            # Look for hours in panel text
                            if panel_text:
                                # Look for hours pattern
                                hours_match = re.search(r'(Open|Closed).*?(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))', panel_text)
                                if hours_match:
                                    opening_hours = hours_match.group(0)[:100]
                                elif "Open" in panel_text or "Closed" in panel_text:
                                    lines = panel_text.split('\n')
                                    for line in lines:
                                        if ("Open" in line or "Closed" in line) and len(line) < 100:
                                            opening_hours = line.strip()
                                            break
                        except Exception as e:
                            st.warning(f"⚠️ Hours extraction error: {str(e)}")
                            pass
                        
                        # Extract Plus Code from details panel
                        plus_code = None
                        try:
                            if panel_text:
                                # Plus codes look like: "7JRV+C8 Lucknow"
                                plus_match = re.search(r'[A-Z0-9]{4}\+[A-Z0-9]{2,3}\s+\w+', panel_text)
                                if plus_match:
                                    plus_code = plus_match.group(0)
                        except Exception as e:
                            st.warning(f"⚠️ Plus code extraction error: {str(e)}")
                            pass
                        
                        # Extract Latitude & Longitude from URL
                        lat = None
                        lng = None
                        try:
                            # Format: @lat,lng,zoom or !3d lat!4d lng
                            coords_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', current_url)
                            if coords_match:
                                lat = coords_match.group(1)
                                lng = coords_match.group(2)
                            else:
                                # Alternative format
                                coords_match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', current_url)
                                if coords_match:
                                    lat = coords_match.group(1)
                                    lng = coords_match.group(2)
                        except:
                            pass
                        
                        # Extract CID (Google Maps Place ID)
                        cid = None
                        google_maps_url = current_url
                        try:
                            # CID format: /maps/place/.../@...
                            if '/place/' in current_url:
                                # Extract place ID from URL
                                place_match = re.search(r'/place/([^/@]+)', current_url)
                                if place_match:
                                    cid = place_match.group(1)
                            
                            # Try to get data-cid attribute
                            cid_element = page.query_selector('[data-cid]')
                            if cid_element and not cid:
                                cid = cid_element.get_attribute('data-cid')
                        except:
                            pass
                        
                        result = {
                            'number': i + 1,
                            'store_name': name,
                            'rating': rating if rating else 'N/A',
                            'total_ratings': total_ratings if total_ratings else 'N/A',
                            'reviews_count': reviews_count if reviews_count else 'N/A',
                            'address': address if address else 'Not found',
                            'phone_number': phone if phone else 'Not found',
                            'opening_hours': opening_hours if opening_hours else 'Not found',
                            'website': website if website else 'Not found',
                            'plus_code': plus_code if plus_code else 'Not found',
                            'latitude': lat if lat else 'Not found',
                            'longitude': lng if lng else 'Not found',
                            'google_maps_url': google_maps_url,
                            'cid': cid if cid else 'Not found',
                        }
                        
                        results.append(result)
                        
                        # Show in UI
                        with st.expander(f"⭐ {result['rating']} | {name} ({result['total_ratings']} ratings)", expanded=False):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**⭐ Rating:** {result['rating']}/5.0")
                                st.write(f"**📊 Total Ratings:** {result['total_ratings']}")
                                st.write(f"**💬 Reviews Count:** {result['reviews_count']}")
                                st.write(f"**📞 Phone:** {result['phone_number']}")
                                st.write(f"**🌐 Website:** {result['website']}")
                            with col2:
                                st.write(f"**📍 Address:** {result['address']}")
                                st.write(f"**🕐 Hours:** {result['opening_hours']}")
                                st.write(f"**📌 Plus Code:** {result['plus_code']}")
                                st.write(f"**🌍 Coordinates:** {result['latitude']}, {result['longitude']}")
                                st.write(f"**🔗 CID:** {result['cid']}")
                            st.write(f"**🗺️ Maps URL:** {result['google_maps_url'][:80]}...")
                        
                    except Exception as e:
                        st.warning(f"⚠️ Error with store {i+1}: {str(e)}")
                        continue
                
                browser.close()
                
                # Summary
                st.success(f"✅ Completed! Scraped {len(results)} stores")
                
                # Statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    ratings_found = sum(1 for r in results if r['rating'] != 'N/A')
                    st.metric("⭐ Ratings", f"{ratings_found}/{len(results)}")
                with col2:
                    phones_found = sum(1 for r in results if r['phone_number'] != 'Not found')
                    st.metric("📞 Phones", f"{phones_found}/{len(results)}")
                with col3:
                    coords_found = sum(1 for r in results if r['latitude'] != 'Not found')
                    st.metric("🌍 Coordinates", f"{coords_found}/{len(results)}")
                with col4:
                    websites_found = sum(1 for r in results if r['website'] != 'Not found')
                    st.metric("🌐 Websites", f"{websites_found}/{len(results)}")
                
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
                            file_name="google_maps_results.json",
                            mime="application/json",
                            help="Complete data in JSON format"
                        )
                    
                    st.info("💡 **Tip:** Upload the Excel file to Google Sheets for team collaboration!")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("""
            **Common issues:**
            
            1. **Timeout** - Google Maps is slow to load
               → Try again, it often works on 2nd attempt
            
            2. **Can't find stores** - Layout changed
               → Check debug_screenshot.png
               → Make sure stores are visible
            
            3. **No phone numbers** - Google hiding data
               → This is normal, only 30-50% success rate
               → Use Google Places API for reliable data
            """)

st.markdown("---")

st.subheader("📋 What Gets Extracted")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **✅ Always extracted:**
    - Store name
    - Google Maps URL
    - Number in list
    
    **⚠️ Often found (60-80%):**
    - Latitude & Longitude
    - Address
    - CID/Place ID
    """)

with col2:
    st.markdown("""
    **🎯 Sometimes found (30-50%):**
    - Phone number
    - Rating & reviews
    - Opening hours
    - Website
    - Plus code
    """)

st.markdown("---")

st.subheader("💡 Tips & Tricks")
st.markdown("""
**For best results:**

1. **Start small** - Test with 10-20 stores first
2. **Enable pagination** - Loads more results automatically
3. **Watch the browser** - See what's being clicked
4. **Check screenshot** - `debug_screenshot.png` shows the view
5. **Be patient** - Takes 5-7 seconds per store

**If it fails:**
- Google may block after too many requests
- Wait 10 minutes and try again
- Try a different search term
- Use fewer stores per run

**For production/reliable data:**
- Google Places API gives 95%+ success rate
- Much faster (no clicking required)
- 5,000 free API calls per month
- Worth $0.20 for 100 stores vs hours of debugging! 😊
""")

