DEBUG = False  # Set to False to disable debug output

def log_failed_record_id(record_id, reason=None, response=None):
    """
    Append a failed record ID (and optional reason) to a log file for later investigation.
    """
    import datetime
    filename = "failed_records.log"
    # Ensure the filename is valid and does not contain any path traversal characters
    try:
        with open(filename, "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().isoformat()
            if reason:
                f.write(f"{timestamp}\t{record_id}\t{reason}\n")
            else:
                f.write(f"{timestamp}\t{record_id}\n")
            if response:
                f.write(f"Response: {response}\n")
    except Exception as e:
        print(f"Failed to log record ID {record_id} to {filename}: {e}")

def log_http_error(request, response):
    
    """
    Log details of an HTTP error response for debugging.
    Prints status code, reason, url, text, and attempts to print JSON if available.
    """
    print("--- HTTP Request ---")
    # Print request details if available
    if request is not None:
        try:
            print(f"Method: {getattr(request, 'method', 'N/A')}")
            print(f"URL: {getattr(request, 'url', 'N/A')}")
            print(f"Headers: {getattr(request, 'headers', 'N/A')}")
            print(f"Body: {getattr(request, 'body', 'N/A')}")
            print(f"Object: {request}")
            # Try to print JSON if possible
            try:
                json_data = request.json()
                print("JSON:", json_data)
            except Exception:
                pass
        except Exception as e:
            print(f"Could not print request details: {e}")

    """
    Log details of an HTTP error response for debugging.
    Prints status code, reason, url, text, and attempts to print JSON if available.
    """
    print("--- HTTP Error Response ---")
    print(f"Status code: {getattr(response, 'status_code', 'N/A')}")
    print(f"Reason: {getattr(response, 'reason', 'N/A')}")
    print(f"URL: {getattr(response, 'url', 'N/A')}")


    # Try to print JSON if possible
    try:
        json_data = response.json()
        print("JSON:", json_data)
    except Exception:
        pass
    print("--------------------------")
def create_hubspot_contact(csv_json):
    """
    Create a new HubSpot contact using the provided CSV JSON record.
    This function creates an empty HubSpot JSON, determines which properties to set using get_hubspot_update_properties,
    and then creates the contact in HubSpot. Returns True if successful, False otherwise.
    """
    hubspot_json = {}
    update_properties = get_hubspot_update_properties(hubspot_json, csv_json)
    if not update_properties:
        print("No properties to set for new contact. Skipping.")
        return False
    import os
    api_key = os.getenv('HUBSPOT_API_KEY')
    if not api_key:
        print("HUBSPOT_API_KEY environment variable not set.")
        return False
    url = "https://api.hubapi.com/crm/v3/objects/contacts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {"properties": update_properties}
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        contact_id = data.get('id')
        print(f"Successfully created new HubSpot contact with email: {update_properties.get('email', '[no email]')} and ID: {contact_id}")
        return contact_id if contact_id else False
    except Exception as e:
        print(f"HubSpot API error while creating contact: {e}")
        return False


import requests
# WARNING: Do not hardcode API keys in source code. Use environment variables for secrets.

def update_secondary_email(contact_id: str, secondary_email: str):

    import os
    api_key = os.getenv('HUBSPOT_API_KEY')
    print(f"Start Email insert record: {contact_id} email: {secondary_email}")

    secondary_url = f"https://api.hubapi.com/contacts/v1/secondary-email/{contact_id}/email/{secondary_email}"
    primary_url = f"https://api.hubapi.com/contacts/v1/contact/vid/{contact_id}/profile"

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    # Try to set secondary email
    response = requests.put(
        url=secondary_url,
        headers=headers,
        json={
            "properties": [
                {"property": "email", "value": secondary_email}
            ]
        }
    )

    print("Setting Secondary")

    # If secondary fails with 400, try to set as primary
    if response.status_code == 400:
        print("Secondary could not be set: 400 - Trying primary")

        response = requests.post(
            url=primary_url,
            headers=headers,
            json={
                "properties": [
                    {"property": "email", "value": secondary_email}
                ]
            }
        )
        print("Setting Primary")
        if response.status_code != 200:
            print(f"Error: Failed to set email as primary. Status: {response.status_code}, Response: {dir(response)}")
            import sys
            sys.exit(1)
    elif response.status_code != 200:
        print(f"Error: Failed to set email as secondary. Status: {response.status_code}, Response: {response}")
        import sys
        sys.exit(1)
    return {"status": "ok", "message": "Email update successful"}


def add_secondary_email_to_hubspot_contact(contact_id, secondary_email):
    """
    Add a secondary email to a HubSpot contact using the legacy v1 endpoint.
    Requires HUBSPOT_API_KEY environment variable to be set.
    contact_id: HubSpot contact ID (int or str)
    secondary_email: The email address to add as secondary (str)
    Returns True if successful, False otherwise.
    """
    import os
    api_key = os.getenv('HUBSPOT_API_KEY')
    if not api_key:
        print("HUBSPOT_API_KEY environment variable not set.")
        return False
    url = f"https://api.hubapi.com/contacts/v1/secondary-email/{contact_id}/email/{secondary_email}?hapikey={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"email": secondary_email}
    try:
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Successfully added secondary email '{secondary_email}' to contact {contact_id}.")
        return True
    except Exception as e:
        print(f"HubSpot API error while adding secondary email to contact {contact_id}: {e}")
        return False
def get_hubspot_language_map():
    """
    Returns a dictionary mapping language labels (and label variants) to HubSpot internal language values.
    Both label and code are included as keys for flexible lookup.
    """
    lang_pairs = [
        ("Afrikaans", "af"),
        ("Albanian", "sq"),
        ("Albanian - Albania", "sq-al"),
        ("Arabic", "ar"),
        ("Arabic - Algeria", "ar-dz"),
        ("Arabic - Bahrain", "ar-bh"),
        ("Arabic - Egypt", "ar-eg"),
        ("Arabic - Iraq", "ar-iq"),
        ("Arabic - Jordan", "ar-jo"),
        ("Arabic - Kuwait", "ar-kw"),
        ("Arabic - Lebanon", "ar-lb"),
        ("Arabic - Libya", "ar-ly"),
        ("Arabic - Morocco", "ar-ma"),
        ("Arabic - Oman", "ar-om"),
        ("Arabic - Qatar", "ar-qa"),
        ("Arabic - Saudi Arabia", "ar-sa"),
        ("Arabic - Sudan", "ar-sd"),
        ("Arabic - Syria", "ar-sy"),
        ("Arabic - Tunisia", "ar-tn"),
        ("Arabic - United Arab Emirates", "ar-ae"),
        ("Arabic - Yemen", "ar-ye"),
        ("Armenian", "hy"),
        ("Assamese", "as"),
        ("Azerbaijani", "az"),
        ("Basque", "eu"),
        ("Belarusian", "be"),
        ("Belarusian - Belarus", "be-by"),
        ("Bengali", "bn"),
        ("Bosnian", "ba"),
        ("Bulgarian", "bg"),
        ("Bulgarian - Bulgaria", "bg-bg"),
        ("Burmese", "my"),
        ("Burmese - Myanmar (Burma)", "my-mm"),
        ("Catalan", "ca"),
        ("Catalan - Catalan", "ca-es"),
        ("Cebuano - Philippines", "cb-pl"),
        ("Chinese", "zh"),
        ("Chinese - China", "zh-cn"),
        ("Chinese - Hong Kong SAR", "zh-hk"),
        ("Chinese - Macau SAR", "zh-mo"),
        ("Chinese - Singapore", "zh-sg"),
        ("Chinese - Taiwan", "zh-tw"),
        ("Chinese (Simplified)", "zh-chs"),
        ("Chinese (Traditional)", "zh-cht"),
        ("Croatian", "hr"),
        ("Croatian - Croatia", "hr-hr"),
        ("Czech", "cs"),
        ("Czech - Czech Republic", "cs-cz"),
        ("Danish", "da"),
        ("Danish - Denmark", "da-dk"),
        ("Dutch", "nl"),
        ("Dutch - Belgium", "nl-be"),
        ("Dutch - The Netherlands", "nl-nl"),
        ("English", "en"),
        ("English - Australia", "en-au"),
        ("English - Canada", "en-ca"),
        ("English - Hong Kong", "en-hk"),
        ("English - India", "en-in"),
        ("English - Ireland", "en-ie"),
        ("English - Malaysia", "en-my"),
        ("English - Malta", "en-mt"),
        ("English - New Zealand", "en-nz"),
        ("English - Philippines", "en-ph"),
        ("English - Singapore", "en-sg"),
        ("English - South Africa", "en-za"),
        ("English - United Kingdom", "en-gb"),
        ("English - United States", "en-us"),
        ("English - Zimbabwe", "en-zw"),
        ("Estonian", "et"),
        ("Estonian - Estonia", "et-ee"),
        ("Faroese", "fo"),
        ("Farsi", "fa"),
        ("Finnish", "fi"),
        ("Finnish - Finland", "fi-fi"),
        ("French", "fr"),
        ("French - Belgium", "fr-be"),
        ("French - Canada", "fr-ca"),
        ("French - France", "fr-fr"),
        ("French - Luxembourg", "fr-lu"),
        ("French - Monaco", "fr-mc"),
        ("French - Switzerland", "fr-ch"),
        ("Galician", "gl"),
        ("Georgian", "ka"),
        ("German", "de"),
        ("German - Austria", "de-at"),
        ("German - Germany", "de-de"),
        ("German - Greece", "de-gr"),
        ("German - Liechtenstein", "de-li"),
        ("German - Luxembourg", "de-lu"),
        ("German - Switzerland", "de-ch"),
        ("Greek", "el"),
        ("Greek - Cyprus", "el-cy"),
        ("Greek - Greece", "el-gr"),
        ("Gujarati", "gu"),
        ("Haitian Creole", "ht"),
        ("Hausa", "ha"),
        ("Hebrew", "he"),
        ("Hebrew - Israel", "he-il"),
        ("Hebrew - Israel (Legacy)", "iw-il"),
        ("Hindi", "hi"),
        ("Hindi - India", "hi-in"),
        ("Hungarian", "hu"),
        ("Hungarian - Hungary", "hu-hu"),
        ("Icelandic", "is"),
        ("Icelandic - Iceland", "is-is"),
        ("Indonesian", "id"),
        ("Indonesian - Indonesia", "in-id"),
        ("Irish", "ga"),
        ("Irish - Ireland", "ga-ie"),
        ("Italian", "it"),
        ("Italian - Italy", "it-it"),
        ("Italian - Switzerland", "it-ch"),
        ("Japanese", "ja"),
        ("Japanese - Japan", "ja-jp"),
        ("Kannada", "kn"),
        ("Kazakh", "kk"),
        ("Kinyarwanda", "rw"),
        ("Kiswahili", "ki"),
        ("Konkani", "kok"),
        ("Korean", "ko"),
        ("Korean - South Korea", "ko-kr"),
        ("Kurdish", "ku"),
        ("Kyrgyz", "ky"),
        ("Lao", "lo"),
        ("Latvian", "lv"),
        ("Latvian - Latvia", "lv-lv"),
        ("Lithuanian", "lt"),
        ("Lithuanian - Lithuania", "lt-lt"),
        ("Macedonian", "mk"),
        ("Macedonian - Macedonia", "mk-mk"),
        ("Malagasy", "mg"),
        ("Malay", "ms"),
        ("Malayalam", "m1"),
        ("Malay - Brunei", "ms-bn"),
        ("Malay - Malaysia", "ms-my"),
        ("Maltese", "mt"),
        ("Maltese - Malta", "mt-mt"),
        ("Marathi", "mr"),
        ("Mongolian", "mn"),
        ("Norwegian", "no"),
        ("Norwegian Bokmal", "nb"),
        ("Norwegian - Norway", "no-no"),
        ("Nyanja", "ny"),
        ("ʻŌlelo Hawaiʻi", "haw"),
        ("Polish", "pl"),
        ("Polish - Poland", "pl-pl"),
        ("Portuguese", "pt"),
        ("Portuguese - Brazil", "pt-br"),
        ("Portuguese - Portugal", "pt-pt"),
        ("Punjabi", "pa"),
        ("Romanian", "ro"),
        ("Romanian - Romania", "ro-ro"),
        ("Russian", "ru"),
        ("Russian - Russia", "ru-ru"),
        ("Sanskrit", "sa"),
        ("Serbian", "sr"),
        ("Serbian - Bosnia and Herzegovina", "sr-ba"),
        ("Serbian - Montenegro", "sr-me"),
        ("Serbian - Serbia", "sr-rs"),
        ("Serbian - Serbia and Montenegro (Former)", "sr-cs"),
        ("Slovak", "sk"),
        ("Slovak - Slovakia", "sk-sk"),
        ("Slovenian", "sl"),
        ("Slovenian - Slovenia", "sl-si"),
        ("Spanish", "es"),
        ("Spanish - Argentina", "es-ar"),
        ("Spanish - Bolivia", "es-bo"),
        ("Spanish - Chile", "es-cl"),
        ("Spanish - Colombia", "es-co"),
        ("Spanish - Costa Rica", "es-cr"),
        ("Spanish - Cuba", "es-cu"),
        ("Spanish - Dominican Republic", "es-do"),
        ("Spanish - Ecuador", "es-ec"),
        ("Spanish - El Salvador", "es-sv"),
        ("Spanish - Guatemala", "es-gt"),
        ("Spanish - Honduras", "es-hn"),
        ("Spanish - Mexico", "es-mx"),
        ("Spanish - Nicaragua", "es-ni"),
        ("Spanish - Panama", "es-pa"),
        ("Spanish - Paraguay", "es-py"),
        ("Spanish - Peru", "es-pe"),
        ("Spanish - Puerto Rico", "es-pr"),
        ("Spanish - Spain", "es-es"),
        ("Spanish - United States", "es-us"),
        ("Spanish - Uruguay", "es-uy"),
        ("Spanish - Venezuela", "es-ve"),
        ("Swahili", "sw"),
        ("Swedish", "sv"),
        ("Swedish - Finland", "sv-fi"),
        ("Swedish - Sweden", "sv-se"),
        ("Syriac", "sy"),
        ("Tagalog", "t1"),
        ("Tamil", "ta"),
        ("Tatar", "tt"),
        ("Telugu", "te"),
        ("Thai", "th"),
        ("Thai - Thailand", "th-th"),
        ("Turkish", "tr"),
        ("Turkish - Türkiye", "tr-tr"),
        ("Ukrainian", "uk"),
        ("Ukrainian - Ukraine", "uk-ua"),
        ("Urdu", "ur"),
        ("Uzbek", "uz"),
        ("Vietnamese", "vi"),
        ("Vietnamese - Vietnam", "vi-vn"),
        ("Yoruba", "yo"),
    ]
    lang_map = {}
    for label, code in lang_pairs:
        lang_map[label.lower()] = code
        lang_map[code.lower()] = code
    return lang_map
def get_hubspot_update_properties(hubspot_json, csv_json):
    """
    Given a HubSpot contact JSON (properties) and a CSV record JSON,
    return a dict of properties to update in HubSpot (only those that should be changed).
    Handles both direct matches and custom logic for specific fields.
    """
    update_props = {}

    # Custom logic: map csv.phone_1 to the correct HubSpot property based on csv.phone_type_1
    phone_type = (csv_json.get('phone_type_1') or '').strip().upper()
    phone_val = (csv_json.get('phone_1') or '').strip()
    if phone_val:
        if phone_type == 'WORK':
            if hubspot_json.get('phone') != phone_val:
                update_props['phone'] = phone_val
        elif phone_type == 'HOME':
            if hubspot_json.get('home_phone') != phone_val:
                update_props['home_phone'] = phone_val
        elif phone_type == 'MOBILE':
            if hubspot_json.get('mobilephone') != phone_val:
                update_props['mobilephone'] = phone_val

    # Custom logic: education_description_1 is education_degree_1 + education_fos_1
    edu_degree = csv_json.get('education_degree_1', '').strip()
    edu_fos = csv_json.get('education_fos_1', '').strip()
    if edu_degree or edu_fos:
        edu_desc = ' '.join([v for v in [edu_degree, edu_fos] if v])
        if edu_desc and hubspot_json.get('education_description_1') != edu_desc:
            update_props['education_description_1'] = edu_desc

    # Custom logic: split csv.location_name into hubspot city, state, country
    if 'location_name' in csv_json and csv_json['location_name']:
        loc = csv_json['location_name']
        loc_parts = [p.strip() for p in loc.split(',') if p.strip()]
        # Reset values to update if different
        if len(loc_parts) == 3:
            city, state, country = loc_parts
            if city and hubspot_json.get('city') != city:
                update_props['city'] = city
            if state and hubspot_json.get('state') != state:
                update_props['state'] = state
            if country and hubspot_json.get('country') != country:
                update_props['country'] = country
        elif len(loc_parts) == 2:
            city, state = loc_parts
            if city and hubspot_json.get('city') != city:
                update_props['city'] = city
            # If state ends with 'Area', strip it away
            state_clean = state[:-4].strip() if state.lower().endswith('area') else state
            if state_clean and hubspot_json.get('state') != state_clean:
                update_props['state'] = state_clean
                update_props['country'] = 'United States'  # Default to US if state is provided
        elif len(loc_parts) == 1:
            city = loc_parts[0]
            if city and hubspot_json.get('city') != city:
                update_props['city'] = city

    # Define fields that can be mapped directly if present in both
    direct_fields = [
        'industry', 'birthday', 'education_start_1' 
    ]

    # Map CSV keys to HubSpot property names if they differ
    csv_to_hubspot_map = {
        'first_name': 'firstname',
        'last_name': 'lastname',
        'mobile': 'mobilephone',
        'organization_url_1': 'website',
        'member_id': 'linkedin_member_id',
        'hash_id': 'linkedin_hash_id',
        'sn_hash_id': 'linkedin_sn_hash_id',
        'lh_id': 'linkedhelper_crm_id',
        'profile_url': 'linkedin_url',  
        'profile_url': 'linkedin',
        'headline': 'linkedin_headline',
        'location_name': 'linkedin_location_name',
        'summary': 'lh_summary',
        'badges_premium': 'linkedin_premium_badge',
        'badges_influencer': 'linkedin_influencer_badge',
        'badges_job_seeker': 'lh_badgesjobseeker',
        'badges_open_link': 'linkedin_open_badge',
        'badges_hiring': 'lh_badgeshiring',
        'current_company': 'company', 
        'current_company_position': 'jobtitle',
        'current_company_position': 'linkedin_title',
        'organization_1': 'company',
        'organization_id_1': 'organization_li_id_1',
        'organization_url_1': 'organization_li_url_1',
        'organization_title_1': 'organization_title_1',
        'organization_start_1': 'organization_start_1',
        'organization_end_1': 'organization_end_1',
        'organization_description_1': 'organization_description_1',
        'organization_location_1': 'organization_location_1',
        'organization_website_1': 'organization_website_1',
        'organization_domain_1': 'organization_domain_1',
        'education_1': 'linkedin_education',
        'education_end_1': 'linkedin_education_end',
        'language_1': 'hs_language',
        'skills': 'linkedin_skills',
        'twitters': 'lh_twitter',
        'website_1': 'website',
        'website_2': 'personal_website_1',
        'tags': 'lh_tags',
        'connected_at': 'linkedin_connected_at',
        'mutual_count': 'linkedin_mutual_count',
        'followers': 'linkedin_followers',
        'connections_count': 'linkedinconnections',
        'member_distance': 'lh_member_distance'
        # Add more mappings as needed
    }

    # 1. Direct field matches (same name in both)
    for field in direct_fields:
        csv_val = csv_json.get(field)
        hub_val = hubspot_json.get(field)
        if csv_val is not None and str(csv_val).strip() != '' and csv_val != hub_val:
            update_props[field] = str(csv_val).strip()

    # 2. Mapped fields (different names)
    badge_keys = {
        'linkedin_premium_badge', 'linkedin_influencer_badge', 'lh_badgesjobseeker',
        'linkedin_open_badge', 'lh_badgeshiring'
    }
    lang_map = get_hubspot_language_map()
    for csv_key, hub_key in csv_to_hubspot_map.items():
        csv_val = csv_json.get(csv_key)
        if csv_val is not None and str(csv_val).strip() != '':
            val_to_set = csv_val
            # Special logic for organization_website_1: normalize malformed URLs
            if csv_key == 'organization_website_1':
                val_str = str(csv_val).strip().lstrip()
                # If value contains a colon, take the part after the last colon and prepend https://
                if val_str:
                    if ':' in val_str:
                        # Split on colon and take the last part (after the last colon)
                        last_part = val_str.split(':')[-1].lstrip('/').lstrip()
                        if last_part:
                            val_to_set = 'https://' + last_part
                        else:
                            val_to_set = 'https://'
                    elif not val_str.lower().startswith('http'):
                        val_to_set = 'https://' + val_str
            if hub_key == 'hs_language':
                # Map language_1 to hs_language using the language map
                lang_code = lang_map.get(str(csv_val).strip().lower())
                if lang_code and hubspot_json.get('hs_language') != lang_code:
                    update_props['hs_language'] = lang_code
                continue
            if hub_key in badge_keys:
                # Convert to lowercase 'true' or 'false' string
                val_str = str(csv_val).strip().lower()
                if val_str in {'true', 'false'}:
                    val_to_set = val_str
                else:
                    # Accept also 1/0, yes/no, y/n
                    if val_str in {'1', 'yes', 'y'}:
                        val_to_set = 'true'
                    elif val_str in {'0', 'no', 'n'}:
                        val_to_set = 'false'
                    else:
                        val_to_set = 'false' if not val_str else val_str
            if hubspot_json.get(hub_key) != val_to_set:
                # For company, only update if not already set or if org_1 is preferred
                if hub_key == 'company' and hubspot_json.get('company'):
                    continue
                update_props[hub_key] = val_to_set

    # 3. Custom logic for special fields
    # If csv.id is not null and csv.id_type is 'public-id', set hubspot 'linkedin_user_id' to csv.id
    if csv_json.get('id') and csv_json.get('id_type') and str(csv_json.get('id_type')).strip().lower() == 'public-id':
        if hubspot_json.get('linkedin_user_id') != csv_json['id']:
            update_props['linkedin_user_id'] = csv_json['id']

    # Custom logic: hub.email is a comma-separated list of csv.email, third_party_email_1/2/3 (no trailing comma)
    email_fields = [csv_json.get('email'), csv_json.get('third_party_email_1'), csv_json.get('third_party_email_2'), csv_json.get('third_party_email_3')]
    email_list = [e.strip() for e in email_fields if e and str(e).strip()]
    if email_list:
        email_value = ','.join(email_list)
        if hubspot_json.get('email') != email_value:
            update_props['email'] = email_value

    # Always set linkedin_url to profile_url if present in CSV
    profile_url = csv_json.get('profile_url')
    linkedin_url = hubspot_json.get('linkedin_url', '')
    # Check for empty or sales/people linkedin_url
    if not linkedin_url or linkedin_url.startswith('https://www.linkedin.com/sales/people'):
        if profile_url and profile_url.startswith('https://www.linkedin.com/sales/people'):
            # Replace sales/people with /in and cut after first comma
            new_url = profile_url.replace('https://www.linkedin.com/sales/people', 'https://www.linkedin.com/in')
            if ',' in new_url:
                new_url = new_url.split(',', 1)[0]
            update_props['linkedin_url'] = new_url
        elif profile_url:
            update_props['linkedin_url'] = profile_url
    elif profile_url is not None and str(profile_url).strip() != '':
        update_props['linkedin_url'] = profile_url



    # Add more custom logic as needed
    return update_props

def update_hubspot_contact_by_id(contact_id, properties):
    """
    Update a HubSpot contact record by ID with the given properties (JSON object).
    Requires HUBSPOT_API_KEY environment variable to be set.
    Returns the updated properties as a JSON object, or None on error.
    """
    import os
    api_key = os.getenv('HUBSPOT_API_KEY')
    if not api_key:
        print("HUBSPOT_API_KEY environment variable not set.")
        return None
    # Special handling for email: if multiple emails, set first as primary, add others as secondary
    email_val = properties.get('email')
    secondary_emails = []
    if email_val and ',' in email_val:
        email_list = [e.strip() for e in email_val.split(',') if e.strip()]
        if email_list:
            properties['email'] = email_list[0]
            # Only add as secondary if not already present in HubSpot
            # Fetch current contact to get all emails
            import os
            api_key = os.getenv('HUBSPOT_API_KEY')
            url = f"https://api.hubapi.com/contacts/v1/contact/vid/{contact_id}/profile"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            try:
                resp = requests.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                existing_emails = set()
                if 'identity-profiles' in data:
                    for profile in data['identity-profiles']:
                        for ident in profile.get('identities', []):
                            if ident.get('type') == 'EMAIL' and ident.get('value'):
                                existing_emails.add(ident['value'].lower())
                # Only add secondary emails not already present
                secondary_emails = [e for e in email_list[1:] if e.lower() not in existing_emails]
            except Exception as e:
                print(f"[WARN] Could not fetch existing emails for contact {contact_id}: {e}")
                secondary_emails = email_list[1:]
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    # Debug: print properties and payload before sending
    payload = {"properties": properties}
    if DEBUG:
        print(f"[DEBUG] update_hubspot_contact_by_id: contact_id={contact_id}")
        print(f"[DEBUG] Properties to update: {properties}")
        print(f"[DEBUG] PATCH payload: {payload}")
    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        # Add secondary emails if needed
        for sec_email in secondary_emails:
            update_secondary_email(contact_id, sec_email)
        return data.get('properties', {})
    except Exception as e:
        print(f"HubSpot API error while updating contact {contact_id}: {e}")
        log_failed_record_id(contact_id, reason=str(e), response=response if 'response' in locals() else None)
        log_http_error(properties, response)
        return None

def get_hubspot_contact_by_id(contact_id):
    """
    Fetch a HubSpot contact record by ID and return its properties as a JSON object.
    Requires HUBSPOT_API_KEY environment variable to be set.
    """
    import os
    api_key = os.getenv('HUBSPOT_API_KEY')
    if not api_key:
        print("HUBSPOT_API_KEY environment variable not set.")
        return None
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get('properties', {})
    except Exception as e:
        print(f"HubSpot API error while fetching contact {contact_id}: {e}")
        return None

def merge_hubspot_contacts(id1, id2):
    """
    Merge two HubSpot contacts. The contact with the smaller ID is merged into the larger (primary).
    Returns the API response or error message.
    """
    import os
    api_key = os.getenv('HUBSPOT_API_KEY')
    if not api_key:
        print("HUBSPOT_API_KEY environment variable not set.")
        return None
    try:
        # Ensure both IDs are strings and compare as integers
        id1_str, id2_str = str(id1), str(id2)
        if int(id1_str) < int(id2_str):
            objectIdToMerge, primaryObjectId = id1_str, id2_str
        else:
            objectIdToMerge, primaryObjectId = id2_str, id1_str
        url = f"https://api.hubapi.com/crm/v3/objects/contacts/merge"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "objectIdToMerge": objectIdToMerge,
            "primaryObjectId": primaryObjectId
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Successfully merged contact {objectIdToMerge} into {primaryObjectId}.")
        return response.json()
    except Exception as e:
        print(f"HubSpot API error during merge: {e}")
        return None

def search_hubspot_by_name(first_name, last_name):
    """
    Search HubSpot contacts by first name and last name using API v3 and return a list of record IDs if found.
    Requires HUBSPOT_API_KEY environment variable to be set.
    """
    import os
    api_key = os.getenv('HUBSPOT_API_KEY')
    if not api_key:
        print("HUBSPOT_API_KEY environment variable not set.")
        return []
    url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "firstname",
                        "operator": "EQ",
                        "value": first_name
                    },
                    {
                        "propertyName": "lastname",
                        "operator": "EQ",
                        "value": last_name
                    }
                ]
            }
        ],
        "properties": ["firstname", "lastname"]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])
        ids = [r.get('id') for r in results if r.get('id')]
        return ids
    except Exception as e:
        print(f"HubSpot API error: {e}")
        return []
