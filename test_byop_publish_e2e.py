#!/usr/bin/env python3
"""
BYOP Publishing E2E Tests
Tests for Bring Your Own Post publishing functionality
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:5000"
PARTNER_ID = "test-partner-publish"

def log_test(test_name: str, status: str, details: str = ""):
    """Log test results"""
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏳"
    print(f"{status_emoji} {test_name}: {status}")
    if details:
        print(f"   {details}")

def test_byop_publish_basic():
    """Test basic BYOP publishing functionality"""
    try:
        # First create a BYOP submission
        payload = {
            "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Test Publishing Content",
            "description": "Content for testing direct publishing",
            "hashtags": "#test #publish",
            "cta": "Test now →"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Partner-ID": PARTNER_ID
        }
        
        # Submit BYOP content
        response = requests.post(f"{BASE_URL}/api/byop/submit", 
                               json=payload, headers=headers)
        
        if response.status_code != 200:
            log_test("BYOP Submit for Publishing", "FAIL", f"HTTP {response.status_code}")
            return None
            
        submission_data = response.json()
        submission_id = submission_data["submission_id"]
        
        # Test publishing to platforms
        publish_payload = {
            "submissionId": submission_id,
            "platforms": ["youtube", "pinterest", "reddit", "instagram"]
        }
        
        publish_response = requests.post(f"{BASE_URL}/api/byop/publish",
                                       json=publish_payload, headers=headers)
        
        if publish_response.status_code == 200:
            data = publish_response.json()
            if data.get("ok"):
                created_count = len(data.get("created", []))
                skipped_count = len(data.get("skipped", []))
                log_test("BYOP Publish", "PASS", 
                        f"Created {created_count} assignments, skipped {skipped_count}")
                return submission_id, data
            else:
                log_test("BYOP Publish", "FAIL", f"Error: {data.get('error')}")
                return None, None
        else:
            log_test("BYOP Publish", "FAIL", f"HTTP {publish_response.status_code}")
            return None, None
            
    except Exception as e:
        log_test("BYOP Publish", "FAIL", str(e))
        return None, None

def test_byop_publish_without_platforms():
    """Test publishing without specifying platforms (should use all available)"""
    try:
        # Create submission first
        payload = {
            "title": "Test All Platforms",
            "description": "Test publishing to all platforms",
            "cta": "Check it out →"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Partner-ID": PARTNER_ID
        }
        
        response = requests.post(f"{BASE_URL}/api/byop/submit", 
                               json=payload, headers=headers)
        
        if response.status_code != 200:
            log_test("Submit for All Platforms", "FAIL", f"HTTP {response.status_code}")
            return False
            
        submission_id = response.json()["submission_id"]
        
        # Publish without specifying platforms
        publish_payload = {"submissionId": submission_id}
        
        publish_response = requests.post(f"{BASE_URL}/api/byop/publish",
                                       json=publish_payload, headers=headers)
        
        if publish_response.status_code == 200:
            data = publish_response.json()
            if data.get("ok"):
                platforms_used = [item["platform"] for item in data.get("created", [])]
                log_test("Publish All Platforms", "PASS", 
                        f"Platforms: {', '.join(platforms_used)}")
                return True
            else:
                log_test("Publish All Platforms", "FAIL", f"Error: {data.get('error')}")
                return False
        else:
            log_test("Publish All Platforms", "FAIL", f"HTTP {publish_response.status_code}")
            return False
            
    except Exception as e:
        log_test("Publish All Platforms", "FAIL", str(e))
        return False

def test_byop_publish_unauthorized():
    """Test publishing without partner authentication"""
    try:
        payload = {
            "submissionId": "test-sub-123",
            "platforms": ["youtube"]
        }
        
        # No partner ID header
        response = requests.post(f"{BASE_URL}/api/byop/publish", json=payload)
        
        if response.status_code == 401:
            data = response.json()
            if data.get("error") == "unauthorized":
                log_test("Publish Unauthorized", "PASS", "Correctly blocked unauthorized access")
                return True
            else:
                log_test("Publish Unauthorized", "FAIL", f"Wrong error: {data.get('error')}")
                return False
        else:
            log_test("Publish Unauthorized", "FAIL", f"Expected 401, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Publish Unauthorized", "FAIL", str(e))
        return False

def test_byop_publish_nonexistent_submission():
    """Test publishing nonexistent submission"""
    try:
        payload = {
            "submissionId": "nonexistent-submission-123",
            "platforms": ["youtube"]
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Partner-ID": PARTNER_ID
        }
        
        response = requests.post(f"{BASE_URL}/api/byop/publish",
                               json=payload, headers=headers)
        
        if response.status_code == 404:
            data = response.json()
            if data.get("error") == "submission_not_found":
                log_test("Publish Nonexistent", "PASS", "Correctly blocked nonexistent submission")
                return True
            else:
                log_test("Publish Nonexistent", "FAIL", f"Wrong error: {data.get('error')}")
                return False
        else:
            log_test("Publish Nonexistent", "FAIL", f"Expected 404, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Publish Nonexistent", "FAIL", str(e))
        return False

def test_byop_publish_status():
    """Test publication status endpoint"""
    try:
        headers = {"X-Partner-ID": PARTNER_ID}
        
        response = requests.get(f"{BASE_URL}/api/byop/publish/status/test-submission",
                              headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and "platforms" in data:
                log_test("Publish Status", "PASS", f"Status for {len(data['platforms'])} platforms")
                return True
            else:
                log_test("Publish Status", "FAIL", "Invalid response format")
                return False
        else:
            log_test("Publish Status", "FAIL", f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Publish Status", "FAIL", str(e))
        return False

def main():
    """Run all BYOP publishing tests"""
    print("🚀 Starting BYOP Publishing E2E Tests")
    print("=" * 50)
    
    # Test 1: Basic publishing functionality
    submission_id, publish_data = test_byop_publish_basic()
    
    # Test 2: Publishing to all platforms (default)
    test_byop_publish_without_platforms()
    
    # Test 3: Unauthorized access
    test_byop_publish_unauthorized()
    
    # Test 4: Nonexistent submission
    test_byop_publish_nonexistent_submission()
    
    # Test 5: Publication status
    test_byop_publish_status()
    
    print("=" * 50)
    print("🎉 BYOP Publishing Tests Completed")

if __name__ == "__main__":
    main()