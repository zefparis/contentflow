#!/usr/bin/env python3
"""
BYOP E2E Smoke Tests
Tests for Bring Your Own Post functionality according to the provided test plan
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:5000"
PARTNER_ID = "test-partner-123"

def log_test(test_name: str, status: str, details: str = ""):
    """Log test results"""
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏳"
    print(f"{status_emoji} {test_name}: {status}")
    if details:
        print(f"   {details}")

def test_byop_config():
    """Test BYOP configuration endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/byop/config")
        if response.status_code == 200:
            data = response.json()
            if data.get("enabled") and data.get("share_email_enabled"):
                log_test("BYOP Config", "PASS", f"Enabled with {data.get('share_email_daily_limit')} email limit")
                return True
            else:
                log_test("BYOP Config", "FAIL", "BYOP not enabled")
                return False
        else:
            log_test("BYOP Config", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test("BYOP Config", "FAIL", str(e))
        return False

def test_byop_submit():
    """Test BYOP submission with URL"""
    try:
        payload = {
            "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Hack IA",
            "description": "Un super outil d'IA pour automatiser vos tâches",
            "hashtags": "#ia #tools",
            "cta": "Essaye →"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Partner-ID": PARTNER_ID
        }
        
        response = requests.post(f"{BASE_URL}/api/byop/submit", 
                               json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("submission_id") and data.get("asset_id"):
                submission_id = data["submission_id"]
                asset_id = data["asset_id"]
                
                # Check meta data contains owner_partner_id
                meta = data.get("meta", {})
                if meta.get("owner_partner_id") == PARTNER_ID:
                    log_test("BYOP Submit", "PASS", f"Created submission {submission_id[:8]}...")
                    return submission_id, asset_id
                else:
                    log_test("BYOP Submit", "FAIL", "Missing owner_partner_id in meta")
                    return None, None
            else:
                log_test("BYOP Submit", "FAIL", "Missing required fields in response")
                return None, None
        else:
            log_test("BYOP Submit", "FAIL", f"HTTP {response.status_code}")
            return None, None
    except Exception as e:
        log_test("BYOP Submit", "FAIL", str(e))
        return None, None

def test_submission_retrieval(submission_id: str):
    """Test submission retrieval and isolation"""
    try:
        headers = {"X-Partner-ID": PARTNER_ID}
        response = requests.get(f"{BASE_URL}/api/byop/submissions/{submission_id}", 
                              headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            submission = data.get("data")
            if submission and submission.get("status") == "ready":
                log_test("Submission Retrieval", "PASS", f"Status: {submission.get('status')}")
                
                # Test isolation - try with different partner ID
                wrong_headers = {"X-Partner-ID": "other-partner"}
                iso_response = requests.get(f"{BASE_URL}/api/byop/submissions/{submission_id}", 
                                          headers=wrong_headers)
                if iso_response.status_code == 404:
                    log_test("Submission Isolation", "PASS", "Properly isolated by partner")
                    return True
                else:
                    log_test("Submission Isolation", "FAIL", f"HTTP {iso_response.status_code}")
                    return False
            else:
                log_test("Submission Retrieval", "FAIL", "Invalid submission data")
                return False
        else:
            log_test("Submission Retrieval", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test("Submission Retrieval", "FAIL", str(e))
        return False

def test_share_kit(submission_id: str):
    """Test share kit generation"""
    try:
        headers = {"X-Partner-ID": PARTNER_ID}
        response = requests.get(f"{BASE_URL}/api/byop/kit?submissionId={submission_id}", 
                              headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            kit_data = data.get("data")
            if kit_data and kit_data.get("short_url") and kit_data.get("share_text"):
                short_url = kit_data["short_url"]
                share_text = kit_data["share_text"]
                intents = kit_data.get("share_intents", {})
                
                # Check URL encoding in intents
                whatsapp_url = intents.get("whatsapp", "")
                if "wa.me" in whatsapp_url and "%20" in whatsapp_url:
                    log_test("Share Kit", "PASS", f"Generated {short_url}")
                    log_test("URL Encoding", "PASS", "Proper encoding in WhatsApp intent")
                    return short_url, share_text
                else:
                    log_test("Share Kit", "FAIL", "Invalid URL encoding")
                    return None, None
            else:
                log_test("Share Kit", "FAIL", "Missing share kit data")
                return None, None
        else:
            log_test("Share Kit", "FAIL", f"HTTP {response.status_code}")
            return None, None
    except Exception as e:
        log_test("Share Kit", "FAIL", str(e))
        return None, None

def test_click_tracking(short_url: str):
    """Test click tracking on short URL"""
    try:
        # Extract short code from URL
        short_code = short_url.split("/l/")[-1]
        
        # Make multiple clicks with different user agents
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]
        
        click_count = 0
        for ua in user_agents:
            try:
                headers = {"User-Agent": ua}
                response = requests.get(short_url, headers=headers, allow_redirects=False)
                if response.status_code in [302, 301]:
                    click_count += 1
                    time.sleep(0.5)  # Avoid rate limiting
            except:
                pass
        
        # Check metrics
        headers = {"X-Partner-ID": PARTNER_ID}
        metrics_response = requests.get(f"{BASE_URL}/api/metrics?partnerId={PARTNER_ID}&kind=click&since=24h", 
                                      headers=headers)
        
        if metrics_response.status_code == 200:
            metrics = metrics_response.json().get("data", {})
            tracked_clicks = metrics.get("clicks", 0)
            revenue = metrics.get("revenue_eur", 0)
            
            if tracked_clicks >= click_count:
                log_test("Click Tracking", "PASS", f"{tracked_clicks} clicks, €{revenue:.2f} revenue")
                return True
            else:
                log_test("Click Tracking", "FAIL", f"Expected {click_count}, got {tracked_clicks}")
                return False
        else:
            log_test("Click Tracking", "FAIL", "Metrics endpoint failed")
            return False
    except Exception as e:
        log_test("Click Tracking", "FAIL", str(e))
        return False

def test_email_rate_limiting():
    """Test email sharing and rate limiting"""
    try:
        headers = {
            "Content-Type": "application/json",
            "X-Partner-ID": PARTNER_ID
        }
        
        # Test normal email sending
        payload = {
            "submissionId": "test-submission",
            "emails": "test1@example.com,test2@example.com"
        }
        
        response = requests.post(f"{BASE_URL}/api/byop/email", 
                               json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("sent_count") == 2:
                remaining = data.get("remaining_daily_quota", 0)
                log_test("Email Share", "PASS", f"Sent 2 emails, {remaining} remaining")
                
                # Test rate limiting (simulate approaching limit)
                large_email_list = ",".join([f"test{i}@example.com" for i in range(200)])
                limit_payload = {
                    "submissionId": "test-submission",
                    "emails": large_email_list
                }
                
                limit_response = requests.post(f"{BASE_URL}/api/byop/email", 
                                             json=limit_payload, headers=headers)
                
                if limit_response.status_code == 429:
                    log_test("Email Rate Limiting", "PASS", "Properly blocked at limit")
                    return True
                else:
                    log_test("Email Rate Limiting", "FAIL", f"Expected 429, got {limit_response.status_code}")
                    return False
            else:
                log_test("Email Share", "FAIL", "Invalid response")
                return False
        else:
            log_test("Email Share", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test("Email Share", "FAIL", str(e))
        return False

def test_submissions_list():
    """Test submissions listing"""
    try:
        headers = {"X-Partner-ID": PARTNER_ID}
        response = requests.get(f"{BASE_URL}/api/byop/submissions", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            submissions = data.get("data", [])
            if isinstance(submissions, list):
                log_test("Submissions List", "PASS", f"Found {len(submissions)} submissions")
                return True
            else:
                log_test("Submissions List", "FAIL", "Invalid response format")
                return False
        else:
            log_test("Submissions List", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test("Submissions List", "FAIL", str(e))
        return False

def main():
    """Run all BYOP E2E tests"""
    print("🚀 Starting BYOP E2E Smoke Tests")
    print("=" * 50)
    
    # Test 1: Configuration
    if not test_byop_config():
        print("❌ Configuration test failed, aborting")
        return
    
    # Test 2: Submit BYOP
    submission_id, asset_id = test_byop_submit()
    if not submission_id:
        print("❌ Submit test failed, aborting")
        return
    
    # Test 3: Pipeline pickup and retrieval
    test_submission_retrieval(submission_id)
    
    # Test 4: Share Kit generation
    short_url, share_text = test_share_kit(submission_id)
    if short_url:
        # Test 5: Click tracking
        test_click_tracking(short_url)
    
    # Test 6: Email rate limiting
    test_email_rate_limiting()
    
    # Test 7: Submissions listing
    test_submissions_list()
    
    print("=" * 50)
    print("🎉 BYOP E2E Tests Completed")

if __name__ == "__main__":
    main()