import sys
import csv
import json

import requests


def main():

    if len(sys.argv) < 2:
        print("Usage: python read_record.py <csv_file> <record_number> [num_records]")
        sys.exit(1)

    csv_file = sys.argv[1]
    try:
        record_number = int(sys.argv[2])
    except ValueError:
        print("Record number must be an integer.")
        sys.exit(1)

    num_records = None
    if len(sys.argv) >= 4:
        try:
            num_records = int(sys.argv[3])
            if num_records < 1:
                print("Number of records to process must be >= 1.")
                sys.exit(1)
        except ValueError:
            print("Number of records to process must be an integer.")
            sys.exit(1)

    try:
        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            records = list(reader)
            if record_number < 1 or record_number > len(records):
                print(f"Record number must be between 1 and {len(records)}.")
                sys.exit(1)
            start_idx = record_number - 1
            if num_records is not None:
                end_idx = min(start_idx + num_records, len(records))
            else:
                end_idx = len(records)
            for idx in range(start_idx, end_idx):
                record = records[idx]
                print(f"\nProcessing record number {idx + 1}...")

                # Extract all email addresses from the record
                email_addresses = extract_emails_from_record(record)
                all_hubspot_ids = set()
                if not email_addresses:
                    print("No email addresses found in the record.")
                else:
                    for email in email_addresses:
                        email_ids = search_hubspot_by_email(email)
                        if email_ids:
                            print(f"Found HubSpot record ID(s): {', '.join(email_ids)} for email: {email}")
                            all_hubspot_ids.update(email_ids)
                        else:
                            print(f"No matching HubSpot record found for email: {email}")

                # LinkedIn ID
                linkedin_id = record.get('id')
                if linkedin_id:
                    print(f"Searching by LinkedIn User Id: {linkedin_id}")
                    linkedin_ids = search_hubspot_by_linkedin_id(linkedin_id)
                    if linkedin_ids:
                        print(f"Found HubSpot record ID(s): {', '.join(linkedin_ids)} for LinkedIn User Id: {linkedin_id}")
                        all_hubspot_ids.update(linkedin_ids)
                    else:
                        print(f"No matching HubSpot record found for LinkedIn User Id: {linkedin_id}")
                    # Try with hash_id if available
                    hash_id = record.get('hash_id')
                    if hash_id:
                        print(f"Trying with hash_id: {hash_id}")
                        hash_ids = search_hubspot_by_linkedin_id(hash_id)
                        if hash_ids:
                            print(f"Found HubSpot record ID(s): {', '.join(hash_ids)} for hash_id: {hash_id}")
                            all_hubspot_ids.update(hash_ids)
                        else:
                            print(f"No matching HubSpot record found for hash_id: {hash_id}")
                    else:
                        print("No hash_id field found in the record.")
                    # Try with public_id_2 if still not found
                    public_id_2 = record.get('public_id_2')
                    if public_id_2:
                        print(f"Trying with public_id_2: {public_id_2}")
                        public_ids = search_hubspot_by_linkedin_id(public_id_2)
                        if public_ids:
                            print(f"Found HubSpot record ID(s): {', '.join(public_ids)} for public_id_2: {public_id_2}")
                            all_hubspot_ids.update(public_ids)
                        else:
                            print(f"No matching HubSpot record found for public_id_2: {public_id_2}")
                    else:
                        print("No public_id_2 field found in the record.")
                else:
                    print("No LinkedIn User Id ('id' field) found in the record.")

                # Only search by name if no matches found yet
                if not all_hubspot_ids:
                    first_name = record.get('first_name') or record.get('firstname')
                    last_name = record.get('last_name') or record.get('lastname')
                    if first_name and last_name:
                        print(f"Trying with first name and last name: {first_name} {last_name}")
                        name_ids = search_hubspot_by_name(first_name, last_name)
                        if name_ids:
                            print(f"Found {len(name_ids)} HubSpot record(s) for name {first_name} {last_name}: {', '.join(name_ids)}")
                            org_names = set()
                            for i in range(1, 11):
                                org = record.get(f'organization_{i}')
                                if org:
                                    org_names.add(org.strip().lower())
                            if org_names:
                                print(f"Corroborating with organization names: {', '.join(org_names)}")
                                corroborated_ids = []
                                for contact_id in name_ids:
                                    company_names = get_company_names_for_contact(contact_id)
                                    if company_names & org_names:
                                        print(f"Contact {contact_id} is associated with company name(s): {', '.join(company_names & org_names)}")
                                        corroborated_ids.append(contact_id)
                                if corroborated_ids:
                                    print(f"After corroboration, keeping contact(s): {', '.join(corroborated_ids)}")
                                    all_hubspot_ids.update(corroborated_ids)
                                else:
                                    print("No contacts corroborated by company names. Keeping all name matches.")
                                    all_hubspot_ids.update(name_ids)
                            else:
                                print("No organization names found in the record. Keeping all name matches.")
                                all_hubspot_ids.update(name_ids)
                        else:
                            print(f"No matching HubSpot record found for name: {first_name} {last_name}")
                    else:
                        print("No first name and/or last name found in the record.")

                # Merge all found IDs if more than one
                all_hubspot_ids = sorted(all_hubspot_ids, key=lambda x: int(x))
                if len(all_hubspot_ids) > 1:
                    print(f"Merging {len(all_hubspot_ids)} duplicate HubSpot contacts: {', '.join(all_hubspot_ids)}")
                    # Always keep the highest ID as primary, but update to the new ID returned by merge
                    primary_id = all_hubspot_ids[-1]
                    for merge_id in reversed(all_hubspot_ids[:-1]):
                        print(f"Merging duplicate contacts: {merge_id} into {primary_id}")
                        merge_result = merge_hubspot_contacts(merge_id, primary_id)
                        if merge_result is not None:
                            # HubSpot may return a new ID for the merged contact
                            new_id = merge_result.get('id') or merge_result.get('primaryObjectId') or primary_id
                            print(f"New primary ID after merge: {new_id}")
                            primary_id = str(new_id)
                        else:
                            print(f"Failed to merge contacts {merge_id} and {primary_id}. Stopping merge attempts.")
                            break
                    print(f"Final remaining HubSpot record ID after merge: {primary_id}")
                    all_hubspot_ids = [primary_id]
                elif len(all_hubspot_ids) == 1:
                    print(f"Single HubSpot record ID found: {all_hubspot_ids[0]}")
                else:
                    print("No HubSpot record found for this contact. Creating a new contact.")
                    create_contact_id = create_hubspot_contact(record)
                    if create_contact_id:
                        print(f"Created new HubSpot contact with ID: {create_contact_id}")
                        all_hubspot_ids = [str(create_contact_id)]
                    else:
                        print("Failed to create a new HubSpot contact.")
                        return

                # At this point, we have a unique HubSpot contact ID
                unique_id = all_hubspot_ids[0]
                hubspot_contact_json = get_hubspot_contact_by_id(unique_id)
                if not hubspot_contact_json:
                    print(f"Could not fetch HubSpot contact with ID {unique_id}.")
                    return
                update_properties = get_hubspot_update_properties(hubspot_contact_json, record)
                # Ensure email addresses found above are added to update_properties['email']
                if email_addresses:
                    # Combine all unique emails from extracted and any already in update_properties
                    existing_emails = []
                    if 'email' in update_properties and update_properties['email']:
                        existing_emails = [e.strip() for e in update_properties['email'].split(',') if e.strip()]
                    all_emails = set(existing_emails) | set(email_addresses)
                    # Only keep emails ending with a letter (not '.', ' ', or other special char)
                    import re
                    valid_emails = [e for e in all_emails if re.match(r'.*[a-zA-Z]$', e)]
                    update_properties['email'] = ','.join(sorted(valid_emails))
                if not update_properties:
                    print("No properties to update for this contact.")
                else:
                    if DEBUG :
                        print(f"Updating HubSpot contact {unique_id} with the following properties:")
                        print("+------------------------------------------+------------------------------------------------+")
                        print("| Property                                 | Value                                          |")
                        print("+------------------------------------------+------------------------------------------------+")
                        for k, v in update_properties.items():
                            k_str = str(k)[:40].ljust(40)
                            v_str = str(v)[:44].ljust(44)
                            print(f"| {k_str} | {v_str}|")
                        print("+--------------------------------------------+------------------------------------------------+")
                    updated = update_hubspot_contact_by_id(unique_id, update_properties)
                    if updated is not None:
                        print(f"Successfully updated HubSpot contact {unique_id}.")
                    else:
                        print(f"Failed to update HubSpot contact {unique_id}.")
                        return
    except FileNotFoundError:
        print("File not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)



def get_company_names_for_contact(contact_id):
    """
    Given a HubSpot contact ID, retrieve associated company names (set, lowercased).
    """
    import os
    api_key = os.getenv('HUBSPOT_API_KEY')
    if not api_key:
        print("HUBSPOT_API_KEY environment variable not set.")
        return set()
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}/associations/companies"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        company_ids = [a['id'] for a in data.get('results', []) if 'id' in a]
        company_names = set()
        for company_id in company_ids:
            try:
                company_url = f"https://api.hubapi.com/crm/v3/objects/companies/{company_id}?properties=name"
                resp = requests.get(company_url, headers=headers)
                resp.raise_for_status()
                company_data = resp.json()
                name = company_data.get('properties', {}).get('name')
                if name:
                    company_names.add(name.strip().lower())
            except Exception as e:
                print(f"HubSpot API error while fetching company name for company {company_id}: {e}")
        return company_names
    except Exception as e:
        print(f"HubSpot API error while fetching company names for contact {contact_id}: {e}")
        return set()


