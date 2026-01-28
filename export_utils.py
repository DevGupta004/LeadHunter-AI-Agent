"""
Export utilities for telecalling team
Exports to Excel/Google Sheets format with deduplication
"""

import pandas as pd
import re
from io import BytesIO
from typing import List, Dict


def normalize_phone(phone: str) -> str:
    """Normalize phone number for deduplication"""
    if not phone or phone == 'Not found' or phone == 'N/A':
        return ''
    
    # Remove all non-digit characters except +
    normalized = re.sub(r'[^\d+]', '', str(phone))
    
    # Remove leading +91, 91, 0
    if normalized.startswith('+91'):
        normalized = normalized[3:]
    elif normalized.startswith('91') and len(normalized) > 10:
        normalized = normalized[2:]
    elif normalized.startswith('0') and len(normalized) > 10:
        normalized = normalized[1:]
    
    return normalized.strip()


def normalize_name(name: str) -> str:
    """Normalize business name for deduplication"""
    if not name or name == 'Unknown Store':
        return ''
    
    # Convert to lowercase and remove extra spaces
    normalized = ' '.join(str(name).lower().split())
    
    # Remove common suffixes/prefixes for better matching
    normalized = re.sub(r'\s+(pvt|ltd|limited|inc|llc|corp|corporation)\.?$', '', normalized)
    
    return normalized.strip()


def deduplicate_records(records: List[Dict]) -> List[Dict]:
    """
    Remove duplicate records based on phone number or business name
    Priority: Keep records with phone numbers, then by rating
    """
    if not records:
        return []
    
    seen_phones = {}
    seen_names = {}
    unique_records = []
    
    for record in records:
        # Extract fields
        name = record.get('store_name', '')
        phone = record.get('phone_number', '')
        rating = record.get('rating', 'N/A')
        
        # Normalize for comparison
        norm_phone = normalize_phone(phone)
        norm_name = normalize_name(name)
        
        is_duplicate = False
        
        # Check by phone number first (most reliable)
        if norm_phone and len(norm_phone) >= 10:
            if norm_phone in seen_phones:
                # Duplicate phone - keep the one with better rating
                existing_record = seen_phones[norm_phone]
                existing_rating = existing_record.get('rating', 'N/A')
                
                # Compare ratings (keep higher rating)
                try:
                    existing_rating_val = float(existing_rating) if existing_rating != 'N/A' else 0
                    current_rating_val = float(rating) if rating != 'N/A' else 0
                    
                    if current_rating_val > existing_rating_val:
                        # Replace with better rating
                        unique_records.remove(existing_record)
                        seen_phones[norm_phone] = record
                        unique_records.append(record)
                    # else: keep existing, skip current
                    is_duplicate = True
                except:
                    # If rating comparison fails, keep first one
                    is_duplicate = True
            else:
                # New phone number
                seen_phones[norm_phone] = record
        
        # Check by name if no phone or phone didn't match
        if not is_duplicate and norm_name:
            if norm_name in seen_names:
                # Duplicate name - check if it's really the same business
                existing_record = seen_names[norm_name]
                existing_phone = normalize_phone(existing_record.get('phone_number', ''))
                
                # If both have phones and they're different, it's not a duplicate
                if norm_phone and existing_phone and norm_phone != existing_phone:
                    # Different businesses with same name - keep both
                    unique_records.append(record)
                else:
                    # Likely duplicate - keep the one with phone number or better rating
                    if norm_phone and not existing_phone:
                        # Current has phone, existing doesn't - replace
                        unique_records.remove(existing_record)
                        seen_names[norm_name] = record
                        unique_records.append(record)
                    elif not norm_phone and existing_phone:
                        # Existing has phone, current doesn't - skip
                        is_duplicate = True
                    else:
                        # Both have or don't have phones - compare ratings
                        existing_rating = existing_record.get('rating', 'N/A')
                        try:
                            existing_rating_val = float(existing_rating) if existing_rating != 'N/A' else 0
                            current_rating_val = float(rating) if rating != 'N/A' else 0
                            
                            if current_rating_val > existing_rating_val:
                                unique_records.remove(existing_record)
                                seen_names[norm_name] = record
                                unique_records.append(record)
                            else:
                                is_duplicate = True
                        except:
                            is_duplicate = True
            else:
                # New name
                seen_names[norm_name] = record
        
        # Add to unique records if not duplicate
        if not is_duplicate:
            unique_records.append(record)
    
    return unique_records


def prepare_telecalling_data(records: List[Dict]) -> List[Dict]:
    """
    Prepare data for telecalling team
    Only includes: name, contact no, location, website, rating
    """
    telecalling_data = []
    
    for record in records:
        # Extract only required fields
        name = record.get('store_name', 'Unknown Store')
        phone = record.get('phone_number', '')
        address = record.get('address', '')
        website = record.get('website', '')
        rating = record.get('rating', 'N/A')
        
        # Clean up values
        if phone == 'Not found' or phone == 'N/A':
            phone = ''
        if address == 'Not found' or address == 'N/A':
            address = ''
        if website == 'Not found' or website == 'N/A':
            website = ''
        if rating == 'N/A':
            rating = ''
        
        telecalling_data.append({
            'Business Name': name,
            'Contact Number': phone,
            'Location': address,
            'Website': website,
            'Rating': rating
        })
    
    return telecalling_data


def export_to_excel(records: List[Dict], filename: str = 'telecalling_leads.xlsx') -> BytesIO:
    """
    Export records to Excel format for telecalling team
    Returns BytesIO object for download
    """
    # Deduplicate records
    unique_records = deduplicate_records(records)
    
    # Prepare telecalling data
    telecalling_data = prepare_telecalling_data(unique_records)
    
    # Create DataFrame
    df = pd.DataFrame(telecalling_data)
    
    # Sort by rating (highest first), then by name
    df['Rating_Numeric'] = df['Rating'].apply(
        lambda x: float(x) if x and x != '' and x != 'N/A' else 0
    )
    df = df.sort_values(['Rating_Numeric', 'Business Name'], ascending=[False, True])
    df = df.drop('Rating_Numeric', axis=1)
    
    # Reset index
    df.index = range(1, len(df) + 1)
    
    # Create Excel file in memory
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Telecalling Leads', index=True, index_label='S.No.')
        
        # Get workbook and worksheet for formatting
        workbook = writer.book
        worksheet = writer.sheets['Telecalling Leads']
        
        # Auto-adjust column widths
        for idx, col in enumerate(df.columns, 1):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            )
            # Set column width (add some padding)
            worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)
        
        # Format header row
        from openpyxl.styles import Font, PatternFill, Alignment
        
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF', size=11)
        
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Freeze header row
        worksheet.freeze_panes = 'A2'
        
        # Add summary info (optional - comment might not work in all Excel versions)
        try:
            from openpyxl.comments import Comment
            comment = Comment(f"Total Unique Leads: {len(df)}\nGenerated for Telecalling Team", "LeadHunter")
            worksheet['A1'].comment = comment
        except:
            pass  # Comments are optional
    
    output.seek(0)
    return output


def get_export_summary(original_count: int, unique_count: int) -> str:
    """Get summary of export"""
    duplicates_removed = original_count - unique_count
    return f"""
    **Export Summary:**
    - 📊 Original records: {original_count}
    - ✅ Unique records: {unique_count}
    - 🗑️ Duplicates removed: {duplicates_removed}
    - 📋 Fields included: Business Name, Contact Number, Location, Website, Rating
    """
