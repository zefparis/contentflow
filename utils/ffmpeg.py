import os
import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def make_vertical(input_path: str, plan: Dict[str, Any], output_path: str) -> bool:
    """
    Transform video to vertical format (1080x1920) with overlays.
    
    Args:
        input_path: Path to source video
        plan: AI plan with segments, overlays, etc.
        output_path: Path for output video
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(input_path):
            logger.error(f"Input video not found: {input_path}")
            return False
        
        # Extract plan parameters
        segments = plan.get('segments', [{'start': 0, 'end': 30}])
        overlays = plan.get('overlays', {})
        
        # Use first segment for demo
        segment = segments[0] if segments else {'start': 0, 'end': 30}
        start_time = segment.get('start', 0)
        duration = segment.get('end', 30) - start_time
        
        # Build FFmpeg command for vertical transformation
        cmd = [
            'ffmpeg', '-y',  # Overwrite output
            '-i', input_path,
            '-ss', str(start_time),  # Start time
            '-t', str(duration),     # Duration
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            output_path
        ]
        
        logger.info(f"Running FFmpeg: {' '.join(cmd)}")
        
        # Run FFmpeg
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully transformed video: {output_path}")
            return True
        else:
            logger.error(f"FFmpeg failed: {result.stderr}")
            return False
        
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg timeout exceeded")
        return False
    except Exception as e:
        logger.error(f"Error in video transformation: {e}")
        return False


def create_demo_vertical_video(output_path: str) -> bool:
    """
    Create a demo vertical video using FFmpeg test patterns.
    
    This is used when no input video is available.
    """
    try:
        # Create a 30-second vertical video with test pattern
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', 'testsrc2=size=1080x1920:duration=30:rate=30',
            '-f', 'lavfi', 
            '-i', 'sine=frequency=440:duration=30',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '28',
            '-c:a', 'aac',
            '-shortest',
            output_path
        ]
        
        logger.info(f"Creating demo video: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info(f"Created demo video: {output_path}")
            return True
        else:
            logger.error(f"Demo video creation failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Demo video creation timeout")
        return False
    except Exception as e:
        logger.error(f"Error creating demo video: {e}")
        return False


def add_text_overlay(input_path: str, text: str, output_path: str, position: str = "top") -> bool:
    """
    Add text overlay to video.
    
    Args:
        input_path: Source video path
        text: Text to overlay
        output_path: Output path
        position: 'top', 'center', or 'bottom'
    
    Returns:
        True if successful
    """
    try:
        # Position mapping
        positions = {
            'top': 'x=(w-text_w)/2:y=50',
            'center': 'x=(w-text_w)/2:y=(h-text_h)/2',
            'bottom': 'x=(w-text_w)/2:y=h-text_h-50'
        }
        
        pos = positions.get(position, positions['top'])
        
        # Escape text for FFmpeg
        escaped_text = text.replace("'", r"\'").replace(":", r"\:")
        
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vf', f"drawtext=text='{escaped_text}':fontsize=60:fontcolor=white:box=1:boxcolor=black@0.5:{pos}",
            '-c:a', 'copy',
            output_path
        ]
        
        logger.info(f"Adding text overlay: {text}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info(f"Added text overlay: {output_path}")
            return True
        else:
            logger.error(f"Text overlay failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error adding text overlay: {e}")
        return False


def get_video_info(video_path: str) -> Optional[Dict[str, Any]]:
    """
    Get video metadata using FFprobe.
    
    Returns dict with duration, width, height, etc.
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if video_stream:
                return {
                    'duration': float(data.get('format', {}).get('duration', 0)),
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'fps': eval(video_stream.get('r_frame_rate', '30/1')),
                    'codec': video_stream.get('codec_name', 'unknown')
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return None


def is_ffmpeg_available() -> bool:
    """Check if FFmpeg is available on the system."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except:
        return False


def install_ffmpeg_hint() -> str:
    """Return installation hint for FFmpeg."""
    return """
FFmpeg not found. To install:

Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg
macOS: brew install ffmpeg
Windows: Download from https://ffmpeg.org/download.html

Or use the package manager in this environment.
"""