def search_hubspot_by_email(email):
    """
    Search HubSpot contacts by email using API v3 and return the record ID if found.
    Requires HUBSPOT_API_KEY environment variable to be set.
    """
    import os
    api_key = os.getenv('HUBSPOT_API_KEY')
    if not api_key:
        print("HUBSPOT_API_KEY environment variable not set.")
        return None
    email = email.strip().lower().rstrip('.')
    # Use legacy endpoint to search by primary and secondary email
    url = f"https://api.hubapi.com/contacts/v1/contact/email/{email}/profile"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    try:
        response = requests.get(url, headers=headers)
        if DEBUG:
            print(f"[DEBUG] search_hubspot_by_email: email={email}")
            print(f"[DEBUG] Response status code: {response.status_code}")
            print(f"[DEBUG] Response content: {response.content.decode('utf-8')}")  
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
        vid = data.get('vid')
        if vid:
            return [str(vid)]
        return []
    except Exception as e:
        print(f"HubSpot API error: {e}")
        return []


def search_hubspot_by_linkedin_id(linkedin_id):
    """
    Search HubSpot contacts by LinkedIn User Id (custom property 'linkedinuserid') using API v3 and return the record ID if found.
    Requires HUBSPOT_API_KEY environment variable to be set.
    """
    import os
    api_key = os.getenv('HUBSPOT_API_KEY')
    if not api_key:
        print("HUBSPOT_API_KEY environment variable not set.")
        return None
    url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    # Try all combinations: https/http, with and without trailing slash
    url_templates = [
        "https://www.linkedin.com/in/{}",
        "https://www.linkedin.com/in/{}/",
        "http://www.linkedin.com/in/{}",
        "http://www.linkedin.com/in/{}/"
    ]
    try:
        all_ids = []
        for template in url_templates:
            linkedin_url = template.format(linkedin_id)
            payload = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "linkedin_url",
                                "operator": "EQ",
                                "value": linkedin_url
                            }
                        ]
                    }
                ],
                "properties": ["linkedin_url"]
            }
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])
            ids = [r.get('id') for r in results if r.get('id')]
            all_ids.extend(ids)
        # Remove duplicates
        all_ids = list(set(all_ids))
        if len(all_ids) > 1:
            print(f"WARNING: Multiple HubSpot records found for LinkedIn ID '{linkedin_id}': {', '.join(all_ids)}")
        if all_ids:
            return all_ids
        return []
    except Exception as e:
        print(f"HubSpot API error: {e}")
        return []


def extract_emails_from_record(record):
    """
    Extract all email addresses from the record values (case-insensitive, supports multiple fields).
    Returns a list of unique email addresses.
    """
    import re
    emails = set()
    email_regex = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    for key, value in record.items():
        if key == "last_received_message_text":
            continue
        if not value:
            continue
        # If value is a string, search for email(s)
        if isinstance(value, str):
            found = email_regex.findall(value)
            emails.update(found)
    # Only keep emails ending with a letter (not '.', ' ', or other special char)
    valid_emails = [e for e in emails if re.match(r'.*[a-zA-Z]$', e)]
    return valid_emails


if __name__ == "__main__":
    main()
