"""
Buffer API Integration for ContentFlow
Provides automated multi-platform publishing via Buffer's API
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any
from app.utils.datetime import utcnow, iso_utc
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Post
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class BufferAPI:
    """Buffer API client for automated social media publishing"""
    
    def __init__(self):
        self.access_token = os.getenv('BUFFER_ACCESS_TOKEN')
        self.base_url = 'https://api.bufferapp.com/1'
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
    def get_profiles(self) -> List[Dict]:
        """Get all connected social media profiles"""
        try:
            response = requests.get(f'{self.base_url}/profiles.json', headers=self.headers)
            response.raise_for_status()
            
            profiles = response.json()
            logger.info(f"Retrieved {len(profiles)} Buffer profiles")
            return profiles
            
        except Exception as e:
            logger.error(f"Failed to get Buffer profiles: {e}")
            return []
    
    def find_profile_by_platform(self, platform: str) -> Optional[str]:
        """Find Buffer profile ID for a specific platform"""
        profiles = self.get_profiles()
        
        platform_mapping = {
            'instagram': 'instagram',
            'tiktok': 'tiktok', 
            'youtube': 'youtube',
            'facebook': 'facebook',
            'linkedin': 'linkedin',
            'pinterest': 'pinterest'
        }
        
        buffer_platform = platform_mapping.get(platform.lower())
        if not buffer_platform:
            return None
            
        for profile in profiles:
            if profile.get('service') == buffer_platform:
                return profile.get('id')
                
        return None
    
    def publish_post(self, post_id: int) -> Dict[str, Any]:
        """Publish a ContentFlow post via Buffer API"""
        db = SessionLocal()
        
        try:
            # Get post from database
            post = db.query(Post).filter(Post.id == post_id).first()
            if not post:
                return {'success': False, 'error': 'Post not found'}
            
            # Find Buffer profile for this platform
            profile_id = self.find_profile_by_platform(post.platform)
            if not profile_id:
                return {
                    'success': False, 
                    'error': f'No Buffer profile found for {post.platform}'
                }
            
            # Prepare post data
            post_data = {
                'text': f"{post.title}\n\n{post.content or ''}",
                'profile_ids[]': [profile_id]
            }
            
            # Add media if available
            if post.media_url:
                post_data['media'] = {
                    'link': post.media_url,
                    'description': post.title
                }
            
            # Schedule for immediate posting or specific time
            if post.scheduled_for:
                post_data['scheduled_at'] = post.scheduled_for.isoformat()
            else:
                post_data['now'] = True
            
            # Make API request to Buffer
            response = requests.post(
                f'{self.base_url}/updates/create.json',
                headers=self.headers,
                data=post_data
            )
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            if result.get('success'):
                # Update post status in database
                post.status = 'published'
                post.posted_at = utcnow()
                post.external_id = result.get('id')
                
                # Store Buffer response metadata
                post.metadata_json = json.dumps({
                    'buffer_update_id': result.get('id'),
                    'buffer_profile_id': profile_id,
                    'published_via': 'buffer_api',
                    'scheduled_at': result.get('scheduled_at'),
                    'due_at': result.get('due_at')
                })
                
                db.commit()
                
                logger.info(f"Successfully published post {post_id} to {post.platform} via Buffer")
                return {
                    'success': True,
                    'buffer_id': result.get('id'),
                    'message': f'Published to {post.platform} via Buffer'
                }
            else:
                post.status = 'failed'
                post.metadata_json = json.dumps({
                    'error': 'Buffer API failed',
                    'buffer_response': result
                })
                db.commit()
                
                return {
                    'success': False,
                    'error': result.get('message', 'Buffer API error')
                }
                
        except requests.RequestException as e:
            logger.error(f"Buffer API request failed for post {post_id}: {e}")
            
            # Update post status to failed
            if 'post' in locals():
                post.status = 'failed'
                post.metadata_json = json.dumps({
                    'error': f'Buffer API request failed: {str(e)}',
                    'timestamp': iso_utc()
                })
                db.commit()
            
            return {'success': False, 'error': f'Buffer API error: {str(e)}'}
            
        except Exception as e:
            logger.error(f"Unexpected error publishing post {post_id}: {e}")
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
            
        finally:
            db.close()
    
    def batch_publish(self, post_ids: List[int]) -> Dict[str, Any]:
        """Publish multiple posts in batch"""
        results = []
        successful = 0
        failed = 0
        
        for post_id in post_ids:
            result = self.publish_post(post_id)
            results.append({
                'post_id': post_id,
                'result': result
            })
            
            if result['success']:
                successful += 1
            else:
                failed += 1
        
        return {
            'success': True,
            'published': successful,
            'failed': failed,
            'results': results
        }
    
    def get_post_analytics(self, buffer_update_id: str) -> Dict[str, Any]:
        """Get analytics for a published post from Buffer"""
        try:
            response = requests.get(
                f'{self.base_url}/updates/{buffer_update_id}.json',
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'success': True,
                'clicks': data.get('clicks', 0),
                'reach': data.get('reach', 0),
                'comments': data.get('comments', 0),
                'likes': data.get('likes', 0),
                'shares': data.get('shares', 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get Buffer analytics for {buffer_update_id}: {e}")
            return {'success': False, 'error': str(e)}

def test_buffer_connection() -> bool:
    """Test Buffer API connection and credentials"""
    try:
        buffer = BufferAPI()
        if not buffer.access_token:
            logger.warning("Buffer access token not configured")
            return False
            
        profiles = buffer.get_profiles()
        logger.info(f"Buffer connection test successful - {len(profiles)} profiles found")
        return len(profiles) > 0
        
    except Exception as e:
        logger.error(f"Buffer connection test failed: {e}")
        return False

# Example usage and testing
if __name__ == "__main__":
    # Test connection
    if test_buffer_connection():
        print("✅ Buffer API connection successful")
        
        # Test publishing (uncomment to test with real post)
        # buffer = BufferAPI()
        # result = buffer.publish_post(1)  # Replace with actual post ID
        # print(f"Publication result: {result}")
    else:
        print("❌ Buffer API connection failed - check BUFFER_ACCESS_TOKEN")