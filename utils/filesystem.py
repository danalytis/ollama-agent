"""
Safe filesystem operations and directory management
"""

import os
import stat
import platform
from pathlib import Path
from typing import List, Tuple, Optional
from utils.display import rich_print


class DirectoryValidator:
    """Validates directory operations for safety"""
    
    # System directories that should be protected
    SYSTEM_DIRS = {
        'linux': [
            '/bin', '/sbin', '/usr/bin', '/usr/sbin', '/usr/local/bin',
            '/etc', '/proc', '/sys', '/dev', '/boot', '/lib', '/lib64',
            '/opt', '/srv', '/var/log', '/var/run', '/var/lib',
            '/root',  # Root home directory
        ],
        'darwin': [  # macOS
            '/bin', '/sbin', '/usr/bin', '/usr/sbin', '/usr/local/bin',
            '/etc', '/proc', '/sys', '/dev', '/boot', '/lib',
            '/System', '/Library', '/Applications', '/var/log',
            '/var/run', '/var/lib', '/private',
        ],
        'windows': [
            'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)',
            'C:\\ProgramData', 'C:\\System Volume Information',
        ]
    }
    
    # Sensitive directories that require confirmation
    SENSITIVE_DIRS = {
        'linux': [
            '/var', '/usr', '/home', '/mnt', '/media',
        ],
        'darwin': [
            '/var', '/usr', '/Users', '/Volumes',
        ],
        'windows': [
            'C:\\Users', 'C:\\', 'D:\\', 'E:\\',
        ]
    }

    @staticmethod
    def get_system_type() -> str:
        """Get normalized system type"""
        system = platform.system().lower()
        return 'windows' if system == 'windows' else system

    @staticmethod
    def is_system_directory(path: str) -> bool:
        """Check if path is a system directory"""
        abs_path = os.path.abspath(path)
        system_type = DirectoryValidator.get_system_type()
        
        system_dirs = DirectoryValidator.SYSTEM_DIRS.get(system_type, [])
        
        for sys_dir in system_dirs:
            # Check if path is exactly a system directory or within one
            if abs_path == sys_dir or abs_path.startswith(sys_dir + os.sep):
                return True
        
        return False

    @staticmethod
    def is_sensitive_directory(path: str) -> bool:
        """Check if path is a sensitive directory requiring confirmation"""
        abs_path = os.path.abspath(path)
        system_type = DirectoryValidator.get_system_type()
        
        sensitive_dirs = DirectoryValidator.SENSITIVE_DIRS.get(system_type, [])
        
        for sens_dir in sensitive_dirs:
            if abs_path == sens_dir:
                return True
        
        return False

    @staticmethod
    def check_directory_permissions(path: str) -> Tuple[bool, str]:
        """Check if directory has appropriate permissions"""
        try:
            abs_path = os.path.abspath(path)
            
            if not os.path.exists(abs_path):
                return False, f"Directory does not exist: {abs_path}"
            
            if not os.path.isdir(abs_path):
                return False, f"Path is not a directory: {abs_path}"
            
            # Check read permissions
            if not os.access(abs_path, os.R_OK):
                return False, f"No read permission for: {abs_path}"
            
            # Check if we can list directory contents
            try:
                os.listdir(abs_path)
            except PermissionError:
                return False, f"Cannot list directory contents: {abs_path}"
            
            return True, "Directory accessible"
            
        except Exception as e:
            return False, f"Error checking directory: {str(e)}"

    @staticmethod
    def is_within_allowed_paths(path: str, allowed_paths: List[str]) -> bool:
        """Check if path is within allowed base directories"""
        abs_path = os.path.abspath(path)
        
        for allowed in allowed_paths:
            allowed_abs = os.path.abspath(allowed)
            # Check if path is within or exactly matches allowed directory
            if abs_path == allowed_abs or abs_path.startswith(allowed_abs + os.sep):
                return True
        
        return False


