"""
Simplified Google Maps Scraper - More Reliable
Tries multiple selectors and has better error handling
"""

import streamlit as st
from playwright.sync_api import sync_playwright
import time
import re
import json

st.title("🗺️ Google Maps Store Scraper")
st.caption("Simplified approach - clicks and extracts visible data")

url = st.text_input(
    "Google Maps URL",
    value="https://www.google.com/maps/search/cloth+stores+in+Lucknow/",
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
                        
                        # Click the store
                        element.click()
                        time.sleep(5)  # Wait for details panel
                        
                        # Get current URL for coordinates and CID
                        current_url = page.url
                        
                        # Try to extract data from the page
                        page_text = page.inner_text('body')
                        
                        # Extract store name
                        name = "Unknown Store"
                        try:
                            name_element = page.query_selector('h1, [class*="fontHeadlineLarge"]')
                            if name_element:
                                name = name_element.inner_text()[:200]
                        except:
                            pass
                        
                        # Extract rating and review count
                        rating = None
                        reviews_count = None
                        total_ratings = None
                        try:
                            # Pattern 1: "4.5 (234)" or "4.5(234)"
                            rating_match = re.search(r'(\d\.\d)[\s\xa0]*\((\d+(?:,\d+)?)\)', page_text)
                            if rating_match:
                                rating = rating_match.group(1)
                                reviews_count = rating_match.group(2).replace(',', '')
                                total_ratings = reviews_count  # Same as review count
                            
                            # Pattern 2: "4.5 stars" or "4.5★"
                            if not rating:
                                rating_match = re.search(r'(\d\.\d)[\s\xa0]*(?:stars?|★)', page_text, re.IGNORECASE)
                                if rating_match:
                                    rating = rating_match.group(1)
                            
                            # Pattern 3: Look for review count separately
                            if not reviews_count:
                                review_match = re.search(r'(\d+(?:,\d+)?)\s*(?:reviews?|ratings?)', page_text, re.IGNORECASE)
                                if review_match:
                                    reviews_count = review_match.group(1).replace(',', '')
                                    total_ratings = reviews_count
                            
                            # Pattern 4: Try to find rating in aria-label or specific elements
                            if not rating:
                                rating_element = page.query_selector('[aria-label*="stars"]')
                                if rating_element:
                                    label = rating_element.get_attribute('aria-label')
                                    rating_text = re.search(r'(\d\.\d)', label)
                                    if rating_text:
                                        rating = rating_text.group(1)
                        except Exception as e:
                            pass
                        
                        # Extract phone number
                        phone = None
                        phone_patterns = [
                            r'\d{5}\s?\d{5}',  # Indian format: 12345 67890
                            r'\d{3,4}[\s-]?\d{3,4}[\s-]?\d{4}',  # General: 1234-567-8900
                            r'\+91[\s-]?\d{10}',  # +91 format
                            r'0\d{2,4}[\s-]?\d{6,8}',  # Landline: 0522-1234567
                        ]
                        
                        for pattern in phone_patterns:
                            matches = re.findall(pattern, page_text)
                            if matches:
                                phone = matches[0].strip()
                                break
                        
                        # Extract address
                        address = None
                        try:
                            # Look for address button or text
                            address_button = page.query_selector('[data-item-id*="address"]')
                            if address_button:
                                address = address_button.inner_text()
                            elif "Lucknow" in page_text:
                                lines = page_text.split('\n')
                                for line in lines:
                                    if "Lucknow" in line and len(line) > 10 and len(line) < 250:
                                        address = line.strip()
                                        break
                        except:
                            pass
                        
                        # Extract website
                        website = None
                        try:
                            website_button = page.query_selector('[data-item-id*="authority"]')
                            if website_button:
                                website = website_button.inner_text()
                            else:
                                # Look for URL patterns in text
                                url_match = re.search(r'https?://[^\s]+|www\.[^\s]+', page_text)
                                if url_match:
                                    website = url_match.group(0)
                        except:
                            pass
                        
                        # Extract opening hours
                        opening_hours = None
                        try:
                            # Look for hours pattern
                            hours_match = re.search(r'(Open|Closed).*?(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))', page_text)
                            if hours_match:
                                opening_hours = hours_match.group(0)[:100]
                            elif "Open" in page_text or "Closed" in page_text:
                                lines = page_text.split('\n')
                                for line in lines:
                                    if ("Open" in line or "Closed" in line) and len(line) < 100:
                                        opening_hours = line.strip()
                                        break
                        except:
                            pass
                        
                        # Extract Plus Code
                        plus_code = None
                        try:
                            # Plus codes look like: "7JRV+C8 Lucknow"
                            plus_match = re.search(r'[A-Z0-9]{4}\+[A-Z0-9]{2,3}\s+\w+', page_text)
                            if plus_match:
                                plus_code = plus_match.group(0)
                        except:
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
                
                # Download button
                if results:
                    st.download_button(
                        "📥 Download JSON",
                        data=json.dumps(results, indent=2, ensure_ascii=False),
                        file_name="google_maps_results.json",
                        mime="application/json"
                    )
                
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