def safe_change_directory(target_path: str, safe_mode: bool = True, 
                         allowed_dirs: Optional[List[str]] = None,
                         force: bool = False) -> Tuple[bool, str]:
    """
    Safely change working directory with comprehensive safety checks
    
    Args:
        target_path: Target directory path
        safe_mode: Enable safety restrictions
        allowed_dirs: List of allowed base directories
        force: Skip safety prompts (use with caution)
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Resolve path
        if target_path == "~":
            target_path = os.path.expanduser("~")
        elif target_path.startswith("~/"):
            target_path = os.path.expanduser(target_path)
        
        abs_target = os.path.abspath(target_path)
        
        # Check if directory exists and is accessible
        accessible, access_msg = DirectoryValidator.check_directory_permissions(abs_target)
        if not accessible:
            return False, access_msg
        
        if safe_mode:
            # Check if it's a system directory
            if DirectoryValidator.is_system_directory(abs_target):
                return False, (
                    f"❌ Cannot change to system directory: {abs_target}\n"
                    f"💡 Use --unsafe-mode or /safemode off to override (NOT RECOMMENDED)"
                )
            
            # Check if within allowed directories
            if allowed_dirs and not DirectoryValidator.is_within_allowed_paths(abs_target, allowed_dirs):
                return False, (
                    f"❌ Directory outside allowed paths: {abs_target}\n"
                    f"💡 Allowed base directories: {', '.join(allowed_dirs)}\n"
                    f"💡 Use /allowdir <path> to add directory or /safemode off to disable"
                )
            
            # Check if it's a sensitive directory and needs confirmation
            if not force and DirectoryValidator.is_sensitive_directory(abs_target):
                return False, (
                    f"⚠️  Sensitive directory detected: {abs_target}\n"
                    f"💡 Use /cd --force {target_path} to confirm"
                )
        
        # Perform the directory change
        current_dir = os.getcwd()
        try:
            os.chdir(abs_target)
            return True, f"✅ Changed directory: {current_dir} → {abs_target}"
        except PermissionError:
            return False, f"❌ Permission denied: {abs_target}"
        except FileNotFoundError:
            return False, f"❌ Directory not found: {abs_target}"
        except Exception as e:
            return False, f"❌ Error changing directory: {str(e)}"
    
    except Exception as e:
        return False, f"❌ Unexpected error: {str(e)}"


def get_directory_info(path: str = ".") -> dict:
    """Get comprehensive directory information"""
    try:
        abs_path = os.path.abspath(path)
        stat_info = os.stat(abs_path)
        
        return {
            "path": abs_path,
            "readable": os.access(abs_path, os.R_OK),
            "writable": os.access(abs_path, os.W_OK),
            "executable": os.access(abs_path, os.X_OK),
            "owner_uid": stat_info.st_uid,
            "group_gid": stat_info.st_gid,
            "permissions": oct(stat_info.st_mode)[-3:],
            "is_system": DirectoryValidator.is_system_directory(abs_path),
            "is_sensitive": DirectoryValidator.is_sensitive_directory(abs_path),
        }
    except Exception as e:
        return {"error": str(e)}


def suggest_safe_directories() -> List[str]:
    """Suggest safe directories for development work"""
    suggestions = []
    
    # User home directory
    home = os.path.expanduser("~")
    suggestions.append(home)
    
    # Common development directories
    dev_dirs = [
        os.path.join(home, "projects"),
        os.path.join(home, "workspace"),
        os.path.join(home, "dev"),
        os.path.join(home, "code"),
        os.path.join(home, "Documents"),
        os.path.join(home, "Desktop"),
    ]
    
    for dev_dir in dev_dirs:
        if os.path.exists(dev_dir) and os.access(dev_dir, os.R_OK):
            suggestions.append(dev_dir)
    
    # Temporary directories
    temp_dirs = ["/tmp", "/var/tmp"]
    if platform.system().lower() == "windows":
        temp_dirs = [os.environ.get("TEMP", "C:\\temp")]
    
    for temp_dir in temp_dirs:
        if temp_dir and os.path.exists(temp_dir) and os.access(temp_dir, os.R_OK):
            suggestions.append(temp_dir)
    
    return list(set(suggestions))  # Remove duplicates


def format_directory_safety_info(path: str = ".") -> str:
    """Format directory safety information for display"""
    info = get_directory_info(path)
    
    if "error" in info:
        return f"❌ Error getting directory info: {info['error']}"
    
    safety_status = []
    
    if info["is_system"]:
        safety_status.append("🚨 SYSTEM DIRECTORY")
    elif info["is_sensitive"]:
        safety_status.append("⚠️  SENSITIVE DIRECTORY")
    else:
        safety_status.append("✅ SAFE DIRECTORY")
    
    perms = []
    if info["readable"]:
        perms.append("Read")
    if info["writable"]:
        perms.append("Write")
    if info["executable"]:
        perms.append("Execute")
    
    return f"""📂 Directory: {info['path']}
🔒 Permissions: {'/'.join(perms)} ({info['permissions']})
🛡️  Safety: {' '.join(safety_status)}"""